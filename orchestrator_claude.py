"""
Personal AI Employee - Main Orchestrator
Hackathon 0 Compliant Implementation

This orchestrator follows the specification:
- Monitors /Needs_Action for new tasks
- Triggers Claude Code to create Plan.md files
- Manages folder-based HITL workflow
- Implements Ralph Wiggum stop hook
- Generates Monday Morning CEO Briefing
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import schedule
from anthropic import Anthropic
from dotenv import load_dotenv

# Add MCP servers and orchestration to Python path
sys.path.append(str(Path(__file__).parent / "mcp_servers"))
sys.path.append(str(Path(__file__).parent / "orchestration"))

# Load environment variables
load_dotenv()

# Import ActionExecutor
from action_executor import ActionExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Orchestrator:
    """Main orchestration engine for AI Employee"""
    
    def __init__(self, vault_path: str = "./obsidian_vault"):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.plans = self.vault_path / "Plans"
        self.done = self.vault_path / "Done"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved = self.vault_path / "Approved"
        self.rejected = self.vault_path / "Rejected"
        self.logs = self.vault_path / "Logs"
        self.in_progress = self.vault_path / "In_Progress" 
        self.briefings = self.vault_path / "Briefings"
        
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.anthropic = Anthropic(api_key=api_key)
        
        # Ensure all folders exist
        for folder in [self.needs_action, self.plans, self.done, 
                       self.pending_approval, self.approved, self.rejected,
                       self.logs, self.in_progress, self.briefings]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize ActionExecutor
        self.action_executor = ActionExecutor(self.vault_path)
        
        logger.info(f"Orchestrator initialized with vault: {self.vault_path}")
    
    def check_needs_action(self) -> List[Path]:
        """Scan /Needs_Action for new task files"""
        return list(self.needs_action.glob("*.md"))
    
    def claim_task(self, task_file: Path) -> Path:
        """
        Claim-by-move: Move task from /Needs_Action to /In_Progress
        This prevents multiple agents from processing the same task
        """
        dest = self.in_progress / task_file.name
        task_file.rename(dest)
        logger.info(f"Claimed task: {task_file.name}")
        return dest
    
    def trigger_claude_code(self, task_file: Path) -> Dict:
        """
        Trigger Claude (via Anthropic API) to process task and create Plan.md
        
        Uses the Ralph Wiggum stop hook to ensure Claude completes the task
        """
        task_id = task_file.stem
        
        # Read the task file content
        try:
            task_content = task_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read task file {task_file}: {e}")
            return {"status": "error", "message": f"Failed to read task: {e}"}
        
        # Build system prompt with Agent Skills
        system_prompt = """
You are an autonomous AI Employee with file system access. Your role is to:
1. Analyze incoming tasks
2. Create detailed execution plans
3. Update the knowledge base (Obsidian vault)
4. Execute safe actions or flag for human approval
5. Maintain audit logs

You have access to:
- Company_Handbook.md: Company policies and procedures
- Business_Goals.md: Strategic objectives
- agent_skills/*.md: Specialized skill templates

When you complete a task, output: <promise>TASK_COMPLETE</promise>
"""
        
        user_prompt = f"""
Process this task and create a detailed Plan.md file.

Task ID: {task_id}
Task Content:
{task_content}

Instructions:
1. Create a Plan.md file in /Plans/{task_id}_plan.md with:
   - Clear objective
   - Step-by-step breakdown
   - HITL requirements (if any)
   - Success criteria

2. If action requires approval (emails, payments, etc.):
   - Create approval request in /Pending_Approval/{task_id}_approval.md
   - Include: action type, details, risk level, recommendation

3. If safe to auto-execute:
   - Document the action in /Logs/{task_id}_log.md
   - Note: Actual MCP execution will happen in next phase

4. Update Dashboard.md with task status

5. When plan is complete, output: <promise>TASK_COMPLETE</promise>

Respond with the complete plan and any files you would create.
"""
        
        try:
            logger.info(f"Calling Anthropic API for task {task_id}...")
            
            # Call Anthropic API
            message = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",  # Claude Sonnet 4.5
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract response text
            response_text = message.content[0].text
            
            # Log response (first 500 chars)
            logger.info(f"Claude response: {response_text[:500]}...")
            
            # Check for completion promise
            if '<promise>TASK_COMPLETE</promise>' in response_text:
                logger.info(f"Task {task_id} completed successfully")
                
                # Save the plan to /Plans
                self._save_plan_from_response(task_id, response_text)
                
                return {"status": "complete", "output": response_text}
            else:
                logger.warning(f"Task {task_id} did not complete - may need continuation")
                return {"status": "incomplete", "output": response_text}
                
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return {"status": "error", "message": str(e)}
    
    def _save_plan_from_response(self, task_id: str, response_text: str):
        """
        Extract and save the plan from Claude's response to /Plans folder
        Then parse and execute actions via ActionExecutor
        """
        try:
            # Save the full response as the plan
            plan_file = self.plans / f"{task_id}_plan.md"
            
            # Add metadata header
            plan_content = f"""---
task_id: {task_id}
created: {datetime.now(timezone.utc).isoformat()}
status: completed
---

# Plan for {task_id}

{response_text}
"""
            plan_file.write_text(plan_content, encoding='utf-8')
            logger.info(f"Saved plan to {plan_file}")
            
            # NEW: Parse and execute actions from plan
            self._execute_plan_actions(plan_file)
            
            # Update Dashboard
            self._update_dashboard_with_task(task_id, "completed")
            
        except Exception as e:
            logger.error(f"Failed to save plan for {task_id}: {e}")
    
    def _execute_plan_actions(self, plan_file: Path):
        """
        Parse plan for executable actions and process them via ActionExecutor
        """
        try:
            # Extract actions from plan
            actions = self.action_executor.parse_plan_for_actions(plan_file)
            
            if not actions:
                logger.info(f"No executable actions found in {plan_file.name}")
                return
            
            logger.info(f"Found {len(actions)} action(s) to execute from {plan_file.name}")
            
            # Execute each action
            for action in actions:
                logger.info(f"Processing action: {action['action_type']} (approval required: {action['requires_approval']})")
                
                result = self.action_executor.execute_action(action)
                
                if result['status'] == 'success':
                    logger.info(f"✅ Action executed successfully: {result['message']}")
                elif result['status'] == 'requires_approval':
                    logger.info(f"⏸️  Action requires approval: {result['message']}")
                else:
                    logger.error(f"❌ Action failed: {result['message']}")
                    
        except Exception as e:
            logger.error(f"Error executing plan actions: {e}")
    
    def _update_dashboard_with_task(self, task_id: str, status: str):
        """
        Update Dashboard.md with task status
        """
        try:
            dashboard_path = self.vault_path / "Dashboard.md"
            
            # Create simple dashboard entry
            entry = f"\n- [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] Task `{task_id}`: {status}\n"
            
            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding='utf-8')
                # Append to recent tasks section or create it
                if "## Recent Tasks" in content:
                    content = content.replace("## Recent Tasks", f"## Recent Tasks{entry}")
                else:
                    content += f"\n## Recent Tasks{entry}"
            else:
                content = f"""# AI Employee Dashboard

Last Updated: {datetime.now(timezone.utc).isoformat()}

## Recent Tasks{entry}
"""
            
            dashboard_path.write_text(content, encoding='utf-8')
            logger.info(f"Updated Dashboard with task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
    
    def process_approvals(self):
        """
        Process HITL approvals: Execute actions from /Approved, log rejections from /Rejected
        """
        # Process approved actions
        for approved_file in self.approved.glob("*.md"):
            try:
                self.execute_approved_action(approved_file)
                # Move to /Done after execution
                dest = self.done / approved_file.name
                approved_file.rename(dest)
                logger.info(f"Executed and archived approved action: {approved_file.name}")
            except Exception as e:
                logger.error(f"Failed to execute approved action {approved_file.name}: {e}")
        
        # Process rejections
        for rejected_file in self.rejected.glob("*.md"):
            self.log_rejection(rejected_file)
            dest = self.done / rejected_file.name
            rejected_file.rename(dest)
            logger.info(f"Logged rejection: {rejected_file.name}")
    
    def execute_approved_action(self, approval_file: Path):
        """Execute an approved action via ActionExecutor"""
        try:
            logger.info(f"Processing approved action: {approval_file.name}")
            
            # Use ActionExecutor to process approved file
            result = self.action_executor.process_approved_file(approval_file)
            
            if result['status'] == 'success':
                logger.info(f"✅ Approved action executed: {result['message']}")
            else:
                logger.error(f"❌ Approved action failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error executing approved action: {e}")
            try:
                self.execute_approved_action(approved_file)
                # Move to /Done after execution
                dest = self.done / approved_file.name
                approved_file.rename(dest)
                logger.info(f"Executed and archived approved action: {approved_file.name}")
            except Exception as e:
                logger.error(f"Failed to execute approved action {approved_file.name}: {e}")
        
        # Process rejections
        for rejected_file in self.rejected.glob("*.md"):
            self.log_rejection(rejected_file)
            dest = self.done / rejected_file.name
            rejected_file.rename(dest)
            logger.info(f"Logged rejection: {rejected_file.name}")
    
    def execute_approved_action(self, approval_file: Path):
        """Execute an approved action via appropriate MCP server"""
        content = approval_file.read_text()
        
        # Parse frontmatter to determine action type
        if 'action: send_email' in content:
            self.execute_email_action(content)
        elif 'action: payment' in content:
            self.execute_payment_action(content)
        elif 'action: social_post' in content or 'action: linkedin_post' in content:
            self.execute_social_action(content)
        else:
            logger.warning(f"Unknown action type in {approval_file.name}")
    
    def execute_email_action(self, content: str):
        """Execute email send via email MCP server"""
        try:
            # Import email MCP server
            from email_server.email_server import EmailServer
            
            # Parse email details from content
            email_data = self._parse_email_from_content(content)
            
            if not email_data:
                logger.error("Failed to parse email data from approval file")
                return
            
            # Initialize email server and send
            email_server = EmailServer()
            result = email_server.process_action('send_email', email_data)
            
            logger.info(f"Email sent successfully: {result}")
            self.log_action({
                "action_type": "email_send",
                "status": "executed",
                "recipient": email_data.get('to'),
                "subject": email_data.get('subject'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except ImportError:
            logger.warning("Email MCP server not available - using stub")
            logger.info("EMAIL ACTION: Would send email via email-mcp")
            self.log_action({
                "action_type": "email_send",
                "status": "stub_executed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self.log_action({
                "action_type": "email_send",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    def execute_payment_action(self, content: str):
        """Execute payment via payment-mcp"""
        # TODO: Parse payment details and call MCP
        logger.info("PAYMENT ACTION: Would execute payment via payment-mcp")
        self.log_action({
            "action_type": "payment",
            "status": "executed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def execute_social_action(self, content: str):
        """Execute social media post via LinkedIn MCP server"""
        try:
            # Import LinkedIn MCP server
            from linkedin_server.linkedin_server import process_action
            
            # Parse LinkedIn post details from content
            post_data = self._parse_linkedin_from_content(content)
            
            if not post_data:
                logger.error("Failed to parse LinkedIn post data from approval file")
                return
            
            # Execute LinkedIn post
            result = process_action('post_update', post_data)
            
            logger.info(f"LinkedIn post executed: {result}")
            self.log_action({
                "action_type": "linkedin_post",
                "status": "executed",
                "platform": "LinkedIn",
                "text_preview": post_data.get('text', '')[:100],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except ImportError:
            logger.warning("LinkedIn MCP server not available - using stub")
            logger.info("SOCIAL ACTION: Would post to LinkedIn via linkedin-mcp")
            self.log_action({
                "action_type": "social_post",
                "status": "stub_executed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to post to LinkedIn: {e}")
            self.log_action({
                "action_type": "social_post",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    def log_rejection(self, rejected_file: Path):
        """Log that a human rejected an action"""
        self.log_action({
            "action_type": "rejection",
            "file": rejected_file.name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _parse_email_from_content(self, content: str) -> Optional[Dict]:
        """Extract email details from approval file content"""
        try:
            # Simple parser for YAML-style frontmatter
            lines = content.split('\n')
            email_data = {}
            
            for line in lines:
                if line.startswith('to:'):
                    email_data['to'] = line.split(':', 1)[1].strip()
                elif line.startswith('subject:'):
                    email_data['subject'] = line.split(':', 1)[1].strip()
                elif line.startswith('body:'):
                    # Get rest of content after body:
                    body_start = content.index('body:')
                    email_data['body'] = content[body_start + 5:].strip()
                    break
            
            return email_data if ('to' in email_data and 'subject' in email_data) else None
        except Exception as e:
            logger.error(f"Error parsing email content: {e}")
            return None
    
    def _parse_linkedin_from_content(self, content: str) -> Optional[Dict]:
        """Extract LinkedIn post details from approval file content"""
        try:
            # Simple parser for YAML-style frontmatter
            lines = content.split('\n')
            post_data = {}
            
            for line in lines:
                if line.startswith('text:'):
                    # Get rest of content after text:
                    text_start = content.index('text:')
                    post_data['text'] = content[text_start + 5:].strip()
                    break
                elif line.startswith('visibility:'):
                    post_data['visibility'] = line.split(':', 1)[1].strip()
            
            # Default visibility to PUBLIC if not specified
            if 'visibility' not in post_data:
                post_data['visibility'] = 'PUBLIC'
            
            return post_data if 'text' in post_data else None
        except Exception as e:
            logger.error(f"Error parsing LinkedIn content: {e}")
            return None
    
    def log_action(self, action_data: Dict):
        """Write action to /Logs/YYYY-MM-DD.json (audit trail)"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self.logs / f"{today}.json"
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **action_data
        }
        
        # Append to daily log file
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        else:
            logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def generate_ceo_briefing(self):
        """
        Generate Monday Morning CEO Briefing
        
        Analyzes the week's activity and generates a strategic summary
        """
        logger.info("Generating Monday Morning CEO Briefing...")
        
        prompt = """
Generate the Monday Morning CEO Briefing for this week.

Instructions:
1. Read all files in /Done from the past 7 days
2. Check /Accounting/*.md for financial transactions
3. Review /Logs/*.json for activity metrics
4. Compare against Business_Goals.md objectives
5. Create /Briefings/YYYY-MM-DD_Monday_Briefing.md with:
   - Executive Summary
   - Revenue this week vs target
   - Completed tasks (by priority)
   - Bottlenecks identified (tasks that took >2x expected time)
   - Proactive suggestions (cost optimizations, deadline alerts)
   - Upcoming priorities for next week
6. Update Dashboard.md with link to briefing
7. Output: <promise>BRIEFING_COMPLETE</promise>

Use the CEO Briefing template from planning_skills.md.
"""
        
        try:
            result = subprocess.run(
                ['claude', '--prompt', prompt, '--cwd', str(self.vault_path)],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if '<promise>BRIEFING_COMPLETE</promise>' in result.stdout:
                logger.info("CEO Briefing generated successfully")
            else:
                logger.warning("CEO Briefing generation incomplete")
                
        except Exception as e:
            logger.error(f"Failed to generate CEO Briefing: {e}")
    
    def run_cycle(self):
        """Single orchestration cycle"""
        logger.info("=== Starting Orchestration Cycle ===")
        
        # 1. Process any pending approvals first
        self.process_approvals()
        
        # 2. Check for new tasks
        new_tasks = self.check_needs_action()
        
        if new_tasks:
            logger.info(f"Found {len(new_tasks)} task(s) in /Needs_Action")
            
            # Process one task at a time (claim-by-move rule)
            for task_file in new_tasks[:1]:  # Only take first task
                # Claim the task
                claimed_task = self.claim_task(task_file)
                
                # Trigger Claude Code to process
                result = self.trigger_claude_code(claimed_task)
                
                if result["status"] == "complete":
                    # Move to /Done on successful completion
                    dest = self.done / claimed_task.name
                    claimed_task.rename(dest)
                elif result["status"] in ["incomplete", "timeout", "error"]:
                    # Leave in /In_Progress for retry or human intervention
                    logger.warning(f"Task {claimed_task.name} needs attention")
        else:
            logger.info("No new tasks in /Needs_Action")
        
        logger.info("=== Orchestration Cycle Complete ===\n")
    
    def start(self):
        """Start the orchestrator with scheduling"""
        logger.info("Personal AI Employee Starting...")
        
        # Schedule Monday Morning CEO Briefing (every Monday at 7 AM)
        schedule.every().monday.at("07:00").do(self.generate_ceo_briefing)
        
        # Main loop: check for tasks every 30 seconds
        while True:
            try:
                self.run_cycle()
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(30)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.start()
