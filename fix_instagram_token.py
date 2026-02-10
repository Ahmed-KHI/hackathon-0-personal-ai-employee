"""
Fix Instagram Token - Get Long-Lived Access Token
Uses Facebook's Graph API to exchange for 60-day token
"""
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

print("="*80)
print("Instagram Long-Lived Token Generator")
print("="*80)

# Load Facebook credentials
app_id = os.getenv('FACEBOOK_APP_ID')
app_secret = os.getenv('FACEBOOK_APP_SECRET')

if not app_id or not app_secret:
    print("❌ Missing FACEBOOK_APP_ID or FACEBOOK_APP_SECRET in .env")
    exit(1)

# Load current Instagram token
token_file = Path('secrets/instagram_token.json')
if not token_file.exists():
    print("❌ Instagram token file not found")
    exit(1)

with open(token_file, 'r') as f:
    data = json.load(f)

short_token = data['access_token']
account_id = data['business_account_id']

print(f"✅ Loaded token for account: {account_id}")
print(f"\n⏳ Exchanging for long-lived token...")

try:
    # Exchange for 60-day token
    response = requests.get(
        'https://graph.facebook.com/v19.0/oauth/access_token',
        params={
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': short_token
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Token exchange failed: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    result = response.json()
    new_token = result['access_token']
    expires_in = result.get('expires_in', 'unknown')
    
    print(f"✅ Long-lived token obtained!")
    print(f"   Expires in: {expires_in} seconds (~{expires_in//86400} days)")
    
    # Update JSON file
    data['access_token'] = new_token
    
    with open(token_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Token updated in {token_file}")
    
    # Test the token
    print("\n⏳ Testing token...")
    test = requests.get(
        f'https://graph.facebook.com/v19.0/{account_id}',
        params={'access_token': new_token, 'fields': 'username,name'}
    )
    
    if test.status_code == 200:
        test_data = test.json()
        print(f"✅ Token works!")
        print(f"   Account: @{test_data.get('username', 'N/A')}")
        print(f"   Name: {test_data.get('name', 'N/A')}")
    else:
        print(f"⚠️  Token test returned: {test.status_code}")
        print(f"Response: {test.text}")
    
    print("\n" + "="*80)
    print("✅ Instagram Token Updated!")
    print("="*80)
    print("\n🚀 Ready to test: python post_instagram_live.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
