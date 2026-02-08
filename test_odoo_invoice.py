#!/usr/bin/env python3
"""Quick test script for Odoo MCP server"""

from mcp_servers.odoo_server.odoo_server import OdooServer
import json

def main():
    print("=" * 70)
    print("Testing Odoo MCP Server")
    print("=" * 70)
    
    server = OdooServer()
    
    # Test 1: Create Invoice
    print("\n📝 Test 1: Creating customer invoice...")
    result1 = server.process_action('create_invoice', {
        'partner_name': 'Acme Corporation',
        'amount': 2500.00,
        'description': 'Web development services - January 2026',
        'dry_run': False
    })
    print(json.dumps(result1, indent=2))
    
    if result1.get('status') == 'success':
        invoice_id = result1.get('invoice_id')
        print(f"✅ Invoice created successfully! ID: {invoice_id}")
        
        # Test 2: List Invoices
        print("\n📋 Test 2: Listing invoices...")
        result2 = server.process_action('list_invoices', {
            'limit': 5,
            'state': 'posted'
        })
        print(json.dumps(result2, indent=2))
        
        # Test 3: Record Payment
        if invoice_id:
            print(f"\n💰 Test 3: Recording payment for invoice {invoice_id}...")
            result3 = server.process_action('record_payment', {
                'invoice_id': invoice_id,
                'amount': 2500.00,
                'payment_date': '2026-02-08'
            })
            print(json.dumps(result3, indent=2))
    else:
        print(f"❌ Failed to create invoice: {result1.get('message')}")
    
    # Test 4: Create Vendor Bill
    print("\n📄 Test 4: Creating vendor bill...")
    result4 = server.process_action('create_bill', {
        'vendor_name': 'AWS',
        'amount': 450.00,
        'description': 'Cloud hosting - February 2026',
        'dry_run': False
    })
    print(json.dumps(result4, indent=2))
    
    # Test 5: Get Account Balance
    print("\n💵 Test 5: Getting account balances...")
    result5 = server.process_action('get_balance', {
        'account_type': 'asset_receivable'
    })
    print(json.dumps(result5, indent=2))
    
    # Test 6: Get Partner Balance
    print("\n🏢 Test 6: Getting partner balance...")
    result6 = server.process_action('get_partner_balance', {
        'partner_name': 'Acme'
    })
    print(json.dumps(result6, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)

if __name__ == '__main__':
    main()
