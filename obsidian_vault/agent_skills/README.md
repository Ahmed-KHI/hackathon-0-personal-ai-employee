# 📚 Agent Skills - Intelligence as Code

All intelligence for the Personal AI Employee is encoded as Markdown files in this directory.

---

## 🎯 Core Principle

**NO HARDCODEDLOGIC IN PYTHON**

All business logic, decision rules, and behavioral patterns must exist as version-controlled Markdown files. This makes the AI's intelligence:
- 🔍 **Transparent**: Anyone can read and understand the rules
- 📝 **Version-Controlled**: Every change is tracked in git
- 🔄 **Modifiable**: Update behavior without touching code
- 🧪 **Testable**: Skills can be validated independently
- 📋 **Auditable**: Clear decision trail

---

## 📦 Available Skills

### Core Automation Skills
- [**email_skills.md**](email_skills.md) - Email triage, response templates, escalation rules
- [**planning_skills.md**](planning_skills.md) - Task decomposition, decision trees, iteration strategy
- [**approval_skills.md**](approval_skills.md) - HITL rules, approval thresholds, risk assessment
- [**finance_skills.md**](finance_skills.md) - Transaction monitoring, invoice processing, budget analysis

### Communication Skills
- [**social_skills.md**](social_skills.md) - General communication best practices
- [**linkedin_skills.md**](linkedin_skills.md) - Professional network posting, engagement strategies
- [**facebook_skills.md**](facebook_skills.md) - Business page management, content guidelines
- [**instagram_skills.md**](instagram_skills.md) - Visual content curation, hashtag strategy
- [**twitter_skills.md**](twitter_skills.md) - Micro-content creation, trending topics

### Business Skills
- [**odoo_skills.md**](odoo_skills.md) - ERP accounting workflows, invoice/bill management

---

## 🏗️ How Skills Work

### 1. Orchestrator Loads Skills

```python
# In orchestrator_claude.py
def process_task(task):
    # Determine required skills
    required_skills = ["planning_skills", "email_skills"]
    
    # Load skill files
    skills = {}
    for skill in required_skills:
        skill_path = f"obsidian_vault/agent_skills/{skill}.md"
        with open(skill_path, 'r') as f:
            skills[skill] = f.read()
    
    # Pass to Claude
    context = {
        "task": task,
        "skills": skills,
        "handbook": load_handbook(),
        "business_goals": load_goals()
    }
    
    plan = claude_api.generate_plan(context)
```

### 2. Claude Reasons with Skills

Claude receives skills as context and follows their instructions:

```
You are an AI Employee. Here are your skills:

## Email Skills
When processing emails:
1. Check subject for urgency keywords: "URGENT", "ASAP", "CRITICAL"
2. If urgent, create high-priority task immediately
3. For non-urgent, batch with similar emails...

Now process this task: [task description]
```

### 3. Decisions Are Audited

```json
{
  "timestamp": "2026-02-11T10:30:00Z",
  "task_id": "EMAIL_urgent_client",
  "skills_used": ["email_skills"],
  "decision": "Created high-priority task (urgent keyword found)",
  "rule_matched": "email_skills.md line 43: URGENT flagging"
}
```

---

## 📐 Skill Structure

Each skill file follows this structure:

````markdown
# Skill Name

**Purpose**: One-sentence description

**When to Use**: Specific triggers or scenarios

---

## Rules

### Rule 1: [Name]
**Condition**: When X happens
**Action**: Do Y
**Example**: ...

### Rule 2: [Name]
**Condition**: When A and B
**Action**: Do C
**Exception**: Unless D

---

## Templates

### Template: Email Response for ...
```
Subject: Re: {original_subject}

Hi {name},

Thank you for...
```

---

## Decision Trees

```
Is this urgent?
├─ YES → Create high-priority task
│   └─ Time-sensitive? (< 24 hrs)
│       ├─ YES → Alert human immediately
│       └─ NO → Standard high-priority flow
└─ NO → Batch with similar emails
```

---

## Examples

### Example 1: [Scenario]
**Input**: ...
**Expected Output**: ...
**Reasoning**: ...

---

## Anti-Patterns (What NOT to Do)

❌ Don't reply to obvious spam
❌ Don't make financial commitments without approval
❌ Don't share confidential information externally
````

---

## 🚀 Skill Development Lifecycle

### 1. Creation
- Identify domain (email, finance, social media)
- Document existing manual processes
- Define rules and patterns
- Create templates and decision trees

### 2. Validation
- Test with historical data
- Review by domain expert (e.g., CFO for finance_skills.md)
- Iterate based on feedback
- Add edge case handling

### 3. Deployment
- Commit to git (automatic version control)
- AI Employee immediately uses new rules
- Zero code changes required
- Zero downtime

### 4. Monitoring
- Track skill usage in audit logs
- Measure success rate (task completion, human intervention needed)
- Identify gaps or ambiguities
- Collect feedback

### 5. Evolution
- Monthly skill reviews
- Update based on learnings
- Add new templates
- Adjust thresholds
- Document changes in git history

---

## 💡 Best Practices

### ✅ Do's
- ✅ Be explicit and specific
- ✅ Provide concrete examples
- ✅ Include decision trees for complex logic
- ✅ Document exceptions and edge cases
- ✅ Use consistent formatting
- ✅ Keep skills focused (single responsibility)

### ❌ Don'ts
- ❌ Don't embed code in skills (Markdown only)
- ❌ Don't make skills too generic
- ❌ Don't leave rules ambiguous
- ❌ Don't skip examples
- ❌ Don't forget to update when processes change

---

## 🧪 Testing Skills

### Manual Testing
```bash
# Test a specific skill
python test_action_extraction.py

# Test with real task
echo "Send invoice to client A" > watch_inbox/test_invoice.txt

# Check generated plan references the skill
cat obsidian_vault/Plans/FILE_test_invoice_plan.md
```

### Validation Checklist
- [ ] All rules are clear and unambiguous
- [ ] Examples cover common scenarios
- [ ] Decision trees don't have dead ends
- [ ] Templates are production-ready
- [ ] Anti-patterns are documented
- [ ] Skill is peer-reviewed
- [ ] Tested with real data

---

## 📊 Skill Metrics

Track effectiveness:
- **Usage Count**: How often is the skill invoked?
- **Success Rate**: Tasks completed without human intervention
- **Modification Frequency**: How often do rules need updating?
- **Exception Rate**: How often do edge cases occur?

---

## 🔮 Future Skills (Planned)

- `sales_skills.md` - Lead qualification, pipeline management
- `hr_skills.md` - Onboarding processes, PTO tracking
- `engineering_skills.md` - Code review, deployment procedures
- `customer_success_skills.md` - Onboarding, churn prevention
- `legal_skills.md` - Contract review, NDA management

---

## 📚 Related Documentation

- [Main README](../../README.md)
- [Hackathon Documentation](../../hackathon.doc)
- [Testing Guide](../../TESTING_GUIDE.md)

---

**Part of**: [Personal AI Employee](../../README.md) - Platinum Tier Complete
