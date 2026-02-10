"""
Facebook Complete Setup - WITH POSTING PERMISSIONS
This gets a Page Access Token with pages_manage_posts permission
"""
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import webbrowser

load_dotenv()

print("="*80)
print("🔧 Facebook Posting Fix - Get Token with Correct Permissions")
print("="*80)

print("\n⚠️  CRITICAL: Your token needs these permissions:")
print("   ✅ pages_show_list")
print("   ✅ pages_read_engagement") 
print("   ✅ pages_manage_posts")
print("   ✅ pages_read_user_content")

print("\n📝 Step 1: Go to Graph API Explorer")
print("\nhttps://developers.facebook.com/tools/explorer")

print("\n🔧 Step 2: Configure Permissions")
print("   1. Select 'JARAGAR AI' app (top right)")
print("   2. Click 'Permissions' tab (middle of screen)")
print("   3. Click 'Add a Permission'")
print("   4. Search and enable these:")
print("      □ pages_show_list")
print("      □ pages_read_engagement")
print("      □ pages_manage_posts")
print("      □ pages_read_user_content")
print("   5. Click 'Generate Access Token'")
print("   6. Approve all permissions in popup")
print("   7. Copy the token")

# Open browser
webbrowser.open("https://developers.facebook.com/tools/explorer")

input("\n⏸️  Press Enter after you've enabled permissions and generated token...")

print("\n📋 Paste your User Access Token:")
user_token = input("Token: ").strip()

if not user_token or len(user_token) < 50:
    print("❌ Token too short")
    exit(1)

print("\n✅ Token received!")

# Step 1: Verify token has permissions
print("\n🔍 Verifying token permissions...")
try:
    perms_response = requests.get(
        'https://graph.facebook.com/v19.0/me/permissions',
        params={'access_token': user_token}
    )
    
    if perms_response.status_code == 200:
        perms = perms_response.json().get('data', [])
        granted = [p['permission'] for p in perms if p['status'] == 'granted']
        
        print(f"\n✅ Granted permissions: {', '.join(granted)}")
        
        required = ['pages_show_list', 'pages_manage_posts', 'pages_read_engagement']
        missing = [p for p in required if p not in granted]
        
        if missing:
            print(f"\n⚠️  WARNING: Missing permissions: {', '.join(missing)}")
            print("\nPosting may fail without these. Continue anyway? (y/n)")
            if input().lower() != 'y':
                exit(0)
    else:
        print(f"⚠️  Couldn't verify permissions: {perms_response.status_code}")
        
except Exception as e:
    print(f"⚠️  Permission check failed: {e}")
    print("Continuing anyway...")

# Step 2: Get pages and convert to page token
print("\n📡 Fetching your Facebook Pages...")

try:
    response = requests.get(
        'https://graph.facebook.com/v19.0/me/accounts',
        params={'access_token': user_token}
    )
    
    if response.status_code != 200:
        print(f"\n❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    data = response.json()
    
    if 'data' not in data or len(data['data']) == 0:
        print("\n❌ No pages found!")
        print("\nMake sure:")
        print("1. You're an admin of 'My Test Page'")
        print("2. Token has pages_show_list permission")
        exit(1)
    
    pages = data['data']
    print(f"\n✅ Found {len(pages)} page(s):\n")
    
    for i, page in enumerate(pages, 1):
        print(f"{i}. {page['name']} (ID: {page['id']})")
    
    # Select page
    if len(pages) == 1:
        selected = pages[0]
        print(f"\n✅ Auto-selected: {selected['name']}")
    else:
        choice = int(input(f"\nSelect page (1-{len(pages)}): ")) - 1
        selected = pages[choice]
    
    page_id = selected['id']
    page_name = selected['name']
    page_token = selected['access_token']
    
    # Step 3: Verify page token can post
    print("\n🧪 Testing page token permissions...")
    
    test_perms = requests.get(
        f'https://graph.facebook.com/v19.0/{page_id}',
        params={
            'access_token': page_token,
            'fields': 'name,fan_count,tasks'
        }
    )
    
    if test_perms.status_code == 200:
        test_data = test_perms.json()
        print(f"✅ Page token valid!")
        print(f"   Name: {test_data['name']}")
        print(f"   Followers: {test_data.get('fan_count', 0)}")
        
        tasks = test_data.get('tasks', [])
        if 'CREATE_CONTENT' in tasks or 'MANAGE' in tasks:
            print(f"   ✅ Posting permission confirmed!")
        else:
            print(f"   ⚠️  Warning: May not have posting permission")
            print(f"   Tasks: {tasks}")
    else:
        print(f"⚠️  Page test returned: {test_perms.status_code}")
    
    # Step 4: Save configuration
    print("\n💾 Saving configuration...")
    
    # Save to .env
    env_path = Path('.env')
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    token_found = False
    id_found = False
    
    for line in lines:
        if line.strip().startswith('FACEBOOK_PAGE_ACCESS_TOKEN='):
            new_lines.append(f'FACEBOOK_PAGE_ACCESS_TOKEN={page_token}\n')
            token_found = True
        elif line.strip().startswith('FACEBOOK_PAGE_ID='):
            new_lines.append(f'FACEBOOK_PAGE_ID={page_id}\n')
            id_found = True
        else:
            new_lines.append(line)
    
    if not token_found:
        new_lines.append(f'FACEBOOK_PAGE_ACCESS_TOKEN={page_token}\n')
    if not id_found:
        new_lines.append(f'FACEBOOK_PAGE_ID={page_id}\n')
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ .env updated!")
    
    # Save to secrets
    secrets_dir = Path('secrets')
    secrets_dir.mkdir(exist_ok=True)
    
    with open(secrets_dir / 'facebook_token.json', 'w') as f:
        json.dump({
            'page_id': page_id,
            'page_name': page_name,
            'page_access_token': page_token,
            'setup_date': '2026-02-10',
            'permissions': granted if 'granted' in locals() else []
        }, f, indent=2)
    
    print("✅ secrets/facebook_token.json saved!")
    
    print("\n" + "="*80)
    print("✅ Facebook Setup Complete with Posting Permissions!")
    print("="*80)
    print(f"\nPage: {page_name}")
    print(f"ID: {page_id}")
    print(f"Token: {page_token[:40]}...")
    print("\n🚀 Ready to test posting!")
    print("\nNext: python post_facebook_now.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
