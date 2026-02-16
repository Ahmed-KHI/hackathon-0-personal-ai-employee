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
        self.task_queue = Path('./task_queue/inbox')
        self.business_goals = vault_path / "Business_Goals.md"
        self.handbook = vault_path / "Company_Handbook.md"
        
        # Track what we've already processed
        self.state_file = Path('./task_queue/.facebook_watcher_state.json')
        self.processed_tasks = self._load_state()
        self.last_weekly_post = None
        
        # Ensure folders exist
        self.task_queue.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Facebook Watcher initialized. Vault: {vault_path}")
    
    def _load_state(self) -> set:
        """Load processed items from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_items', []))
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return set()
    
    def _save_state(self):
        """Save processed items to state file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'processed_items': list(self.processed_tasks),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
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
                    # Create unique key for this milestone
                    milestone_key = f"milestone:{line[:50]}"
                    
                    # Skip if already processed
                    if milestone_key in self.processed_tasks:
                        continue
                    
                    opportunities.append({
                        'type': 'milestone_achievement',
                        'content': line.strip(),
                        'context': '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                    })
                    self.processed_tasks.add(milestone_key)
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
        """Create JSON task file in task_queue/inbox for Claude to generate Facebook post"""
        task_id = f"facebook_{opportunity['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.task_queue / f"{task_id}.json"
        
        # Build instructions based on opportunity type
        if opportunity['type'] == 'project_completion':
            instructions = f"""Review obsidian_vault/agent_skills/facebook_skills.md for posting guidelines.

Task: Announce project completion on Facebook

Project: {opportunity['file']}
Preview: {opportunity['content_preview']}

Action Steps:
1. Read full project details from /Done/{opportunity['file']}
2. Create engaging Facebook post highlighting:
   - Project achievement and outcome
   - Business value delivered
   - Customer impact (if applicable)
   - Call-to-action (contact, learn more, etc.)
3. Use professional yet relatable tone
4. Include relevant hashtags (3-5)
5. Keep within 300-500 characters for optimal engagement
6. Requires HITL approval before posting (see facebook_skills.md)
7. Post via facebook_server.py post_message
8. Log result in audit trail

Post Tone:
- Professional but approachable
- Emphasize value and impact
- Gratitude to team/client where appropriate
- Forward-looking statement
- Community engagement element
"""
            content = {
                'project_file': opportunity['file'],
                'content_preview': opportunity['content_preview']
            }
        
        elif opportunity['type'] == 'milestone_achievement':
            instructions = f"""Review obsidian_vault/agent_skills/facebook_skills.md for posting guidelines.

Task: Celebrate business milestone on Facebook

Milestone: {opportunity['content']}
Context: {opportunity['context']}

Action Steps:
1. Review Business_Goals.md for full milestone context
2. Create celebratory Facebook post including:
   - Milestone description (what was achieved)
   - Why it matters (impact/significance)
   - Team/company acknowledgment
   - Gratitude to customers/partners/team
   - Forward-looking statement (what's next)
3. Use inspiring and authen authentic tone (not boastful)
4. Include milestone hashtags (#milestone #achievement #growth)
5. Consider suggesting visual element (graphic, photo)
6. Requires CEO approval (milestone posts require HITL)
7. Post via facebook_server.py
8. Monitor and respond to engagement

Post Tone:
- Celebratory but humble
- Grateful and inclusive
- Inspiring and authentic
- Community-focused
"""
            content = {
                'milestone': opportunity['content'],
                'milestone_context': opportunity['context']
            }
        
        elif opportunity['type'] == 'weekly_business_update':
            instructions = f"""Review obsidian_vault/agent_skills/facebook_skills.md for posting guidelines.

Task: Share weekly business update on Facebook

Scheduled: {opportunity['day']} {opportunity['time']}

Action Steps:
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
8. Requires approval before posting (see facebook_skills.md)
9. Post via facebook_server.py

Post Guidelines:
- Start with hook ("This week we..." or "Just wrapped...")
- Highlight 2-3 specific wins (not vague)
- Show personality/culture
- Ask engagement question
- Use 1-2 emojis (not excessive)
"""
            content = {
                'update_day': opportunity['day'],
                'update_time': opportunity['time']
            }
        
        else:
            instructions = f"Unknown Facebook opportunity type: {opportunity['type']}"
            content = opportunity
        
        # Create JSON task
        task = {
            'task_id': task_id,
            'task_type': 'facebook_action',
            'trigger': opportunity['type'],
            'priority': 'medium',
            'created_at': datetime.now().isoformat(),
            'content': content,
            'instructions': instructions,
            'requires_approval': True,
            'required_skills': ['facebook_skills', 'social_skills', 'approval_skills', 'planning_skills']
        }
        
        try:
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            logger.info(f"Created Facebook task: {task_id} (trigger: {opportunity['type']})")
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
            self._save_state()
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
