"""
Twitter (X) Watcher
Monitors for timely news and quick updates to post on Twitter

Triggers:
1. Breaking business updates in Business_Goals.md (new achievements marked ✅)
2. Timely industry insights or commentary opportunities
3. Quick wins in Done/ folder (rapid turnaround announcements)
4. Weekly schedule: Monday, Wednesday, Friday 10 AM - 11 AM (peak engagement)

Task Creation:
Creates tasks in task_queue/inbox/ with Twitter posting instructions
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
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
        logging.FileHandler('logs/watcher_twitter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('twitter_watcher')


class TwitterWatcher:
    """Monitor for Twitter-worthy timely updates"""
    
    def __init__(self):
        self.vault_path = Path(os.getenv('VAULT_PATH', './obsidian_vault'))
        self.task_queue = Path('./task_queue/inbox')
        self.task_queue.mkdir(parents=True, exist_ok=True)
        
        self.check_interval = int(os.getenv('TWITTER_CHECK_INTERVAL', '1800'))  # 30 minutes
        
        # Track processed items
        self.state_file = Path('./task_queue/.twitter_watcher_state.json')
        self.processed_items = self._load_state()
        
        # Track recent tweets to avoid over-posting
        self.recent_tweets_file = Path('./task_queue/.twitter_recent.json')
        self.recent_tweets = self._load_recent_tweets()
        
        # Timely/breaking news keywords
        self.breaking_keywords = [
            'breaking', 'just', 'now', 'today', 'urgent',
            'announcement', 'launch', 'new', 'update',
            'milestone', 'achieved', 'completed', 'won',
            'partnership', 'deal', 'client', 'revenue'
        ]
        
        # Industry insight keywords
        self.insight_keywords = [
            'insight', 'lesson', 'learned', 'tip',
            'strategy', 'approach', 'method', 'technique',
            'analysis', 'trend', 'observation'
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
    
    def _load_recent_tweets(self) -> List[Dict]:
        """Load recent tweets from tracking file"""
        if self.recent_tweets_file.exists():
            try:
                with open(self.recent_tweets_file, 'r') as f:
                    data = json.load(f)
                    # Filter tweets from last 24 hours
                    cutoff = datetime.now() - timedelta(hours=24)
                    recent = [
                        t for t in data.get('tweets', [])
                        if datetime.fromisoformat(t['timestamp']) > cutoff
                    ]
                    return recent
            except Exception as e:
                logger.warning(f"Could not load recent tweets: {e}")
        return []
    
    def _track_tweet(self, tweet_type: str, content_key: str):
        """Track a tweet to prevent over-posting"""
        tweet_record = {
            'type': tweet_type,
            'content_key': content_key,
            'timestamp': datetime.now().isoformat()
        }
        
        self.recent_tweets.append(tweet_record)
        
        # Save to file
        try:
            with open(self.recent_tweets_file, 'w') as f:
                json.dump({
                    'tweets': self.recent_tweets,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save recent tweets: {e}")
    
    def _check_rate_limit(self, tweet_type: str) -> bool:
        """Check if we're within posting rate limits"""
        # Count tweets by type in last 24 hours
        type_count = sum(1 for t in self.recent_tweets if t['type'] == tweet_type)
        
        # Rate limits by type
        limits = {
            'breaking_news': 3,  # Max 3 breaking news tweets per day
            'quick_win': 5,      # Max 5 quick win tweets per day
            'insight': 3,        # Max 3 insight tweets per day
            'weekly_schedule': 1 # Max 1 scheduled tweet per day
        }
        
        limit = limits.get(tweet_type, 10)
        
        if type_count >= limit:
            logger.info(f"Rate limit reached for {tweet_type}: {type_count}/{limit}")
            return False
        
        return True
    
    def _create_task(self, trigger_type: str, content: Dict[str, Any]):
        """Create Twitter task in inbox"""
        task_id = f"twitter_{trigger_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.task_queue / f"{task_id}.json"
        
        task = {
            'task_id': task_id,
            'task_type': 'twitter_action',
            'trigger': trigger_type,
            'priority': 'high' if trigger_type == 'breaking_news' else 'medium',
            'created_at': datetime.now().isoformat(),
            'content': content,
            'instructions': self._get_instructions(trigger_type, content)
        }
        
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        logger.info(f"Created Twitter task: {task_id} (trigger: {trigger_type})")
    
    def _get_instructions(self, trigger_type: str, content: Dict[str, Any]) -> str:
        """Generate AI instructions based on trigger type"""
        base = "Review obsidian_vault/agent_skills/twitter_skills.md for posting guidelines."
        
        if trigger_type == 'breaking_news':
            return f"""{base}

Task: Post breaking business update to Twitter

Update: {content.get('update_text')}
Context: {content.get('context', '')}

Action Steps:
1. Extract key announcement (what happened, why it matters)
2. Write concise tweet (280 characters max, aim for 200-250)
3. Lead with action/result, not unnecessary context
4. Add 1-2 relevant hashtags (max 2)
5. Consider thread if additional context needed (see twitter_skills.md)
6. Check HITL approval (breaking news may need CEO approval)
7. Post via twitter_server.py
8. Monitor engagement for first 30 minutes
9. Respond to replies promptly

Tweet Structure:
[Emoji] [What happened] [Why it matters] [Optional CTA] #Hashtag

Example:
"🚀 Just launched [project] for [client]. 
[Key metric/benefit]. 
Big milestone for the team! 
#[Industry] #Milestone"
"""
        
        elif trigger_type == 'quick_win':
            return f"""{base}

Task: Share quick win on Twitter

Win: {content.get('win_description')}
Context: {content.get('context', '')}

Action Steps:
1. Identify core achievement (completed project, client win, milestone)
2. Write celebratory but professional tweet
3. Use 1 emoji opener (🎉 ✅ 🚀)
4. Keep under 250 characters for easy RT
5. Tag relevant people/companies if appropriate (max 2 tags)
6. Add 2-3 hashtags
7. Auto-approve if non-sensitive
8. Post and engage with responses

Tweet Tone:
- Excited but not boastful
- Specific outcome, not vague "great work"
- Give credit to team/client where appropriate
- Invite engagement ("What's your approach?")
"""
        
        elif trigger_type == 'insight':
            return f"""{base}

Task: Share industry insight or tip on Twitter

Insight: {content.get('insight_text')}
Context: {content.get('context', '')}

Action Steps:
1. Identify key lesson or observation
2. Write as actionable tip or thought-provoking question
3. Consider thread format if >280 characters (see twitter_skills.md)
4. Add value: "Here's why this matters..."
5. Use 2-3 hashtags (industry + topic)
6. Include CTA: "What's worked for you?"
7. Auto-approve if educational/neutral
8. Post during peak times (see twitter_skills.md)

Tweet Formats:
- Tip: "Pro tip: [Action]. Result: [Benefit]. #[Industry]Tip"
- Observation: "[Trend noticed]. [Why it matters]. Thoughts?"
- Lesson: "Learned: [What]. Changed our approach. [How]."
"""
        
        elif trigger_type == 'weekly_schedule':
            return f"""{base}

Task: Regular Twitter engagement (Mon/Wed/Fri posts)

Day: {content.get('day')}
Time: {content.get('time')}

Action Steps:
1. Review recent Business_Goals.md for tweet ideas
2. Check Done/ folder for wins to share
3. Plan tweet type:
   - Monday: Week kickoff (goals, focus areas)
   - Wednesday: Mid-week tip or insight
   - Friday: Week recap or weekend reflection
4. Write tweet (200-250 characters ideal)
5. Add 2-3 hashtags
6. Consider thread for deeper insights
7. Post during optimal time (see twitter_skills.md)
8. Engage with replies within 1 hour

Content Ideas by Day:
- Monday: "This week we're tackling [goal]. What's on your plate?"
- Wednesday: "Quick tip: [Insight from experience]."
- Friday: "Week recap: [Achievement]. [Lesson learned]."
"""
        
        return f"{base}\n\nTask Type: {trigger_type}\nContent: {json.dumps(content, indent=2)}"
    
    def check_breaking_news(self) -> List[Dict]:
        """Check for breaking business updates"""
        triggers = []
        
        if not self._check_rate_limit('breaking_news'):
            return triggers
        
        goals_file = self.vault_path / 'Business_Goals.md'
        
        if not goals_file.exists():
            return triggers
        
        try:
            content = goals_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check for recently added lines with breaking keywords
            for i, line in enumerate(lines):
                if ('✅' in line or '[x]' in line.lower()):
                    has_breaking = any(kw in line.lower() for kw in self.breaking_keywords)
                    
                    if has_breaking:
                        breaking_key = f"breaking:{line[:50]}"
                        
                        if breaking_key not in self.processed_items:
                            triggers.append({
                                'type': 'breaking_news',
                                'content': {
                                    'update_text': line.strip(),
                                    'context': '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                                },
                                'key': breaking_key
                            })
        
        except Exception as e:
            logger.error(f"Could not read Business_Goals.md: {e}")
        
        return triggers
    
    def check_quick_wins(self) -> List[Dict]:
        """Check Done folder for quick wins"""
        triggers = []
        
        if not self._check_rate_limit('quick_win'):
            return triggers
        
        done_path = self.vault_path / 'Done'
        
        if not done_path.exists():
            return triggers
        
        # Check items added in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        
        for item in done_path.iterdir():
            if item.is_file() and item.suffix == '.md':
                # Check if recent
                if datetime.fromtimestamp(item.stat().st_mtime) < cutoff:
                    continue
                
                item_key = f"quick_win:{item.name}"
                
                if item_key in self.processed_items:
                    continue
                
                try:
                    content = item.read_text(encoding='utf-8').lower()
                    
                    # Check for announcement-worthy wins
                    is_announcement_worthy = any(kw in content for kw in [
                        'client', 'customer', 'project', 'launch', 'milestone',
                        'achievement', 'completed', 'delivered', 'success'
                    ])
                    
                    if is_announcement_worthy:
                        triggers.append({
                            'type': 'quick_win',
                            'content': {
                                'win_description': item.stem,
                                'context': content[:500]
                            },
                            'key': item_key
                        })
                
                except Exception as e:
                    logger.warning(f"Could not read {item.name}: {e}")
        
        return triggers
    
    def check_insights(self) -> List[Dict]:
        """Check for shareable insights"""
        triggers = []
        
        if not self._check_rate_limit('insight'):
            return triggers
        
        # Check Done folder for lessons learned
        done_path = self.vault_path / 'Done'
        
        if not done_path.exists():
            return triggers
        
        for item in done_path.iterdir():
            item_key = f"insight:{item.name}"
            
            if item_key in self.processed_items:
                continue
            
            try:
                if item.is_file() and item.suffix == '.md':
                    content = item.read_text(encoding='utf-8').lower()
                    
                    has_insight = any(kw in content for kw in self.insight_keywords)
                    
                    if has_insight:
                        triggers.append({
                            'type': 'insight',
                            'content': {
                                'insight_text': item.stem,
                                'context': content[:500]
                            },
                            'key': item_key
                        })
            
            except Exception as e:
                logger.warning(f"Could not read {item.name}: {e}")
        
        return triggers
    
    def check_weekly_schedule(self) -> List[Dict]:
        """Check if it's posting time (Mon/Wed/Fri 10-11 AM)"""
        triggers = []
        now = datetime.now()
        
        # Monday = 0, Wednesday = 2, Friday = 4
        if now.weekday() in [0, 2, 4] and 10 <= now.hour < 11:
            if not self._check_rate_limit('weekly_schedule'):
                return triggers
            
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
        logger.info("Twitter watcher started")
        logger.info(f"Vault path: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        
        while True:
            try:
                logger.info("Checking for Twitter opportunities...")
                
                all_triggers = []
                all_triggers.extend(self.check_breaking_news())
                all_triggers.extend(self.check_quick_wins())
                all_triggers.extend(self.check_insights())
                all_triggers.extend(self.check_weekly_schedule())
                
                for trigger in all_triggers:
                    self._create_task(trigger['type'], trigger['content'])
                    self.processed_items.add(trigger['key'])
                    self._track_tweet(trigger['type'], trigger['key'])
                
                if all_triggers:
                    self._save_state()
                    logger.info(f"Created {len(all_triggers)} Twitter tasks")
                else:
                    logger.info("No new Twitter opportunities found")
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            logger.info(f"Sleeping for {self.check_interval}s...")
            time.sleep(self.check_interval)


if __name__ == "__main__":
    watcher = TwitterWatcher()
    watcher.monitor()
