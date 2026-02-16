# Email Triage Skill - Priority Detection

**Purpose**: Determine email priority based on sender, subject, and content keywords.

**CRITICAL**: This skill provides structured rules for email classification. NO hardcoded logic allowed in Python code.

---

## Priority Detection Algorithm

### CRITICAL Priority (Process within 1 hour)
**Triggers:**
- Subject contains: "URGENT", "CRITICAL", "ASAP", "EMERGENCY", "DOWN", "OUTAGE"
- From domain matches: CEO, board members (check Company_Handbook.md)
- Keywords: "legal notice", "contract breach", "security incident", "data breach"
- Payment issues: "payment failed", "account suspended", "overdue invoice"

**Actions:**
- Create high-priority task immediately
- Send human alert notification
- Log in audit trail with CRITICAL flag
- Set auto-reminder for 30 minutes if not handled

---

### HIGH Priority (Process within 4 hours)
**Triggers:**
- Subject contains: "invoice", "payment", "contract", "proposal", "deadline"
- From: Paying customers (check vault for customer list)
- From: Sales prospects with engagement history
- Keywords: "complaint", "issue", "problem", "not working", "broken"
- Meeting requests from important contacts

**Actions:**
- Process with elevated priority
- Notify relevant team (if multi-person setup)
- Set deadline for response
- Track in Dashboard under "Pending High Priority"

---

### NORMAL Priority (Process within 24 hours)
**Triggers:**
- From: Known contacts in vault
- General questions or status updates
- Routine business correspondence
- Follow-ups on existing conversations
- Internal team communication

**Actions:**
- Standard processing workflow
- Use email_skills.md for response templates
- Normal audit logging
- Update Dashboard.md

---

### LOW Priority (Process within 3 days)
**Triggers:**
- Newsletters, marketing emails
- Non-time-sensitive requests
- "FYI" emails with no action required
- Updates from subscriptions
- Automated notifications (non-critical)

**Actions:**
- Batch process during low-activity periods
- Summarize if needed (don't reply individually)
- Archive after reading
- Minimal Dashboard impact

---

### SPAM/IGNORE (Auto-handle)
**Triggers:**
- Obvious spam patterns
- Phishing attempts (suspicious links, urgent password resets from non-official domains)
- Unsubscribe requests (handle automatically)
- Out-of-office replies
- Delivery failure notifications (unless critical sender)
- Marketing from unknown senders

**Actions:**
- Mark as spam (if Gmail API allows)
- Auto-archive
- Do NOT create task
- Log in spam log for audit

---

## Sender Reputation Check

**Known Sender (Good Standing):**
- Email in vault contacts
- Previous successful interactions logged
- No complaints or issues

**Unknown Sender (New Contact):**
- First-time email
- Requires extra caution
- May need HITL approval for response

**Suspicious Sender:**
- Mismatched "From" and "Reply-To"
- Generic sender name with suspicious domain
- Excessive urgency or fear tactics
- Requesting credentials or payments

---

## Example Classification Logic

```
IF subject contains "URGENT" AND sender in known_customers:
    → Priority: HIGH (not CRITICAL, known sender reduces urgency)

IF subject contains "CRITICAL" AND sender is unknown:
    → Priority: CRITICAL (unknown + critical keyword = maximum caution)

IF subject contains "invoice" AND sender in known_vendors:
    → Priority: HIGH

IF subject contains "newsletter":
    → Priority: LOW (or SPAM if unsubscribed)
```

---

## Integration with Email Skills

After classification, use [email_skills.md](email_skills.md) for:
- Response templates based on priority
- Tone and voice guidelines
- Escalation rules
- HITL approval thresholds

---

**This skill is authoritative for email triage. All triage logic must reference this file.**
