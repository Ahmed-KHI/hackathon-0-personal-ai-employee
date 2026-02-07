# Gmail OAuth Setup Guide

## Prerequisites
- Google Cloud Console account
- Gmail account you want to monitor

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click "Create Project" or select existing project
3. Name it: "Personal AI Employee"
4. Click "Create"

### 2. Enable Gmail API

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" (unless you have Google Workspace)
3. Fill in:
   - App name: "Personal AI Employee"
   - User support email: YOUR_EMAIL
   - Developer contact: YOUR_EMAIL
4. Click "Save and Continue"
5. Add scope: `https://www.googleapis.com/auth/gmail.readonly`
6. Add scope: `https://www.googleapis.com/auth/gmail.send`  
7. Click "Save and Continue"
8. Add your email as test user
9. Click "Save and Continue"

### 4. Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS" > "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Gmail Watcher"
5. Click "Create"
6. Click "Download JSON"
7. Save file as: `secrets/gmail_credentials.json`

### 5. Authorize and Generate Token

Run this command in your terminal:

```powershell
python -c "from watcher_gmail import GmailWatcher; GmailWatcher().authorize()"
```

OR create this authorization script:

```powershell
# Save as: setup_gmail.py
from google_auth_oauthlib.flow import InstalledAppFlow
import json
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

# Create secrets directory  
Path('secrets').mkdir(exist_ok=True)

# Run OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(
    'secrets/gmail_credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save token
with open('secrets/gmail_token.json', 'w') as token:
    token.write(creds.to_json())

print("✅ Gmail OAuth setup complete!")
print("Token saved to: secrets/gmail_token.json")
```

Then run:
```powershell
python setup_gmail.py
```

### 6. Verify Setup

```powershell
# Test Gmail watcher
python watcher_gmail.py
```

Should see: "Gmail watcher initialized successfully"

### 7. Update .env (Optional)

```env
GMAIL_ENABLED=true  
GMAIL_CREDENTIALS_PATH=./secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=./secrets/gmail_token.json
GMAIL_CHECK_INTERVAL_SECONDS=120
```

## Troubleshooting

### Error: "File not found: gmail_credentials.json"
- Make sure you downloaded OAuth JSON from Google Cloud Console
- Save it as `secrets/gmail_credentials.json` (exact name)

### Error: "insufficient authentication scopes"
- Delete `secrets/gmail_token.json`
- Re-run setup_gmail.py
- Make sure both readonly and send scopes are added

### No emails detected
- Check Gmail query: `is:unread is:important`  
- Label some test emails as "Important" in Gmail
- Check logs: `pm2 logs watcher-gmail`

## Security Notes

- ✅ `secrets/gmail_token.json` is in .gitignore (never commit!)
- ✅ Token auto-refreshes when expired
- ⚠️ Token gives full Gmail access - keep secure
- 🔄 Rotate credentials every 90 days

## Testing

Send yourself an email:
1. Mark it as "Important" (star it)
2. Leave it unread
3. Wait 2 minutes
4. Check `obsidian_vault/Needs_Action/` for new EMAIL_*.md file

---

**Need help?** Check Gmail API docs: https://developers.google.com/gmail/api/quickstart/python
