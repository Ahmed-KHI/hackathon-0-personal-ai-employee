# Email Skills - Agent Intelligence for Email Handling

**Purpose**: Guide AI Employee in email triage, response, and escalation decisions.

**CRITICAL**: This is the ONLY place email intelligence should live. No hardcoded logic in watchers or orchestrator.

---

## My Custom Email Rules

- Always CC my assistant on client emails
- Use "Best regards" for external, "Thanks" for internal
- Flag emails with "contract" or "legal" for HITL approval

---

## Email Triage Rules

### Priority Classification

**CRITICAL** (Immediate attention within 1 hour):
- Subject contains: "URGENT", "CRITICAL", "ASAP", "EMERGENCY", "DOWN"
- From: CEO, board members, key clients (check Company_Handbook.md)
- Contains: "legal notice", "contract breach", "security incident"
- Action: Alert human immediately, create high-priority task

**HIGH** (Response within 4 hours):
- Subject contains: "invoice", "payment", "contract", "proposal"
- From: Paying customers, sales prospects
- Contains: "complaint", "issue", "problem", "not working"
- Action: Process with priority, notify relevant team

**NORMAL** (Response within 24 hours):
- From: Known contacts, internal team
- General questions, status updates
- Routine business correspondence
- Action: Standard processing workflow

**LOW** (Response within 3 days):
- Newsletters, marketing, informational
- Non-time-sensitive requests
- "FYI" emails
- Action: Batch process, summarize if needed

### Spam/Ignore Classification
- Obvious spam, phishing attempts
- Unsubscribe requests (auto-handle)
- Out-of-office replies
- Delivery failure notifications

---

## Response Templates

### Acknowledgment (Urgent Emails)
```
Subject: Re: {original_subject}

Thank you for your email. I've received your message marked as urgent and am reviewing it now.

I'll provide a detailed response within [timeframe based on issue].

If this is extremely time-sensitive, please call [phone number from handbook].

Best regards,
[Company Name] AI Assistant
```

### Standard Inquiry Response
```
Subject: Re: {original_subject}

Hi {customer_name},

Thank you for reaching out to us regarding {topic}.

{answer_based_on_context}

{if_needs_human}: I've forwarded this to [relevant team] who will follow up with you within [SLA timeframe].

Is there anything else I can help with?

Best regards,
[Company Name] AI Assistant
```

### Invoice/Payment Inquiry
```
Subject: Re: {original_subject}

Hi {customer_name},

Thank you for your inquiry about {invoice_number/payment}.

{provide_status_or_details}

{if_issue}: I've escalated this to our finance team. You should receive an update within [timeframe].

If you need immediate assistance, please contact [finance_email from handbook].

Best regards,
[Company Name] AI Assistant
```

### Escalation to Human
```
Subject: Re: {original_subject}

Hi {customer_name},

Thank you for your email. I've reviewed your request regarding {topic}.

This requires review by our {relevant_team}. I've forwarded your email to {contact_name} who will respond within {SLA_timeframe}.

You can also reach them directly at {email/phone}.

Best regards,
[Company Name] AI Assistant
```

---

## Escalation Rules (HITL Required)

### Automatic Escalation (Cannot Auto-Respond)
1. **Legal/Contracts**:
   - Any email containing: "contract", "agreement", "terms", "legal", "attorney", "lawsuit"
   - Action: Create approval task, notify legal team

2. **Financial Commitments**:
   - Mentions specific dollar amounts >$500
   - Payment disputes or refund requests
   - Action: Create approval task, notify finance

3. **Confidential Information Requests**:
   - Requests for: employee data, financial reports, strategic plans
   - Action: Do NOT respond, escalate immediately

4. **Negative Sentiment/Complaints**:
   - Contains: "cancel my account", "terrible service", "lawsuit", "BBB complaint"
   - Action: Escalate to customer success, CC management

5. **Technical Issues Beyond Scope**:
   - Requires code changes, architecture decisions
   - Mentions data loss or security concerns
   - Action: Escalate to engineering

### Human Approval Before Sending
- Any response making commitments (dates, pricing, features)
- Responses to C-level executives
- First-time client communications
- Anything outside standard FAQ responses

---

## Context Loading

Before crafting a response, load:

1. **Company_Handbook.md**: 
   - Communication protocols
   - SLA timelines
   - Key contacts
   - Escalation procedures

2. **Business_Goals.md**:
   - Strategic priorities
   - Current initiatives
   - Key clients

3. **Previous Email Thread** (if available):
   - Customer history
   - Prior issues
   - Promises made

4. **FAQ/Knowledge Base** (future: separate file):
   - Common questions
   - Standard answers
   - Product documentation

---

## Email Actions

### Can Auto-Execute (No HITL)
- ✅ Mark as read
- ✅ Send acknowledgment (template-based)
- ✅ Answer FAQ-style questions
- ✅ Forward to appropriate team (with notification)
- ✅ Update CRM/ERP with customer communication
- ✅ Schedule follow-up reminder

### Requires HITL Approval
- ⚠️ Send response with commitments (dates, pricing)
- ⚠️ Send response to C-level or key clients
- ⚠️ Forward confidential information
- ⚠️ Send anything not matching a template
- ⚠️ Attach files or documents

### Never Auto-Execute
- ❌ Delete emails
- ❌ Unsubscribe on behalf of user
- ❌ Forward to external parties
- ❌ Modify sent emails (obviously)

---

## Response Quality Checklist

Before sending any email, verify:
- [ ] Addresses customer by name (if known)
- [ ] References specific issue/question
- [ ] Provides clear answer or next steps
- [ ] Includes timeframe for resolution (if applicable)
- [ ] Offers alternative contact method
- [ ] Professional but friendly tone
- [ ] No typos or grammar errors
- [ ] Signature includes company name
- [ ] CCs appropriate parties (if needed)
- [ ] Matches company's communication style (see handbook)

---

## Threading Rules

- **Reply to Thread**: If original email is part of a thread, reply to thread (not new email)
- **Subject Line**: Keep "Re:" prefix, don't change subject
- **Quoting**: Include relevant portions of previous email for context
- **Trimming**: Remove excessive quoted history (keep last 2-3 messages max)

---

## Anti-Patterns (What NOT to Do)

❌ **DON'T** send generic "Thanks for contacting us" without addressing the issue
❌ **DON'T** promise features or timelines without checking with engineering
❌ **DON'T** share customer data with unauthorized parties
❌ **DON'T** use emojis (unless company culture explicitly allows)
❌ **DON'T** argue or be defensive in responses
❌ **DON'T** send after-hours emails to customers (respect their time)
❌ **DON'T** reply-all unless absolutely necessary

---

## Metrics to Track

- Response time (by priority level)
- Resolution rate (auto-resolved vs escalated)
- Customer satisfaction (if follow-up survey available)
- Escalation rate (should decrease over time as skills improve)
- HITL approval rate (should stabilize around 5-10%)

---

## Version History

- **2026-02-05**: Initial email skills created
- **Future**: Update based on actual usage patterns

---

**This file is authoritative for email handling. When in doubt, escalate to HITL.**
