# Task Decomposition Skill - Break Down Complex Work

**Purpose**: Decompose complex tasks into small, manageable, sequential steps for autonomous execution.

**CRITICAL**: This skill enables Claude to reason about multi-step work without hardcoded workflows.

---

## Decomposition Framework

### Principle: Small, Verifiable Steps

**Good Task:**
- Single clear action
- Verifiable completion criteria
- Takes < 5 minutes (ideally)
- No ambiguity
- Can fail or succeed clearly

**Bad Task:**
- "Handle the project" (too vague)
- "Improve sales" (no completion criteria)
- "Research competitors" (unbounded scope)
- "Do whatever makes sense" (no structure)

---

## Step-by-Step Decomposition

### Step 1: Understand the Goal ✅

**Ask:**
- What is the desired end state?
- What does "done" look like?
- Who is the beneficiary (me, customer, team)?
- What is the deadline (if any)?
- What are the constraints?

**Example:**
```
Task: "Send invoice to Client A for January work"

Goal Understanding:
- End state: Client A receives valid invoice, payment initiated
- "Done" = Invoice sent + logged + tracked
- Beneficiary: Company (gets paid), Client (receives service billing)
- Deadline: Within 3 days of project completion (standard)
- Constraints: Must use Odoo, must have approval, must follow invoice_workflow
```

---

### Step 2: Identify Dependencies ✅

**Map what must happen before what:**

**Example Invoice Task:**
```
Dependencies:
1. Need project completion confirmation (check /Done folder)
2. Need customer record (check Odoo)
3. Need pricing information (check contract or rate sheet)
4. Need accounting system access (Odoo must be running)
5. Need approval system working (HITL mechanism)
6. Need email capability (to send invoice)
```

**Critical Path:**
```
Project Complete → Gather Info → Draft Invoice → Get Approval → Post → Send → Track
```

**Parallel Opportunities:**
```
While waiting for approval:
- Can prepare email template
- Can update Dashboard with "Pending approval" status
- Can queue next non-dependent task
```

---

### Step 3: Break Into Atomic Actions ✅

**Each step should be:**
- One action verb (Read, Write, Create, Send, Update, Check)
- Specific target (which file, which system, which person)
- Clear success criteria
- Explicit failure handling

**Example Breakdown:**
```markdown
## Task: Send Invoice to Client A

### Subtasks (Sequential):

1. **Read project completion file**
   - Action: Read /Done/ClientA_Project.md
   - Success: File exists, contains project details
   - Failure: If missing, flag for human ("Cannot find completion record")

2. **Extract billing information**
   - Action: Parse file for services, hours, dates
   - Success: Have list of billable items
   - Failure: If incomplete, flag for human ("Missing billing details")

3. **Load invoice_workflow_skill**
   - Action: Read obsidian_vault/agent_skills/invoice_workflow_skill.md
   - Success: Skill loaded, workflow understood
   - Failure: If skill missing, use fallback (generic approach + approval)

4. **Look up customer in Odoo**
   - Action: Call odoo_server.search_customer("Client A")
   - Success: Customer found, have partner_id
   - Failure: If not found, create approval request to add customer

5. **Calculate invoice total**
   - Action: Sum line items, apply tax rate
   - Success: Have subtotal, tax, total
   - Failure: If pricing uncertain, flag for review

6. **Create invoice draft in Odoo**
   - Action: Call odoo_server.create_invoice_draft(params)
   - Success: Draft created, have draft_id
   - Failure: If Odoo error, retry 3x, then flag for human

7. **Create approval request**
   - Action: Write JSON to /Pending_Approval/INVOICE_ClientA_[date].json
   - Success: File created with all details
   - Failure: If write fails, log error and alert human

8. **Wait for approval**
   - Action: Monitor /Pending_Approval folder
   - Success: File moved to /Approved
   - Failure: File moved to /Rejected → stop, log reason

9. **Post invoice in Odoo**
   - Action: Call odoo_server.post_invoice(draft_id)
   - Success: Invoice posted, have invoice_number
   - Failure: If post fails, alert human (cannot easily undo)

10. **Send invoice email**
    - Action: Call email_server.send(to, subject, body, attachment)
    - Success: Email sent confirmation
    - Failure: If send fails, retry 2x, then manual send alert

11. **Update Dashboard**
    - Action: Add line to Dashboard.md "Invoice sent to Client A: $X,XXX"
    - Success: Dashboard updated
    - Failure: Log error but continue (not critical)

12. **Move task to complete**
    - Action: Move pending task file to /task_queue/completed/
    - Success: Task marked complete
    - Failure: Log but continue

13. **Audit log entry**
    - Action: Write to audit_logs/[date].jsonl
    - Success: Entry added
    - Failure: Alert (audit logs are critical)
```

---

### Step 4: Estimate Effort & Risk ✅

**For each subtask:**
- Effort: Trivial / Low / Medium / High
- Risk: Low / Medium / High / Critical
- Failure impact: Recoverable / Retry-able / Requires Human

**Example:**
```
Task: Create invoice draft in Odoo
- Effort: Low (API call, well-understood)
- Risk: Medium (Odoo might be down or misconfigured)
- Failure Impact: Retry-able (drafts can be deleted/recreated)

Task: Post invoice in Odoo
- Effort: Low (single API call)
- Risk: High (posting is permanent, affects accounting)
- Failure Impact: Requires Human (cannot easily undo)
```

**Use for prioritization and approval:**
- High risk → Require approval before execution
- Critical failure impact → Add extra validation
- High effort → Consider if worth automating

---

### Step 5: Add Checkpoints & Rollback ✅

**Checkpoint Pattern:**
```
After each major step:
- Log progress
- Save state
- Verify success
- Prepare rollback if possible
```

**Example:**
```
After "Create invoice draft":
→ Save draft_id to state file
→ If next steps fail, can delete draft
→ Log: "Invoice draft created: draft_123"

After "Post invoice":
→ Save invoice_number to state file
→ If email fails, still have posted invoice (no rollback needed)
→ Log: "Invoice posted: INV-2026-001"
```

**Rollback Strategy:**
```
IF step fails AND step is reversible:
    → Undo previous steps in reverse order
    → Log rollback actions
    → Return to safe state
    → Create approval request for manual handling

IF step fails AND step is NOT reversible:
    → STOP immediately
    → Alert human
    → Do NOT proceed
    → Log partial state for human to fix
```

---

### Step 6: Parallel vs. Sequential ✅

**Sequential (must be in order):**
- Draft invoice BEFORE post invoice
- Approval BEFORE execution
- Read file BEFORE parse file

**Parallel (can happen simultaneously):**
- Look up customer AND fetch pricing (independent lookups)
- Draft email template WHILE waiting for approval
- Update Dashboard AND send notification (both post-completion)

**Claude's Planning:**
```
Sequential tasks → One at a time, wait for completion
Parallel tasks → Can batch or queue separately
```

---

## Integration with Ralph Loop

**Ralph Loop uses this skill to:**
1. Decompose initial task into subtasks
2. Execute first subtask
3. Check completion
4. Execute next subtask
5. Repeat until all done
6. Max iterations protects from infinite loops

**Task State File:**
```json
{
    "task_id": "invoice_ClientA_20260216",
    "subtasks": [
        {"step": 1, "action": "Read completion file", "status": "done"},
        {"step": 2, "action": "Extract billing info", "status": "done"},
        {"step": 3, "action": "Load workflow skill", "status": "done"},
        {"step": 4, "action": "Lookup customer", "status": "in_progress"},
        {"step": 5, "action": "Calculate total", "status": "pending"},
        ...
    ],
    "current_step": 4,
    "iterations": 12,
    "max_iterations": 50
}
```

---

## Common Patterns

### Pattern: Data Pipeline
```
1. Read input
2. Validate input
3. Transform data
4. Write output
5. Verify output
```

### Pattern: API Call with Retry
```
1. Prepare request data
2. Call API (attempt 1)
3. If success → proceed
4. If failure and retryable → wait, call API (attempt 2)
5. If failure and retryable → wait longer, call API (attempt 3)
6. If still failure → flag for human
```

### Pattern: Approval-Gated Action
```
1. Prepare action details
2. Create approval request
3. Wait (Ralph Loop sleeps here)
4. Check approval status
5. If approved → execute action
6. If rejected → log and stop
7. If timeout → escalate
```

### Pattern: Multi-System Update
```
1. Update System A
2. If success, update System B
3. If System B fails → rollback System A
4. If all succeed → update Dashboard
5. Audit log all changes
```

---

## Error Handling Guidelines

**Transient Errors (retry):**
- Network timeouts
- API rate limits
- Temporary file locks

**Permanent Errors (stop):**
- Invalid credentials
- Missing required data
- Business rule violations

**Logic Errors (rethink):**
- Misunderstood task
- Wrong approach
- Circular dependencies

---

## Integration with Other Skills

- **planning_skills.md** → High-level planning
- **approval_skills.md** → When to gate steps
- **invoice_workflow_skill.md** → Domain-specific decomposition
- **file_analysis_skill.md** → Understanding inputs

---

**This skill is authoritative for task decomposition. Use it for all complex, multi-step work.**
