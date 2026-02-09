"""
Facebook Page Token - Working 2026 Method
Gets USER token, converts to PAGE token via API
"""
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("Facebook Page Token Setup - Working Method")
print("="*70)

print("\n📝 Step 1: Get a User Access Token")
print("\nGo to: https://developers.facebook.com/tools/explorer")
print("\n1. Select your 'JARAGAR AI' app (top right dropdown)")
print("2. Click 'Generate Access Token' button")
print("3. In the popup, just click 'Continue' (default permissions are fine)")
print("4. Copy the token that appears in the 'Access Token' field")
print("\nThis will be a USER token - we'll convert it to a PAGE token")
print("="*70)

import webbrowser
webbrowser.open("https://developers.facebook.com/tools/explorer")

print("\n⏳ After getting your token, paste it here:")
user_token = input("User Token: ").strip()

if not user_token or len(user_token) < 50:
    print("❌ Token too short")
    exit(1)

print("\n✅ Token received! Converting to Page Token...")

# Step 2: Use the user token to get page tokens
try:
    response = requests.get(
        'https://graph.facebook.com/v19.0/me/accounts',
        params={'access_token': user_token}
    )
    
    if response.status_code != 200:
        print(f"\n❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Check if it's a permissions error
        if 'permissions' in response.text.lower() or 'scope' in response.text.lower():
            print("\n🔧 Your token needs page permissions!")
            print("\nIn Graph API Explorer:")
            print("1. Look for 'Permissions' section")
            print("2. Click 'Add a Permission'")
            print("3. Search for: pages_show_list")
            print("4. Enable it and click 'Generate Access Token' again")
        exit(1)
    
    data = response.json()
    
    if 'data' not in data or len(data['data']) == 0:
        print("\n❌ No pages found for this user token!")
        print("\nPossible reasons:")
        print("1. You're not an admin of 'My Test Page'")
        print("2. The token doesn't have pages_show_list permission")
        print("3. Your page isn't connected to Facebook")
        print(f"\nAPI Response: {json.dumps(data, indent=2)}")
        exit(1)
    
    pages = data['data']
    print(f"\n✅ Found {len(pages)} page(s)!\n")
    
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
    
    print("\n" + "="*70)
    print("🎉 SUCCESS - Page Token Obtained!")
    print("="*70)
    print(f"Page: {page_name}")
    print(f"ID: {page_id}")
    print(f"Token: {page_token[:40]}...")
    
    # Save to .env
    print("\n📋 Saving configuration...")
    
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
    
    if not token_found or not id_found:
        for i, line in enumerate(new_lines):
            if 'FACEBOOK_APP_SECRET=' in line:
                idx = i + 1
                if not id_found:
                    new_lines.insert(idx, f'FACEBOOK_PAGE_ID={page_id}\n')
                    idx += 1
                if not token_found:
                    new_lines.insert(idx, f'FACEBOOK_PAGE_ACCESS_TOKEN={page_token}\n')
                break
    
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
            'page_access_token': page_token
        }, f, indent=2)
    
    print("✅ secrets/facebook_token.json saved!")
    
    # Test
    print("\n📋 Testing token...")
    test = requests.get(
        f'https://graph.facebook.com/v19.0/{page_id}',
        params={'access_token': page_token, 'fields': 'name,fan_count'}
    )
    
    if test.status_code == 200:
        test_data = test.json()
        print(f"✅ Token works!")
        print(f"   Page: {test_data['name']}")
        print(f"   Followers: {test_data.get('fan_count', 0)}")
    else:
        print(f"⚠️  Test returned: {test.status_code}")
    
    print("\n" + "="*70)
    print("✅ Setup Complete!")
    print("="*70)
    print("\nNext: python test_facebook_setup.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
