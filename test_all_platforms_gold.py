"""
ALL PLATFORMS TEST - Verify LinkedIn, Instagram, AND Facebook
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp_servers.linkedin_server.linkedin_server import LinkedInMCPServer
from mcp_servers.instagram_server.instagram_server import InstagramServer  
from mcp_servers.facebook_server.facebook_server import FacebookServer
from datetime import datetime

print("="*80)
print("🚀 GOLD TIER VERIFICATION - ALL 3 PLATFORMS TEST")
print("="*80)

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

# Test content
post_content = f"""🎉 Gold Tier Complete - All Platforms Working!

✅ LinkedIn - Automated posting verified
✅ Instagram - Image posting verified  
✅ Facebook - Page posting verified

The Personal AI Employee system is now posting autonomously to all 3 major platforms with human oversight.

Posted: {timestamp}

#GoldTier #Automation #PersonalAI #MultiPlatform #Achievement"""

results = {}

# =============================================================================
# TEST 1: LINKEDIN
# =============================================================================
print("\n" + "="*80)
print("📱 TEST 1/3: LINKEDIN")
print("="*80)

try:
    print("⏳ Authenticating with LinkedIn...")
    linkedin = LinkedInMCPServer()
    
    print("⏳ Posting to LinkedIn...")
    result = linkedin.post_update(
        text=post_content,
        visibility="PUBLIC"
    )
    
    if result.get('success'):
        print(f"✅ LINKEDIN SUCCESS!")
        print(f"   Post ID: {result.get('post_id')}")
        results['linkedin'] = 'SUCCESS'
    else:
        print(f"❌ LINKEDIN FAILED: {result}")
        results['linkedin'] = 'FAILED'
        
except Exception as e:
    print(f"❌ LINKEDIN ERROR: {e}")
    results['linkedin'] = f'ERROR: {e}'

# =============================================================================
# TEST 2: INSTAGRAM  
# =============================================================================
print("\n" + "="*80)
print("📷 TEST 2/3: INSTAGRAM")
print("="*80)

try:
    print("⏳ Authenticating with Instagram...")
    instagram = InstagramServer()
    
    print("⏳ Posting to Instagram...")
    result = instagram.post_photo(
        image_url='https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=1080&h=1080&fit=crop&q=80',
        caption=post_content
    )
    
    if result.get('success'):
        print(f"✅ INSTAGRAM SUCCESS!")
        print(f"   Post ID: {result.get('post_id')}")
        results['instagram'] = 'SUCCESS'
    else:
        print(f"❌ INSTAGRAM FAILED: {result}")
        results['instagram'] = 'FAILED'
        
except Exception as e:
    print(f"❌ INSTAGRAM ERROR: {e}")
    results['instagram'] = f'ERROR: {e}'

# =============================================================================
# TEST 3: FACEBOOK
# =============================================================================
print("\n" + "="*80)
print("👤 TEST 3/3: FACEBOOK")
print("="*80)

try:
    print("⏳ Authenticating with Facebook...")
    facebook = FacebookServer()
    
    print("⏳ Posting to Facebook...")
    result = facebook.post_message(message=post_content)
    
    if result.get('status') == 'success':
        print(f"✅ FACEBOOK SUCCESS!")
        print(f"   Post ID: {result.get('post_id')}")
        results['facebook'] = 'SUCCESS'
    else:
        print(f"❌ FACEBOOK FAILED: {result}")
        results['facebook'] = 'FAILED'
        
except Exception as e:
    print(f"❌ FACEBOOK ERROR: {e}")
    results['facebook'] = f'ERROR: {e}'

# =============================================================================
# FINAL RESULTS
# =============================================================================
print("\n" + "="*80)
print("📊 FINAL RESULTS - GOLD TIER VERIFICATION")
print("="*80)

success_count = sum(1 for v in results.values() if v == 'SUCCESS')

for platform, status in results.items():
    icon = "✅" if status == "SUCCESS" else "❌"
    print(f"{icon} {platform.upper()}: {status}")

print("\n" + "="*80)
if success_count == 3:
    print("🏆 GOLD TIER COMPLETE - ALL 3 PLATFORMS WORKING!")
    print("="*80)
    print("\n✅ LinkedIn posting: VERIFIED")
    print("✅ Instagram posting: VERIFIED")
    print("✅ Facebook posting: VERIFIED")
    print("\n🚀 Ready for Platinum Tier features!")
    exit(0)
elif success_count == 2:
    print("⚠️  GOLD TIER INCOMPLETE - 1 PLATFORM FAILING")
    print("="*80)
    failed = [k for k, v in results.items() if v != 'SUCCESS'][0]
    print(f"\n⚠️  {failed.upper()} needs attention")
    print(f"\nTo fix {failed}:")
    if failed == 'facebook':
        print("   Run: python fix_facebook_permissions.py")
    exit(1)
else:
    print("❌ GOLD TIER FAILED - MULTIPLE PLATFORMS NOT WORKING")
    print("="*80)
    exit(1)
