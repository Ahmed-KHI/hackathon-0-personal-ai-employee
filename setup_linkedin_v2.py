"""
LinkedIn OAuth 2.0 Setup Script (OpenID Connect)
Updated for LinkedIn's current API (2026)

Prerequisites:
1. LinkedIn app created at https://www.linkedin.com/developers/
2. "Share on LinkedIn" product added (should show under "Added products")
3. Redirect URI added: http://localhost:8000/callback
4. CLIENT_ID and CLIENT_SECRET in .env file

Required scopes: openid, profile, w_member_social
"""

import os
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv

load_dotenv()

# LinkedIn OAuth Configuration
CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'

# Updated scopes for LinkedIn API v2 with OpenID Connect
SCOPES = 'openid profile w_member_social'

TOKEN_PATH = Path('secrets/linkedin_token.json')

class LinkedInCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from LinkedIn"""
    
    def do_GET(self):
        """Handle the OAuth callback request"""
        query_components = parse_qs(urlparse(self.path).query)
        
        if 'code' in query_components:
            # Got authorization code
            auth_code = query_components['code'][0]
            
            # Exchange code for access token
            token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            
            try:
                print("\n⏳ Exchanging authorization code for access token...")
                response = requests.post(token_url, data=token_data, headers=headers)
                response.raise_for_status()
                token_json = response.json()
                
                print(f"✅ Access token received!")
                print(f"   Expires in: {token_json.get('expires_in', 'N/A')} seconds")
                
                # Save token to secrets/
                TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(TOKEN_PATH, 'w') as f:
                    json.dump(token_json, f, indent=2)
                
                print(f"✅ Token saved to: {TOKEN_PATH}")
                
                # Get user profile info
                try:
                    profile = get_user_profile(token_json['access_token'])
                    print(f"\n✅ Authenticated as: {profile.get('name', 'Unknown')}")
                    if 'email' in profile:
                        print(f"   Email: {profile['email']}")
                except Exception as e:
                    print(f"⚠️  Could not fetch profile: {e}")
                
                # Send success response to browser
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>LinkedIn Authentication Success</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #0077B5;">✅ LinkedIn Authentication Successful!</h1>
                    <p>Your LinkedIn account is now connected to the AI Employee.</p>
                    <p>You can close this window and return to the terminal.</p>
                    <p style="color: #666; margin-top: 30px;">Personal AI Employee - LinkedIn Integration</p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
                print("\n" + "="*70)
                print("✅ LinkedIn authentication successful!")
                print("="*70)
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP Error: {e}"
                try:
                    error_data = e.response.json()
                    error_msg = f"{error_data.get('error', 'unknown')}: {error_data.get('error_description', 'No description')}"
                except:
                    error_msg = e.response.text
                
                print(f"\n❌ Error exchanging code for token:")
                print(f"   {error_msg}")
                
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = f'<h1>Error: {error_msg}</h1>'
                self.wfile.write(error_html.encode())
        
        elif 'error' in query_components:
            # User denied access or error occurred
            error = query_components.get('error', ['unknown'])[0]
            error_desc = query_components.get('error_description', ['No description'])[0]
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>LinkedIn Authentication Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #E0245E;">❌ Authentication Failed</h1>
                <p><strong>Error:</strong> {error}</p>
                <p>{error_desc}</p>
                <p style="margin-top: 30px;">Please return to the terminal and check the troubleshooting steps.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
            
            print(f"\n❌ Authentication failed:")
            print(f"   Error: {error}")
            print(f"   Description: {error_desc}")
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass


def get_user_profile(access_token: str) -> dict:
    """Get user profile using OpenID Connect userinfo endpoint"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(
        'https://api.linkedin.com/v2/userinfo',
        headers=headers
    )
    response.raise_for_status()
    
    return response.json()


def main():
    """Run the LinkedIn OAuth flow"""
    print("="*70)
    print("LinkedIn OAuth 2.0 Setup (OpenID Connect) - AI Employee")
    print("="*70)
    
    # Check credentials
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: LinkedIn credentials not found in .env file")
        print("\n🔧 To fix this:")
        print("   1. Go to https://www.linkedin.com/developers/")
        print("   2. Select your app (AI Employee Bot)")
        print("   3. Go to 'Auth' tab")
        print("   4. Copy Client ID and Client Secret")
        print("   5. Add to .env file:")
        print("      LINKEDIN_CLIENT_ID=your_client_id")
        print("      LINKEDIN_CLIENT_SECRET=your_client_secret")
        print("   6. Run: python setup_linkedin_v2.py")
        return
    
    print(f"\n✅ Client ID found: {CLIENT_ID}")
    print(f"✅ Redirect URI: {REDIRECT_URI}")
    print(f"✅ Scopes: {SCOPES}")
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES
    }
    
    auth_url = f'https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}'
    
    print("\n📋 Authorization Flow:")
    print("   1. Opening browser for LinkedIn authorization...")
    print("   2. Sign in to your LinkedIn account")
    print("   3. Click 'Allow' to grant permissions")
    print("   4. You'll be redirected back automatically")
    print("\n" + "="*70)
    
    # Start local server to receive callback
    server = HTTPServer(('localhost', 8000), LinkedInCallbackHandler)
    
    # Open authorization URL in browser
    print("\n🌐 Opening browser...")
    webbrowser.open(auth_url)
    
    print("\n⏳ Waiting for authorization...")
    print("✋ If browser doesn't open, visit this URL manually:")
    print(f"\n{auth_url}\n")
    
    # Handle one request (the callback) then shut down
    server.handle_request()
    server.server_close()
    
    # Verify token was saved
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'r') as f:
            token_data = json.load(f)
        
        print("\n" + "="*70)
        print("✅ LinkedIn Setup Complete!")
        print("="*70)
        print(f"\n📄 Token file: {TOKEN_PATH}")
        print(f"⏰ Expires in: {token_data.get('expires_in', 'unknown')} seconds")
        print(f"🔐 Scopes: {token_data.get('scope', SCOPES)}")
        
        print("\n💡 Next steps:")
        print("   1. Test posting: python post_linkedin_live.py")
        print("   2. Start watcher: python watcher_linkedin.py")
        print("   3. Test full workflow with orchestrator")
        
        print("\n⚠️  Security: Token is gitignored automatically")
        print("="*70)
    else:
        print("\n❌ Authentication failed. Token file not created.")
        print("\n🔧 Troubleshooting:")
        print("   - Verify 'Share on LinkedIn' product is added in your app")
        print("   - Check redirect URI exactly matches: http://localhost:8000/callback")
        print("   - Ensure you clicked 'Allow' on the authorization page")
        print("   - Try again: python setup_linkedin_v2.py")


if __name__ == '__main__':
    main()
