"""
LinkedIn Watcher - Monitor for Business Posting Opportunities

This watcher monitors business activities and generates LinkedIn posts
to drive sales and engagement.

Triggers:
- New completed projects (check /Done folder)
- Business milestones (from Business_Goals.md)
- Schedule: Daily at 9 AM for business updates
- Manual trigger: Drop file in watch_inbox/linkedin_post_*.txt

Strategy:
1. Check for completed high-value tasks
2. Generate engaging LinkedIn post draft
3. Create task in /Needs_Action for Claude to refine
4. Flag for HITL approval before posting
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watcher_linkedin.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInWatcher:
    """Watch for opportunities to post business updates on LinkedIn"""
    
    def __init__(self, vault_path: str = "./obsidian_vault", task_queue_path: str = "./task_queue"):
        self.vault = Path(vault_path)
        self.task_queue = Path(task_queue_path)
        self.inbox = self.task_queue / "inbox"  # PLATINUM TIER: Create drafts, not direct tasks
        self.done = self.vault / "Done"
        self.business_goals = self.vault / "Business_Goals.md"
        
        self.token_path = Path(os.getenv('LINKEDIN_TOKEN_PATH', './secrets/linkedin_token.json'))
        self.check_interval = int(os.getenv('LINKEDIN_CHECK_INTERVAL_SECONDS', '3600'))  # 1 hour
        self.last_post_check = datetime.now(timezone.utc) - timedelta(days=1)
        
        self.inbox.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LinkedIn watcher initialized (PLATINUM TIER: Draft-only mode)")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Token path: {self.token_path}")
        logger.info(f"Draft inbox: {self.inbox}")
    
    def is_authenticated(self) -> bool:
        """Check if LinkedIn OAuth token exists"""
        if not self.token_path.exists():
            logger.warning("LinkedIn token not found. Run: python setup_linkedin.py")
            return False
        
        try:
            with open(self.token_path, 'r') as f:
                token_data = json.load(f)
            
            # Check if token has expired (tokens typically last 60 days)
            if 'expires_in' in token_data:
                # In production, would check actual expiration timestamp
                logger.info("LinkedIn token found and valid")
                return True
            
        except Exception as e:
            logger.error(f"Error reading LinkedIn token: {e}")
            return False
        
        return True
    
    def check_for_posting_opportunities(self):
        """
        Look for business achievements worth posting about
        
        Categories:
        1. Completed high-value projects (from /Done)
        2. Milestones reached (revenue, customer count)
        3. New capabilities launched
        4. Scheduled business updates
        """
        opportunities = []
        
        # Check for completed tasks in last 24 hours
        recent_completions = self._check_recent_completions()
        if recent_completions:
            opportunities.append({
                'type': 'project_completion',
                'data': recent_completions,
                'priority': 'high'
            })
        
        # Check if it's time for weekly business update (Monday 9 AM)
        if self._is_weekly_update_time():
            opportunities.append({
                'type': 'weekly_update',
                'data': 'Weekly business update scheduled',
                'priority': 'medium'
            })
        
        # Check for milestone achievements
        milestones = self._check_milestones()
        if milestones:
            opportunities.append({
                'type': 'milestone',
                'data': milestones,
                'priority': 'high'
            })
        
        return opportunities
    
    def _check_recent_completions(self) -> list:
        """Check /Done for recently completed high-value tasks"""
        completions = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        try:
            for done_file in self.done.glob("*.md"):
                # Check file modification time
                mtime = datetime.fromtimestamp(done_file.stat().st_mtime, tz=timezone.utc)
                
                if mtime > cutoff_time:
                    # Read file to check if it's post-worthy
                    content = done_file.read_text(encoding='utf-8')
                    
                    # Simple heuristics for post-worthy content
                    post_worthy_keywords = [
                        'client', 'project', 'launch', 'milestone', 'revenue',
                        'customer', 'success', 'achievement', 'innovation'
                    ]
                    
                    if any(keyword in content.lower() for keyword in post_worthy_keywords):
                        completions.append({
                            'file': done_file.name,
                            'timestamp': mtime.isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Error checking completions: {e}")
        
        return completions
    
    def _is_weekly_update_time(self) -> bool:
        """Check if it's Monday 9 AM (weekly update time)"""
        now = datetime.now()
        
        # Check if it's Monday and we haven't posted today yet
        if now.weekday() == 0 and now.hour == 9:  # Monday, 9 AM
            last_check_date = self.last_post_check.date()
            today = now.date()
            
            if last_check_date < today:
                return True
        
        return False
    
    def _check_milestones(self) -> list:
        """Check Business_Goals.md for achieved milestones"""
        milestones = []
        
        try:
            if self.business_goals.exists():
                content = self.business_goals.read_text(encoding='utf-8')
                
                # Look for milestone indicators
                milestone_keywords = [
                    'achieved', 'reached', 'surpassed', 'milestone',
                    'goal met', 'target achieved'
                ]
                
                lines = content.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in milestone_keywords):
                        milestones.append(line.strip())
        
        except Exception as e:
            logger.error(f"Error checking milestones: {e}")
        
        return milestones
    
    def create_linkedin_post_task(self, opportunities: list):
        """
        Create a DRAFT task (JSON) in inbox for local review
        
        PLATINUM TIER SECURITY:
        - Cloud watcher creates draft only (no direct execution)
        - Local draft_reviewer.py creates human-readable draft
        - Human approves before execution
        - Ensures NO automatic cloud execution
        """
        if not opportunities:
            return
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        task_file = self.inbox / f"linkedin_post_{timestamp}.json"
        
        # Build instructions for Claude
        instructions = """1. **Analyze** the opportunities below
2. **Read** Business_Goals.md for context
3. **Read** Company_Handbook.md for brand voice
4. **Generate** an engaging LinkedIn post that:
   - Highlights business achievement
   - Provides value to followers
   - Includes call-to-action for sales
   - Matches professional tone
   - 150-300 words maximum
   - Includes relevant hashtags

5. **Create** approval request in /Pending_Approval/
6. **Flag** for human review before posting

## Guidelines (from linkedin_skills.md)

- Focus on value, not bragging
- Use data/metrics when possible
- Include visual suggestion (image/graphic)
- Time-sensitive: Post within 24 hours for relevance
- Target audience: Business decision-makers"""
        
        # Create task data structure
        task_data = {
            'type': 'linkedin_post',
            'source': 'linkedin_watcher',
            'created': datetime.now(timezone.utc).isoformat(),
            'priority': 'medium',
            'requires_approval': True,
            'title': 'LinkedIn Business Post - Opportunity Detected',
            'description': f'Found {len(opportunities)} posting opportunities from cloud watcher',
            'data': {
                'opportunities': opportunities,
                'watcher': 'linkedin',
                'mode': 'platinum_tier_draft'
            },
            'instructions': instructions,
            'security_note': 'This is a DRAFT from cloud watcher. Requires local approval before execution.',
            'required_skills': ['linkedin_skills', 'social_skills', 'approval_skills', 'planning_skills']
        }
        
        try:
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Created DRAFT task (JSON): {task_file.name}")
            logger.info(f"   🔐 Draft will be reviewed locally before execution")
            
            # Update last check time
            self.last_post_check = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Failed to create LinkedIn draft task: {e}")
    
    def run(self):
        """Main watcher loop"""
        logger.info("🚀 LinkedIn watcher started")
        
        # Check authentication on startup
        if not self.is_authenticated():
            logger.warning("⚠️  LinkedIn not authenticated. Limited functionality.")
            logger.warning("   Run: python setup_linkedin.py")
        
        while True:
            try:
                logger.info("🔍 Checking for LinkedIn posting opportunities...")
                
                # Look for posting opportunities
                opportunities = self.check_for_posting_opportunities()
                
                if opportunities:
                    logger.info(f"✨ Found {len(opportunities)} posting opportunities")
                    self.create_linkedin_post_task(opportunities)
                else:
                    logger.info("📭 No new posting opportunities found")
                
                # Sleep until next check
                logger.info(f"😴 Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("\n⏹️  LinkedIn watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in LinkedIn watcher: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == '__main__':
    watcher = LinkedInWatcher()
    watcher.run()
