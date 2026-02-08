"""
Instagram Watcher
Monitors for visual content opportunities to post on Instagram

Triggers:
1. New visual content in obsidian_vault/Done/ (images, product photos, infographics)
2. Business milestones with visual appeal (logo updates, office photos, team wins)
3. Behind-the-scenes moments (work-in-progress, process documentation)
4. Weekly schedule: Tuesday & Thursday 11 AM - 12 PM (optimal posting times)

Task Creation:
Creates tasks in task_queue/inbox/ with Instagram posting instructions
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watcher_instagram.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('instagram_watcher')


class InstagramWatcher:
    """Monitor for Instagram-worthy visual content"""
    
    def __init__(self):
        self.vault_path = Path(os.getenv('VAULT_PATH', './obsidian_vault'))
        self.task_queue = Path('./task_queue/inbox')
        self.task_queue.mkdir(parents=True, exist_ok=True)
        
        self.check_interval = int(os.getenv('INSTAGRAM_CHECK_INTERVAL', '3600'))  # 1 hour
        
        # Track processed items
        self.state_file = Path('./task_queue/.instagram_watcher_state.json')
        self.processed_items = self._load_state()
        
        # Visual keywords for triggering posts
        self.visual_keywords = [
            'photo', 'image', 'picture', 'graphic', 'design',
            'infographic', 'chart', 'diagram', 'screenshot',
            'product', 'showcase', 'gallery', 'visual',
            'before-after', 'comparison', 'result'
        ]
        
        # Behind-the-scenes keywords
        self.bts_keywords = [
            'process', 'workflow', 'workspace', 'setup',
            'tools', 'equipment', 'behind', 'making',
            'development', 'progress', 'work-in-progress', 'wip'
        ]
    
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
                    'processed_items': list(self.processed_items),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def _create_task(self, trigger_type: str, content: Dict[str, Any]):
        """Create Instagram task in inbox"""
        task_id = f"instagram_{trigger_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.task_queue / f"{task_id}.json"
        
        task = {
            'task_id': task_id,
            'task_type': 'instagram_action',
            'trigger': trigger_type,
            'priority': 'medium',
            'created_at': datetime.now().isoformat(),
            'content': content,
            'instructions': self._get_instructions(trigger_type, content)
        }
        
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        logger.info(f"Created Instagram task: {task_id} (trigger: {trigger_type})")
    
    def _get_instructions(self, trigger_type: str, content: Dict[str, Any]) -> str:
        """Generate AI instructions based on trigger type"""
        base = "Review obsidian_vault/agent_skills/instagram_skills.md for posting guidelines."
        
        if trigger_type == 'visual_content':
            return f"""{base}

Task: Post visual content to Instagram

Content: {content.get('item_name')}
Category: {content.get('category', 'Unknown')}
Description: {content.get('description', 'No description')}

Action Steps:
1. Extract image URL or visual asset from content
2. Craft Instagram-optimized caption (125 chars or less for preview)
3. Add relevant hashtags (15-20 hashtags, max 30)
4. Determine if Story or Feed post is more appropriate
5. Check HITL approval requirements (see instagram_skills.md)
6. If approved, use instagram_server.py to post_photo or post_story
7. Log result in audit log

Caption Guidelines:
- Lead with visual hook or key benefit
- Use emojis (2-4 per caption)
- Add call-to-action (tag someone, comment, visit link)
- Keep it authentic and conversational
- Place hashtags at end or in first comment

Visual Requirements:
- Square (1:1) or Vertical (4:5) preferred
- Minimum 1080x1080 pixels
- High contrast and clear subject
- Brand-consistent filters/style
"""
        
        elif trigger_type == 'milestone':
            return f"""{base}

Task: Share business milestone on Instagram

Milestone: {content.get('milestone_text')}
Context: {content.get('context', '')}

Action Steps:
1. Design milestone graphic or find celebratory image
2. Craft celebration caption with story element
3. Tag relevant people/companies if applicable
4. Use milestone hashtags (#milestone #success #achievement)
5. Consider carousel format if multiple images available
6. Get CEO approval (milestone posts require HITL)
7. Post via instagram_server.py
8. Monitor engagement for first hour, respond to comments

Caption Structure:
- Emoji opener (🎉 🚀 ✨)
- What was achieved
- Why it matters
- Thank supporters/team
- Future outlook
- Call-to-action
- Hashtags
"""
        
        elif trigger_type == 'behind_the_scenes':
            return f"""{base}

Task: Share behind-the-scenes content on Instagram

Subject: {content.get('subject')}
Context: {content.get('context', '')}

Action Steps:
1. Select most authentic/candid photo from BTS content
2. Write relatable caption showing process/journey
3. Use BTS and educational hashtags
4. Consider Stories format for ephemeral content
5. Show tools, workspace, or team in action
6. Auto-approve if positive/neutral (see instagram_skills.md)
7. Post and engage with comments

Caption Tone:
- Authentic and human
- Educational value ("Here's how we...")
- Relatable struggles/wins
- Conversational language
- Invite questions/discussion
"""
        
        elif trigger_type == 'weekly_schedule':
            return f"""{base}

Task: Regular Instagram engagement (Tuesday/Thursday posts)

Action Steps:
1. Review recent Business_Goals.md updates for content ideas
2. Check Done/ folder for visual content from past week
3. Plan 2 posts: 1 educational/value-add, 1 personal/BTS
4. Ensure 1:1 or 4:5 aspect ratio for Feed posts
5. Write captions with strong hooks and CTAs
6. Add 15-20 hashtags (mix popular and niche)
7. Post during optimal times (Tue/Thu 11 AM - 12 PM)
8. Monitor and respond to engagement within 1 hour

Content Mix Goals:
- 40% Educational (tips, insights, how-tos)
- 30% Behind-the-Scenes (process, tools, workspace)
- 20% Success Stories (client wins, milestones)
- 10% Personal (team, culture, values)
"""
        
        return f"{base}\n\nTask Type: {trigger_type}\nContent: {json.dumps(content, indent=2)}"
    
    def check_visual_content(self) -> List[Dict]:
        """Check Done folder for visual content"""
        triggers = []
        done_path = self.vault_path / 'Done'
        
        if not done_path.exists():
            return triggers
        
        for item in done_path.iterdir():
            item_key = f"visual_content:{item.name}"
            
            if item_key in self.processed_items:
                continue
            
            # Read item content
            try:
                if item.is_file() and item.suffix == '.md':
                    content = item.read_text(encoding='utf-8').lower()
                    
                    # Check for visual keywords
                    has_visual = any(kw in content for kw in self.visual_keywords)
                    has_bts = any(kw in content for kw in self.bts_keywords)
                    
                    if has_visual or has_bts:
                        triggers.append({
                            'type': 'behind_the_scenes' if has_bts and not has_visual else 'visual_content',
                            'content': {
                                'item_name': item.stem,
                                'item_path': str(item),
                                'category': 'behind_the_scenes' if has_bts else 'visual_showcase',
                                'description': content[:300]
                            },
                            'key': item_key
                        })
            
            except Exception as e:
                logger.warning(f"Could not read {item.name}: {e}")
        
        return triggers
    
    def check_business_milestones(self) -> List[Dict]:
        """Check Business_Goals.md for milestone achievements"""
        triggers = []
        goals_file = self.vault_path / 'Business_Goals.md'
        
        if not goals_file.exists():
            return triggers
        
        try:
            content = goals_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Look for checked milestones
                if ('✅' in line or '[x]' in line.lower()) and i > 0:
                    # Check if visual-worthy milestone
                    visual_worthy = any(kw in line.lower() for kw in [
                        'launch', 'release', 'revenue', 'client', 'award',
                        'partnership', 'growth', 'milestone', 'achievement'
                    ])
                    
                    if visual_worthy:
                        milestone_key = f"milestone:{line[:50]}"
                        
                        if milestone_key not in self.processed_items:
                            triggers.append({
                                'type': 'milestone',
                                'content': {
                                    'milestone_text': line.strip(),
                                    'context': '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                                },
                                'key': milestone_key
                            })
        
        except Exception as e:
            logger.error(f"Could not read Business_Goals.md: {e}")
        
        return triggers
    
    def check_weekly_schedule(self) -> List[Dict]:
        """Check if it's posting time (Tuesday/Thursday 11 AM - 12 PM)"""
        triggers = []
        now = datetime.now()
        
        # Tuesday = 1, Thursday = 3
        if now.weekday() in [1, 3] and 11 <= now.hour < 12:
            schedule_key = f"weekly_schedule:{now.strftime('%Y-%m-%d')}"
            
            if schedule_key not in self.processed_items:
                triggers.append({
                    'type': 'weekly_schedule',
                    'content': {
                        'day': now.strftime('%A'),
                        'time': now.strftime('%I:%M %p'),
                        'week': now.isocalendar()[1]
                    },
                    'key': schedule_key
                })
        
        return triggers
    
    def monitor(self):
        """Main monitoring loop"""
        logger.info("Instagram watcher started")
        logger.info(f"Vault path: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        
        while True:
            try:
                logger.info("Checking for Instagram opportunities...")
                
                all_triggers = []
                all_triggers.extend(self.check_visual_content())
                all_triggers.extend(self.check_business_milestones())
                all_triggers.extend(self.check_weekly_schedule())
                
                for trigger in all_triggers:
                    self._create_task(trigger['type'], trigger['content'])
                    self.processed_items.add(trigger['key'])
                
                if all_triggers:
                    self._save_state()
                    logger.info(f"Created {len(all_triggers)} Instagram tasks")
                else:
                    logger.info("No new Instagram opportunities found")
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            logger.info(f"Sleeping for {self.check_interval}s...")
            time.sleep(self.check_interval)


if __name__ == "__main__":
    watcher = InstagramWatcher()
    watcher.monitor()
