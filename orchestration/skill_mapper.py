"""
Skill Mapper - Auto-detect required skills for tasks

ARCHITECTURAL RULE:
This is a SAFETY NET. Watchers SHOULD specify required_skills,
but this mapper ensures Claude always has access to relevant skills
even if watchers forget.

Per Hackathon Doc Section 2B: "All AI functionality should be 
implemented as Agent Skills" - This ensures that happens.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger("skill_mapper")


# SKILL MAPPING - Maps task types to required skills
TASK_TYPE_TO_SKILLS = {
    # Email tasks
    "email": ["email_skills", "approval_skills", "planning_skills"],
    "email_triage": ["email_skills", "approval_skills"],
    "email_response": ["email_skills", "approval_skills"],
    
    # Social media tasks
    "twitter_action": ["twitter_skills", "social_skills", "approval_skills", "planning_skills"],
    "linkedin_post": ["linkedin_skills", "social_skills", "approval_skills", "planning_skills"],
    "facebook_action": ["facebook_skills", "social_skills", "approval_skills", "planning_skills"],
    "instagram_action": ["instagram_skills", "social_skills", "approval_skills", "planning_skills"],
    
    # Accounting/Finance tasks
    "odoo_action": ["odoo_skills", "finance_skills", "approval_skills", "planning_skills"],
    "invoice": ["odoo_skills", "finance_skills", "approval_skills"],
    "payment": ["finance_skills", "approval_skills"],
    "accounting": ["odoo_skills", "finance_skills", "approval_skills"],
    
    # File processing
    "file_process": ["planning_skills", "approval_skills"],
    "file_drop": ["planning_skills", "approval_skills"],
    
    # Generic/Planning
    "generic": ["planning_skills", "approval_skills"],
    "planning": ["planning_skills"],
}

# TRIGGER-SPECIFIC SKILLS - More granular mapping based on trigger type
TRIGGER_TO_SKILLS = {
    # Twitter triggers
    "breaking_news": ["twitter_skills", "social_skills", "approval_skills"],
    "quick_win": ["twitter_skills", "social_skills"],
    "insight": ["twitter_skills", "social_skills"],
    
    # Odoo triggers
    "create_invoice": ["odoo_skills", "finance_skills", "approval_skills"],
    "payment_received": ["odoo_skills", "finance_skills"],
    "invoice_due": ["odoo_skills", "finance_skills", "approval_skills"],
    
    # General triggers
    "project_completion": ["planning_skills", "social_skills"],
    "milestone_achievement": ["planning_skills", "social_skills"],
}


class SkillMapper:
    """Auto-detect and map required skills for tasks"""
    
    def __init__(self):
        logger.info("SkillMapper initialized - providing skill safety net")
    
    def get_required_skills(self, task: Dict[str, Any]) -> List[str]:
        """
        Determine required skills for a task.
        
        Priority:
        1. Use task['required_skills'] if present (watcher specified)
        2. Map from task_type
        3. Map from trigger
        4. Fall back to planning_skills
        
        Args:
            task: Task dict
        
        Returns:
            List of skill names (without .md extension)
        """
        # Priority 1: Respect watcher's explicit skill list
        if "required_skills" in task and task["required_skills"]:
            skills = task["required_skills"]
            logger.info(f"Using watcher-specified skills: {skills}")
            return skills
        
        skills_set = set()
        
        # Priority 2: Map from task_type
        task_type = task.get("task_type") or task.get("type") or "generic"
        if task_type in TASK_TYPE_TO_SKILLS:
            skills_set.update(TASK_TYPE_TO_SKILLS[task_type])
            logger.info(f"Mapped task_type '{task_type}' to skills: {TASK_TYPE_TO_SKILLS[task_type]}")
        
        # Priority 3: Map from trigger
        trigger = task.get("trigger")
        if trigger and trigger in TRIGGER_TO_SKILLS:
            skills_set.update(TRIGGER_TO_SKILLS[trigger])
            logger.info(f"Mapped trigger '{trigger}' to skills: {TRIGGER_TO_SKILLS[trigger]}")
        
        # Priority 4: Fallback
        if not skills_set:
            skills_set.add("planning_skills")
            skills_set.add("approval_skills")
            logger.warning(f"No skill mapping found for task {task.get('task_id')}, using fallback")
        
        return list(skills_set)
    
    def add_skills_to_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add required_skills to task if missing.
        DOES NOT MODIFY if already present.
        
        Args:
            task: Task dict
        
        Returns:
            Task dict with required_skills added
        """
        if "required_skills" not in task or not task["required_skills"]:
            task["required_skills"] = self.get_required_skills(task)
            logger.info(f"Auto-added skills to task {task.get('task_id')}: {task['required_skills']}")
        
        return task


def get_skill_mapper() -> SkillMapper:
    """Get singleton SkillMapper instance"""
    return SkillMapper()
