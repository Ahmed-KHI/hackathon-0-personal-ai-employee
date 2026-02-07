"""
LinkedIn OAuth 2.0 Setup Script

This script handles LinkedIn authentication for the AI Employee.
It opens a browser for the user to authorize the app and saves the access token.

Prerequisites:
1. Create LinkedIn Developer App at https://www.linkedin.com/developers/
2. Add redirect URI: http://localhost:8000/callback
3. Set CLIENT_ID and CLIENT_SECRET in .env file

Required scopes: w_member_social, r_liteprofile
"""

import os
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

load_dotenv()

# LinkedIn OAuth Configuration
CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'
SCOPES = 'w_member_social r_liteprofile'
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
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            
            try:
                response = requests.post(token_url, data=token_data)
                response.raise_for_status()
                token_json = response.json()
                
                # Save token to secrets/
                TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(TOKEN_PATH, 'w') as f:
                    json.dump(token_json, f, indent=2)
                
                # Send success response to browser
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                    <html>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: green;">✅ LinkedIn Authentication Successful!</h1>
                        <p>Your LinkedIn account is now connected to the AI Employee.</p>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                ''')
                
                print(f"\n✅ OAuth token saved to {TOKEN_PATH}")
                print("✅ LinkedIn authentication successful!")
                
            except Exception as e:
                print(f"\n❌ Error exchanging code for token: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f'<h1>Error: {e}</h1>'.encode())
        
        elif 'error' in query_components:
            # User denied access or error occurred
            error = query_components.get('error', ['unknown'])[0]
            error_desc = query_components.get('error_description', [''])[0]
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Authentication Failed</h1>
                    <p>Error: {error}</p>
                    <p>{error_desc}</p>
                </body>
                </html>
            '''.encode())
            
            print(f"\n❌ Authentication failed: {error} - {error_desc}")
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass


def main():
    """Run the LinkedIn OAuth flow"""
    print("=" * 60)
    print("LinkedIn OAuth 2.0 Setup for AI Employee")
    print("=" * 60)
    
    # Check credentials
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: LinkedIn credentials not found in .env file")
        print("\nPlease add to your .env file:")
        print("LINKEDIN_CLIENT_ID=your_client_id_here")
        print("LINKEDIN_CLIENT_SECRET=your_client_secret_here")
        print("\nGet credentials from: https://www.linkedin.com/developers/")
        return
    
    # Build authorization URL
    auth_url = (
        f'https://www.linkedin.com/oauth/v2/authorization'
        f'?response_type=code'
        f'&client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&scope={SCOPES}'
    )
    
    print("\n📋 Steps:")
    print("1. Opening browser for LinkedIn authorization...")
    print("2. Sign in to your LinkedIn account")
    print("3. Grant permissions to the AI Employee")
    print("4. You'll be redirected back automatically")
    print("\n" + "=" * 60)
    
    # Start local server to receive callback
    server = HTTPServer(('localhost', 8000), LinkedInCallbackHandler)
    
    # Open authorization URL in browser
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
        
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print(f"\n📄 Token saved to: {TOKEN_PATH}")
        print(f"⏰ Expires in: {token_data.get('expires_in', 'unknown')} seconds")
        print("\n💡 Next steps:")
        print("1. Run: pm2 restart watcher-linkedin")
        print("2. Test posting by dropping a task in watch_inbox/")
        print("\n⚠️  Security: Token is gitignored automatically")
    else:
        print("\n❌ Authentication may have failed. Check errors above.")


if __name__ == '__main__':
    main()
