# Invoice Processing Workflow - Step-by-Step Accounting

**Purpose**: Define exact steps for invoice creation, review, and posting in Odoo.

**CRITICAL**: This workflow ensures accounting compliance and prevents errors. No hardcoded invoice logic in Python.

---

## Invoice Creation Workflow

### Step 1: Gather Invoice Data ✅

**Required Information:**
- Customer name (exact match from Odoo customer database)
- Invoice date (default: today)
- Due date (default: Net 30 unless otherwise specified)
- Line items:
  - Product/Service description
  - Quantity
  - Unit price
  - Tax rate (check customer's tax jurisdiction)
  - Subtotal
- Terms and conditions (check Company_Handbook.md)

**Data Sources:**
- Project completion file in /Done folder
- Customer record in vault (obsidian_vault/Customers/)
- Pricing sheet (check Business_Goals.md for current rates)
- Contract or SOW (Statement of Work) if exists

**Validation:**
```
IF customer_name NOT in Odoo:
    → STOP, create customer first
    → Flag for human review

IF pricing differs from standard rates:
    → Require approval
    → Note justification in invoice notes

IF invoice > $5,000:
    → Require CEO approval
    → Add to high-value transaction log
```

---

### Step 2: Draft Invoice in Odoo ✅

**Using Odoo MCP Server:**
```python
# Call structure (for Claude's planning)
{
    "mcp_server": "odoo_server",
    "command": "create_invoice_draft",
    "parameters": {
        "partner_id": <customer_id>,
        "invoice_date": "2026-02-16",
        "invoice_date_due": "2026-03-18",
        "invoice_line_ids": [
            {
                "name": "Service Description",
                "quantity": 1,
                "price_unit": 1500.00,
                "tax_ids": [<tax_id>]
            }
        ]
    }
}
```

**Draft Status:**
- Invoice created in Odoo with status: "Draft"
- NOT posted to accounting yet (reversible)
- Can be edited or deleted
- Not visible to customer
- Not affecting financial reports

---

### Step 3: Review & Validation ✅

**Automated Checks:**
- [ ] Customer exists in Odoo
- [ ] All required fields populated
- [ ] Line items have descriptions
- [ ] Prices match rate sheet (or variance justified)
- [ ] Tax calculations correct
- [ ] Due date is reasonable (not in past)
- [ ] Total matches project scope
- [ ] Currency is correct

**Manual Review Triggers:**
- Invoice > $5,000 → CEO approval
- New customer → Manager approval
- Pricing variance > 20% → Approval required
- Custom terms → Legal review
- International customer → Tax verification

**Claude's Action:**
- Create approval request in /Pending_Approval/INVOICE_<customer>_<date>.json
- Include invoice preview (PDF if possible)
- List all validation results
- Highlight any concerns or variances

---

### Step 4: Human Approval ✅

**Approval File Format:**
````markdown
---
type: invoice_approval
customer: Client A
invoice_number: INV-2026-001
amount: $1,500.00
due_date: 2026-03-18
risk_level: LOW
created: 2026-02-16T10:30:00Z
---

## Invoice Details
- **Customer:** Client A
- **Amount:** $1,500.00
- **Due Date:** March 18, 2026 (Net 30)
- **Services:** Website Development - Phase 1

## Line Items
1. Frontend Development (40 hrs × $75/hr) = $3,000.00
2. Backend API (20 hrs × $75/hr) = $1,500.00
**Subtotal:** $4,500.00
**Tax (0%):** $0.00
**Total:** $4,500.00

## Validation Results
✅ Customer exists in system
✅ Pricing matches rate sheet
✅ Tax calculation correct
✅ Due date is Net 30
✅ All required fields complete

## Risk Assessment
**Level:** LOW
**Reason:** Standard project, known customer, routine pricing

## Action Required
**To Approve:** Move to /Approved/
**To Reject:** Move to /Rejected/ with feedback
**To Revise:** Edit amounts and move back to /Pending_Approval/
````

---

### Step 5: Post Invoice ✅

**Only after approval file moved to /Approved:**

**Using Odoo MCP Server:**
```python
{
    "mcp_server": "odoo_server",
    "command": "post_invoice",
    "parameters": {
        "invoice_id": <draft_invoice_id>
    }
}
```

**Post-Actions:**
- Invoice status: Draft → Posted
- Invoice now **immutable** (requires credit note to reverse)
- Accounting entries created in Odoo
- Customer can now view invoice
- Updates Accounts Receivable
- Affects financial reports

**Audit Log Entry:**
```json
{
    "timestamp": "2026-02-16T10:45:00Z",
    "action": "invoice_posted",
    "task_id": "odoo_create_invoice_...",
    "invoice_number": "INV-2026-001",
    "customer": "Client A",
    "amount": 1500.00,
    "approved_by": "human",
    "posted_by": "ai_employee",
    "status": "success"
}
```

---

### Step 6: Send Invoice to Customer ✅

**Delivery Methods:**
1. **Email (Primary):**
   - Use email_server MCP
   - Attach invoice PDF
   - Use invoice email template (see email_skills.md)
   - CC accounting@company.com

2. **Portal (Secondary):**
   - Customer accesses via Odoo portal
   - Receives notification automatically
   - Can view/download/pay online

**Email Template:**
```
Subject: Invoice INV-2026-001 from [Company Name]

Dear [Customer Name],

Please find attached invoice INV-2026-001 for [services/products].

Invoice Details:
- Amount: $1,500.00
- Due Date: March 18, 2026 (Net 30)
- Payment Methods: [Bank Transfer / Credit Card / Check]

If you have any questions, please contact us at [support email].

Thank you for your business!

Best regards,
[Company Name]
Accounting Department
```

---

### Step 7: Track Payment ✅

**Monitor Invoice Status:**
- Check Odoo daily for payment updates
- Aging report (30/60/90 days)
- Send reminders:
  - 7 days before due: Friendly reminder
  - Day of due date: Payment due today
  - 7 days overdue: Polite follow-up
  - 14 days overdue: Firm follow-up
  - 30 days overdue: Escalate to collections

**Payment Received:**
- Update invoice status: Open → Paid
- Record payment in Odoo
- Send thank you email
- Update Dashboard.md with revenue
- Log in audit trail

---

## Error Handling

### Customer Not Found
```
→ Search vault for customer info
→ Create customer in Odoo first (requires approval)
→ Then retry invoice creation
```

### Odoo Connection Error
```
→ Retry with exponential backoff (3 attempts)
→ If still failing, create alert for human
→ Save invoice draft to vault for manual entry
→ Log incident in audit trail
```

### Pricing Discrepancy
```
→ Flag for human review
→ Do NOT proceed with invoice
→ Create approval request with explanation
→ Wait for human decision
```

### Tax Rate Uncertainty
```
→ Check customer address in Odoo
→ Verify tax jurisdiction
→ If uncertain, default to 0% and flag for review
→ Better to under-tax and adjust than over-tax
```

---

## Integration with Other Skills

- **odoo_skills.md**: Technical Odoo API details
- **finance_skills.md**: General accounting principles
- **approval_skills.md**: HITL approval rules
- **email_skills.md**: Customer communication templates

---

**This workflow is authoritative for invoice processing. All invoice tasks must follow these steps.**
