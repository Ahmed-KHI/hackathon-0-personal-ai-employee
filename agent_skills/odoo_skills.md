# Odoo ERP Agent Skills

**Purpose**: Guide AI agent on Odoo ERP accounting operations for automated financial management and business transaction tracking.

**Platform**: Odoo Community Edition 19.0 via JSON-RPC API  
**Database**: PostgreSQL-backed Odoo instance  
**Posting Authority**: AI agent with Human-in-the-Loop approval for large transactions

---

## 💼 Odoo Overview

### What is Odoo?
Odoo is an **open-source ERP (Enterprise Resource Planning) system** with comprehensive accounting modules. For Personal AI Employee, we use it to:
- Create and track customer invoices
- Record vendor bills and expenses
- Manage payments (received and made)
- Monitor accounts receivable and payable
- Generate financial reports

### Accounting Module Components
1. **Partners** (Customers & Vendors)
2. **Invoices** (Accounts Receivable)
3. **Bills** (Accounts Payable)
4. **Payments** (Cash flow)
5. **Chart of Accounts** (Account types and balances)
6. **Journals** (Sales, Purchase, Bank, Miscellaneous)

---

## 📋 Core Operations

### 1. Create Customer Invoice

**When to Use**:
- Client project completed (from Done/ folder)
- Contract milestone reached
- Subscription renewal
- Service delivered

**MCP Action**: `create_invoice`

**Required Information**:
- **partner_name**: Customer/client name (string)
- **amount**: Invoice total (float, e.g., 2500.00)
- **description**: Service/product description (string)

**Example**:
```python
odoo_server.create_invoice(
    partner_name="Acme Corporation",
    amount=2500.00,
    description="Web development services - January 2026"
)
```

**Process Flow**:
1. Check if partner exists in Odoo (search by name)
2. If not found, create new customer partner
3. Create invoice with line item
4. Invoice status: Draft (can be edited)
5. Post invoice (finalizes and generates invoice number)

**HITL Thresholds**:
- **Auto-approve**: Invoices ≤ $5,000 for existing customers
- **CEO approval required**: 
  - Invoices > $5,000
  - New customers (first invoice)
  - Custom payment terms

---

### 2. Create Vendor Bill

**When to Use**:
- Vendor invoice received (email or watch_inbox/)
- Subscription payment due
- Office expense incurred
- Professional services billed

**MCP Action**: `create_bill`

**Required Information**:
- **vendor_name**: Vendor/supplier name (string)
- **amount**: Bill total (float)
- **description**: Expense category (string)

**Example**:
```python
odoo_server.create_bill(
    vendor_name="AWS",
    amount=450.00,
    description="Cloud hosting - January 2026"
)
```

**Expense Categories**:
- **Software/Subscriptions**: "Software subscription fee"
- **Office Supplies**: "Office equipment and supplies"
- **Professional Services**: "Consulting/legal/accounting services"
- **Marketing**: "Advertising and marketing expenses"
- **Utilities**: "Internet/phone/utilities"
- **Other**: [Specific description]

**HITL Thresholds**:
- **Auto-approve**: Bills ≤ $1,000 from known vendors
- **CEO approval required**:
  - Bills > $1,000
  - New vendors (first bill)
  - Unusual expense categories

---

### 3. Record Payment

**When to Use**:
- Payment received notification (Gmail watcher)
- Customer pays invoice (bank notification)
- Recording past payment

**MCP Action**: `record_payment`

**Required Information**:
- **invoice_id**: Odoo invoice ID (integer)
- **amount**: Payment amount (float)
- **payment_date**: Date received (ISO format, optional)

**Example**:
```python
# Step 1: Find invoice
invoices = odoo_server.list_invoices(limit=20)
invoice_id = [inv for inv in invoices if inv['partner'] == 'Acme Corporation'][0]['invoice_id']

# Step 2: Record payment
odoo_server.record_payment(
    invoice_id=invoice_id,
    amount=2500.00,
    payment_date="2026-02-08"
)
```

**Payment Matching  Logic**:
1. **Exact Match**: Customer name + Amount + Invoice reference
2. **Partial Match**: Customer name + Amount (select most recent unpaid invoice)
3. **No Match**: Create standalone payment, flag for human review

**HITL Thresholds**:
- **Auto-approve**: All payments ≤ $10,000
- **CEO notification** (not approval): Payments > $10,000
- **Flag for review**: Payments with no matching invoice

---

### 4. Get Account Balance

**When to Use**:
- Weekly financial review (Friday 5 PM)
- Monthly reporting (CEO briefing)
- Checking current financial position
- Investigating account discrepancies

**MCP Action**: `get_balance`

**Account Types**:
- `asset_receivable`: Accounts Receivable (what customers owe us)
- `liability_payable`: Accounts Payable (what we owe vendors)
- `income`: Revenue accounts
- `expense`: Expense accounts
- `asset`: Asset accounts (cash, equipment)

**Example**:
```python
# Check receivables
receivable = odoo_server.get_balance(account_type='asset_receivable')
# Returns: {'balance': 15000.00, 'accounts': [...]}

# Check payables
payable = odoo_server.get_balance(account_type='liability_payable')
# Returns: {'balance': 3500.00, 'accounts': [...]}
```

**Reporting Guidelines**:
- Run weekly (Friday evening before CEO briefing)
- Include in monthly financial summary
- Flag unusual balances (sudden spikes or drops)
- Track trends over time

---

### 5. List Invoices

**When to Use**:
- Finding specific invoice for payment recording
- Weekly review of unpaid invoices
- Financial reporting
- Checking invoice status

**MCP Action**: `list_invoices`

**Parameters**:
- **limit**: Number of invoices (default: 10)
- **state**: Invoice state (default: 'posted')
  - `draft`: Not finalized
  - `posted`: Finalized and sent
  - `cancel`: Cancelled

**Example**:
```python
# Recent posted invoices
invoices = odoo_server.list_invoices(limit=20, state='posted')

# Find unpaid invoices (amount_due > 0)
unpaid = [inv for inv in invoices['invoices'] if inv['amount_due'] > 0]
```

**Use Cases**:
- **Payment Matching**: Find invoice to match incoming payment
- **Overdue Tracking**: Identify invoices >30 days old
- **Revenue Reporting**: Sum invoice totals for period
- **Client History**: Filter by partner name

---

### 6. Get Partner Balance

**When to Use**:
- Checking customer payment history
- Verifying vendor account status
- Before creating new invoice (check for overdue amounts)
- Client relationship management

**MCP Action**: `get_partner_balance`

**Required Information**:
- **partner_name**: Customer or vendor name (string, partial match supported)

**Example**:
```python
balance = odoo_server.get_partner_balance(partner_name="Acme")
# Returns: {
#     'partner': 'Acme Corporation',
#     'receivable': 2500.00,  # What they owe us
#     'payable': 0.00  # What we owe them
# }
```

**Interpretation**:
- **Positive receivable**: Customer owes us money (good)
- **Negative receivable**: We owe customer money (refund/credit)
- **Positive payable**: We owe vendor money (bill due)
- **Zero balance**: All settled

---

## 🔄 Common Workflows

### Workflow 1: Project Completion → Invoice → Payment

**Trigger**: Completed project file appears in Done/ folder

**Steps**:
1. **Watcher detects** project file with client keywords
2. **Extract details**:
   - Client name from content
   - Project name from filename
   - Invoice amount (from contract or estimate)
3. **Create invoice**:
   ```python
   result = odoo_server.create_invoice(
       partner_name="Client Name",
       amount=5000.00,
       description="Project ABC - Development services"
   )
   ```
4. **Post to Dashboard**: "Invoice INV-XXX created for Client Name ($5,000)"
5. **Update Business_Goals**: Add invoice to revenue tracking

**When Payment Received**:
1. **Gmail watcher** detects "Payment received" notification
2. **Find invoice** by client name + amount
3. **Record payment**:
   ```python
   odoo_server.record_payment(
       invoice_id=invoice_id,
       amount=5000.00
   )
   ```
4. **Post to Dashboard**: "Payment of $5,000 received from Client Name"
5. **Celebrate on social media** (if milestone worth sharing)

---

### Workflow 2: Vendor Bill → Payment Tracking

**Trigger**: Bill document in watch_inbox/ or email notification

**Steps**:
1. **Identify vendor** from filename or email sender
2. **Extract amount** from document or email body
3. **Create bill**:
   ```python
   result = odoo_server.create_bill(
       vendor_name="AWS",
       amount=450.00,
       description="Cloud hosting - February 2026"
   )
   ```
4. **Check HITL threshold**:
   - If > $1,000 or new vendor → `/Needs_Approval/`
   - Otherwise → Auto-approve and create
5. **Update expense tracking** in Business_Goals.md

**When Payment is Made** (manual by CEO or auto-pay):
- Record payment in Odoo (similar to customer payment)
- Update cash flow tracking

---

### Workflow 3: Weekly Financial Review (Fridays)

**Trigger**: Friday 5 PM - 6 PM (weekly schedule)

**Steps**:
1. **Fetch current state**:
   ```python
   # Recent invoices
   invoices = odoo_server.list_invoices(limit=50)
   
   # Account balances
   receivable = odoo_server.get_balance('asset_receivable')
   payable = odoo_server.get_balance('liability_payable')
   ```

2. **Calculate metrics**:
   - Total invoices issued this week
   - Total payments received this week
   - Outstanding receivables
   - Overdue invoices (>30 days)
   - Bills due this week

3. **Generate report** (Markdown):
   ```markdown
   # Week X Financial Review
   **Period**: Feb 3 - Feb 7, 2026
   
   ## Revenue
   - Invoices Issued: 3 totaling $12,500
   - Payments Received: 2 totaling $8,000
   
   ## Outstanding
   - Accounts Receivable: $15,000
   - Overdue (>30 days): $2,500 (1 invoice)
   
   ## Expenses
   - Bills Paid: 4 totaling $1,800
   - Accounts Payable: $450 (AWS bill due Feb 15)
   
   ## Action Items
   - [ ] Follow up on overdue invoice INV-101 from Client X ($2,500)
   - [ ] Pay AWS bill by Feb 15
   ```

4. **Save to `/Needs_Approval/`** for CEO review
5. **Include in Monday CEO briefing**

---

## 🔒 HITL Approval Rules

### Auto-Approve Transactions

✅ **Invoices**:
- Amount ≤ $5,000
- Existing customer (has previous invoices)
- Standard payment terms (Net 30)

✅ **Bills**:
- Amount ≤ $1,000
- Known vendor (has previous bills)
- Recurring expenses (subscriptions, utilities)

✅ **Payments**:
- All payment recordings (just tracking, not sending money)

### Require CEO Approval

⏸️ **Invoices**:
- Amount > $5,000
- New customer (first invoice ever)
- Custom payment terms or discounts
- Uncertain invoice details extracted from project

⏸️ **Bills**:
- Amount > $1,000
- New vendor (first bill ever)
- Unusual expense category
- Unclear vendor or amount from document

⏸️ **Financial Milestones**:
- Large transactions (>$10,000)
- Account discrepancies
- Negative balances requiring investigation

### Approval Process

1. **AI creates draft** in `/Needs_Approval/`
2. **File contents**:
   ```json
   {
     "action": "create_invoice",
     "params": {
       "partner_name": "New Client Inc",
       "amount": 7500.00,
       "description": "Consulting services Q1 2026"
     },
     "reason_for_approval": "New customer + Amount > $5,000",
     "recommendation": "Approve - Contract signed, project delivered",
     "risk_assessment": "Low risk - Verified customer, work completed"
   }
   ```
3. **CEO reviews** and renames file:
   - `.approved` → Execute immediately
   - `.rejected` → Cancel, do not create
   - `.edit_[instructions]` → Revise per feedback

---

## 📊 Financial Reporting

### Weekly Summary (Every Friday)

**Include**:
- Revenue: Invoices issued + Payments received
- Expenses: Bills created + Bills paid
- Outstanding: Receivables + Payables
- Trends: Week-over-week comparison
- Action Items: Overdue follow-ups, upcoming payments

### Monthly Report (First Monday of Month)

**Include**:
- Total revenue (invoiced + received)
- Total expenses (billed + paid)
- Net income/loss
- Accounts receivable aging (0-30, 31-60, 61-90, 90+ days)
- Top customers by revenue
- Top expense categories
- Cash flow projection

### Quarter/Year-End (As Needed)

**Include**:
- Full financial statements (P&L, Balance Sheet)
- Tax preparation data
- Growth metrics
- Revenue targets vs. actual

---

## ⚠️ Risk Management

### Data Validation

Before creating any financial transaction:
1. **Verify amounts**: Must be numeric and positive
2. **Check partner names**: No typos or variations
3. **Validate dates**: Must be valid ISO format
4. **Confirm descriptions**: Clear and specific

### Error Handling

**If Odoo API Error**:
1. Log error details to audit trail
2. Save transaction details to `/Needs_Action/` for retry
3. Notify CEO if critical (e.g., payment recording failed)
4. Do not silently fail

**Common Errors**:
- **Authentication failed**: Re-authenticate, check credentials in .env
- **Partner not found**: Create partner first, then retry transaction
- **Invalid invoice state**: Cannot record payment on draft invoice
- **Missing required fields**: Extract more details or flag for HITL

### Compliance

**Accounting Standards**:
- All transactions timestamped (UTC)
- Audit trail for every financial action
- No retroactive deletions (only corrections via credit notes)
- Backup Odoo database weekly

**Privacy**:
- Never log full Odoo credentials
- Secure secrets/odoo_token.json with restricted permissions
- Don't expose customer financial details in social media posts
- HITL approval for sensitive transactions

---

## 🛠️ Technical Integration

### MCP Server Methods

```python
# Initialize
from mcp_servers.odoo_server.odoo_server import OdooServer
odoo = OdooServer()

# Create invoice
invoice_result = odoo.process_action('create_invoice', {
    'partner_name': 'Acme Corp',
    'amount': 2500.00,
    'description': 'Consulting services',
    'dry_run': False  # Set True for testing
})

# Create bill
bill_result = odoo.process_action('create_bill', {
    'vendor_name': 'AWS',
    'amount': 450.00,
    'description': 'Cloud hosting',
    'dry_run': False
})

# Record payment
payment_result = odoo.process_action('record_payment', {
    'invoice_id': 123,
    'amount': 2500.00,
    'payment_date': '2026-02-08'
})

# Get balance
balance_result = odoo.process_action('get_balance', {
    'account_type': 'asset_receivable'
})

# List invoices
invoices_result = odoo.process_action('list_invoices', {
    'limit': 20,
    'state': 'posted'
})

# Get partner balance
partner_result = odoo.process_action('get_partner_balance', {
    'partner_name': 'Acme'
})
```

### Task Queue Integration

Odoo watcher creates tasks in `task_queue/inbox/` with:
- `task_type: "odoo_action"`
- `trigger`: Type of financial event
- `content`: Transaction details (partner, amount, description)
- `instructions`: AI guidance generated by watcher

Orchestrator claims task, executes Odoo MCP action, logs result.

---

## 🏆 Gold Tier Success Indicators

### Required for 100% Gold Tier Completion

#### 1. Infrastructure
- ✅ Odoo Community Edition installed and accessible
- ✅ Accounting module configured with Chart of Accounts
- ✅ Odoo MCP server operational (6 actions implemented)
- ✅ Odoo watcher monitoring financial triggers
- ✅ Odoo agent skills documented

#### 2. Operational Metrics (4-week period)
- **Invoices Created**: 5+ customer invoices
- **Bills Recorded**: 5+ vendor bills
- **Payments Processed**: 3+ payment recordings
- **Weekly Reviews**: 4 financial summaries generated
- **HITL Compliance**: 100% approval for transactions requiring it

#### 3. Integration Points
- **From Done/**: Completed projects → Create invoices
- **From Gmail**: Payment notifications → Record payments
- **From watch_inbox/**: Vendor bills → Create bills
- **From Business_Goals**: Financial milestones → Odoo transactions
- **To CEO Briefing**: Weekly financial summary included

#### 4. Data Quality
- **No duplicate transactions**: Each invoice/bill created once
- **Accurate partner matching**: 95%+ correct customer/vendor identification
- **Complete audit trail**: Every financial action logged
- **Balanced accounts**: Receivables + Payables match transaction history

---

## 📚 References & Resources

- **Odoo Documentation**: https://www.odoo.com/documentation/19.0/
- **Odoo Accounting**: https://www.odoo.com/documentation/19.0/applications/finance/accounting.html
- **Odoo JSON-RPC API**: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- **Installation Guide**: https://www.odoo.com/documentation/19.0/administration/install.html
- **Chart of Accounts**: Country-specific from Odoo setup wizard

---

**Last Updated**: 2026-02-08  
**Next Review**: After 4 weeks of Odoo usage (2026-03-08)  
**Owner**: Personal AI Employee - Orchestrator + Claude Code
