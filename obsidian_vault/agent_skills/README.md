# Agent Skills - Intelligence as Code

This directory contains all intelligence for the Personal AI Employee.

## Principle: Skills as Markdown

ALL intelligence must be encoded as Markdown files in this directory. No hardcoded logic in Python code.

## Why Markdown?

1. **Human-Readable**: Non-technical stakeholders can review and edit
2. **Version-Controlled**: Git tracks every change
3. **Deterministic**: Same input → same output
4. **Auditable**: Clear decision trail
5. **Modifiable**: Update skills without changing code

## Available Skills

### Core Skills (All Tiers)
- [`email_skills.md`](email_skills.md) - Email triage, response templates, escalation rules
- [`finance_skills.md`](finance_skills.md) - Transaction monitoring, invoice processing, budget management
- [`planning_skills.md`](planning_skills.md) - Task decomposition, decision trees, iteration strategy
- [`approval_skills.md`](approval_skills.md) - HITL rules, approval thresholds, risk assessment

### Communication Skills
- [`social_skills.md`](social_skills.md) - WhatsApp, Slack, social media communication

### Future Skills (Gold/Platinum)
- `sales_skills.md` - Lead qualification, pipeline management
- `hr_skills.md` - Onboarding, PTO requests, benefits FAQ
- `engineering_skills.md` - Code review, deployment, incident response
- `customer_success_skills.md` - Onboarding, retention, NPS tracking

## How Skills Are Used

### In Task Processing

```python
# In orchestrator.py
def process_task(task):
    # Load required skills
    required_skills = task.get("required_skills", [])
    skills = {}
    
    for skill_name in required_skills:
        skill_file = f"obsidian_vault/agent_skills/{skill_name}.md"
        with open(skill_file, 'r') as f:
            skills[skill_name] = f.read()
    
    # Pass skills to Claude Code for reasoning
    context = {
        "task": task,
        "handbook": load_handbook(),
        "goals": load_goals(),
        "skills": skills
    }
    
    # Claude reasons using skills as instructions
    response = claude.reason(context)
```

### In Decision Making

Skills provide:
- **Rules**: "If amount >$500, require approval"
- **Templates**: Pre-written responses
- **Decision Trees**: Step-by-step logic
- **Examples**: Sample scenarios
- **Anti-Patterns**: What NOT to do

## Skill Development Lifecycle

### 1. Initial Creation
- Define skill domain (email, finance, etc.)
- Document rules and patterns
- Create templates
- Define escalation criteria

### 2. Validation
- Test with real scenarios
- Review by domain expert (CFO for finance_skills.md)
- Iterate based on feedback

### 3. Deployment
- Commit to git
- AI Employee immediately uses new rules
- No code changes required

### 4. Monitoring
- Track skill usage in audit logs
- Measure success rate
- Identify gaps or errors

### 5. Evolution
- Monthly skill review
- Update based on learnings
- Add new templates
- Adjust thresholds

## Skill Composition

Skills can reference each other:

```markdown
# In email_skills.md

## Financial Email Handling

See [finance_skills.md](finance_skills.md) for:
- Invoice processing rules
- Payment thresholds
- Vendor management

When email contains invoice:
1. Extract details
2. Apply finance_skills.md rules
3. Draft response using templates below
```

## Skill Testing

### Manual Testing
```bash
# Create test task
cat > task_queue/inbox/test.json << EOF
{
  "task_id": "test-001",
  "type": "email_response",
  "required_skills": ["email_skills"],
  "context": {
    "from": "client@example.com",
    "subject": "URGENT: Invoice Question",
    "body": "Where is my invoice?"
  }
}
EOF

# Watch orchestrator process it
python orchestration/orchestrator.py
```

### Automated Testing (Future)
```python
# tests/test_skills.py
def test_email_urgency_detection():
    email = {"subject": "URGENT: Help"}
    priority = apply_skill("email_skills", "classify_priority", email)
    assert priority == "critical"
```

## Skill Versioning

Track major changes:

```markdown
# At bottom of skill file

## Version History

- **2026-02-05 v1.0**: Initial creation
- **2026-02-12 v1.1**: Added template for refunds
- **2026-03-01 v2.0**: Raised approval threshold to $1000
```

## Best Practices

### DO
✅ Write skills in plain language
✅ Provide examples for ambiguous cases
✅ Include "Why" explanations for rules
✅ Reference Company_Handbook.md for context
✅ Update skills based on actual usage
✅ Version control every change

### DON'T
❌ Hardcode intelligence in Python
❌ Make skills overly complex
❌ Contradict Company_Handbook.md
❌ Skip version history updates
❌ Make changes without testing
❌ Use technical jargon unnecessarily

## Skill Conflicts

If two skills contradict:

1. **Approval Skills** override all others (safety)
2. **Domain-specific skills** override general (e.g., finance_skills beats email_skills for invoices)
3. **Company_Handbook.md** overrides all skills (policy)
4. **When in doubt**: Escalate to HITL

## Contributing Skills

Anyone in the company can propose skill updates:

1. Fork the repo
2. Edit skill Markdown file
3. Submit pull request
4. Technical review: Syntax valid?
5. Domain review: Rules correct?
6. Approve & merge
7. AI Employee uses new skills immediately

## Skill Performance Metrics

Track in audit logs:
- Skill usage frequency
- Success rate per skill
- Average confidence score
- Escalation rate
- Time saved (estimated)

## Future: Multi-Tenant Skills

Platinum tier will support:
```
agent_skills/
├── _shared/          # Common skills
│   ├── email_skills.md
│   └── planning_skills.md
├── company_a/        # Company A overrides
│   └── finance_skills.md
└── company_b/        # Company B overrides
    └── finance_skills.md
```

---

**Remember**: Skills are the "brain" of the AI Employee. Keep them clear, tested, and up-to-date.
