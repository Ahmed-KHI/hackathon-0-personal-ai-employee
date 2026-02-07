# Planning Skills - Agent Intelligence for Task Planning & Execution

**Purpose**: Guide AI Employee in breaking down complex tasks, planning execution, and managing workflows.

**CRITICAL**: This is how the AI Employee reasons about multi-step tasks.

---

## Task Decomposition

### Simple Tasks (Single-Step)
Execute immediately if:
- No dependencies
- Clear input/output
- No HITL required
- Estimated time <5 minutes

Examples:
- Mark email as read
- Update dashboard
- Log audit entry
- Send acknowledgment

### Complex Tasks (Multi-Step)
Break down if:
- Multiple dependencies
- Requires multiple MCP servers
- Estimated time >15 minutes
- Involves decision points

**Decomposition Strategy**:
```
Task: "Respond to client invoice inquiry"

Step 1: Load context
  - Read original email
  - Check Company_Handbook for client info
  - Load finance_skills.md

Step 2: Gather data
  - Query ERP for invoice details
  - Check payment status
  - Get transaction history

Step 3: Analyze
  - Is payment overdue?
  - Any disputes or issues?
  - What does customer need?

Step 4: Draft response
  - Use email_skills.md template
  - Include specific invoice details
  - Provide clear next steps

Step 5: Execute
  - If standard: Send email
  - If complex: Create HITL approval
  - Log action in audit trail

Step 6: Follow-up
  - Update CRM/ERP
  - Set reminder if needed
  - Close task
```

---

## Decision Trees

### Email Response Decision Tree
```
New Email Received
├─ Is it spam/automated? 
│  └─ Yes → Mark read, ignore
│  └─ No → Continue
│
├─ Is it urgent? (check email_skills.md)
│  └─ Yes → Process immediately
│  └─ No → Add to queue
│
├─ Can I answer from FAQ?
│  └─ Yes → Draft response
│  └─ No → Continue
│
├─ Do I have all context?
│  └─ No → Load handbook, previous emails
│  └─ Yes → Continue
│
├─ Does it require HITL?
│  └─ Yes → Create approval task
│  └─ No → Draft response
│
└─ Send response & close task
```

### Finance Transaction Decision Tree
```
Transaction Detected
├─ Amount >$5,000?
│  └─ Yes → Escalate to CFO
│  └─ No → Continue
│
├─ Known vendor?
│  └─ No → Escalate for vendor onboarding
│  └─ Yes → Continue
│
├─ Matches PO?
│  └─ No → Flag for review
│  └─ Yes → Continue
│
├─ Within budget?
│  └─ No → Require approval
│  └─ Yes → Process payment
│
└─ Update ERP & close task
```

---

## Iteration Strategy (Ralph Loop Protection)

### Iteration Counter
Each task tracks iterations:
```
Iteration 1: Claim task, load context
Iteration 2: Attempt execution
Iteration 3: If failed, retry with different approach
...
Iteration 50: STOP - Ralph Loop triggered
```

### Progressive Problem-Solving

**Iteration 1-5**: Standard approach
- Use existing templates
- Follow documented procedures
- Minimal creativity

**Iteration 6-15**: Alternative approaches
- Try different data sources
- Check for edge cases
- Load additional context

**Iteration 16-30**: Advanced troubleshooting
- Break task into smaller pieces
- Seek human clarification
- Check for system issues

**Iteration 31-49**: Prepare for failure
- Document what was tried
- Identify blocking issue
- Prepare escalation report

**Iteration 50**: Ralph Loop triggered
- Task aborted
- Human alerted
- Full context logged

### When to Stop Iterating Early

Stop and escalate if:
- Same error occurs 3 times
- No progress after 10 iterations
- Missing critical information
- External dependency blocked
- Security concern detected

---

## Context Management

### Information to Load

**Always Load**:
1. Company_Handbook.md (business context)
2. Business_Goals.md (strategic priorities)
3. Relevant agent skill file
4. Task-specific context

**Load If Needed**:
- Previous tasks from same source
- Customer history (CRM)
- Financial data (ERP)
- Email threads
- Related documents

### Context Priority

If context loading takes too long (>30 seconds):
1. Load handbook (must have)
2. Load task context (must have)
3. Load agent skills (must have)
4. Skip nice-to-have context
5. Note in audit log: "Limited context due to timeout"

---

## Parallel vs Sequential Execution

### Can Execute in Parallel
- Independent data fetches
- Multiple status checks
- Non-conflicting updates
- Read-only operations

Example:
```
Task: Generate weekly report

Parallel fetch:
- Email count (Gmail API)
- Transaction count (Finance API)
- Task completion count (local files)
- Calendar events (Calendar API)

Then: Compile report
```

### Must Execute Sequentially
- Dependencies between steps
- State-modifying operations
- Approval workflows
- Write operations to same resource

Example:
```
Task: Process invoice

Step 1: Validate invoice (must complete first)
Step 2: Check budget (depends on validation)
Step 3: Get approval (depends on budget check)
Step 4: Process payment (depends on approval)
Step 5: Update ERP (depends on payment)
```

---

## Error Handling

### Retry-able Errors
- Network timeouts
- API rate limits
- Temporary service unavailable
- Transient failures

**Action**: Use retry_handler with exponential backoff

### Permanent Errors
- Authentication failure
- Invalid input data
- Permission denied
- Resource not found

**Action**: Log error, escalate to human

### Unknown Errors
- Unexpected exceptions
- System errors
- Data corruption

**Action**: Abort task, alert human immediately

---

## Priority Queue Management

### Task Prioritization

**P0 - CRITICAL** (Drop everything):
- System down alerts
- Security incidents
- CEO/board requests
- Fraud detection

**P1 - HIGH** (Process within 4 hours):
- Client complaints
- Payment issues
- Contract-related
- SLA violations

**P2 - NORMAL** (Process within 24 hours):
- Standard emails
- Routine transactions
- Status updates
- Internal requests

**P3 - LOW** (Process when idle):
- Cleanup tasks
- Optimization
- Nice-to-have reports
- Archive old data

### Dynamic Reprioritization

Elevate priority if:
- Multiple follow-ups from same person
- Approaching deadline
- Mentioned by CEO/executive
- Customer satisfaction at risk

Lower priority if:
- Requester says "no rush"
- Internal non-critical task
- Can wait for batch processing

---

## Batch Processing

### Tasks Suitable for Batching

- Mark multiple emails as read
- Update multiple CRM records
- Generate multiple reports
- Process small transactions (<$100)

### Batch Execution Strategy
```
Every [interval]:
1. Collect all P3 tasks
2. Group by type (emails, transactions, etc.)
3. Execute similar tasks together
4. Update status in bulk
5. Generate summary report
```

---

## Resource Management

### API Rate Limits

Track API calls per service:
- Gmail: 250/day (user), 25,000/day (domain)
- Anthropic Claude: [per plan]
- Calendar: 10,000/day
- Slack: Tier-dependent

If approaching limit:
- Batch requests
- Cache results
- Defer non-critical tasks
- Alert human if critical task blocked

### Cost Tracking

Monitor spending:
- Claude API tokens
- Email API calls
- Calendar API calls
- MCP server costs

If exceeding budget:
- Reduce non-essential queries
- Use cached data
- Defer low-priority tasks
- Alert finance team

---

## Monday Morning CEO Briefing

### Weekly Report Generation

**Trigger**: Every Monday at 6:00 AM

**Process**:
1. Load audit logs (past 7 days)
2. Query task_queue/completed
3. Load Business_Goals.md
4. Generate summary report
5. Update Dashboard.md
6. Send email notification (if configured)

**Report Structure**:
```markdown
# Weekly AI Employee Report - [Week of Date]

## Executive Summary
- [X] tasks completed
- [Y] hours saved (estimated)
- [Z] pending approvals

## Key Achievements 🎉
1. [Notable task 1]
2. [Notable task 2]

## By the Numbers 📊
- Emails processed: [X]
- Transactions monitored: [Y]
- Approvals required: [Z]
- System uptime: [%]

## Challenges & Escalations ⚠️
- [Issue 1 + resolution]
- [Issue 2 + pending]

## Week Ahead 📅
- [Upcoming tasks]
- [Scheduled meetings]
- [Deadlines]

## Recommendations 💡
- [Improvement 1]
- [Process optimization 2]

---
Generated by AI Employee | [Timestamp]
```

---

## Continuous Learning

### Pattern Recognition

Track successful patterns:
- What approaches worked?
- Which templates were most effective?
- Common escalation triggers
- Frequently asked questions

### Failure Analysis

When task fails:
- Document root cause
- Identify missing skills
- Suggest handbook updates
- Propose new templates

### Skill Evolution

Periodically (monthly):
- Review task success rate
- Identify skill gaps
- Propose new agent skills
- Update existing skills

---

## Anti-Patterns (What NOT to Do)

❌ **DON'T** iterate forever (Ralph Loop protection)
❌ **DON'T** execute tasks out of priority order
❌ **DON'T** skip context loading
❌ **DON'T** make assumptions without verification
❌ **DON'T** proceed without required approvals
❌ **DON'T** ignore error patterns
❌ **DON'T** batch critical tasks
❌ **DON'T** exceed API/cost budgets

---

## Metrics to Track

- Average iterations per task
- Task completion rate
- Time to completion by task type
- Escalation rate
- Ralph Loop trigger frequency
- Resource utilization (API calls, costs)

---

## Version History

- **2026-02-05**: Initial planning skills created
- **Future**: Update based on execution patterns

---

**This file is authoritative for task planning and execution. When in doubt, break task into smaller steps.**
