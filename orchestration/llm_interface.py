"""
LLM Interface - Multi-Provider Reasoning Engine

ARCHITECTURAL RULES:
1. Supports both OpenAI and Anthropic APIs
2. Used ONLY for reasoning (no direct actions)
3. Orchestrator uses this to analyze tasks and plan actions
4. All actions must still go through MCP servers
5. Respects provider selection from .env
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dotenv import load_dotenv

# Import LLM providers (conditional based on availability)
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False

if TYPE_CHECKING:
    from anthropic import Anthropic
    from openai import OpenAI

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

load_dotenv()

logger = logging.getLogger("llm_interface")


class LLMInterface:
    """
    Unified interface for OpenAI and Anthropic LLM APIs.
    
    Responsibilities:
    - Initialize correct provider based on .env configuration
    - Provide unified reasoning interface
    - Handle provider-specific API differences
    - Log all LLM interactions for audit
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.client: Any = None
        self.model: str = ""
        self.max_tokens = int(os.getenv("MAX_LLM_RESPONSE_TOKENS", "2000"))
        
        if self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        logger.info(f"LLM Interface initialized with provider: {self.provider}")
        logger.info(f"Max tokens per response: {self.max_tokens}")
    
    def _init_anthropic(self) -> None:
        """Initialize Anthropic Claude API."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic library not installed. Run: pip install anthropic"
            )
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        logger.info(f"Anthropic initialized with model: {self.model}")
    
    def _init_openai(self) -> None:
        """Initialize OpenAI API."""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Run: pip install openai"
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        # Use budget-friendly gpt-4o-mini by default (60x cheaper than GPT-4 Turbo)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        logger.info(f"OpenAI initialized with model: {self.model}")
    
    def reason(
        self,
        task: Dict[str, Any],
        skills: Dict[str, str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to reason about a task and generate action plan.
        
        Args:
            task: Task dict from task queue
            skills: Agent skills loaded from vault
            context: Optional additional context
        
        Returns:
            Dict with:
                - thought_process: LLM's reasoning
                - actions: List of actions to execute
                - requires_approval: Boolean
                - confidence: Float 0-1
        """
        
        # Build prompt from task and skills
        prompt = self._build_reasoning_prompt(task, skills, context)
        
        try:
            if self.provider == "anthropic":
                return self._reason_anthropic(prompt)
            elif self.provider == "openai":
                return self._reason_openai(prompt)
            else:
                # Should never reach here due to __init__ validation
                raise ValueError(f"Invalid provider: {self.provider}")
        
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return {
                "thought_process": f"Error: {str(e)}",
                "actions": [],
                "requires_approval": True,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _build_reasoning_prompt(
        self,
        task: Dict[str, Any],
        skills: Dict[str, str],
        context: Optional[str]
    ) -> str:
        """Build structured prompt for LLM reasoning."""
        
        # Extract task details
        task_type = task.get("type", "unknown")
        task_data = task.get("data", {})
        priority = task.get("priority", "normal")
        
        # Build skills context
        skills_text = "\n\n".join([
            f"## {name}\n{content}"
            for name, content in skills.items()
        ])
        
        prompt = f"""You are the reasoning engine for a Personal AI Employee system.

Your role is to analyze tasks and generate action plans (NOT execute them).

# Task Details
- **Type**: {task_type}
- **Priority**: {priority}
- **Task ID**: {task.get('task_id')}

# Task Data
{self._format_task_data(task_data)}

# Available Agent Skills
{skills_text if skills else "*No specific skills loaded*"}

# Additional Context
{context if context else "*No additional context*"}

---

# Your Task
Analyze this task and provide:

1. **Thought Process**: Your reasoning about what needs to be done
2. **Action Plan**: Step-by-step actions to accomplish the task
3. **Risk Assessment**: Potential issues or concerns
4. **HITL Required**: Does this need human approval? (true/false)
5. **Confidence**: Your confidence level (0.0 to 1.0)

# Action Format
Actions should be MCP-compatible commands like:
- `email.send` - Send email via email_server
- `calendar.create_event` - Create calendar event
- `browser.navigate` - Navigate to URL
- `slack.post_message` - Post to Slack

# Important Constraints
- You ONLY plan actions, you don't execute them
- All actions must go through MCP servers
- Be specific and detailed in your action plans
- If uncertain, request HITL approval
- Consider security and privacy implications

# Response Format
Provide your response as structured JSON:
```json
{{
  "thought_process": "Your detailed reasoning here",
  "actions": [
    {{
      "mcp_server": "email_server",
      "command": "send",
      "parameters": {{}},
      "description": "What this action does"
    }}
  ],
  "risk_assessment": "Potential risks or concerns",
  "requires_approval": false,
  "confidence": 0.85
}}
```

Now analyze the task and provide your reasoning.
"""
        
        return prompt
    
    def _format_task_data(self, data: Dict[str, Any]) -> str:
        """Format task data for prompt."""
        if not data:
            return "*No data*"
        
        formatted = []
        for key, value in data.items():
            formatted.append(f"- **{key}**: {value}")
        
        return "\n".join(formatted)
    
    def _reason_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Use Anthropic Claude for reasoning."""
        if self.provider != "anthropic" or self.client is None:
            raise ValueError("Anthropic client not initialized")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response text
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text = block.text
                    break
            
            if not response_text:
                raise ValueError("No text content in response")
            
            # Try to parse JSON response
            # Find JSON in response (might be wrapped in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            logger.info(f"Anthropic reasoning complete: {result.get('confidence', 0)}")
            
            return result
        
        except Exception as e:
            logger.error(f"Anthropic reasoning error: {e}")
            raise
    
    def _reason_openai(self, prompt: str) -> Dict[str, Any]:
        """Use OpenAI GPT for reasoning."""
        if self.provider != "openai" or self.client is None:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a reasoning engine for a Personal AI Employee. Analyze tasks and provide structured JSON action plans."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract response
            response_text = response.choices[0].message.content
            
            if not response_text:
                raise ValueError("No content in response")
            
            # Parse JSON
            result = json.loads(response_text)
            
            logger.info(f"OpenAI reasoning complete: {result.get('confidence', 0)}")
            
            return result
        
        except Exception as e:
            logger.error(f"OpenAI reasoning error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test LLM connection with simple prompt."""
        try:
            test_prompt = "Respond with a single word: 'connected'"
            
            if self.provider == "anthropic" and self.client:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": test_prompt}]
                )
                result = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        result = block.text
                        break
            
            elif self.provider == "openai" and self.client:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10
                )
                result = response.choices[0].message.content or ""
            
            else:
                raise ValueError(f"Invalid provider configuration: {self.provider}")
            
            logger.info(f"LLM connection test: {result}")
            return True
        
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False


# Singleton instance
_llm_interface = None


def get_llm_interface() -> LLMInterface:
    """Get singleton LLM interface instance."""
    global _llm_interface
    
    if _llm_interface is None:
        _llm_interface = LLMInterface()
    
    return _llm_interface


if __name__ == "__main__":
    """Test LLM interface."""
    print("Testing LLM Interface...")
    
    llm = get_llm_interface()
    
    if llm.test_connection():
        print(f"✅ {llm.provider.upper()} connection successful")
        
        # Test reasoning
        test_task = {
            "task_id": "test_123",
            "type": "email",
            "data": {
                "from": "boss@company.com",
                "subject": "Urgent: Need report by EOD",
                "body": "Please send the Q4 report today"
            },
            "priority": "high"
        }
        
        test_skills = {
            "email_skills": "# Email Skills\n- Reply professionally\n- Check urgency"
        }
        
        result = llm.reason(test_task, test_skills)
        
        print("\n✅ Reasoning test:")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Actions: {len(result.get('actions', []))}")
        print(f"  Requires Approval: {result.get('requires_approval')}")
    else:
        print(f"❌ {llm.provider.upper()} connection failed")
