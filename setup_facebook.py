"""
Facebook OAuth 2.0 Setup Script
Authenticates with Facebook Graph API for page posting permissions

Requirements:
1. Facebook Developer account (developers.facebook.com)
2. Create Facebook App with Pages API enabled
3. Add Facebook Page to the app
4. Get App ID and App Secret from app settings

Setup Instructions:
1. Go to https://developers.facebook.com/apps
2. Create new app → Business → App name
3. Add "Facebook Login" product
4. Settings → Basic → Copy App ID and App Secret
5. Add to .env:
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
6. Run: python setup_facebook.py
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Facebook OAuth configuration
APP_ID = os.getenv('FACEBOOK_APP_ID')
APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
REDIRECT_URI = os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:8000/callback')
TOKEN_PATH = Path('secrets/facebook_token.json')

# Scopes needed for page posting and insights
SCOPES = [
    'pages_show_list',           # List pages
    'pages_read_engagement',     # Read page insights
    'pages_manage_posts',        # Create and manage posts
    'pages_read_user_content',   # Read page content
    'business_management'        # Business integrations
]

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from Facebook OAuth redirect"""
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <body>
                    <h1>Facebook Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            ''')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error = params.get('error_description', ['Unknown error'])[0]
            self.wfile.write(f'''
                <html>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
            '''.encode())
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def exchange_code_for_token(auth_code: str) -> dict:
    """Exchange authorization code for access token"""
    token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    
    params = {
        'client_id': APP_ID,
        'client_secret': APP_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': auth_code
    }
    
    response = requests.get(token_url, params=params)
    response.raise_for_status()
    return response.json()


def get_long_lived_token(short_token: str) -> dict:
    """Exchange short-lived token for long-lived token (60 days)"""
    exchange_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': APP_ID,
        'client_secret': APP_SECRET,
        'fb_exchange_token': short_token
    }
    
    response = requests.get(exchange_url, params=params)
    response.raise_for_status()
    return response.json()


def get_page_access_token(user_token: str) -> dict:
    """Get page access token (never expires for pages)"""
    pages_url = 'https://graph.facebook.com/v19.0/me/accounts'
    
    params = {
        'access_token': user_token
    }
    
    response = requests.get(pages_url, params=params)
    response.raise_for_status()
    pages = response.json()
    
    if not pages.get('data'):
        raise Exception("No Facebook Pages found. Please create a page first at facebook.com/pages/create")
    
    # Return first page (you can modify to select specific page)
    return pages['data'][0]


def save_tokens(tokens: dict):
    """Save tokens to secrets directory"""
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    
    with open(TOKEN_PATH, 'w') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n✅ Tokens saved to: {TOKEN_PATH}")
    print(f"   Page: {tokens['page_name']}")
    print(f"   Page ID: {tokens['page_id']}")


def main():
    """Main OAuth flow"""
    print("="*70)
    print("Facebook OAuth Setup for Personal AI Employee")
    print("="*70)
    
    # Validate environment variables
    if not APP_ID or not APP_SECRET:
        print("\n❌ Error: Missing Facebook credentials in .env file")
        print("   Please add:")
        print("   FACEBOOK_APP_ID=your_app_id_here")
        print("   FACEBOOK_APP_SECRET=your_app_secret_here")
        return
    
    print(f"\nApp ID: {APP_ID[:10]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    
    # Build authorization URL
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={APP_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={','.join(SCOPES)}&"
        f"response_type=code&"
        f"state=random_state_string"
    )
    
    print("\n📌 Step 1: Opening browser for Facebook authorization...")
    print("   Please log in and authorize the app to manage your Facebook Page.")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print("\n⏳ Step 2: Waiting for authorization callback...")
    print("   (Local server listening on http://localhost:8000)")
    
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server.auth_code = None
    
    # Wait for one request (the callback)
    server.handle_request()
    
    if not server.auth_code:
        print("\n❌ Authorization failed or was cancelled")
        return
    
    print("\n✅ Step 3: Authorization code received!")
    
    try:
        # Exchange code for short-lived user token
        print("   Exchanging code for access token...")
        token_data = exchange_code_for_token(server.auth_code)
        short_token = token_data['access_token']
        
        # Get long-lived user token (60 days)
        print("   Getting long-lived user token...")
        long_token_data = get_long_lived_token(short_token)
        user_token = long_token_data['access_token']
        
        # Get page access token (never expires)
        print("   Getting page access token...")
        page_data = get_page_access_token(user_token)
        
        # Save tokens
        tokens = {
            'page_id': page_data['id'],
            'page_name': page_data['name'],
            'page_access_token': page_data['access_token'],
            'user_access_token': user_token,
            'category': page_data.get('category', 'N/A')
        }
        
        save_tokens(tokens)
        
        print("\n" + "="*70)
        print("✅ Facebook Setup Complete!")
        print("="*70)
        print(f"Page Name: {tokens['page_name']}")
        print(f"Page ID: {tokens['page_id']}")
        print(f"Category: {tokens['category']}")
        print("\nYou can now use the Facebook MCP server to post updates.")
        print("Token file location: secrets/facebook_token.json")
        print("\nNext steps:")
        print("  1. Start watcher: python watcher_facebook.py")
        print("  2. Test posting via orchestrator")
        print("="*70)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
