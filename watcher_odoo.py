"""
Odoo ERP Watcher
Monitors for financial events and business transactions requiring Odoo actions

Triggers:
1. New client contracts/agreements in Done/ folder (create invoices)
2. Payment received notifications in Gmail (record payments)
3. Expense reports or bills in watch_inbox/ (create vendor bills)
4. Financial milestones in Business_Goals.md (record transactions)
5. Weekly schedule: Friday 5 PM - 6 PM (weekly financial review prep)

Task Creation:
Creates tasks in task_queue/inbox/ with Odoo accounting instructions
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watcher_odoo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('odoo_watcher')


class OdooWatcher:
    """Monitor for financial events requiring Odoo actions"""
    
    def __init__(self):
        self.vault_path = Path(os.getenv('VAULT_PATH', './obsidian_vault'))
        self.task_queue = Path('./task_queue/inbox')
        self.watch_inbox = Path('./watch_inbox')
        self.task_queue.mkdir(parents=True, exist_ok=True)
        
        self.check_interval = int(os.getenv('ODOO_CHECK_INTERVAL', '3600'))  # 1 hour
        
        # Track processed items
        self.state_file = Path('./task_queue/.odoo_watcher_state.json')
        self.processed_items = self._load_state()
        
        # Financial keywords
        self.invoice_keywords = [
            'invoice', 'bill', 'payment', 'contract', 'agreement',
            'client', 'customer', 'project complete', 'delivered',
            'payment received', 'paid'
        ]
        
        self.expense_keywords = [
            'expense', 'purchase', 'vendor', 'supplier', 'bill',
            'cost', 'spent', 'bought', 'subscription'
        ]
    
    def _load_state(self) -> set:
        """Load processed items from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_items', []))
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return set()
    
    def _save_state(self):
        """Save processed items to state file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'processed_items': list(self.processed_items),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def _create_task(self, trigger_type: str, content: Dict[str, Any]):
        """Create Odoo task in inbox"""
        task_id = f"odoo_{trigger_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.task_queue / f"{task_id}.json"
        
        task = {
            'task_id': task_id,
            'task_type': 'odoo_action',
            'trigger': trigger_type,
            'priority': 'high' if trigger_type in ['payment_received', 'invoice_due'] else 'medium',
            'created_at': datetime.now().isoformat(),
            'content': content,
            'instructions': self._get_instructions(trigger_type, content),
            'required_skills': ['odoo_skills', 'finance_skills', 'approval_skills', 'planning_skills']
        }
        
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        logger.info(f"Created Odoo task: {task_id} (trigger: {trigger_type})")
    
    def _get_instructions(self, trigger_type: str, content: Dict[str, Any]) -> str:
        """Generate AI instructions based on trigger type"""
        base = "Review obsidian_vault/agent_skills/odoo_skills.md for Odoo operations."
        
        if trigger_type == 'create_invoice':
            return f"""{base}

Task: Create customer invoice in Odoo

Project: {content.get('project_name')}
Client: {content.get('client_name', 'Unknown')}
Context: {content.get('context', '')}

Action Steps:
1. Extract invoice details:
   - Customer name (from project or context)
   - Invoice amount (from contract or estimate)
   - Service description
   - Payment terms
2. Check if customer exists in Odoo (use get_partner_balance to verify)
3. Create invoice via odoo_server.py:
   - partner_name: [Customer name]
   - amount: [Invoice amount]
   - description: [Service description]
4. If HITL required (amount > $5000), move to /Needs_Approval/
5. If auto-approved, create invoice and log result
6. Update Business_Goals.md with "Invoice INV-XXX created for [Client]"

Invoice Details Format:
- Partner: [Company name or individual]
- Amount: [Numeric value]
- Description: [Brief service description]
- Due Date: Net 30 (30 days from invoice date)
"""
        
        elif trigger_type == 'record_payment':
            return f"""{base}

Task: Record payment received in Odoo

Payment Details: {content.get('payment_details')}
Context: {content.get('context', '')}

Action Steps:
1. Extract payment information:
   - Customer name
   - Payment amount
   - Payment date
   - Invoice reference (if available)
2. Find matching invoice in Odoo:
   - Use list_invoices() to find unpaid invoices
   - Match by customer name and amount
3. Record payment via odoo_server.py:
   - invoice_id: [Odoo invoice ID]
   - amount: [Payment amount]
   - payment_date: [Date received]
4. Verify payment posted successfully
5. Update Business_Goals.md: "Payment of $[amount] received from [Client]"
6. Log in audit trail

Payment Matching Priority:
1. Exact match: Customer + Amount + Invoice reference
2. Partial match: Customer + Amount (closest date)
3. If no match found, create standalone payment and flag for human review
"""
        
        elif trigger_type == 'create_bill':
            return f"""{base}

Task: Create vendor bill in Odoo

Expense: {content.get('expense_description')}
Vendor: {content.get('vendor_name', 'Unknown')}
Context: {content.get('context', '')}

Action Steps:
1. Extract bill details:
   - Vendor name
   - Bill amount
   - Expense category/description
   - Bill date
2. Verify vendor exists or create new partner (is_vendor=True)
3. Create bill via odoo_server.py:
   - vendor_name: [Vendor name]
   - amount: [Bill amount]
   - description: [Expense category]
4. If HITL required (amount > $1000 or new vendor), move to /Needs_Approval/
5. If auto-approved, create bill and log result
6. Update expense tracking in Business_Goals.md

Expense Categories:
- Software/Subscriptions: "Software subscription"
- Office expenses: "Office supplies"
- Professional services: "Professional services"
- Marketing: "Marketing expenses"
- Other: [Specific description]
"""
        
        elif trigger_type == 'financial_milestone':
            return f"""{base}

Task: Record financial milestone in Odoo

Milestone: {content.get('milestone_text')}
Context: {content.get('context', '')}

Action Steps:
1. Identify milestone type:
   - Revenue milestone: Create invoice or record payment
   - Expense milestone: Create bill
   - Account balance milestone: Get current balance for reporting
2. Execute appropriate Odoo action based on type
3. Verify transaction completed
4. Update Business_Goals.md with financial summary
5. If monthly/quarterly milestone, prepare financial report for CEO briefing

Common Milestones:
- "$X revenue achieved": Record payments or create pending invoices
- "New client signed": Create invoice for initial payment
- "Subscription renewed": Create recurring invoice
- "Expense budget exceeded": Get balance and flag for review
"""
        
        elif trigger_type == 'weekly_review':
            return f"""{base}

Task: Weekly financial review preparation (Friday evening)

Week: {content.get('week')}
Date: {content.get('date')}

Action Steps:
1. Fetch financial summary from Odoo:
   - list_invoices(state='posted', limit=50) - All invoices this week
   - get_balance(account_type='asset_receivable') - Accounts receivable
   - get_balance(account_type='liability_payable') - Accounts payable
2. Calculate weekly metrics:
   - Total invoices issued
   - Total payments received
   - Outstanding receivables
   - Bills paid this week
3. Identify issues:
   - Overdue invoices (>30 days)
   - Unpaid bills approaching due date
   - Unusual transactions requiring attention
4. Generate summary for Monday CEO briefing:
   - Week X Financial Summary
   - Revenue: $[total invoiced] | Collected: $[total paid]
   - Outstanding: $[receivable] | Payable: $[bills due]
   - Action Items: [List of follow-ups]
5. Save summary to /Needs_Approval/ for CEO review

Report Format (Markdown):
# Week X Financial Review
**Period**: [Start Date] - [End Date]

## Revenue
- Invoices Issued: [Count] totaling $[Amount]
- Payments Received: [Count] totaling $[Amount]

## Outstanding
- Accounts Receivable: $[Amount]
- Overdue (>30 days): $[Amount] ([Count] invoices)

## Expenses
- Bills Paid: [Count] totaling $[Amount]
- Accounts Payable: $[Amount]

## Action Items
- [ ] Follow up on overdue invoice INV-XXX ($[Amount])
- [ ] Pay bill BILL-XXX by [Due Date]
"""
        
        return f"{base}\n\nTask Type: {trigger_type}\nContent: {json.dumps(content, indent=2)}"
    
    def check_done_folder(self) -> List[Dict]:
        """Check Done folder for completed projects requiring invoicing"""
        triggers = []
        done_path = self.vault_path / 'Done'
        
        if not done_path.exists():
            return triggers
        
        for item in done_path.iterdir():
            item_key = f"done_invoice:{item.name}"
            
            if item_key in self.processed_items:
                continue
            
            try:
                if item.is_file() and item.suffix == '.md':
                    content = item.read_text(encoding='utf-8').lower()
                    
                    # Check for invoice-worthy items
                    has_invoice_trigger = any(kw in content for kw in self.invoice_keywords)
                    
                    if has_invoice_trigger:
                        triggers.append({
                            'type': 'create_invoice',
                            'content': {
                                'project_name': item.stem,
                                'client_name': self._extract_client_name(content),
                                'context': content[:500]
                            },
                            'key': item_key
                        })
            
            except Exception as e:
                logger.warning(f"Could not read {item.name}: {e}")
        
        return triggers
    
    def check_watch_inbox(self) -> List[Dict]:
        """Check watch_inbox for bill/expense documents"""
        triggers = []
        
        if not self.watch_inbox.exists():
            return triggers
        
        for item in self.watch_inbox.iterdir():
            item_key = f"expense:{item.name}"
            
            if item_key in self.processed_items:
                continue
            
            try:
                if item.is_file():
                    # Check filename or content for expense indicators
                    item_name_lower = item.name.lower()
                    
                    has_expense = any(kw in item_name_lower for kw in self.expense_keywords)
                    
                    if has_expense:
                        triggers.append({
                            'type': 'create_bill',
                            'content': {
                                'expense_description': item.stem,
                                'vendor_name': self._extract_vendor_from_filename(item.name),
                                'file_path': str(item)
                            },
                            'key': item_key
                        })
            
            except Exception as e:
                logger.warning(f"Could not process {item.name}: {e}")
        
        return triggers
    
    def check_business_goals(self) -> List[Dict]:
        """Check Business_Goals.md for financial milestones"""
        triggers = []
        goals_file = self.vault_path / 'Business_Goals.md'
        
        if not goals_file.exists():
            return triggers
        
        try:
            content = goals_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if ('✅' in line or '[x]' in line.lower()):
                    # Check for financial milestones
                    has_financial = any(kw in line.lower() for kw in [
                        'revenue', 'invoice', 'payment', 'client', 'contract',
                        'subscription', 'expense', '$', 'paid'
                    ])
                    
                    if has_financial:
                        milestone_key = f"milestone_finance:{line[:50]}"
                        
                        if milestone_key not in self.processed_items:
                            triggers.append({
                                'type': 'financial_milestone',
                                'content': {
                                    'milestone_text': line.strip(),
                                    'context': '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                                },
                                'key': milestone_key
                            })
        
        except Exception as e:
            logger.error(f"Could not read Business_Goals.md: {e}")
        
        return triggers
    
    def check_weekly_review(self) -> List[Dict]:
        """Check if it's time for weekly financial review (Friday 5-6 PM)"""
        triggers = []
        now = datetime.now()
        
        # Friday = 4
        if now.weekday() == 4 and 17 <= now.hour < 18:
            review_key = f"weekly_review:{now.strftime('%Y-W%W')}"
            
            if review_key not in self.processed_items:
                triggers.append({
                    'type': 'weekly_review',
                    'content': {
                        'week': now.isocalendar()[1],
                        'date': now.strftime('%Y-%m-%d'),
                        'time': now.strftime('%I:%M %p')
                    },
                    'key': review_key
                })
        
        return triggers
    
    def _extract_client_name(self, content: str) -> str:
        """Extract client name from content (simplified)"""
        # Look for common patterns like "Client: Name" or "for CompanyName"
        for line in content.split('\n')[:10]:  # Check first 10 lines
            if 'client:' in line.lower():
                return line.split(':', 1)[1].strip()
            if 'customer:' in line.lower():
                return line.split(':', 1)[1].strip()
        
        return "Unknown Client"
    
    def _extract_vendor_from_filename(self, filename: str) -> str:
        """Extract vendor name from filename"""
        # Example: "Bill_from_AWS_Jan2026.pdf" -> "AWS"
        name = Path(filename).stem
        
        for keyword in ['bill', 'invoice', 'receipt', 'expense']:
            name = name.replace(keyword, '').replace(keyword.upper(), '')
        
        name = name.replace('_', ' ').replace('-', ' ').strip()
        
        # Take first meaningful word
        words = [w for w in name.split() if len(w) > 2]
        return words[0] if words else "Unknown Vendor"
    
    def monitor(self):
        """Main monitoring loop"""
        logger.info("Odoo watcher started")
        logger.info(f"Vault path: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        
        while True:
            try:
                logger.info("Checking for Odoo financial events...")
                
                all_triggers = []
                all_triggers.extend(self.check_done_folder())
                all_triggers.extend(self.check_watch_inbox())
                all_triggers.extend(self.check_business_goals())
                all_triggers.extend(self.check_weekly_review())
                
                for trigger in all_triggers:
                    self._create_task(trigger['type'], trigger['content'])
                    self.processed_items.add(trigger['key'])
                
                if all_triggers:
                    self._save_state()
                    logger.info(f"Created {len(all_triggers)} Odoo tasks")
                else:
                    logger.info("No new financial events found")
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            logger.info(f"Sleeping for {self.check_interval}s...")
            time.sleep(self.check_interval)


if __name__ == "__main__":
    watcher = OdooWatcher()
    watcher.monitor()
