---
type: approval_request
action: email_send
priority: high
risk_level: medium
---

# Approval Required: Email to Client

## Action Type
Send email response regarding Invoice #INV-2024-001

## Recipient
- **To**: important.client@example.com
- **Subject**: Re: Invoice Payment Question

## Draft Email Content

```
Dear Valued Client,

Thank you for your inquiry regarding Invoice #INV-2024-001 for $2,500.

I'm happy to provide the information you requested:

**1. Payment Due Date:**
This invoice is due 30 days from the invoice date. The payment deadline is March 10, 2026.

**2. Accepted Payment Methods:**
We accept the following payment methods:
- Bank Transfer (preferred)
- Credit/Debit Card
- PayPal
- Check (by mail)

**3. Late Payment Penalties:**
Our standard terms include:
- Grace period: 5 days after due date (no penalty)
- After grace period: 1.5% monthly interest on outstanding balance
- After 60 days overdue: Account may be sent to collections

**Bank Transfer Details:**
- Bank Name: Example Business Bank
- Account Name: Your Company LLC
- Account Number: 1234567890
- Routing Number: 987654321
- SWIFT/BIC: EXAMPBUS

Please let me know if you have any other questions. We value your business and look forward to your prompt payment.

Best regards,
AI Assistant
Your Company LLC
```

## Risk Assessment
- **Financial Impact**: None (information only)
- **Reputation Risk**: Medium (client communication)
- **Compliance**: Low (standard terms)

## Recommendation
**APPROVE** - Standard invoice inquiry response with accurate information.

---

## Instructions for Human
- Move to `/Approved/` to authorize sending
- Move to `/Rejected/` to cancel
- Edit content and move to `/Approved/` to send with modifications
