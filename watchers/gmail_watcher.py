"""
Gmail Watcher - Silver Tier

Watches Gmail inbox for new emails via Gmail API.
Creates tasks for emails that match configured criteria.

DEPLOYMENT TIER: Silver
DEPENDENCIES: google-api-python-client, google-auth
"""

import os
import pickle
import base64
from pathlib import Path
from typing import Any, List, Dict, Optional
from email.mime.text import MIMEText
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import cast

from base_watcher import BaseWatcher, WatcherConfigError, WatcherConnectionError
from dotenv import load_dotenv
import time

load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for new emails.
    
    Configuration (.env):
        GMAIL_CREDENTIALS_PATH: Path to OAuth2 credentials JSON
        GMAIL_TOKEN_PATH: Path to store OAuth2 token
        GMAIL_WATCH_LABELS: Comma-separated labels to watch (default: INBOX)
        GMAIL_CHECK_INTERVAL: Seconds between checks (default: 60)
    
    Usage:
        watcher = GmailWatcher()
        watcher.start()
    """
    
    def __init__(self):
        super().__init__("gmail_watcher")
        
        # Get configuration
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./secrets/gmail_credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "./secrets/gmail_token.json")
        self.watch_labels = os.getenv("GMAIL_WATCH_LABELS", "INBOX").split(",")
        self.check_interval = int(os.getenv("GMAIL_CHECK_INTERVAL", "60"))
        
        self.service = None
        self.last_history_id = None
        
        # Validate configuration
        if not Path(self.credentials_path).exists():
            raise WatcherConfigError(
                f"Gmail credentials not found at {self.credentials_path}. "
                "Please follow setup instructions in secrets/README.md"
            )
    
    def _get_credentials(self) -> Credentials:
        """Get or refresh OAuth2 credentials."""
        creds: Optional[Credentials] = None
        
        # Load token if exists
        if Path(self.token_path).exists():
            with open(self.token_path, 'rb') as token:
                creds = cast(Credentials, pickle.load(token))
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired token...")
                creds.refresh(Request())
            else:
                self.logger.info("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = cast(Credentials, flow.run_local_server(port=0))
            
            # Save credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            
            self.logger.info("Credentials saved")
        
        return creds
    
    def _connect(self) -> None:
        """Connect to Gmail API."""
        try:
            creds = self._get_credentials()
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Connected to Gmail API")
        except Exception as e:
            raise WatcherConnectionError(f"Failed to connect to Gmail: {e}")
    
    def _get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full message details."""
        if not self.service:
            return None
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Parse headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to_email = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Get body
            body = self._get_message_body(message['payload'])
            
            # Get thread ID
            thread_id = message.get('threadId', message_id)
            
            return {
                "message_id": message_id,
                "thread_id": thread_id,
                "subject": subject,
                "from": from_email,
                "to": to_email,
                "date": date,
                "body": body[:5000],  # Limit body size
                "labels": message.get('labelIds', []),
                "snippet": message.get('snippet', '')
            }
            
        except HttpError as e:
            self.logger.error(f"Error fetching message {message_id}: {e}")
            return None
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract message body from payload."""
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Simple message
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return "[No plain text body]"
    
    def _check_for_new_messages(self) -> List[str]:
        """Check for new messages matching watch criteria."""
        if not self.service:
            return []
        
        try:
            # Build query
            query_parts = []
            for label in self.watch_labels:
                query_parts.append(f"label:{label.strip()}")
            query = " OR ".join(query_parts)
            query += " is:unread"  # Only unread messages
            
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Process in batches
            ).execute()
            
            messages = results.get('messages', [])
            
            if messages:
                self.logger.info(f"Found {len(messages)} unread messages")
                return [msg['id'] for msg in messages]
            
            return []
            
        except HttpError as e:
            self.logger.error(f"Error checking for messages: {e}")
            return []
    
    def on_event(self, message_id: str) -> None:
        """
        Handle a new email by creating a task.
        
        Args:
            message_id: Gmail message ID
        """
        details = self._get_message_details(message_id)
        
        if not details:
            return
        
        # Determine priority from subject/sender
        priority = "normal"
        subject_lower = details['subject'].lower()
        
        if any(word in subject_lower for word in ['urgent', 'asap', 'critical']):
            priority = "high"
        elif any(word in subject_lower for word in ['invoice', 'payment', 'contract']):
            priority = "high"
        
        # Determine if HITL required
        hitl_required = False
        if any(word in subject_lower for word in ['contract', 'agreement', 'legal']):
            hitl_required = True
        
        # Create task
        self.create_task(
            task_type="email_response",
            context=details,
            priority=priority,
            required_skills=["email_skills"],
            hitl_required=hitl_required
        )
        
        self.logger.info(f"Task created for email: {details['subject'][:50]}")
    
    def start(self) -> None:
        """Start watching Gmail."""
        if self.running:
            self.logger.warning("Watcher already running")
            return
        
        # Connect to Gmail
        self._connect()
        
        self.running = True
        
        self.logger.info(f"Gmail watcher started. Checking every {self.check_interval}s")
        
        try:
            while self.running:
                # Check for new messages
                message_ids = self._check_for_new_messages()
                
                # Process each message
                for message_id in message_ids:
                    self.on_event(message_id)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in watch loop: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop watching Gmail."""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Gmail watcher stopped")


def main():
    """Run Gmail watcher standalone."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║    PERSONAL AI EMPLOYEE - GMAIL WATCHER (SILVER TIER)      ║
    ╚════════════════════════════════════════════════════════════╝
    
    This watcher monitors your Gmail inbox for new messages.
    
    Setup Instructions:
    1. Create OAuth2 credentials in Google Cloud Console
    2. Download client_secret.json to secrets/gmail_credentials.json
    3. Run this script and authorize in browser
    4. Token will be saved to secrets/gmail_token.json
    
    Press Ctrl+C to stop
    """)
    
    try:
        watcher = GmailWatcher()
        watcher.start()
    except WatcherConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nSee secrets/README.md for setup instructions.")
    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    main()
