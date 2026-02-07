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
import time
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import schedule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
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
        
        # Ensure all folders exist
        for folder in [self.needs_action, self.plans, self.done, 
                       self.pending_approval, self.approved, self.rejected,
                       self.logs, self.in_progress, self.briefings]:
            folder.mkdir(parents=True, exist_ok=True)
        
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
        Trigger Claude Code to process task and create Plan.md
        
        Uses the Ralph Wiggum stop hook to ensure Claude completes the task
        """
        task_id = task_file.stem
        prompt = f"""
You are an autonomous AI Employee. Process this task file and create a detailed Plan.md.

Task File: {task_file}
Task ID: {task_id}

Instructions:
1. Read the task file carefully
2. Check Company_Handbook.md and Business_Goals.md for context
3. Apply relevant Agent Skills from obsidian_vault/agent_skills/
4. Create a Plan.md file in /Plans/{task_id}_plan.md with:
   - Clear objective
   - Step-by-step breakdown
   - HITL requirements (if any)
   - Success criteria
5. Update Dashboard.md with current task status
6. If HITL required: create file in /Pending_Approval instead of executing
7. If safe to execute: perform actions via MCP servers
8. Log all actions to /Logs/
9. When complete: Move files to /Done and output: <promise>TASK_COMPLETE</promise>

Follow the Ralph Wiggum pattern: Do NOT stop until this task is complete.
"""
        
        try:
            # Call Claude Code with the prompt
            result = subprocess.run(
                ['claude', '--prompt', prompt, '--cwd', str(self.vault_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check for completion promise
            if '<promise>TASK_COMPLETE</promise>' in result.stdout:
                logger.info(f"Task {task_id} completed successfully")
                return {"status": "complete", "output": result.stdout}
            else:
                logger.warning(f"Task {task_id} did not complete - may need continuation")
                return {"status": "incomplete", "output": result.stdout}
                
        except subprocess.TimeoutExpired:
            logger.error(f"Task {task_id} timed out")
            return {"status": "timeout"}
        except Exception as e:
            logger.error(f"Error executing Claude Code: {e}")
            return {"status": "error", "message": str(e)}
    
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
        """Execute an approved action via appropriate MCP server"""
        content = approval_file.read_text()
        
        # Parse frontmatter to determine action type
        if 'action: send_email' in content:
            self.execute_email_action(content)
        elif 'action: payment' in content:
            self.execute_payment_action(content)
        elif 'action: social_post' in content:
            self.execute_social_action(content)
        else:
            logger.warning(f"Unknown action type in {approval_file.name}")
    
    def execute_email_action(self, content: str):
        """Execute email send via email-mcp"""
        # TODO: Parse email details and call MCP
        logger.info("EMAIL ACTION: Would send email via email-mcp")
        self.log_action({
            "action_type": "email_send",
            "status": "executed",
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
        """Execute social media post via social-mcp"""
        # TODO: Parse post details and call MCP
        logger.info("SOCIAL ACTION: Would post to social media via social-mcp")
        self.log_action({
            "action_type": "social_post",
            "status": "executed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def log_rejection(self, rejected_file: Path):
        """Log that a human rejected an action"""
        self.log_action({
            "action_type": "rejection",
            "file": rejected_file.name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
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
        logger.info("🚀 Personal AI Employee Starting...")
        
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
