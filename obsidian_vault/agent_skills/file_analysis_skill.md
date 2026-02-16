# File Analysis Skill - Intelligent Document Processing

**Purpose**: Analyze dropped files to determine intent, extract information, and plan appropriate actions.

**CRITICAL**: This skill enables Claude to reason about arbitrary file content without hardcoded handlers.

---

## File Analysis Framework

### Step 1: Determine File Type ✅

**By Extension:**
- `.txt`, `.md` → Text document (easy to analyze)
- `.pdf` → PDF document (may need OCR)
- `.docx`, `.doc` → Word document
- `.xlsx`, `.xls`, `.csv` → Spreadsheet data
- `.json` → Structured data
- `.jpg`, `.png` → Image (needs OCR/vision)
- `.mp3`, `.mp4` → Media (needs transcription)

**By Content Inspection:**
- Look for structured patterns (JSON, CSV headers)
- Check for email headers (forwarded email as .txt)
- Detect invoice patterns (subtotal, total, due date)
- Identify contracts (signature, terms, parties)

---

### Step 2: Extract Key Information ✅

**For Text Files:**
```
1. Read full content
2. Identify document type:
   - Email? → Extract sender, subject, date, body
   - Invoice? → Extract customer, amount, date, line items
   - Contract? → Extract parties, terms, dates, amounts
   - Note? → Extract topic, action items, deadlines
   - Data? → Extract rows, columns, key values
```

**Information Extraction Patterns:**

**Email Indicators:**
- "From:", "To:", "Subject:", "Date:"
- Email address patterns
- Reply chains ("On [date], [person] wrote:")
- Signature blocks

**Invoice Indicators:**
- "Invoice #", "Invoice Number", "Reference"
- "Total:", "Subtotal:", "Tax:"
- "Due Date:", "Payment Terms"
- Line items with quantities and prices
- Customer/vendor names

**Contract Indicators:**
- "Agreement", "Contract", "Terms and Conditions"
- "Party A", "Party B", signatory names
- Dates (effective date, expiration)
- Dollar amounts, payment terms
- Signatures or signature lines

**Action Request Indicators:**
- "TODO", "Action:", "Next Steps"
- Imperative verbs: "Create", "Send", "Update", "Review"
- Deadlines: "by [date]", "due [date]"
- Assignments: "assign to", "owner:", "@mention"

---

### Step 3: Determine Intent ✅

**Ask:**
- Why did human drop this file?
- What action is expected?
- Is this informational or actionable?
- Is there urgency?

**Common Intents:**

**1. Process Invoice/Bill:**
- File contains invoice from vendor
- Intent: Create bill in Odoo
- Action: Extract details → Draft bill → Approval

**2. Send Email:**
- File is email draft or contains email content
- Intent: Send email to specified recipient
- Action: Load email_skills → Draft → Approval → Send

**3. Update Records:**
- File contains data to update (customer info, prices, etc.)
- Intent: Update vault or Odoo records
- Action: Parse data → Validate → Update with approval

**4. Create Task:**
- File describes work to be done
- Intent: Create task or project plan
- Action: Use planning_skills → Break down → Create tasks

**5. Archive/Reference:**
- File is for record-keeping
- Intent: Store for future reference
- Action: File in appropriate vault folder

**6. Generate Content:**
- File has notes for social post, blog, document
- Intent: Generate polished content
- Action: Use social_skills → Draft → Approval → Publish

---

### Step 4: Plan Actions ✅

**Based on intent, create specific action plan:**

**Example 1: Invoice/Bill Detected**
```markdown
## Analysis Result
- File Type: Text invoice
- Document: Vendor invoice from ABC Corp
- Amount: $450.00
- Due Date: March 1, 2026

## Planned Actions
1. Extract invoice details (customer, amount, line items)
2. Load invoice_workflow_skill.md
3. Create vendor bill draft in Odoo via odoo_server MCP
4. Create approval request in /Pending_Approval/
5. Wait for human approval
6. Post bill to Odoo (after approval)
7. Update Dashboard.md
8. Move original file to vault/Accounting/Bills/

## Required Skills
- invoice_workflow_skill
- odoo_skills
- finance_skills
- approval_skills
```

**Example 2: Email Draft Detected**
```markdown
## Analysis Result
- File Type: Email draft
- To: client@example.com
- Subject: Project Update - Q1 2026
- Body: [draft content]

## Planned Actions
1. Load email_skills.md for tone guidelines
2. Review draft against Company_Handbook voice
3. Check if client is known (search vault)
4. Polish draft (improve clarity, add CTA)
5. Create email approval request in /Pending_Approval/
6. Wait for human review
7. Send via email_server MCP (after approval)
8. Mark email as sent in Dashboard

## Required Skills
- email_skills
- approval_skills
- planning_skills
```

**Example 3: Generic Text Note**
```markdown
## Analysis Result
- File Type: Plain text note
- Content: Ideas for blog post about AI automation
- No clear action items
- Appears informational

## Planned Actions
1. Read and understand content
2. Categorize topic (blog ideas)
3. Move to vault/Drafts/Blog_Ideas/
4. Add entry to Dashboard "Ideas" section
5. No immediate action required
6. Available for future content generation

## Required Skills
- planning_skills
```

---

### Step 5: Confidence Assessment ✅

**Rate confidence in analysis:**

**HIGH Confidence (90-100%):**
- Clear document type (obvious invoice, email headers)
- All key information extracted
- Intent is unambiguous
- Standard workflow applies

**MEDIUM Confidence (60-89%):**
- Document type likely but not certain
- Some information missing
- Intent can be inferred but has alternatives
- May need human clarification

**LOW Confidence (0-59%):**
- Document type unclear
- Cannot extract key information
- Intent is ambiguous
- Multiple possible interpretations

**Action Based on Confidence:**
```
IF confidence >= 90%:
    → Proceed with planned actions (with approval for high-risk)

IF confidence >= 60% AND < 90%:
    → Create approval request with "REVIEW NEEDED" flag
    → Explain uncertainty
    → Suggest alternatives

IF confidence < 60%:
    → STOP, do not proceed
    → Create human review request
    → Ask clarifying questions
    → Wait for human guidance
```

---

### Step 6: Security & Privacy Check ✅

**Before processing:**

**Check for Sensitive Data:**
- [ ] Social Security Numbers / Tax IDs
- [ ] Credit card numbers
- [ ] Bank account details
- [ ] Passwords or credentials
- [ ] Personal health information
- [ ] Confidential business data

**If sensitive data detected:**
```
→ STOP immediate processing
→ Create secure approval request (no data in filename)
→ Flag as HIGH RISK
→ Require CEO approval
→ Use encrypted storage if available
→ Add to high-security audit log
```

**Privacy Rules:**
- Never log full credit card numbers
- Redact SSN/TIN in logs (show last 4 digits only)
- Encrypt files containing passwords
- Delete sensitive data after processing (if allowed)
- Follow data retention policies in Company_Handbook

---

## Integration with Other Skills

**After file analysis, use appropriate skills:**
- **invoice_workflow_skill.md** → For invoices/bills
- **email_skills.md** → For email-related files
- **planning_skills.md** → For notes, tasks, projects
- **social_skills.md** → For social media content
- **approval_skills.md** → For HITL decisions

---

## Error Handling

**File Unreadable:**
```
→ Check encoding (try UTF-8, Latin-1, ASCII)
→ If still unreadable, treat as binary
→ Note in task: "Binary file, cannot analyze content"
→ Store metadata only (filename, size, date)
→ Flag for human review
```

**Ambiguous Intent:**
```
→ List possible interpretations
→ Create approval request with options
→ Ask human to clarify
→ Do NOT guess or assume
```

**Missing Information:**
```
→ Extract what's available
→ Note what's missing
→ Create approval request with gaps highlighted
→ Suggest where to find missing data
```

---

**This skill is authoritative for file analysis. Use it before processing any dropped files.**
