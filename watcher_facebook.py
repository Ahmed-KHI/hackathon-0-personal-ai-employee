"""
Facebook Watcher - Monitor business activities for Facebook posting opportunities
Part of Personal AI Employee Gold Tier Implementation

Monitors:
1. /Done folder for completed high-value projects
2. Business_Goals.md for milestone achievements
3. Weekly schedule for regular business updates
4. Company news and announcements

Creates tasks in /Needs_Action for Claude to generate Facebook posts
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './obsidian_vault'))
CHECK_INTERVAL = int(os.getenv('FACEBOOK_CHECK_INTERVAL_SECONDS', '3600'))  # 1 hour
LOG_PATH = Path('logs/watcher_facebook.log')

# Setup logging
LOG_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FacebookWatcher')


class FacebookWatcher:
    """Monitor business activities for Facebook posting opportunities"""
    
    def __init__(self, vault_path: Path = VAULT_PATH):
        self.vault_path = vault_path
        self.done_folder = vault_path / "Done"
        self.needs_action = vault_path / "Needs_Action"
        self.business_goals = vault_path / "Business_Goals.md"
        self.handbook = vault_path / "Company_Handbook.md"
        
        # Track what we've already processed
        self.processed_tasks = set()
        self.last_weekly_post = None
        
        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Facebook Watcher initialized. Vault: {vault_path}")
    
    def check_completed_projects(self) -> List[Dict]:
        """Check /Done folder for high-value completed projects to announce"""
        opportunities = []
        
        if not self.done_folder.exists():
            return opportunities
        
        for task_file in self.done_folder.glob("*.md"):
            # Skip if already processed
            if task_file.name in self.processed_tasks:
                continue
            
            try:
                content = task_file.read_text(encoding='utf-8')
                
                # Check if this is a significant project worth announcing
                if self._is_announcement_worthy(content):
                    opportunities.append({
                        'type': 'project_completion',
                        'file': task_file.name,
                        'content_preview': content[:300]
                    })
                    self.processed_tasks.add(task_file.name)
                    logger.info(f"Found Facebook announcement opportunity: {task_file.name}")
            
            except Exception as e:
                logger.error(f"Error reading {task_file}: {e}")
        
        return opportunities
    
    def _is_announcement_worthy(self, content: str) -> bool:
        """Determine if a completed task is worth a Facebook announcement"""
        # Keywords that indicate announcement-worthy projects
        announcement_keywords = [
            'client', 'customer', 'project', 'launch', 'success',
            'milestone', 'achievement', 'award', 'partnership',
            'revenue', 'sales', 'growth', 'expansion', 'new service',
            'testimonial', 'case study', 'results', 'impact'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in announcement_keywords)
    
    def check_business_milestones(self) -> List[Dict]:
        """Check Business_Goals.md for milestone achievements"""
        opportunities = []
        
        if not self.business_goals.exists():
            return opportunities
        
        try:
            content = self.business_goals.read_text(encoding='utf-8')
            
            # Look for recently checked milestones (marked with [x] or ✅)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if ('[x]' in line.lower() or '✅' in line) and 'milestone' in line.lower():
                    opportunities.append({
                        'type': 'milestone_achievement',
                        'content': line.strip(),
                        'context': '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                    })
                    logger.info(f"Found milestone for Facebook: {line.strip()[:50]}")
        
        except Exception as e:
            logger.error(f"Error reading Business_Goals.md: {e}")
        
        return opportunities
    
    def check_weekly_update_schedule(self) -> List[Dict]:
        """Check if it's time for weekly business update (Monday 10 AM)"""
        opportunities = []
        
        now = datetime.now()
        
        # Check if it's Monday between 10 AM and 11 AM
        if now.weekday() == 0 and 10 <= now.hour < 11:
            # Check if we've already posted this week
            if self.last_weekly_post is None or \
               (now - self.last_weekly_post) > timedelta(days=6):
                opportunities.append({
                    'type': 'weekly_business_update',
                    'day': 'Monday',
                    'time': now.strftime('%Y-%m-%d %H:%M')
                })
                self.last_weekly_post = now
                logger.info("Time for weekly Facebook business update")
        
        return opportunities
    
    def create_facebook_task(self, opportunity: Dict):
        """Create task file in /Needs_Action for Claude to generate Facebook post"""
        task_id = f"FACEBOOK_{opportunity['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.needs_action / f"{task_id}.md"
        
        # Build task content
        task_content = f"""---
type: facebook_post
platform: Facebook
opportunity_type: {opportunity['type']}
created: {datetime.now().isoformat()}
priority: medium
status: pending
requires_approval: true
---

# Facebook Posting Opportunity

## Opportunity Type
{opportunity['type'].replace('_', ' ').title()}

## Context
"""
        
        if opportunity['type'] == 'project_completion':
            task_content += f"""
Task completed: {opportunity['file']}
Preview: {opportunity['content_preview']}

## Instructions for AI
1. Read the completed task details from /Done/{opportunity['file']}
2. Review facebook_skills.md for posting guidelines
3. Create engaging Facebook post highlighting:
   - Project achievement
   - Business value delivered
   - Customer impact (if applicable)
   - Call-to-action
4. Use professional yet relatable tone
5. Include relevant hashtags (3-5)
6. Keep within 300-500 characters for optimal engagement
7. Create approval file in /Pending_Approval before posting
"""
        
        elif opportunity['type'] == 'milestone_achievement':
            task_content += f"""
Milestone: {opportunity['content']}
Context: {opportunity['context']}

## Instructions for AI
1. Review Business_Goals.md for full context
2. Review facebook_skills.md for announcement guidelines
3. Create celebratory Facebook post including:
   - Milestone description
   - Team/company achievement
   - Gratitude to customers/team
   - Forward-looking statement
4. Use inspiring and authentic tone
5. Include relevant hashtags
6. Consider adding visual element suggestion
7. Create approval file in /Pending_Approval before posting
"""
        
        elif opportunity['type'] == 'weekly_business_update':
            task_content += f"""
Weekly update scheduled for: {opportunity['day']} {opportunity['time']}

## Instructions for AI
1. Review /Done folder for last week's accomplishments
2. Check Business_Goals.md for progress updates
3. Review Company_Handbook.md for brand voice
4. Create engaging weekly update post including:
   - 2-3 key achievements from past week
   - Current focus areas
   - Behind-the-scenes insight (optional)
   - Community engagement question
5. Use conversational and authentic tone
6. Include company-relevant hashtags
7. Aim for 200-400 characters
8. Create approval file in /Pending_Approval before posting
"""
        
        task_content += """

## Facebook Posting Guidelines
- Review obsidian_vault/agent_skills/facebook_skills.md
- Follow brand voice from Company_Handbook.md
- Ensure HITL approval before posting
- Log all actions to audit trail

## Approval Required
✅ YES - This requires human approval before posting to Facebook
"""
        
        try:
            task_file.write_text(task_content, encoding='utf-8')
            logger.info(f"Created Facebook task: {task_file.name}")
        except Exception as e:
            logger.error(f"Failed to create task file: {e}")
    
    def run_check(self):
        """Run one check cycle"""
        logger.info("=== Facebook Watcher Check Cycle ===")
        
        all_opportunities = []
        
        # Check completed projects
        completed = self.check_completed_projects()
        all_opportunities.extend(completed)
        
        # Check business milestones
        milestones = self.check_business_milestones()
        all_opportunities.extend(milestones)
        
        # Check weekly schedule
        weekly = self.check_weekly_update_schedule()
        all_opportunities.extend(weekly)
        
        # Create tasks for each opportunity
        for opportunity in all_opportunities:
            self.create_facebook_task(opportunity)
        
        if all_opportunities:
            logger.info(f"Found {len(all_opportunities)} Facebook posting opportunities")
        else:
            logger.info("No new Facebook posting opportunities")
        
        logger.info("=== Check Cycle Complete ===\n")
    
    def run(self):
        """Main loop - run checks continuously"""
        logger.info("Facebook Watcher starting...")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        
        while True:
            try:
                self.run_check()
                time.sleep(CHECK_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("Facebook Watcher stopped by user")
                break
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    watcher = FacebookWatcher()
    watcher.run()
