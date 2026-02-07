"""
Email MCP Server - Hackathon 0 Compliant
Real working MCP server for sending emails via Gmail API
"""

import os
import json
import base64
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


class EmailMCP:
    """MCP Server for email actions"""
    
    def __init__(self):
        token_path = os.getenv('GMAIL_TOKEN_PATH', './secrets/gmail_token.json')
        self.creds = Credentials.from_authorized_user_file(token_path)
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def send_email(self, to: str, subject: str, body: str, attachment_path: Optional[str] = None) -> dict:
        """
        Send email via Gmail API
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            attachment_path: Optional path to file attachment
        
        Returns:
            dict with status and message_id
        """
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment_path and Path(attachment_path).exists():
                with open(attachment_path, 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment_path).name}'
                )
                message.attach(part)
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_message = {'raw': raw_message}
            
            result = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()
            
            return {
                "status": "success",
                "message_id": result['id'],
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "to": to,
                "subject": subject
            }
    
    def draft_email(self, to: str, subject: str, body: str) -> dict:
        """
        Create email draft without sending
        
        Returns draft_id for later sending
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            draft_body = {'message': {'raw': raw_message}}
            
            draft = self.service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            return {
                "status": "success",
                "draft_id": draft['id'],
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def handle_request(self, request: dict) -> dict:
        """
        Handle MCP request
        
        Request format:
        {
            "action": "send_email" | "draft_email",
            "params": {
                "to": "recipient@example.com",
                "subject": "Subject line",
                "body": "Email body",
                "attachment_path": "/path/to/file" (optional)
            }
        }
        """
        action = request.get('action')
        params = request.get('params', {})
        
        if action == 'send_email':
            return self.send_email(**params)
        elif action == 'draft_email':
            return self.draft_email(**params)
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}


def main():
    """MCP Server main loop - listens for requests on stdin"""
    mcp = EmailMCP()
    
    print("Email MCP Server started", flush=True)
    
    # MCP protocol: read JSON requests from stdin, write responses to stdout
    while True:
        try:
            line = input()
            if not line:
                continue
            
            request = json.loads(line)
            response = mcp.handle_request(request)
            print(json.dumps(response), flush=True)
            
        except EOFError:
            break
        except Exception as e:
            error_response = {"status": "error", "error": str(e)}
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
