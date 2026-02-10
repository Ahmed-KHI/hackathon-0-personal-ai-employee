# Approval Skills - Agent Intelligence for HITL (Human-in-the-Loop)

**Purpose**: Guide AI Employee in determining when human approval is required and how to request it.

**CRITICAL**: This prevents the AI from taking unauthorized actions.

---

## When to Require Approval (HITL)

### ALWAYS Require Approval

**Financial Commitments**:
- Any transaction >$500
- New vendor payments
- Refunds to customers
- Budget reallocations
- Contract payments

**Legal & Compliance**:
- Sending/signing contracts
- Legal correspondence
- Terms & conditions changes
- Privacy policy updates
- Any document with legal implications

**Confidential Information**:
- Sharing financial reports
- Employee data (salaries, performance)
- Strategic plans or roadmaps
- Customer lists or proprietary data
- Board meeting materials

**External Commitments**:
- Promising delivery dates
- Committing to features/functionality
- Pricing quotes >$1,000
- Service level agreements
- Partnership terms

**High-Stakes Communication**:
- First-time client emails
- Responses to C-level executives
- Public statements (social media, press)
- Customer complaints/escalations
- Termination or cancellation notices

**System Changes**:
- Production database access
- Code deployments
- Infrastructure changes
- Security policy updates
- Access control modifications

---

## Approval Thresholds by Category

### Financial
| Amount | Approval Required |
|--------|-------------------|
| <$100 | None (auto-process) |
| $100-$500 | Manager |
| $500-$5,000 | CFO |
| $5,000-$50,000 | CFO + CEO |
| >$50,000 | CEO + Board |

### Data Sharing
| Data Type | Approval Required |
|-----------|-------------------|
| Public info | None |
| Customer names | Manager |
| Financial data | CFO |
| Employee PII | CEO + Legal |
| Trade secrets | CEO + Board |

### Communication
| Recipient | Approval Required |
|-----------|-------------------|
| Internal team | None (routine) |
| Known clients | Manager (first time) |
| New prospects | Sales Lead |
| Press/Media | CEO + Marketing |
| Regulators | CEO + Legal |

---

## Approval Request Format

### File Structure
Create: `task_queue/approvals/{task_id}.json`

```json
{
  "task_id": "uuid-v4",
  "created_at": "2026-02-05T10:00:00Z",
  "approval_type": "financial|communication|data_sharing|system_change",
  "urgency": "critical|high|normal|low",
  "requester": "ai_employee",
  "reason": "Transaction exceeds $500 threshold",
  
  "action_preview": {
    "action": "send_payment",
    "to": "Acme Corp",
    "amount": 1200.00,
    "description": "Invoice #1234 - Q1 Services"
  },
  
  "context": {
    "original_task": "process_invoice",
    "source": "finance_watcher",
    "related_documents": ["invoice_1234.pdf"],
    "business_justification": "Regular quarterly payment"
  },
  
  "risk_assessment": {
    "financial_risk": "low (known vendor, expected amount)",
    "reputational_risk": "none",
    "compliance_risk": "none"
  },
  
  "recommendation": "approve",
  "ai_confidence": "high",
  
  "approval_deadline": "2026-02-06T17:00:00Z",
  "approvers_required": ["cfo@company.com"],
  
  "approval_status": "pending",
  "approved_by": null,
  "approved_at": null,
  "rejection_reason": null
}
```

### Human Approval Actions

**To Approve**:
1. Review `{task_id}.json`
2. Rename to `{task_id}.approved`
3. AI resumes task execution

**To Reject**:
1. Review `{task_id}.json`
2. Rename to `{task_id}.rejected`
3. Add `rejection_reason` to file
4. AI aborts task, logs rejection

**To Request Changes**:
1. Edit `{task_id}.json`
2. Add field: `"requested_changes": "details here"`
3. AI re-plans task with feedback

---

## Approval Workflow

### Step 1: Detect HITL Requirement
```python
def requires_hitl(task):
    # Check approval_skills.md rules
    if task.amount > 500:
        return True
    if task.contains("contract"):
        return True
    if task.recipient in c_level_executives:
        return True
    # ... more checks
    return False
```

### Step 2: Pause Task Execution
- Move task from `pending/` to `approvals/`
- Create approval request file
- Log in audit trail

### Step 3: Notify Approvers
- Send email notification (if configured)
- Update Dashboard.md
- Set timeout (default: 24 hours)

### Step 4: Wait for Approval
- Poll `approvals/` directory
- Check for `.approved` or `.rejected` extension
- If timeout: escalate to higher authority

### Step 5: Resume or Abort
- If approved: Move back to `pending/`, execute
- If rejected: Move to `completed/`, mark failed
- Log outcome in audit trail

---

## Approval Templates

### Financial Approval Email
```
Subject: Approval Required: ${task_type} - $${amount}

Hi ${approver_name},

The AI Employee needs approval for the following action:

Action: ${action_description}
Amount: $${amount}
Vendor/Recipient: ${recipient}
Reason: ${business_justification}

Details:
${action_preview}

Risk Assessment:
- Financial Risk: ${financial_risk}
- Compliance Risk: ${compliance_risk}

AI Recommendation: ${recommendation} (Confidence: ${confidence})

To approve: Rename file approvals/${task_id}.json to ${task_id}.approved
To reject: Rename to ${task_id}.rejected

Deadline: ${approval_deadline}

Questions? Reply to this email or call [phone].

---
AI Employee Approval System
```

### Communication Approval Email
```
Subject: Approval Required: Email to ${recipient}

Hi ${approver_name},

The AI Employee has drafted the following email and needs approval:

To: ${to}
Subject: ${subject}

${email_body}

Context:
${context_summary}

This requires approval because: ${reason}

To approve: Rename approvals/${task_id}.json to ${task_id}.approved
To reject or request changes: Rename to ${task_id}.rejected and add feedback

Deadline: ${approval_deadline}

---
AI Employee Approval System
```

---

## Approval Timeout Handling

### Timeout Scenarios

**No Response After 24 Hours**:
- Send reminder notification
- Escalate to next level approver
- Mark task as "awaiting_approval_timeout"

**No Response After 48 Hours**:
- Escalate to CEO
- Alert in Dashboard (critical)
- Log as potential blocker

**No Response After 72 Hours**:
- Auto-reject task (safety measure)
- Alert CEO and task requester
- Review approval process

### Urgent Tasks (Timeout: 2 hours)
- Send SMS/phone notification
- Escalate immediately if no response
- Provide alternative contact method

---

## Approval Analytics

### Track Metrics
- **Approval Rate**: % approved vs rejected
- **Response Time**: Time to approval decision
- **Approval Accuracy**: Were approvals justified?
- **Override Rate**: Times human overrode AI recommendation

### Optimization
If approval rate >95% for category:
- Consider raising auto-approval threshold
- Update agent skills with new patterns

If approval rate <70% for category:
- AI is misjudging risk
- Lower auto-approval threshold
- Improve decision logic

---

## Multi-Level Approvals

### Sequential Approvals
```
Task: Large contract payment ($25,000)

Level 1: Manager reviews business justification
  ↓ Approved
Level 2: CFO reviews financial impact
  ↓ Approved
Level 3: CEO reviews strategic alignment
  ↓ Approved
Execute: Payment processed
```

### Parallel Approvals
```
Task: New product launch announcement

Legal Team: Reviews compliance ─┐
                                  ├→ All approve → Execute
Marketing Team: Reviews messaging ─┘
```

---

## Approval Delegation

### Delegation Rules (from Company_Handbook.md)

**Manager can delegate to**:
- Senior team member
- Acting manager (during absence)

**CFO can delegate to**:
- Controller
- VP Finance

**CEO can delegate to**:
- COO
- President

### Out-of-Office Handling
If primary approver is OOO:
1. Check calendar for return date
2. If <24 hours: Wait
3. If >24 hours: Escalate to delegate
4. If no delegate: Escalate to next level

---

## Emergency Override

### When Human Can Override Approval Process

**Critical Business Need**:
- Company survival at risk
- Legal deadline
- Customer emergency
- Security incident

**Override Procedure**:
1. Human creates: `approvals/{task_id}.emergency_override`
2. File must include:
   - Override reason
   - Approver identity
   - Risk acknowledgment
3. AI executes immediately
4. Log as "emergency_override" in audit trail
5. Post-hoc review by CEO

**Restrictions**:
- Max 1 emergency override per month
- Must be documented in board meeting
- Requires 2-person authorization (CEO + CFO)

---

## Approval Skill Evolution

### Self-Improvement Loop

**Monthly Review**:
1. Analyze all approval requests
2. Identify false positives (unnecessary approvals)
3. Identify false negatives (missed approvals)
4. Propose threshold adjustments
5. Update approval_skills.md

**Continuous Learning**:
- Track approval decisions
- Learn from rejections
- Adjust risk assessment model
- Improve confidence scoring

---

## Anti-Patterns (What NOT to Do)

❌ **DON'T** bypass approval process (ever)
❌ **DON'T** execute before approval received
❌ **DON'T** assume silence = approval
❌ **DON'T** re-request same approval repeatedly
❌ **DON'T** pressure approver for quick decision
❌ **DON'T** hide information from approver
❌ **DON'T** make action seem less risky than it is
❌ **DON'T** group unrelated actions for single approval

---

## Integration with Other Skills

### Email Skills → Approval Skills
- Check if email requires approval
- If yes, create approval request
- Include email draft in preview

### Finance Skills → Approval Skills
- Check amount thresholds
- Verify vendor status
- Assess financial risk

### Planning Skills → Approval Skills
- Build approval into task plan
- Account for approval wait time
- Handle approval rejection

---

## Metrics to Track

- Approval request volume
- Approval response time (by approver, by category)
- Approval vs rejection rate
- False positive rate (unnecessary approvals)
- False negative rate (missed approvals)
- Emergency override frequency

---

## Version History

- **2026-02-05**: Initial approval skills created
- **Future**: Adjust thresholds based on actual approvals

---

**This file is authoritative for approval decisions. When in doubt, require approval.**
