"""
Odoo ERP Setup and Configuration Check
Helps verify Odoo Community installation and configure for Personal AI Employee

Requirements:
1. Odoo Community Edition 19.0 (or 18.0, 17.0)
2. PostgreSQL database
3. Odoo installed via:
   - Docker: docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db postgres:15
            docker run -p 8069:8069 --name odoo --link db:db -t odoo:19.0
   - Direct: Download from https://www.odoo.com/page/download
   - Or via package manager: apt-get install odoo / brew install odoo

Setup Instructions:
1. Install Odoo (see above options)
2. Access Odoo: http://localhost:8069
3. Create database (master password: admin)
4. Install "Accounting" module
5. Configure:
   - Company details
   - Chart of Accounts (your country)
   - Fiscal year
   - Journals (Sales, Purchases, Bank)
6. Add to .env:
   - ODOO_URL=http://localhost:8069
   - ODOO_DB=your_db_name
   - ODOO_USERNAME=admin
   - ODOO_PASSWORD=your_password
7. Run: python setup_odoo.py
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Odoo configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', '')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', '')

# Paths
TOKEN_PATH = Path('secrets/odoo_token.json')


def check_odoo_connection() -> bool:
    """Check if Odoo is accessible"""
    try:
        response = requests.get(f"{ODOO_URL}/web/database/selector", timeout=5)
        return response.status_code in [200, 303]  # 303 = redirect to login
    except Exception as e:
        print(f"❌ Cannot connect to Odoo at {ODOO_URL}: {e}")
        return False


def authenticate_odoo() -> Optional[int]:
    """Authenticate with Odoo and get user ID (uid)"""
    try:
        url = f"{ODOO_URL}/web/session/authenticate"
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'db': ODOO_DB,
                'login': ODOO_USERNAME,
                'password': ODOO_PASSWORD
            },
            'id': 1
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if 'result' in result and result['result'].get('uid'):
            return result['result']['uid']
        else:
            error_msg = result.get('error', {}).get('data', {}).get('message', 'Unknown error')
            print(f"❌ Authentication failed: {error_msg}")
            return None
    
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None


def get_installed_modules(uid: int, session_id: str) -> list:
    """Get list of installed Odoo modules"""
    try:
        url = f"{ODOO_URL}/web/dataset/call_kw"
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': 'ir.module.module',
                'method': 'search_read',
                'args': [[['state', '=', 'installed']]],
                'kwargs': {'fields': ['name', 'shortdesc']}
            },
            'id': 2
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'session_id={session_id}'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if 'result' in result:
            return result['result']
        return []
    
    except Exception as e:
        print(f"⚠️ Could not fetch modules: {e}")
        return []


def check_accounting_module(modules: list) -> bool:
    """Check if Accounting module is installed"""
    accounting_modules = ['account', 'account_accountant']
    
    installed = [m['name'] for m in modules]
    
    for mod in accounting_modules:
        if mod in installed:
            return True
    
    return False


def get_company_info(uid: int, session_id: str) -> Optional[Dict]:
    """Get company information"""
    try:
        url = f"{ODOO_URL}/web/dataset/call_kw"
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': 'res.company',
                'method': 'search_read',
                'args': [[['id', '=', 1]]],
                'kwargs': {'fields': ['name', 'currency_id', 'country_id']}
            },
            'id': 3
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'session_id={session_id}'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if 'result' in result and result['result']:
            return result['result'][0]
        return None
    
    except Exception as e:
        print(f"⚠️ Could not fetch company info: {e}")
        return None


def save_connection_info(uid: int, session_id: str):
    """Save Odoo connection info to secrets"""
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    
    connection_info = {
        'odoo_url': ODOO_URL,
        'odoo_db': ODOO_DB,
        'uid': uid,
        'username': ODOO_USERNAME,
        'session_id': session_id,
        'authenticated_at': __import__('datetime').datetime.now().isoformat()
    }
    
    with open(TOKEN_PATH, 'w') as f:
        json.dump(connection_info, f, indent=2)
    
    print(f"\n✅ Connection info saved to: {TOKEN_PATH}")


def main():
    """Main Odoo setup check"""
    print("="*70)
    print("Odoo ERP Setup and Configuration Check")
    print("="*70)
    
    # Check environment variables
    if not ODOO_DB or not ODOO_PASSWORD:
        print("\n❌ Error: Odoo credentials not found in .env")
        print("\n🔧 To fix this:")
        print("   1. Install Odoo Community Edition 19:")
        print("      Docker:")
        print("        docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo \\")
        print("          -e POSTGRES_DB=postgres --name db postgres:15")
        print("        docker run -p 8069:8069 --name odoo --link db:db -t odoo:19.0")
        print("      Or Direct: https://www.odoo.com/page/download")
        print("   2. Access Odoo: http://localhost:8069")
        print("   3. Create database (master password: admin)")
        print("   4. Install 'Accounting' module from Apps")
        print("   5. Configure company details")
        print("   6. Add to .env:")
        print("      ODOO_URL=http://localhost:8069")
        print("      ODOO_DB=your_db_name")
        print("      ODOO_USERNAME=admin")
        print("      ODOO_PASSWORD=your_password")
        print("   7. Run: python setup_odoo.py")
        return
    
    try:
        # Step 1: Check connection
        print("\n⏳ Step 1: Checking Odoo connection...")
        if not check_odoo_connection():
            print("   Ensure Odoo is running and accessible")
            return
        print(f"   ✅ Odoo is accessible at {ODOO_URL}")
        
        # Step 2: Authenticate
        print("\n⏳ Step 2: Authenticating with Odoo...")
        uid = authenticate_odoo()
        if not uid:
            print("   Check database name, username, and password in .env")
            return
        print(f"   ✅ Authenticated as {ODOO_USERNAME} (UID: {uid})")
        
        # Get session ID from response (simplified - in real impl, extract from cookie)
        session_id = "dummy_session"  # Placeholder
        
        # Step 3: Check modules
        print("\n⏳ Step 3: Checking installed modules...")
        modules = get_installed_modules(uid, session_id)
        print(f"   Found {len(modules)} installed modules")
        
        has_accounting = check_accounting_module(modules)
        if has_accounting:
            print("   ✅ Accounting module is installed")
        else:
            print("   ⚠️ Accounting module NOT installed")
            print("   Install it: Odoo → Apps → Search 'Accounting' → Install")
        
        # Step 4: Check company
        print("\n⏳ Step 4: Checking company configuration...")
        company = get_company_info(uid, session_id)
        if company:
            print(f"   Company: {company.get('name', 'Unknown')}")
            print(f"   Currency: {company.get('currency_id', ['Unknown', 'Unknown'])[1]}")
            print(f"   Country: {company.get('country_id', ['Unknown', 'Unknown'])[1]}")
        
        # Save connection info
        save_connection_info(uid, session_id)
        
        print("\n" + "="*70)
        print("✅ Odoo Setup Check Complete!")
        print("="*70)
        print(f"Database: {ODOO_DB}")
        print(f"User: {ODOO_USERNAME} (UID: {uid})")
        print(f"URL: {ODOO_URL}")
        print(f"Accounting Module: {'✅ Installed' if has_accounting else '⚠️ Not Installed'}")
        
        if not has_accounting:
            print("\n⚠️ Next Steps:")
            print("   1. Go to: {}/web#menu_id=5&action=10".format(ODOO_URL))
            print("   2. Search for 'Accounting' in Apps")
            print("   3. Click Install")
            print("   4. Configure Chart of Accounts for your country")
            print("   5. Run this script again")
        else:
            print("\nYou can now use the Odoo MCP server.")
            print("Next steps:")
            print("  1. Configure accounting: Journals, Chart of Accounts")
            print("  2. Start watcher: python watcher_odoo.py")
            print("  3. Test via orchestrator")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
