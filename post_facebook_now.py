#!/usr/bin/env python3
"""
Facebook Live Post Test - Personal AI Employee
"""
import json
import sys
from pathlib import Path

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_servers.facebook_server.facebook_server import FacebookServer

def main():
    print("=" * 80)
    print("Facebook Live Post Test - Personal AI Employee")
    print("=" * 80)
    print()
    
    try:
        # Initialize Facebook server
        print("⏳ Loading Facebook OAuth token...")
        fb = FacebookServer()
        print("✅ Token loaded successfully")
        print()
        
        # Post content
        post_text = """🤖 Personal AI Employee - Facebook Integration Test 

✅ Successfully authenticated via Facebook Graph API
🔧 Automated posting working perfectly
📅 2026-02-10 16:35:00 UTC

This post was created by an AI-powered automation system with full human oversight. Building the future of personal productivity!

#AI #Automation #Productivity #Hackathon #FacebookAPI"""
        
        print("📝 Post content:")
        print("-" * 80)
        print(post_text)
        print("-" * 80)
        print()
        
        # Post to Facebook
        print("⏳ Posting to Facebook...")
        result = fb.post_message(post_text)
        
        if result.get("success"):
            print()
            print("=" * 80)
            print("✅ FACEBOOK POST PUBLISHED SUCCESSFULLY!")
            print("=" * 80)
            print(f"🆔 Post ID: {result.get('post_id', 'N/A')}")
            print(f"📝 Post Text: {post_text[:100]}...")
            print()
            print("🔗 View your post on Facebook:")
            print("   https://www.facebook.com/me")
            print("   (Check your profile's recent activity)")
            print()
            
            # Audit log
            print("⏳ Creating audit log...")
            from datetime import datetime
            import os
            
            log_dir = Path(__file__).parent / "audit_logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            
            with open(log_file, "a", encoding="utf-8") as f:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "action": "social_post",
                    "platform": "facebook",
                    "post_id": result.get("post_id"),
                    "success": True,
                    "source": "manual_test"
                }
                f.write(json.dumps(log_entry) + "\n")
            
            print(f"✅ Audit log entry created: {log_file}")
            print()
            print("=" * 80)
            print("✅ Facebook Integration Test Complete!")
            print("=" * 80)
            print("💡 Next Steps:")
            print("   1. View your post on Facebook.com")
            print("   2. Start watcher: python watcher_facebook.py")
            print("   3. Test end-to-end workflow with orchestrator")
            print()
            print("=" * 80)
        else:
            print()
            print("❌ FACEBOOK POST FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Full response: {result}")
            sys.exit(1)
            
    except Exception as e:
        print()
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
