"""
Instagram OAuth Setup Script
Authenticates with Instagram Graph API via Facebook for Business Account posting

Requirements:
1. Instagram Business or Creator Account
2. Facebook Page connected to Instagram account
3. Facebook Developer App with Instagram Basic Display or Instagram Graph API
4. Already completed setup_facebook.py (reuses Facebook tokens)

Setup Instructions:
1. Convert Instagram account to Business:
   - Instagram app → Settings → Account → Switch to Professional Account
2. Connect Instagram to Facebook Page:
   - Instagram → Settings → Account → Linked Accounts → Facebook
3. Facebook Developer Console:
   - Same app used for Facebook integration
   - No additional setup needed (uses Facebook Page access token)
4. Run: python setup_instagram.py
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Paths
FACEBOOK_TOKEN_PATH = Path('secrets/facebook_token.json')
INSTAGRAM_TOKEN_PATH = Path('secrets/instagram_token.json')


def load_facebook_tokens() -> dict:
    """Load Facebook tokens (already authenticated via setup_facebook.py)"""
    if not FACEBOOK_TOKEN_PATH.exists():
        raise FileNotFoundError(
            "Facebook token not found. Please run setup_facebook.py first."
        )
    
    with open(FACEBOOK_TOKEN_PATH, 'r') as f:
        return json.load(f)


def get_instagram_business_account(page_id: str, page_token: str) -> dict:
    """Get Instagram Business Account ID connected to Facebook Page"""
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    
    params = {
        'fields': 'instagram_business_account',
        'access_token': page_token
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if 'instagram_business_account' not in data:
        raise Exception(
            "No Instagram Business Account connected to this Facebook Page.\n"
            "Please:\n"
            "1. Convert your Instagram to a Business Account\n"
            "2. Connect it to your Facebook Page\n"
            "3. Go to Instagram → Settings → Account → Linked Accounts → Facebook"
        )
    
    return data['instagram_business_account']


def get_instagram_account_info(instagram_id: str, access_token: str) -> dict:
    """Get Instagram account details"""
    url = f"https://graph.facebook.com/v19.0/{instagram_id}"
    
    params = {
        'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count',
        'access_token': access_token
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def save_instagram_tokens(tokens: dict):
    """Save Instagram tokens to secrets directory"""
    INSTAGRAM_TOKEN_PATH.parent.mkdir(exist_ok=True)
    
    with open(INSTAGRAM_TOKEN_PATH, 'w') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n✅ Instagram tokens saved to: {INSTAGRAM_TOKEN_PATH}")
    print(f"   Username: @{tokens['username']}")
    print(f"   Account ID: {tokens['instagram_business_account_id']}")


def main():
    """Main Instagram setup flow"""
    print("="*70)
    print("Instagram Business Account Setup for Personal AI Employee")
    print("="*70)
    
    print("\n📌 This setup uses your existing Facebook authentication.")
    print("   Make sure you've already run setup_facebook.py\n")
    
    try:
        # Load Facebook tokens
        print("⏳ Step 1: Loading Facebook authentication...")
        fb_tokens = load_facebook_tokens()
        page_id = fb_tokens['page_id']
        page_token = fb_tokens['page_access_token']
        print(f"   ✅ Facebook Page: {fb_tokens['page_name']}")
        
        # Get Instagram Business Account ID
        print("\n⏳ Step 2: Finding connected Instagram Business Account...")
        ig_account = get_instagram_business_account(page_id, page_token)
        ig_id = ig_account['id']
        print(f"   ✅ Found Instagram Business Account ID: {ig_id}")
        
        # Get Instagram account details
        print("\n⏳ Step 3: Retrieving Instagram account information...")
        ig_info = get_instagram_account_info(ig_id, page_token)
        
        # Prepare tokens
        instagram_tokens = {
            'instagram_business_account_id': ig_id,
            'username': ig_info.get('username'),
            'name': ig_info.get('name'),
            'profile_picture_url': ig_info.get('profile_picture_url'),
            'followers_count': ig_info.get('followers_count', 0),
            'follows_count': ig_info.get('follows_count', 0),
            'media_count': ig_info.get('media_count', 0),
            'access_token': page_token,  # Same as Facebook Page token
            'facebook_page_id': page_id,
            'facebook_page_name': fb_tokens['page_name']
        }
        
        # Save tokens
        save_instagram_tokens(instagram_tokens)
        
        print("\n" + "="*70)
        print("✅ Instagram Business Account Setup Complete!")
        print("="*70)
        print(f"Username: @{instagram_tokens['username']}")
        print(f"Name: {instagram_tokens['name']}")
        print(f"Followers: {instagram_tokens['followers_count']:,}")
        print(f"Posts: {instagram_tokens['media_count']}")
        print(f"Connected to Facebook Page: {instagram_tokens['facebook_page_name']}")
        print("\nYou can now use the Instagram MCP server to post photos and stories.")
        print("Token file location: secrets/instagram_token.json")
        print("\nNext steps:")
        print("  1. Start watcher: python watcher_instagram.py")
        print("  2. Test posting via orchestrator")
        print("\nNote: Instagram posting requires:")
        print("  - Photo URLs (publicly accessible)")
        print("  - Caption (optional, max 2200 characters)")
        print("  - Hashtags (max 30 per post)")
        print("="*70)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 To fix this:")
        print("   1. Run: python setup_facebook.py")
        print("   2. Then run: python setup_instagram.py")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response:
            error_data = e.response.json()
            print(f"   Details: {error_data}")
            
            if 'instagram_business_account' in str(e):
                print("\n🔧 To fix this:")
                print("   1. Open Instagram app")
                print("   2. Go to Settings → Account")
                print("   3. Switch to Professional Account → Business")
                print("   4. Go to Linked Accounts → Facebook")
                print("   5. Connect to your Facebook Page")
                print("   6. Refresh and try again")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
