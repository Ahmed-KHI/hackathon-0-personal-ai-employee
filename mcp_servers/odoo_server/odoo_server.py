"""
Odoo ERP MCP Server
Handles Odoo JSON-RPC interactions for accounting and business management

Actions:
- create_invoice: Create customer invoice
- create_bill: Create vendor bill
- record_payment: Record payment for invoice/bill
- get_balance: Get account balance or financial summary
- list_invoices: Get recent invoices
- list_bills: Get recent bills
- get_partner_balance: Get customer/vendor balance
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class OdooServer:
    """Odoo JSON-RPC MCP Server"""
    
    def __init__(self, token_path: str = "./secrets/odoo_token.json"):
        self.token_path = Path(token_path)
        self.config = self._load_config()
        
        self.odoo_url = os.getenv('ODOO_URL', 'http://localhost:8069')
        self.odoo_db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME', 'admin')
        self.password = os.getenv('ODOO_PASSWORD')
        
        self.uid = None
        self.session_id = None
        self.session = requests.Session()  # Persistent session for cookies
        
        # Authenticate on init
        self._authenticate()
        
    def _load_config(self) -> Dict:
        """Load Odoo connection config from secrets"""
        if self.token_path.exists():
            try:
                with open(self.token_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _authenticate(self):
        """Authenticate with Odoo and get UID"""
        try:
            url = f"{self.odoo_url}/web/session/authenticate"
            
            payload = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'db': self.odoo_db,
                    'login': self.username,
                    'password': self.password
                },
                'id': 1
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if 'result' in result:
                self.uid = result['result'].get('uid')
                self.session_id = result['result'].get('session_id')
                
                if not self.uid:
                    raise Exception("Authentication failed: No UID returned")
            else:
                error = result.get('error', {})
                raise Exception(f"Authentication failed: {error}")
        
        except Exception as e:
            raise Exception(f"Odoo authentication error: {e}")
    
    def _call_odoo(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        """Make JSON-RPC call to Odoo"""
        if not self.uid:
            raise Exception("Not authenticated with Odoo")
        
        url = f"{self.odoo_url}/web/dataset/call_kw/{model}/{method}"
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': model,
                'method': method,
                'args': args,
                'kwargs': kwargs or {}
            },
            'id': datetime.now().timestamp()
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Session cookies are handled automatically by self.session
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                error_msg = result['error'].get('data', {}).get('message', 'Unknown error')
                raise Exception(f"Odoo API error: {error_msg}")
            
            return result.get('result')
        
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error calling Odoo: {e}")
    
    def create_invoice(self, partner_name: str, amount: float, 
                      description: str = "", dry_run: bool = False) -> Dict:
        """
        Create customer invoice
        
        Args:
            partner_name: Customer name
            amount: Invoice amount
            description: Invoice description/reference
            dry_run: If True, don't actually create
        
        Returns:
            Dict with invoice_id and status
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'create_invoice',
                'partner': partner_name,
                'amount': amount,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Find or create partner
            partner_id = self._find_or_create_partner(partner_name)
            
            # Create invoice
            invoice_vals = {
                'partner_id': partner_id,
                'move_type': 'out_invoice',  # Customer invoice
                'invoice_date': datetime.now().date().isoformat(),
                'invoice_line_ids': [(0, 0, {
                    'name': description or 'Service',
                    'quantity': 1,
                    'price_unit': amount
                })]
            }
            
            invoice_id = self._call_odoo('account.move', 'create', [invoice_vals])
            
            # Extract ID if returned as array
            if isinstance(invoice_id, list):
                invoice_id = invoice_id[0] if invoice_id else None
            
            # Post the invoice (validate it)
            if invoice_id:
                self._call_odoo('account.move', 'action_post', [[invoice_id]])
            
            return {
                'status': 'success',
                'invoice_id': invoice_id,
                'partner': partner_name,
                'amount': amount,
                'message': f'Invoice created and posted for {partner_name}',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'create_invoice',
                'timestamp': datetime.now().isoformat()
            }
    
    def create_bill(self, vendor_name: str, amount: float,
                   description: str = "", dry_run: bool = False) -> Dict:
        """
        Create vendor bill
        
        Args:
            vendor_name: Vendor/supplier name
            amount: Bill amount
            description: Bill description/reference
            dry_run: If True, don't actually create
        
        Returns:
            Dict with bill_id and status
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'create_bill',
                'vendor': vendor_name,
                'amount': amount,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Find or create vendor partner
            partner_id = self._find_or_create_partner(vendor_name, is_vendor=True)
            
            # Create bill
            bill_vals = {
                'partner_id': partner_id,
                'move_type': 'in_invoice',  # Vendor bill
                'invoice_date': datetime.now().date().isoformat(),
                'invoice_line_ids': [(0, 0, {
                    'name': description or 'Purchase',
                    'quantity': 1,
                    'price_unit': amount
                })]
            }
            
            bill_id = self._call_odoo('account.move', 'create', [bill_vals])
            
            # Extract ID if returned as array
            if isinstance(bill_id, list):
                bill_id = bill_id[0] if bill_id else None
            
            # Post the bill (validate it)
            if bill_id:
                self._call_odoo('account.move', 'action_post', [[bill_id]])
            
            return {
                'status': 'success',
                'bill_id': bill_id,
                'vendor': vendor_name,
                'amount': amount,
                'message': f'Bill created and posted for {vendor_name}',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'create_bill',
                'timestamp': datetime.now().isoformat()
            }
    
    def record_payment(self, invoice_id: int, amount: float,
                      payment_date: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        Record payment for invoice/bill
        
        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_date: Payment date (ISO format), defaults to today
            dry_run: If True, don't actually record
        
        Returns:
            Dict with payment_id and status
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'record_payment',
                'invoice_id': invoice_id,
                'amount': amount,
                'payment_date': payment_date or datetime.now().date().isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Ensure invoice_id is an integer
            if isinstance(invoice_id, list):
                invoice_id = invoice_id[0] if invoice_id else None
            
            if not invoice_id:
                raise Exception("Invalid invoice_id")
            
            payment_vals = {
                'amount': amount,
                'payment_type': 'inbound',  # Receiving payment
                'partner_type': 'customer',
                'date': payment_date or datetime.now().date().isoformat(),
                'invoice_ids': [(4, invoice_id)]  # Link to invoice
            }
            
            payment_id = self._call_odoo('account.payment', 'create', [payment_vals])
            
            # Extract ID if returned as array
            if isinstance(payment_id, list):
                payment_id = payment_id[0] if payment_id else None
            
            # Post payment
            if payment_id:
                self._call_odoo('account.payment', 'action_post', [[payment_id]])
            
            return {
                'status': 'success',
                'payment_id': payment_id,
                'invoice_id': invoice_id,
                'amount': amount,
                'message': 'Payment recorded and posted',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'record_payment',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_balance(self, account_type: str = 'asset_receivable') -> Dict:
        """
        Get account balance
        
        Args:
            account_type: Account type (asset_receivable, asset, liability, etc.)
        
        Returns:
            Dict with balance information
        """
        try:
            # Search for accounts of specific type
            account_ids = self._call_odoo(
                'account.account',
                'search',
                [[['account_type', '=', account_type]]],
                {'limit': 10}
            )
            
            if not account_ids:
                return {
                    'status': 'success',
                    'account_type': account_type,
                    'balance': 0,
                    'message': f'No accounts found for type: {account_type}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get account details
            accounts = self._call_odoo(
                'account.account',
                'read',
                [account_ids],
                {'fields': ['name', 'code', 'current_balance']}
            )
            
            total_balance = sum(acc.get('current_balance', 0) for acc in accounts)
            
            return {
                'status': 'success',
                'account_type': account_type,
                'balance': total_balance,
                'accounts': [
                    {
                        'name': acc['name'],
                        'code': acc.get('code', ''),
                        'balance': acc.get('current_balance', 0)
                    }
                    for acc in accounts
                ],
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'get_balance',
                'timestamp': datetime.now().isoformat()
            }
    
    def list_invoices(self, limit: int = 10, state: str = 'posted') -> Dict:
        """
        List recent customer invoices
        
        Args:
            limit: Number of invoices to return
            state: Invoice state (draft, posted, cancel)
        
        Returns:
            Dict with invoices array
        """
        try:
            domain = [['move_type', '=', 'out_invoice']]
            if state:
                domain.append(['state', '=', state])
            
            invoice_ids = self._call_odoo(
                'account.move',
                'search',
                [domain],
                {'limit': limit, 'order': 'id desc'}
            )
            
            if not invoice_ids:
                return {
                    'status': 'success',
                    'invoices': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            invoices = self._call_odoo(
                'account.move',
                'read',
                [invoice_ids],
                {'fields': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'state']}
            )
            
            return {
                'status': 'success',
                'invoices': [
                    {
                        'invoice_id': inv['id'],
                        'number': inv['name'],
                        'partner': inv['partner_id'][1] if inv.get('partner_id') else 'Unknown',
                        'amount_total': inv.get('amount_total', 0),
                        'amount_due': inv.get('amount_residual', 0),
                        'date': inv.get('invoice_date'),
                        'state': inv.get('state')
                    }
                    for inv in invoices
                ],
                'count': len(invoices),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'list_invoices',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_partner_balance(self, partner_name: str) -> Dict:
        """
        Get customer/vendor balance (accounts receivable/payable)
        
        Args:
            partner_name: Partner name
        
        Returns:
            Dict with partner balance
        """
        try:
            # Find partner
            partner_ids = self._call_odoo(
                'res.partner',
                'search',
                [[['name', 'ilike', partner_name]]],
                {'limit': 1}
            )
            
            if not partner_ids:
                return {
                    'status': 'error',
                    'message': f'Partner not found: {partner_name}',
                    'timestamp': datetime.now().isoformat()
                }
            
            partner_id = partner_ids[0]
            
            # Get partner with balance
            partner = self._call_odoo(
                'res.partner',
                'read',
                [[partner_id]],
                {'fields': ['name', 'debit', 'credit']}
            )[0]
            
            return {
                'status': 'success',
                'partner': partner['name'],
                'receivable': partner.get('debit', 0),  # What they owe us
                'payable': partner.get('credit', 0),  # What we owe them
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'get_partner_balance',
                'timestamp': datetime.now().isoformat()
            }
    
    def _find_or_create_partner(self, name: str, is_vendor: bool = False) -> int:
        """Find existing partner or create new one"""
        # Search for existing partner
        partner_ids = self._call_odoo(
            'res.partner',
            'search',
            [[['name', 'ilike', name]]],
            {'limit': 1}
        )
        
        if partner_ids and len(partner_ids) > 0:
            return partner_ids[0]
        
        # Create new partner
        partner_vals = {
            'name': name,
            'customer_rank': 0 if is_vendor else 1,
            'supplier_rank': 1 if is_vendor else 0
        }
        
        partner_id = self._call_odoo('res.partner', 'create', [partner_vals])
        return partner_id
    
    def process_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """
        Process MCP action request
        
        Args:
            action: Action name
            params: Action parameters
        
        Returns:
            Dict with action result
        """
        try:
            if action == 'create_invoice':
                return self.create_invoice(
                    partner_name=params.get('partner_name', ''),
                    amount=params.get('amount', 0),
                    description=params.get('description', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'create_bill':
                return self.create_bill(
                    vendor_name=params.get('vendor_name', ''),
                    amount=params.get('amount', 0),
                    description=params.get('description', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'record_payment':
                return self.record_payment(
                    invoice_id=params.get('invoice_id', 0),
                    amount=params.get('amount', 0),
                    payment_date=params.get('payment_date'),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'get_balance':
                return self.get_balance(
                    account_type=params.get('account_type', 'asset_receivable')
                )
            
            elif action == 'list_invoices':
                return self.list_invoices(
                    limit=params.get('limit', 10),
                    state=params.get('state', 'posted')
                )
            
            elif action == 'get_partner_balance':
                return self.get_partner_balance(
                    partner_name=params.get('partner_name', '')
                )
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown action: {action}",
                    'supported_actions': [
                        'create_invoice', 'create_bill', 'record_payment',
                        'get_balance', 'list_invoices', 'get_partner_balance'
                    ]
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': action,
                'timestamp': datetime.now().isoformat()
            }


# CLI testing
if __name__ == "__main__":
    import sys
    
    try:
        server = OdooServer()
        
        if len(sys.argv) < 2:
            print("Odoo MCP Server")
            print("Usage:")
            print("  python odoo_server.py list_invoices")
            print("  python odoo_server.py get_balance")
            sys.exit(1)
        
        action = sys.argv[1]
        
        if action == 'list_invoices':
            result = server.process_action('list_invoices', {'limit': 5})
            print(json.dumps(result, indent=2))
        
        elif action == 'get_balance':
            result = server.process_action('get_balance', {})
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown action: {action}")
    
    except Exception as e:
        print(f"Error: {e}")
