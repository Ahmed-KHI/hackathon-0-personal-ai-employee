"""
Gmail Watcher - Hackathon 0 Compliant
Monitors Gmail for important emails and creates tasks in /Needs_Action
"""

import os
import time
import logging
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
    """Watches Gmail for important emails and creates tasks in /Needs_Action"""
    
    def __init__(self, vault_path: str = "./obsidian_vault", check_interval: int = 120):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.needs_action.mkdir(parents=True, exist_ok=True)
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
            
        """Create task file in /Needs_Action for email"""
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
            
            # Create markdown file per Hackathon 0 spec
            task_file = self.needs_action / f"EMAIL_{message_id}.md"
            
            markdown_content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now(timezone.utc).isoformat()}
priority: high
status: pending
message_id: {message_id}
---

## Email Content

**From**: {sender}  
**Subject**: {subject}  
**Date**: {date}

### Message Body

```
{body[:2000] if len(body) > 2000 else body}
{'...[truncated]' if len(body) > 2000 else ''}
```

## Suggested Actions
- [ ] Read and understand email content
- [ ] Check if sender is known (search vault)
- [ ] Draft appropriate response following Company_Handbook tone guidelines
- [ ] If new sender OR sensitive topic → create approval request in /Pending_Approval
- [ ] If known sender + routine → execute response
- [ ] Update Dashboard.md
- [ ] Mark email as read after processing
"""
            
            task_file.write_text(markdown_content)
            self.processed_ids.add(message_id)
            logger.info(f"Created email task: {task_file.name}")
            
        except Exception as e:
            logger.error(f"Error creating task for message {message_id}: {e}")
    
    def run(self):
        """Main watcher loop"""
        logger.info(f"👀 Gmail watcher starting (checking  every {self.check_interval}s)...")
        
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
