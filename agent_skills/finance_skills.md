# Finance Skills - Agent Intelligence for Financial Operations

**Purpose**: Guide AI Employee in transaction monitoring, invoice processing, and financial decision-making.

**CRITICAL**: All financial logic lives here. No hardcoded rules in watchers or orchestrator.

---

## Transaction Monitoring

### Transaction Classification

**CRITICAL** (Immediate review):
- Amount >$5,000
- Keywords: "fraud", "dispute", "chargeback", "unauthorized"
- Unusual vendors not in approved list
- International wires
- Action: Alert human, do NOT process automatically

**HIGH** (Review within 4 hours):
- Amount $1,000-$5,000
- New vendor (first transaction)
- Recurring payment failed
- Unusual transaction pattern (time, amount, frequency)
- Action: Flag for review, notify finance team

**NORMAL** (Standard processing):
- Amount <$1,000
- Known vendors (see Company_Handbook.md)
- Recurring subscriptions
- Expected payroll
- Action: Auto-process if within budget

**LOW** (Batch processing):
- Micro-transactions (<$50)
- Refunds to customers
- Internal transfers
- Action: Log and process in batch

---

## Invoice Processing

### Auto-Approval Thresholds

**Can Auto-Approve**:
- Amount <$100
- Vendor in approved list (check Company_Handbook.md)
- Matches purchase order (PO)
- Within budget category
- Action: Process payment, log in ERP

**Requires Manager Approval**:
- Amount $100-$5,000
- New vendor with proper documentation
- No PO but reasonable expense
- Action: Create approval task for manager

**Requires CFO Approval**:
- Amount $5,000+
- Capital expenditures
- Contract payments
- Annual subscriptions >$1,000
- Action: Create approval task for CFO

**Requires CEO + Board Approval**:
- Amount >$50,000
- Acquisition or major investment
- Legal settlements
- Action: Escalate with full context

### Invoice Validation Checklist

Before processing any invoice:
- [ ] Vendor exists in system (or has valid W-9 for new vendor)
- [ ] Amount matches PO (if applicable)
- [ ] Budget category has sufficient funds
- [ ] Not a duplicate (check invoice number)
- [ ] Payment terms match agreement (Net 30, Net 60, etc.)
- [ ] Expense category is appropriate
- [ ] Proper documentation attached

---

## Expense Categories

Map transactions to correct categories:

**Operating Expenses**:
- Office supplies, software subscriptions
- Utilities, rent, insurance
- Marketing, advertising

**Payroll**:
- Salaries, benefits, taxes
- Contractor payments
- Payroll service fees

**Cost of Goods Sold (COGS)**:
- Inventory purchases
- Direct materials
- Shipping/fulfillment

**Capital Expenditures**:
- Equipment purchases
- Furniture, hardware
- Vehicles

**Uncategorized**:
- If unclear, flag for human review

---

## Payment Timing

### Pay Immediately
- Payroll (never delay)
- Critical services (hosting, infrastructure)
- Legal obligations
- Penalties/interest due

### Pay on Schedule (Net 30)
- Standard vendor invoices
- Recurring subscriptions
- Utilities

### Can Negotiate Delay
- Large capital expenditures
- Cash flow constraints
- Vendor has flexible terms

### Never Pay
- Duplicate invoices
- Invoices without proper approval
- Suspected fraud
- Vendors not in system

---

## Bank Reconciliation

### Daily Checks
- Compare bank balance to expected balance
- Flag unexpected charges
- Verify all deposits match invoices
- Alert if balance <$[threshold from handbook]

### Weekly Review
- Reconcile all transactions
- Categorize expenses
- Update budget vs actual
- Generate cash flow report

### Monthly Close
- Final reconciliation
- Generate P&L statement
- Budget variance analysis
- Send summary to CFO

---

## Budget Monitoring

### Real-Time Alerts
- Category >90% of budget
- Single transaction >25% of category budget
- Unusual spending pattern

### Budget Categories (from Business_Goals.md)
```
Sales & Marketing: $X/month
Engineering: $Y/month
Operations: $Z/month
AI/Automation: $A/month
```

If transaction would exceed budget:
- <10% over: Notify manager, allow with note
- 10-25% over: Require manager approval
- >25% over: Require CFO approval

---

## Fraud Detection Rules

**Immediate Fraud Alert**:
- Multiple failed transaction attempts
- Transaction from unusual location
- Round number amounts (potential test transactions)
- Merchant name mismatch with category
- Velocity: many transactions in short time
- Amount just below approval threshold (structuring)

**Action on Fraud Suspicion**:
1. Freeze transaction (if possible)
2. Alert CFO and CEO immediately
3. Create HITL approval task
4. Log in audit trail with "fraud_suspected" flag
5. Do NOT process until human reviews

---

## Vendor Management

### Approved Vendors (from Company_Handbook.md)
- Recurring vendors pre-approved up to $[amount]
- New vendors require onboarding:
  - W-9 form (US) or equivalent
  - Background check for critical services
  - Contract review if >$10K annual

### Vendor Onboarding Workflow
1. Receive new vendor invoice
2. Check if vendor in system → No
3. Request W-9 or vendor information
4. Create HITL approval task
5. Human approves/rejects
6. If approved, add to system
7. Process invoice

---

## Payment Methods

### ACH/Wire Transfer
- For amounts >$1,000
- Requires dual approval (for security)
- 2-3 day processing time

### Credit Card
- For amounts <$5,000
- Preferred for subscriptions
- Instant processing, earn rewards

### Check
- Legacy vendors requiring it
- Government payments
- 5-7 day processing time

### International Payments
- Requires additional documentation
- Higher fees
- Currency conversion considerations

---

## Financial Reporting

### Daily Dashboard
- Cash balance
- Today's expenses
- Pending invoices
- Budget remaining by category

### Weekly Summary
- Total income vs expenses
- Top 5 expenses
- Budget variance
- Upcoming payments

### Monthly Report (for CEO)
```
# Financial Summary - [Month Year]

## Executive Summary
- Revenue: $X
- Expenses: $Y
- Net Income: $Z
- Cash on Hand: $A

## Key Metrics
- Burn Rate: $B/month
- Runway: C months
- Budget Compliance: D%

## Highlights
- [Top achievements]
- [Cost savings]

## Concerns
- [Budget overruns]
- [Unusual expenses]

## Next Month Forecast
- Expected revenue: $E
- Planned expenses: $F
- Key initiatives: [List]
```

---

## Tax & Compliance

### Tax Documents to Track
- W-9s from vendors (1099 reporting)
- Receipts for all expenses
- Payroll tax records
- Sales tax collected (if applicable)

### Quarterly Reminders
- Estimated tax payments
- Payroll tax filings
- Sales tax filings

### Annual Tasks
- 1099 preparation (January)
- Annual audit support
- Tax return preparation

---

## Integration with ERP/Odoo

### When to Update ERP
- Every invoice processed
- Every payment made
- Budget changes
- Vendor additions

### Data to Sync
- Invoice details
- Payment status
- Expense categories
- Budget vs actual

---

## Escalation Rules (HITL Required)

### Always Escalate
- Suspected fraud
- Amount >$5,000
- New vendor without documentation
- Budget overrun >25%
- Unusual transaction pattern
- Legal or tax implications
- Refund requests >$500
- Currency exchange transactions

### Human Approval Required
- First payment to new vendor
- Budget reallocation
- Contract modifications
- Financial commitments

---

## Anti-Patterns (What NOT to Do)

❌ **DON'T** pay invoices without validation
❌ **DON'T** ignore duplicate invoices
❌ **DON'T** process payments outside approved workflows
❌ **DON'T** share financial data with unauthorized parties
❌ **DON'T** ignore fraud alerts
❌ **DON'T** exceed budget without approval
❌ **DON'T** make commitments about payment timing
❌ **DON'T** delete financial records (audit requirement)

---

## Metrics to Track

- Invoice processing time (target: <3 days)
- Payment accuracy (target: 99.9%)
- Fraud detection rate
- Budget compliance (target: >95%)
- Vendor onboarding time
- Auto-approval rate (target: 60-80%)

---

## Version History

- **2026-02-05**: Initial finance skills created
- **Future**: Update based on actual financial patterns

---

**This file is authoritative for financial operations. When in doubt, escalate to CFO.**
