"""
Twitter (X) OAuth Setup Script
Authenticates with Twitter API v2 for posting tweets

Requirements:
1. Twitter Developer Account (developer.twitter.com)
2. Twitter App with OAuth 2.0 enabled
3. Read and Write permissions
4. OAuth 2.0 Client ID and Client Secret

Setup Instructions:
1. Twitter Developer Portal (developer.twitter.com):
   - Create project and app
   - Enable OAuth 2.0 (User authentication settings)
   - Set permissions: Read and Write
   - Add callback URL: http://localhost:8080/callback
   - Copy Client ID and Client Secret
2. Add to .env:
   - TWITTER_CLIENT_ID=your_client_id
   - TWITTER_CLIENT_SECRET=your_client_secret
3. Run: python setup_twitter.py
"""

import os
import json
import hashlib
import base64
import secrets
import requests
from pathlib import Path
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Twitter API v2 OAuth 2.0 endpoints
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# OAuth configuration
CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8080/callback')
SCOPES = ['tweet.read', 'tweet.write', 'users.read', 'offline.access']

# Paths
TOKEN_PATH = Path('secrets/twitter_token.json')


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    # Code verifier: random string 43-128 characters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Code challenge: SHA256 hash of verifier, base64 encoded
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Twitter"""
    
    authorization_code = None
    state = None
    
    def do_GET(self):
        """Handle GET request with authorization code"""
        query = self.path.split('?', 1)[-1]
        params = parse_qs(query)
        
        if 'code' in params and 'state' in params:
            CallbackHandler.authorization_code = params['code'][0]
            CallbackHandler.state = params['state'][0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>Twitter Authentication Success</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #1DA1F2;">✅ Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p style="color: #666; margin-top: 30px;">Personal AI Employee - Twitter Integration</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = """
            <html>
            <head><title>Twitter Authentication Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #E0245E;">❌ Authentication Failed</h1>
                <p>No authorization code received. Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def get_authorization_code(code_challenge: str, state: str) -> str:
    """Step 1: Get authorization code via browser"""
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    
    print(f"\n🔗 Opening browser for Twitter authorization...")
    print(f"   If browser doesn't open, visit: {auth_url}\n")
    
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    
    print("⏳ Waiting for authorization...")
    print("   (Complete authorization in your browser)\n")
    
    server.handle_request()
    
    if CallbackHandler.authorization_code:
        print("✅ Authorization code received\n")
        return CallbackHandler.authorization_code
    else:
        raise Exception("Failed to receive authorization code")


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    """Step 2: Exchange authorization code for access token"""
    token_data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }
    
    # Twitter requires Basic Auth with client credentials
    auth = (CLIENT_ID, CLIENT_SECRET)
    
    response = requests.post(TOKEN_URL, data=token_data, auth=auth)
    response.raise_for_status()
    
    return response.json()


def save_tokens(tokens: dict):
    """Save Twitter tokens to secrets directory"""
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    
    with open(TOKEN_PATH, 'w') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n✅ Twitter tokens saved to: {TOKEN_PATH}")


def get_user_info(access_token: str) -> dict:
    """Get authenticated user information"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'user.fields': 'id,username,name,description,public_metrics'
    }
    
    response = requests.get(
        'https://api.twitter.com/2/users/me',
        headers=headers,
        params=params
    )
    response.raise_for_status()
    
    return response.json()['data']


def main():
    """Main Twitter setup flow"""
    print("="*70)
    print("Twitter (X) API v2 OAuth 2.0 Setup for Personal AI Employee")
    print("="*70)
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: Twitter credentials not found in .env")
        print("\n🔧 To fix this:")
        print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
        print("   2. Create a project and app (or use existing)")
        print("   3. Enable OAuth 2.0 in User authentication settings")
        print("   4. Set Type: Web App, Automated App or Bot")
        print("   5. Add Callback URL: http://localhost:8080/callback")
        print("   6. Set Permissions: Read and Write")
        print("   7. Copy Client ID and Client Secret")
        print("   8. Add to .env:")
        print("      TWITTER_CLIENT_ID=your_client_id")
        print("      TWITTER_CLIENT_SECRET=your_client_secret")
        print("   9. Run: python setup_twitter.py")
        return
    
    try:
        # Generate PKCE pair
        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = generate_pkce_pair()
        
        # Step 1: Get authorization code
        print("\n⏳ Step 1: Requesting authorization from Twitter...")
        auth_code = get_authorization_code(code_challenge, state)
        
        # Step 2: Exchange for access token
        print("⏳ Step 2: Exchanging authorization code for access token...")
        token_response = exchange_code_for_token(auth_code, code_verifier)
        
        # Save tokens
        save_tokens(token_response)
        
        # Step 3: Get user info
        print("\n⏳ Step 3: Retrieving user information...")
        user_info = get_user_info(token_response['access_token'])
        
        print("\n" + "="*70)
        print("✅ Twitter (X) Authentication Complete!")
        print("="*70)
        print(f"Username: @{user_info['username']}")
        print(f"Name: {user_info['name']}")
        print(f"User ID: {user_info['id']}")
        
        if 'public_metrics' in user_info:
            metrics = user_info['public_metrics']
            print(f"Followers: {metrics.get('followers_count', 0):,}")
            print(f"Following: {metrics.get('following_count', 0):,}")
            print(f"Tweets: {metrics.get('tweet_count', 0):,}")
        
        print("\nToken Details:")
        print(f"  Access Token: {token_response['access_token'][:20]}...")
        print(f"  Refresh Token: {'Yes' if 'refresh_token' in token_response else 'No'}")
        print(f"  Expires In: {token_response.get('expires_in', 'N/A')} seconds")
        print(f"  Scopes: {', '.join(SCOPES)}")
        
        print("\nYou can now use the Twitter MCP server to post tweets.")
        print("Token file location: secrets/twitter_token.json")
        print("\nNext steps:")
        print("  1. Start watcher: python watcher_twitter.py")
        print("  2. Test posting via orchestrator")
        print("\nNote: Access token expires in ~2 hours. Refresh token allows renewal.")
        print("="*70)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response:
            try:
                error_data = e.response.json()
                print(f"   Details: {error_data}")
            except:
                print(f"   Response: {e.response.text}")
        
        print("\n🔧 Troubleshooting:")
        print("   - Check Client ID and Client Secret in .env")
        print("   - Verify callback URL is exactly: http://localhost:8080/callback")
        print("   - Ensure app has Read and Write permissions")
        print("   - Try regenerating Client Secret in Twitter Developer Portal")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
