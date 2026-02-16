"""
Gmail Watcher - Hackathon 0 Compliant
Monitors Gmail for important emails and creates tasks in task_queue/inbox
"""

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailWatcher:
    """Watches Gmail for important emails and creates tasks in task_queue/inbox"""
    
    def __init__(self, task_queue_path: str = "./task_queue", check_interval: int = 120):
        self.task_queue = Path(task_queue_path) / "inbox"
        self.task_queue.mkdir(parents=True, exist_ok=True)
        self.check_interval = check_interval
        self.processed_ids = set()
        self.service: Optional[Any] = None
        
        # Gmail API setup
        creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', './secrets/gmail_credentials.json')
        token_path = os.getenv('GMAIL_TOKEN_PATH', './secrets/gmail_token.json')
        
        try:
            self.creds = Credentials.from_authorized_user_file(token_path)
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail watcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {e}")
            self.service = None
    
    def check_for_new_emails(self):
        """Check for new unread important emails"""
        if not self.service:
            return []
        
        try:
            # Query for unread important emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important OR is:unread is:starred',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            
            return new_messages
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return []
    
    def create_task_file(self, message_id: str):
        if not self.service:
            logger.error("Gmail service not initialized")
            return
            
        """Create task file in task_queue/inbox for email"""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', '')
            
            # Extract body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                import base64
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
            
            # Create JSON task file per Hackathon 0 spec
            task_id = f"email_{message_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            task_file = self.task_queue / f"{task_id}.json"
            
            # Build task with required_skills for proper skill-based reasoning
            task = {
                'task_id': task_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source': 'gmail_watcher',
                'type': 'email',
                'priority': 'high',
                'context': {
                    'message_id': message_id,
                    'from': sender,
                    'subject': subject,
                    'date': date,
                    'body': body[:2000] if len(body) > 2000 else body,
                    'body_truncated': len(body) > 2000,
                    'full_body_length': len(body)
                },
                'instructions': """Review obsidian_vault/agent_skills/email_skills.md for email handling guidelines.

Action Steps:
1. Read and understand email content
2. Check if sender is known (search vault)
3. Determine priority based on email_skills.md rules
4. Draft appropriate response following Company_Handbook tone guidelines
5. If new sender OR sensitive topic → create approval request in /Pending_Approval
6. If known sender + routine → execute response
7. Update Dashboard.md
8. Mark email as read after processing
""",
                'required_skills': ['email_skills', 'approval_skills', 'planning_skills']
            }
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, indent=2, ensure_ascii=False)
            
            self.processed_ids.add(message_id)
            logger.info(f"✅ Created email task: {task_file.name}")
            
        except Exception as e:
            logger.error(f"Error creating task for message {message_id}: {e}")
    
    def run(self):
        """Main watcher loop"""
        logger.info(f"Gmail watcher starting (checking  every {self.check_interval}s)...")
        
        while True:
            try:
                new_emails = self.check_for_new_emails()
                
                if new_emails:
                    logger.info(f"Found {len(new_emails)} new important email(s)")
                    for msg in new_emails:
                        self.create_task_file(msg['id'])
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Gmail watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Gmail watcher loop: {e}")
                time.sleep(self.check_interval)


if __name__ == "__main__":
    watcher = GmailWatcher()
    watcher.run()
