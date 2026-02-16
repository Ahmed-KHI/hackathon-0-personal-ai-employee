"""
Orchestrator - Main Coordination Loop

ARCHITECTURAL RULES:
1. Claim-by-move: Only ONE task in pending/ at a time
2. Only component that writes to Dashboard.md
3. Coordinates watcher → reasoning → action
4. Enforces Ralph Loop protection
5. Manages HITL approvals
6. Updates audit logs
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.audit_logger import get_audit_logger
from orchestration.ralph_loop import get_ralph_loop, RalphLoopException
from orchestration.retry_handler import get_retry_handler, RetryExhausted
from orchestration.llm_interface import get_llm_interface
from orchestration.skill_mapper import get_skill_mapper

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("orchestrator")


class Orchestrator:
    """
    Main orchestrator for the Personal AI Employee.
    
    Responsibilities:
    - Claim tasks from inbox (claim-by-move)
    - Load agent skills
    - Invoke Claude Code for reasoning
    - Execute actions via MCP servers
    - Update Dashboard.md
    - Enforce HITL approvals
    - Track iterations (Ralph Loop)
    - Log all actions (audit trail)
    """
    
    def __init__(self):
        # Paths
        self.vault_path = Path(os.getenv("VAULT_PATH", "./obsidian_vault"))
        self.dashboard_path = Path(os.getenv("DASHBOARD_PATH", self.vault_path / "Dashboard.md"))
        self.task_queue = Path("./task_queue")
        self.inbox = self.task_queue / "inbox"
        self.pending = self.task_queue / "pending"
        self.approvals = self.task_queue / "approvals"
        self.completed = self.task_queue / "completed"
        self.agent_skills_path = self.vault_path / "agent_skills"
        
        # Components
        self.audit_logger = get_audit_logger()
        self.ralph_loop = get_ralph_loop()
        self.retry_handler = get_retry_handler()
        self.llm = get_llm_interface()  # LLM for reasoning (OpenAI or Anthropic)
        self.skill_mapper = get_skill_mapper()  # Auto-detect skills (safety net)
        
        # State
        self.running = False
        self.check_interval = int(os.getenv("TASK_QUEUE_CHECK_INTERVAL", "10"))
        
        # Validate paths
        self._validate_paths()
        
        logger.info("Orchestrator initialized")
    
    def _validate_paths(self) -> None:
        """Ensure all required paths exist."""
        for path in [self.inbox, self.pending, self.approvals, self.completed]:
            path.mkdir(parents=True, exist_ok=True)
        
        if not self.dashboard_path.exists():
            logger.warning(f"Dashboard not found: {self.dashboard_path}")
    
    def claim_task(self) -> Optional[Dict[str, Any]]:
        """
        Claim a task from inbox using claim-by-move.
        
        Returns:
            Task dict if claimed, None if no tasks or pending queue occupied
        """
        # CRITICAL: Only one task in pending at a time
        pending_files = list(self.pending.glob("*.json"))
        if pending_files:
            logger.info("Pending queue occupied. Waiting...")
            return None
        
        # Get tasks from inbox
        inbox_files = sorted(self.inbox.glob("*.json"))
        if not inbox_files:
            return None
        
        # Claim first task (FIFO)
        task_file = inbox_files[0]
        
        try:
            # Read task
            with open(task_file, 'r') as f:
                task = json.load(f)
            
            # Move to pending (claim-by-move)
            dest_file = self.pending / task_file.name
            shutil.move(str(task_file), str(dest_file))
            
            task_id = task.get("task_id")
            
            # Log claim
            self.audit_logger.log(
                action="task_claimed",
                task_id=task_id,
                result="success",
                details={
                    "source": task.get("source"),
                    "type": task.get("type"),
                    "priority": task.get("priority")
                }
            )
            
            logger.info(f"Claimed task: {task_id} | Type: {task.get('type')}")
            
            return task
        
        except Exception as e:
            logger.error(f"Error claiming task: {e}")
            self.audit_logger.log(
                action="task_claim_failed",
                task_id="unknown",
                result="failure",
                error=str(e)
            )
            return None
    
    def load_agent_skills(self, required_skills: list) -> Dict[str, str]:
        """
        Load agent skills from Markdown files.
        
        Args:
            required_skills: List of skill names (without .md)
        
        Returns:
            Dict of skill_name -> skill_content
        """
        skills = {}
        
        for skill_name in required_skills:
            skill_file = self.agent_skills_path / f"{skill_name}.md"
            
            if skill_file.exists():
                with open(skill_file, 'r', encoding='utf-8') as f:
                    skills[skill_name] = f.read()
                logger.info(f"Loaded skill: {skill_name}")
            else:
                logger.warning(f"Skill not found: {skill_name}")
        
        return skills
    
    def process_task(self, task: Dict[str, Any]) -> None:
        """
        Process a task through reasoning → action pipeline.
        
        Args:
            task: Task dict
        """
        task_id = task.get("task_id")
        
        if not task_id:
            logger.error("Task missing task_id, skipping")
            return
        
        try:
            # Track iteration (Ralph Loop protection)
            iteration = self.ralph_loop.track_iteration(task_id)
            
            # CRITICAL: Ensure task has required_skills (auto-detect if missing)
            # Per Hackathon Doc: "All AI functionality should be implemented as Agent Skills"
            task = self.skill_mapper.add_skills_to_task(task)
            
            # Load required skills
            required_skills = task.get("required_skills", [])
            skills = self.load_agent_skills(required_skills)
            
            # Check if HITL required
            if task.get("hitl_required", False):
                self._handle_hitl_approval(task)
                return
            
            # Use LLM for reasoning
            logger.info(f"Processing task {task_id} - Invoking LLM reasoning engine")
            
            reasoning_result = self.llm.reason(
                task=task,
                skills=skills,
                context=self._get_vault_context()
            )
            
            # Log reasoning
            self.audit_logger.log(
                action="llm_reasoning",
                task_id=task_id,
                result="success",
                details={
                    "confidence": reasoning_result.get("confidence"),
                    "actions_planned": len(reasoning_result.get("actions", [])),
                    "requires_approval": reasoning_result.get("requires_approval")
                }
            )
            
            # Check if approval required
            if reasoning_result.get("requires_approval", False):
                task["hitl_required"] = True
                task["reasoning_result"] = reasoning_result
                self._handle_hitl_approval(task)
                return
            
            # Execute actions from LLM plan
            action_results = self._execute_action_plan(task_id, reasoning_result.get("actions", []))
            
            # Mark complete
            result_summary = f"Completed {len(action_results)} actions. Confidence: {reasoning_result.get('confidence', 0)}"
            self._complete_task(task, success=True, result=result_summary)
            
        except RalphLoopException as e:
            logger.error(f"Ralph Loop triggered for {task_id}: {e}")
            self._fail_task(task, str(e))
            self._alert_human(task_id, "ralph_loop_triggered", str(e))
        
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            
            # Try retry
            try:
                self.retry_handler.execute_with_retry(
                    self._retry_process_task,
                    task,
                    task_id=task_id
                )
            except RetryExhausted:
                self._fail_task(task, str(e))
    
    def _retry_process_task(self, task: Dict[str, Any]) -> None:
        """Retry processing a task."""
        # Simple retry logic
        time.sleep(1)
        logger.info(f"Retrying task {task.get('task_id')}")
    
    def _get_vault_context(self) -> str:
        """
        Get relevant context from vault for LLM reasoning.
        
        Returns:
            Concatenated content from Business_Goals and Company_Handbook
        """
        context_parts = []
        
        # Load business goals
        goals_file = self.vault_path / "Business_Goals.md"
        if goals_file.exists():
            with open(goals_file, 'r', encoding='utf-8') as f:
                context_parts.append(f"# Business Goals\n{f.read()}")
        
        # Load company handbook
        handbook_file = self.vault_path / "Company_Handbook.md"
        if handbook_file.exists():
            with open(handbook_file, 'r', encoding='utf-8') as f:
                context_parts.append(f"# Company Handbook\n{f.read()}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def _execute_action_plan(self, task_id: str, actions: list) -> list:
        """
        Execute action plan via MCP servers.
        
        Args:
            task_id: Task identifier
            actions: List of actions from LLM reasoning
        
        Returns:
            List of action results
        """
        results = []
        
        for idx, action in enumerate(actions):
            action_id = f"{task_id}_action_{idx}"
            mcp_server = action.get("mcp_server", "unknown")
            command = action.get("command", "unknown")
            parameters = action.get("parameters", {})
            
            logger.info(f"Executing action {idx+1}/{len(actions)}: {mcp_server}.{command}")
            
            try:
                # BRONZE TIER: MCP servers are stubs
                # In Silver tier, this would use real MCP client
                result = self._execute_mcp_action(mcp_server, command, parameters)
                
                results.append({
                    "action_id": action_id,
                    "mcp_server": mcp_server,
                    "command": command,
                    "status": "success",
                    "result": result
                })
                
                # Log action
                self.audit_logger.log(
                    action=f"mcp_action_{mcp_server}_{command}",
                    task_id=task_id,
                    result="success",
                    details={
                        "action_id": action_id,
                        "parameters": parameters,
                        "result": result
                    }
                )
            
            except Exception as e:
                logger.error(f"Action failed: {mcp_server}.{command} - {e}")
                
                results.append({
                    "action_id": action_id,
                    "mcp_server": mcp_server,
                    "command": command,
                    "status": "failed",
                    "error": str(e)
                })
                
                # Log failure
                self.audit_logger.log(
                    action=f"mcp_action_{mcp_server}_{command}",
                    task_id=task_id,
                    result="failure",
                    error=str(e)
                )
        
        return results
    
    def _execute_mcp_action(self, server: str, command: str, parameters: Dict[str, Any]) -> str:
        """
        Execute action via MCP server.
        
        BRONZE TIER: Returns stub response
        SILVER TIER: Would use real MCP client
        
        Args:
            server: MCP server name
            command: Command to execute
            parameters: Command parameters
        
        Returns:
            Action result
        """
        # BRONZE TIER STUB
        tier = os.getenv("DEPLOYMENT_TIER", "bronze")
        
        if tier == "bronze":
            logger.info(f"[STUB] MCP call: {server}.{command} with {parameters}")
            return f"STUB: Action {server}.{command} would be executed here"
        
        # TODO: Silver tier - implement real MCP client
        # from mcp_client import MCPClient
        # client = MCPClient(server)
        # return client.call(command, parameters)
        
        raise NotImplementedError(f"MCP integration not implemented for tier: {tier}")
    
    def _handle_hitl_approval(self, task: Dict[str, Any]) -> None:
        """Handle task requiring human approval."""
        task_id = task.get("task_id")
        
        if not task_id:
            logger.error("Cannot create HITL approval: task missing task_id")
            return
        
        # Create approval request
        approval_file = self.approvals / f"{task_id}.json"
        
        approval_request = {
            "task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "task_type": task.get("type"),
            "context": task.get("context"),
            "reason": "Task requires human approval",
            "status": "pending"
        }
        
        with open(approval_file, 'w') as f:
            json.dump(approval_request, f, indent=2)
        
        # Move task to approvals
        pending_file = self.pending / f"{task_id}.json"
        if pending_file.exists():
            shutil.move(str(pending_file), str(self.approvals / f"{task_id}_task.json"))
        
        logger.info(f"Task {task_id} requires HITL approval")
        
        self.audit_logger.log(
            action="hitl_approval_requested",
            task_id=task_id,
            result="pending"
        )
    
    def _check_hitl_approvals(self) -> None:
        """
        Check for approved or rejected tasks in approvals directory.
        
        Handles:
        - *.json.approved → Resume task execution
        - *.json.rejected → Mark task as failed
        """
        # Check for approved tasks
        approved_files = list(self.approvals.glob("*.json.approved"))
        
        for approved_file in approved_files:
            task_id = approved_file.stem.replace(".json", "")
            
            logger.info(f"Processing approved task: {task_id}")
            
            # Find the task file
            task_file = self.approvals / f"{task_id}_task.json"
            
            if task_file.exists():
                try:
                    # Load task
                    with open(task_file, 'r') as f:
                        task = json.load(f)
                    
                    # Reset HITL flag so it doesn't loop
                    task["hitl_required"] = False
                    
                    # Move task back to inbox for reprocessing
                    dest_file = self.inbox / f"{task_id}.json"
                    with open(dest_file, 'w') as f:
                        json.dump(task, f, indent=2)
                    
                    # Clean up approval files
                    approved_file.unlink()
                    task_file.unlink()
                    
                    # Log approval
                    self.audit_logger.log(
                        action="hitl_approval_granted",
                        task_id=task_id,
                        result="success",
                        details={"action": "task_moved_to_inbox"}
                    )
                    
                    logger.info(f"Task {task_id} approved and moved to inbox")
                
                except Exception as e:
                    logger.error(f"Error processing approved task {task_id}: {e}")
        
        # Check for rejected tasks
        rejected_files = list(self.approvals.glob("*.json.rejected"))
        
        for rejected_file in rejected_files:
            task_id = rejected_file.stem.replace(".json", "")
            
            logger.info(f"Processing rejected task: {task_id}")
            
            # Find the task file
            task_file = self.approvals / f"{task_id}_task.json"
            
            if task_file.exists():
                try:
                    # Load task
                    with open(task_file, 'r') as f:
                        task = json.load(f)
                    
                    # Mark as rejected and move to completed (failed)
                    task["status"] = "rejected"
                    task["completed_at"] = datetime.now(timezone.utc).isoformat()
                    task["result"] = "Rejected by human approval"
                    
                    # Save to completed
                    completed_file = self.completed / f"{task_id}.json"
                    with open(completed_file, 'w') as f:
                        json.dump(task, f, indent=2)
                    
                    # Clean up approval files
                    rejected_file.unlink()
                    task_file.unlink()
                    
                    # Log rejection
                    self.audit_logger.log(
                        action="hitl_approval_denied",
                        task_id=task_id,
                        result="rejected",
                        details={"reason": "human_rejected"}
                    )
                    
                    logger.info(f"Task {task_id} rejected and moved to completed")
                
                except Exception as e:
                    logger.error(f"Error processing rejected task {task_id}: {e}")
    
    def _cleanup_stuck_tasks(self) -> None:
        """
        Clean up stuck _task.json files in pending directory.
        
        These can occur if tasks are manually moved from approvals
        to pending without proper renaming.
        """
        stuck_files = list(self.pending.glob("*_task.json"))
        
        for stuck_file in stuck_files:
            # Extract task_id (remove _task.json suffix)
            task_id = stuck_file.stem.replace("_task", "")
            
            logger.warning(f"Found stuck _task.json file in pending: {stuck_file.name}")
            
            try:
                # Load task
                with open(stuck_file, 'r') as f:
                    task = json.load(f)
                
                # Check if task is truly stuck (should have been completed)
                # If it has hitl_required=false, it should have completed
                if not task.get("hitl_required", False):
                    logger.info(f"Completing stuck task: {task_id}")
                    self._complete_task(task, success=True, result="Recovered from stuck state")
                else:
                    # Move back to approvals where it belongs
                    logger.info(f"Moving stuck HITL task back to approvals: {task_id}")
                    dest_file = self.approvals / f"{task_id}_task.json"
                    shutil.move(str(stuck_file), str(dest_file))
            
            except Exception as e:
                logger.error(f"Error cleaning up stuck task {task_id}: {e}")
    
    def _complete_task(self, task: Dict[str, Any], success: bool, result: str) -> None:
        """Mark task as complete."""
        task_id = task.get("task_id")
        
        if not task_id:
            logger.error("Cannot complete task: missing task_id")
            return
        
        # Move from pending to completed
        # Check both naming patterns: {task_id}.json and {task_id}_task.json
        pending_file = self.pending / f"{task_id}.json"
        pending_file_alt = self.pending / f"{task_id}_task.json"
        
        # Use whichever file exists
        if pending_file.exists():
            actual_pending_file = pending_file
        elif pending_file_alt.exists():
            actual_pending_file = pending_file_alt
            logger.warning(f"Found task file with _task suffix: {actual_pending_file.name}")
        else:
            logger.error(f"Cannot complete task {task_id}: file not found in pending/")
            return
        
        # Update task with result
        task["status"] = "completed" if success else "failed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["result"] = result
        
        # Save to completed
        completed_file = self.completed / f"{task_id}.json"
        with open(completed_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        # Remove from pending
        actual_pending_file.unlink()
        
        # Reset Ralph Loop counter
        self.ralph_loop.reset_task(task_id)
        
        # Log completion
        self.audit_logger.log(
            action="task_completed",
            task_id=task_id,
            result="success" if success else "failure",
            details={"result": result}
        )
        
        logger.info(f"Task completed: {task_id}")
    
    def _fail_task(self, task: Dict[str, Any], error: str) -> None:
        """Mark task as failed."""
        self._complete_task(task, success=False, result=f"Failed: {error}")
    
    def _alert_human(self, task_id: str, alert_type: str, message: str) -> None:
        """Alert human of critical issue."""
        logger.critical(f"🚨 ALERT: {alert_type} | Task: {task_id} | {message}")
        
        # In production, send email/Slack notification
        # For now, just log
        
        self.audit_logger.log(
            action="human_alert",
            task_id=task_id,
            result="sent",
            details={"alert_type": alert_type, "message": message}
        )
    
    def update_dashboard(self) -> None:
        """
        Update Dashboard.md with current status.
        
        CRITICAL: This is the ONLY place that writes to Dashboard.md
        """
        try:
            # Get task counts
            inbox_count = len(list(self.inbox.glob("*.json")))
            pending_count = len(list(self.pending.glob("*.json")))
            approval_count = len(list(self.approvals.glob("*.json")))
            
            # Get recent completions (last 24h)
            completed_files = sorted(
                self.completed.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:10]
            
            # Build dashboard content
            dashboard = f"""# Dashboard - Personal AI Employee

**Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Status**: {'🟢 Operational' if self.running else '🔴 Stopped'}  
**Active Tasks**: {pending_count}  
**Pending Approvals**: {approval_count}

---

## 📊 Current Status

### Active Task
{self._get_active_task_summary()}

### Today's Activity
- **Tasks in Inbox**: {inbox_count}
- **Tasks in Progress**: {pending_count}
- **Pending Approvals**: {approval_count}
- **Tasks Completed (recent)**: {len(completed_files)}

---

## 📋 Task Queue Status

- **Inbox**: {inbox_count} tasks
- **Pending**: {pending_count} tasks (max: 1)
- **Approvals**: {approval_count} tasks
- **Completed**: {len(completed_files)} tasks (recent)

---

## 🔧 System Health

- **Orchestrator**: {'🟢 Running' if self.running else '🔴 Stopped'}
- **Vault**: {'🟢 Accessible' if self.vault_path.exists() else '🔴 Not found'}
- **Audit Logs**: {'🟢 Active' if Path('./audit_logs').exists() else '🔴 Not configured'}

---

**Schema Version**: 1.0  
**Single-Writer Rule**: Only `orchestration/orchestrator.py` may modify this file.
"""
            
            # Write dashboard
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard)
            
            logger.debug("Dashboard updated")
        
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _get_active_task_summary(self) -> str:
        """Get summary of active task."""
        pending_files = list(self.pending.glob("*.json"))
        
        if not pending_files:
            return "*None - waiting for new tasks*"
        
        try:
            with open(pending_files[0], 'r') as f:
                task = json.load(f)
            
            return f"**{task.get('type')}** (ID: {task.get('task_id')[:8]}...)"
        except:
            return "*Task in progress*"
    
    def start(self) -> None:
        """Start orchestrator main loop."""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        self.running = True
        
        logger.info("🚀 Orchestrator started")
        logger.info(f"Checking task queue every {self.check_interval}s")
        
        try:
            while self.running:
                # Clean up any stuck _task.json files
                self._cleanup_stuck_tasks()
                
                # Check for HITL approvals/rejections
                self._check_hitl_approvals()
                
                # Claim and process tasks
                task = self.claim_task()
                
                if task:
                    self.process_task(task)
                
                # Update dashboard
                self.update_dashboard()
                
                # Wait before next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop orchestrator."""
        if not self.running:
            return
        
        self.running = False
        self.update_dashboard()
        logger.info("Orchestrator stopped")


def main():
    """Run orchestrator standalone."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║      PERSONAL AI EMPLOYEE - ORCHESTRATOR (BRONZE TIER)     ║
    ╚════════════════════════════════════════════════════════════╝
    
    Orchestrator is the main coordination loop.
    It claims tasks, coordinates reasoning, and updates the dashboard.
    
    Press Ctrl+C to stop
    """)
    
    orchestrator = Orchestrator()
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        orchestrator.stop()


if __name__ == "__main__":
    main()
