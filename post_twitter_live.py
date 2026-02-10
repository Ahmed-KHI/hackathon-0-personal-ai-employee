"""
Twitter Live Post Test Script
Posts a test tweet to verify Twitter API v2 integration

This script:
1. Loads OAuth 2.0 access token from secrets/twitter_token.json
2. Posts a tweet with timestamp
3. Logs the result to audit logs
"""

import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
TOKEN_PATH = Path('secrets/twitter_token.json')
AUDIT_LOG_PATH = Path('audit_logs')

# Twitter API v2 endpoint
TWEET_URL = 'https://api.twitter.com/2/tweets'


def load_token():
    """Load Twitter OAuth token"""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(f"Twitter token not found at {TOKEN_PATH}")
    
    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)
    
    return token_data['access_token']


def post_tweet(text: str, access_token: str) -> dict:
    """Post a tweet using Twitter API v2"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'text': text
    }
    
    response = requests.post(TWEET_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


def audit_log(tweet_data: dict):
    """Log tweet to audit trail"""
    AUDIT_LOG_PATH.mkdir(exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': 'twitter_post',
        'tweet_id': tweet_data['data']['id'],
        'tweet_text': tweet_data['data']['text'],
        'status': 'success'
    }
    
    # Append to today's audit log
    log_file = AUDIT_LOG_PATH / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"✅ Audit log entry created: {log_file}")


def get_user_info(access_token: str) -> dict:
    """Get authenticated user information"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'user.fields': 'id,username,name,public_metrics'
    }
    
    response = requests.get(
        'https://api.twitter.com/2/users/me',
        headers=headers,
        params=params
    )
    response.raise_for_status()
    
    return response.json()['data']


def main():
    """Main test flow"""
    print("="*70)
    print("Twitter Live Post Test - Personal AI Employee")
    print("="*70)
    
    try:
        # Load token
        print("\n⏳ Loading Twitter OAuth token...")
        access_token = load_token()
        print("✅ Token loaded successfully")
        
        # Get user info
        print("\n⏳ Retrieving user information...")
        user_info = get_user_info(access_token)
        print(f"✅ Authenticated as: @{user_info['username']} ({user_info['name']})")
        print(f"   User ID: {user_info['id']}")
        
        if 'public_metrics' in user_info:
            metrics = user_info['public_metrics']
            print(f"   Followers: {metrics.get('followers_count', 0):,}")
            print(f"   Following: {metrics.get('following_count', 0):,}")
            print(f"   Tweets: {metrics.get('tweet_count', 0):,}")
        
        # Compose tweet
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        tweet_text = f"""🤖 Personal AI Employee - Twitter Integration Test

✅ Successfully authenticated via OAuth 2.0
🔧 Automated posting working perfectly
📅 {timestamp}

#AI #Automation #Hackathon"""
        
        print(f"\n📝 Tweet content:")
        print("-" * 70)
        print(tweet_text)
        print("-" * 70)
        
        # Post tweet
        print("\n⏳ Posting tweet...")
        result = post_tweet(tweet_text, access_token)
        
        print("\n" + "="*70)
        print("✅ TWEET POSTED SUCCESSFULLY!")
        print("="*70)
        print(f"\n🆔 Tweet ID: {result['data']['id']}")
        print(f"📝 Tweet Text: {result['data']['text'][:100]}...")
        print(f"\n🔗 View tweet at:")
        print(f"   https://twitter.com/{user_info['username']}/status/{result['data']['id']}")
        
        # Audit log
        print("\n⏳ Creating audit log...")
        audit_log(result)
        
        print("\n" + "="*70)
        print("✅ Twitter Integration Test Complete!")
        print("="*70)
        print("\n💡 Next Steps:")
        print("   1. View your tweet on Twitter/X")
        print("   2. Start watcher: python watcher_twitter.py")
        print("   3. Test end-to-end workflow with orchestrator")
        print("\n⚠️  Note: Access token expires in 2 hours. Refresh token allows renewal.")
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
        print("   - Check that app has Read and Write permissions")
        print("   - Verify token hasn't expired (2 hour limit)")
        print("   - Run setup_twitter.py again to get fresh token")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
