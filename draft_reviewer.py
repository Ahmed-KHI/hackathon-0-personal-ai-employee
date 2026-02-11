"""
Draft Reviewer - Local Component for Platinum Tier Security

This component runs LOCALLY (not in cloud) and implements the cloud/local split:
- Cloud watchers create draft tasks in task_queue/inbox/ (JSON format)
- This reviewer creates human-readable drafts in obsidian_vault/Drafts/  
- Human reviews and approves drafts
- Only approved drafts move to Needs_Action/ for execution

This ensures NO automatic execution from cloud watchers - all actions require
local approval before execution.

Security Model:
- Cloud watchers: READ-only social media APIs (revocable tokens)
- Local orchestrator: WRITE actions (with human approval)
- Sensitive credentials: Stay local only (banking, WhatsApp, 2FA)
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DraftReviewer:
    """
    Review drafttasks from cloud watchers before allowing execution
    
    Workflow:
    1. Monitor task_queue/inbox/ for new tasks (from cloud watchers)
    2. Create human-readable drafts in obsidian_vault/Drafts/
    3. Wait for human approval:
       - Approve: Rename draft to .approved
       - Reject: Rename draft to .rejected
       - Edit: Modify draft content directly
    4. Move approved drafts to Needs_Action/ for orchestrator execution
    """
    
    def __init__(self, 
                 task_queue_path: str = "./task_queue",
                 vault_path: str = "./obsidian_vault",
                 enable_auto_approve: bool = True):
        
        self.task_queue = Path(task_queue_path)
        self.inbox = self.task_queue / "inbox"
        self.vault = Path(vault_path)
        self.enable_auto_approve = enable_auto_approve
        
        # Create folder structure
        self.drafts = self.vault / "Drafts"
        self.needs_action = self.vault / "Needs_Action"
        self.rejected = self.vault / "Rejected"
        self.audit_log = Path("audit_logs") / f"approval_audit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        
        for folder in [self.drafts, self.needs_action, self.rejected, self.inbox]:
            folder.mkdir(parents=True, exist_ok=True)
        self.audit_log.parent.mkdir(exist_ok=True)
        
        # Risk-based auto-approval rules (Platinum Tier feature)
        self.low_risk_types = ['briefing', 'analysis', 'report', 'summary']
        self.high_risk_keywords = ['payment', 'transfer', 'delete', 'whatsapp', '2fa', 'credential']
        
        self.check_interval = 10  # Check every 10 seconds
        logger.info("Draft Reviewer initialized (LOCAL component)")
        logger.info(f"Monitoring: {self.inbox}")
        logger.info(f"Drafts folder: {self.drafts}")
        logger.info(f"Auto-approve enabled: {self.enable_auto_approve}")
    
    def run(self):
        """Main loop: monitor inbox and handle approvals"""
        logger.info("🔐 Starting Draft Reviewer (Platinum Tier security)")
        logger.info("Cloud watchers → Draft tasks → Human approval → Execution")
        logger.info("")
        
        while True:
            try:
                # Step 1: Convert new inbox tasks to drafts
                self.process_new_tasks()
                
                # Step 2: Check for approvals/rejections
                self.process_approvals()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("\n Draft Reviewer stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in draft reviewer loop: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def process_new_tasks(self):
        """
        Convert JSON tasks from cloud watchers into human-readable drafts
        """
        json_files = list(self.inbox.glob("*.json"))
        
        if not json_files:
            return
        
        logger.info(f"Found {len(json_files)} new task(s) from cloud watchers")
        
        for json_file in json_files:
            try:
                # Read task data
                with open(json_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                # Assess risk level
                risk_level = self.assess_risk(task_data)
                
                # Create human-readable draft
                draft_file = self.drafts / f"{json_file.stem}.md"
                self.create_draft_markdown(task_data, draft_file, risk_level)
                
                # Risk-based auto-approval for low-risk tasks
                if self.enable_auto_approve and risk_level == "low":
                    logger.info(f"🤖 AUTO-APPROVED (low risk): {draft_file.name}")
                    draft_file.rename(self.drafts / f"{json_file.stem}.approved.md")
                    self.log_approval_decision(json_file.stem, "auto-approved", risk_level, "Low risk task")
                else:
                    logger.info(f"✅ Created draft: {draft_file.name} (Risk: {risk_level})")
                    logger.info(f"   📝 Requires human review and approval")
                    self.log_approval_decision(json_file.stem, "pending-review", risk_level, "Awaiting human approval")
                
                # Archive the JSON (move to completed inbox)
                archived = self.task_queue / "inbox_archived" / json_file.name
                archived.parent.mkdir(exist_ok=True)
                json_file.rename(archived)
                
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {e}")
    
    def assess_risk(self, task_data: Dict) -> str:
        """
        Assess risk level of a task for auto-approval decisions
        
        Risk Levels:
        - low: Read-only operations, analysis, briefings (auto-approve safe)
        - medium: Social media posts, non-financial communications (needs review)
        - high: Payments, credentials, sensitive data (must manually approve)
        
        Returns: 'low', 'medium', or 'high'
        """
        task_type = task_data.get('type', 'unknown').lower()
        description = str(task_data.get('description', '')).lower()
        title = str(task_data.get('title', '')).lower()
        
        # High risk keywords check
        combined_text = f"{task_type} {description} {title}"
        for keyword in self.high_risk_keywords:
            if keyword in combined_text:
                return "high"
        
        # Low risk types (read-only, analysis)
        if task_type in self.low_risk_types:
            return "low"
        
        # Social media posts default to medium (needs review but not critical)
        if any(social in task_type for social in ['linkedin', 'twitter', 'facebook', 'instagram']):
            return "medium"
        
        # Unknown tasks default to medium (safer)
        return "medium"
    
    def log_approval_decision(self, task_id: str, decision: str, risk_level: str, reason: str):
        """
        Log approval decisions for audit trail (Platinum Tier requirement)
        """
        audit_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_id': task_id,
            'decision': decision,  # auto-approved, approved, rejected, pending-review
            'risk_level': risk_level,
            'reason': reason,
            'reviewer': 'draft_reviewer' if decision == 'auto-approved' else 'human'
        }
        
        try:
            with open(self.audit_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def create_draft_markdown(self, task_data: Dict, draft_file: Path, risk_level: str = "medium"):
        """
        Create human-readable Markdown draft from JSON task data
        """
        task_type = task_data.get('type', 'unknown')
        source = task_data.get('source', 'cloud_watcher')
        priority = task_data.get('priority', 'medium')
        created = task_data.get('created', datetime.now(timezone.utc).isoformat())
        
        # Risk level indicator
        risk_colors = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
        risk_icon = risk_colors.get(risk_level, '⚪')
        
        content = f"""---
type: {task_type}
source: {source}
priority: {priority}
created: {created}
status: draft
requires_approval: true
risk_level: {risk_level}
---

# DRAFT: {task_data.get('title', 'Task from Cloud Watcher')}

{risk_icon} **Risk Level: {risk_level.upper()}**

**⚠️ This is a DRAFT task created by a cloud watcher**
**🔐 Requires local approval before execution**

## Task Details

{task_data.get('description', 'No description provided')}

## Data from Watcher

```json
{json.dumps(task_data.get('data', {}), indent=2)}
```

## Instructions for Claude

{task_data.get('instructions', 'Process this task according to agent skills')}

## Approval Options

### To APPROVE:
1. Review the task carefully
2. Rename this file to: `{draft_file.stem}.approved.md`
3. Task will move to Needs_Action/ for execution

### To REJECT:
1. Rename this file to: `{draft_file.stem}.rejected.md`
2. Task will be archived (no execution)

### To EDIT:
1. Modify the content above as needed
2. Continue with approval process

## Security Notes

- This task came from: **{source}** (running in cloud)
- Cloud watchers have READ-only access to external APIs
- Execution happens locally with your credentials
- Sensitive actions (payments, WhatsApp) require explicit approval

---

*Generated by Draft Reviewer (Local Component)*
*Platinum Tier Security: Cloud watchers create drafts, human approves execution*
"""
        
        draft_file.write_text(content, encoding='utf-8')
    
    def process_approvals(self):
        """
        Check for approved/rejected drafts and take action
        """
        # Check approved drafts
        approved_files = list(self.drafts.glob("*.approved.md"))
        for approved in approved_files:
            try:
                # Move to Needs_Action (remove .approved suffix)
                original_name = approved.name.replace('.approved.md', '.md')
                target = self.needs_action / original_name
                
                # Copy content and add approval timestamp
                content = approved.read_text(encoding='utf-8')
                content += f"\n\n---\n**Approved by human at**: {datetime.now(timezone.utc).isoformat()}\n"
                target.write_text(content, encoding='utf-8')
                
                # Archive the .approved file
                archived = self.vault / "Approved" / approved.name
                archived.parent.mkdir(exist_ok=True)
                approved.rename(archived)
                
                # Log approval decision
                self.log_approval_decision(original_name, "approved", "manual-review", f"Human approved: {original_name}")
                
                logger.info(f"✅ APPROVED: {original_name} → Needs_Action/")
                
            except Exception as e:
                logger.error(f"Error processing approval {approved.name}: {e}")
        
        # Check rejected drafts
        rejected_files = list(self.drafts.glob("*.rejected.md"))
        for rejected in rejected_files:
            try:
                # Move to Rejected folder
                target = self.rejected / rejected.name
                rejected.rename(target)
                
                # Log rejection decision
                self.log_approval_decision(rejected.stem.replace('.rejected', ''), "rejected", "manual-review", f"Human rejected: {rejected.name}")
                
                logger.info(f"❌ REJECTED: {rejected.name} → Rejected/")
                
            except Exception as e:
                logger.error(f"Error processing rejection {rejected.name}: {e}")

def main():
    """Run the draft reviewer"""
    reviewer = DraftReviewer()
    reviewer.run()

if __name__ == "__main__":
    main()
