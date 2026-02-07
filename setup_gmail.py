"""
Gmail OAuth Setup Script
Run this to authorize Gmail access and generate token
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import json

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def setup_gmail_oauth():
    """
    Runs OAuth flow to authorize Gmail access and save credentials
    """
    print("=== Gmail OAuth Setup ===\n")
    
    # Check if credentials file exists
    creds_file = Path('secrets/gmail_credentials.json')
    if not creds_file.exists():
        print("❌ Error: secrets/gmail_credentials.json not found!")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create/select project")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download JSON and save as: secrets/gmail_credentials.json")
        print("\nDetailed guide: docs/GMAIL_SETUP.md")
        return False
    
    try:
        # Create secrets directory
        Path('secrets').mkdir(exist_ok=True)
        
        print("📱 Opening browser for Gmail authorization...")
        print("Please sign in and grant permissions.\n")
        
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file), SCOPES)
        creds = flow.run_local_server(
            port=0,
            prompt='consent',
            success_message='Authorization successful! You can close this window.'
        )
        
        # Save token
        token_file = Path('secrets/gmail_token.json')
        token_file.write_text(creds.to_json())
        
        print("\n✅ Gmail OAuth setup complete!")
        print(f"✅ Token saved to: {token_file}")
        print("\nYou can now run:")
        print("  python watcher_gmail.py")
        print("  pm2 restart watcher-gmail")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you have google-auth-oauthlib installed")
        print("- Check that gmail_credentials.json is valid JSON")
        print("- Ensure Gmail API is enabled in Google Cloud Console")
        return False

if __name__ == '__main__':
    success = setup_gmail_oauth()
    exit(0 if success else 1)
