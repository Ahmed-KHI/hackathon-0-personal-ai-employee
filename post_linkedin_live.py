"""
LinkedIn Live Post Test Script
Posts a test update to verify LinkedIn API integration

This script:
1. Loads OAuth 2.0 access token from secrets/linkedin_token.json
2. Gets user profile (sub/urn)
3. Posts a text update to LinkedIn
4. Logs the result to audit logs
"""

import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
TOKEN_PATH = Path('secrets/linkedin_token.json')
AUDIT_LOG_PATH = Path('audit_logs')

# LinkedIn API v2 endpoints
USERINFO_URL = 'https://api.linkedin.com/v2/userinfo'
POST_URL = 'https://api.linkedin.com/v2/ugcPosts'


def load_token():
    """Load LinkedIn OAuth token"""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(f"LinkedIn token not found at {TOKEN_PATH}")
    
    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)
    
    return token_data['access_token']


def get_user_profile(access_token: str) -> dict:
    """Get user profile using OpenID Connect userinfo endpoint"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(USERINFO_URL, headers=headers)
    response.raise_for_status()
    
    return response.json()


def post_to_linkedin(text: str, access_token: str, author_urn: str) -> dict:
    """Post a text update to LinkedIn using UGC Posts API"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    # UGC Post payload
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(POST_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


def audit_log(post_data: dict, post_text: str):
    """Log LinkedIn post to audit trail"""
    AUDIT_LOG_PATH.mkdir(exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': 'linkedin_post',
        'post_id': post_data.get('id', 'unknown'),
        'post_text': post_text,
        'status': 'success'
    }
    
    # Append to today's audit log
    log_file = AUDIT_LOG_PATH / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"✅ Audit log entry created: {log_file}")


def main():
    """Main test flow"""
    print("="*70)
    print("LinkedIn Live Post Test - Personal AI Employee")
    print("="*70)
    
    try:
        # Load token
        print("\n⏳ Loading LinkedIn OAuth token...")
        access_token = load_token()
        print("✅ Token loaded successfully")
        
        # Get user profile
        print("\n⏳ Retrieving user profile...")
        profile = get_user_profile(access_token)
        print(f"✅ Authenticated as: {profile.get('name', 'Unknown')}")
        print(f"   Sub (ID): {profile.get('sub', 'N/A')}")
        if 'email' in profile:
            print(f"   Email: {profile['email']}")
        
        # Convert sub to author URN
        author_urn = f"urn:li:person:{profile['sub']}"
        print(f"   Author URN: {author_urn}")
        
        # Compose LinkedIn post
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        post_text = f"""🤖 Personal AI Employee - LinkedIn Integration Test

✅ Successfully authenticated via OAuth 2.0 with OpenID Connect
🔧 Automated posting working perfectly
📅 {timestamp}

This post was created by an AI-powered automation system with full human oversight. Building the future of personal productivity!

#AI #Automation #Productivity #Hackathon #LinkedInAPI"""
        
        print(f"\n📝 Post content:")
        print("-" * 70)
        print(post_text)
        print("-" * 70)
        
        # Post to LinkedIn
        print("\n⏳ Posting to LinkedIn...")
        result = post_to_linkedin(post_text, access_token, author_urn)
        
        print("\n" + "="*70)
        print("✅ LINKEDIN POST PUBLISHED SUCCESSFULLY!")
        print("="*70)
        print(f"\n🆔 Post ID: {result.get('id', 'N/A')}")
        print(f"📝 Post Text: {post_text[:100]}...")
        print(f"\n🔗 View your post on LinkedIn:")
        print(f"   https://www.linkedin.com/feed/")
        print(f"   (Check your profile's recent activity)")
        
        # Audit log
        print("\n⏳ Creating audit log...")
        audit_log(result, post_text)
        
        print("\n" + "="*70)
        print("✅ LinkedIn Integration Test Complete!")
        print("="*70)
        print("\n💡 Next Steps:")
        print("   1. View your post on LinkedIn.com")
        print("   2. Start watcher: python watcher_linkedin.py")
        print("   3. Test end-to-end workflow with orchestrator")
        print("\n⚠️  Note: Access token expires in ~60 days (very long-lived)")
        print("="*70)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response:
            try:
                error_data = e.response.json()
                print(f"   Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {e.response.text}")
        
        print("\n🔧 Troubleshooting:")
        print("   - Verify 'Share on LinkedIn' product is added")
        print("   - Check token hasn't expired (should last 60 days)")
        print("   - Ensure w_member_social scope is granted")
        print("   - Run setup_linkedin_v2.py again if needed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
