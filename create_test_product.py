"""
Create a test service product in Odoo via API
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers" / "odoo_server"))

from odoo_server import OdooServer

def create_test_product():
    """Create a test service product in Odoo"""
    
    print("=" * 70)
    print("CREATING TEST PRODUCT IN ODOO")
    print("=" * 70)
    
    try:
        # Connect to Odoo
        print("\n⏳ Connecting to Odoo...")
        server = OdooServer()
        print(f"   ✅ Connected! UID: {server.uid}")
        
        # Create service product
        print("\n⏳ Creating 'Consulting Service' product...")
        
        product_data = {
            'name': 'Consulting Service',
            'type': 'service',  # Service product
            'list_price': 150.00,  # Sales price
            'standard_price': 0.00,  # Cost price
            'sale_ok': True,  # Can be sold
            'purchase_ok': False,  # Not purchasable
            'description_sale': 'Professional consulting and advisory services',
        }
        
        # Create the product
        product_id = server._call_odoo(
            'product.product',
            'create',
            [product_data]
        )
        
        print(f"   ✅ Product created successfully! ID: {product_id}")
        
        # Verify it was created
        print("\n⏳ Verifying product...")
        product = server._call_odoo(
            'product.product',
            'read',
            [[product_id]],
            {'fields': ['name', 'list_price', 'type']}
        )
        
        if product:
            p = product[0]
            print(f"   ✅ Verified:")
            print(f"      - Name: {p['name']}")
            print(f"      - Price: ${p['list_price']}")
            print(f"      - Type: {p['type']}")
        
        print("\n" + "=" * 70)
        print("✅ PRODUCT CREATED SUCCESSFULLY!")
        print("=" * 70)
        print("\n📊 You can now:")
        print("   1. Create invoices using this product")
        print("   2. View it in Odoo: Invoicing → Configuration → Products")
        print("   3. Run: python test_odoo_integration.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  This might mean:")
        print("   - You don't have permission to create products")
        print("   - The product might already exist")
        print("   - Odoo connection issue")
        return False

if __name__ == '__main__':
    load_dotenv()
    success = create_test_product()
    sys.exit(0 if success else 1)
