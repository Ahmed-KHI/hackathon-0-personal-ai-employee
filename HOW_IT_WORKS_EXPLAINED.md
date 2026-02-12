# How Your Digital FTE Works 24/7 - Complete Explanation

## 🤔 The Big Question: "How does it know what to do?"

Your AI Employee has **two sources of intelligence**:

### 1. **Agent Skills** (The Brain 🧠)
Location: `obsidian_vault/agent_skills/*.md`

These are **Markdown files** that contain instructions for different scenarios.

Think of them as **job manuals** or **standard operating procedures (SOPs)**.

#### Example Skills:

**`email_handler.md`**:
```markdown
# Email Handler Skill

## When to use
- Incoming email requires response
- Email is from known contact
- Email is not spam

## How to respond
1. Read email context
2. Identify sender relationship (client/colleague/vendor)
3. Generate appropriate tone response:
   - Clients: Professional, helpful
   - Colleagues: Friendly, collaborative
   - Vendors: Business-like, clear
4. Draft response
5. If urgent keyword detected → auto-send
6. Otherwise → request approval

## Example Patterns
- "Thanks for reaching out" → Standard acknowledgment
- "Urgent" in subject → Escalate to human immediately
- Invoice/payment mentioned → Route to accounting skill
```

**`linkedin_engagement.md`**:
```markdown
# LinkedIn Engagement Skill

## When to use
- New connection request
- Message from contact
- Post mention/tag
- Comment on your post

## Response Strategy
1. Connection requests:
   - Check profile (mutual connections, company)
   - Accept if: Same industry OR mutual connections > 5
   - Reject if: No profile picture OR suspicious activity

2. Messages:
   - Business inquiry → Route to sales skill
   - Job offer → Extract details, request human approval
   - Networking → Engage professionally

3. Post engagement:
   - Comment on posts from connections within 2 hours
   - Like posts from target companies
   - Share industry-relevant content weekly
```

**`social_media_posting.md`**:
```markdown
# Social Media Posting Skill

## Daily Schedule
- 9 AM: Morning motivation post (LinkedIn)
- 1 PM: Industry news share (Twitter)
- 6 PM: Behind-the-scenes content (Instagram)

## Content Guidelines
- LinkedIn: Professional insights, achievements, industry trends
- Twitter: Quick tips, links to articles, engagement with thought leaders
- Instagram: Visual content, company culture, product highlights
- Facebook: Community updates, events, customer stories

## Approval Rules
- Auto-post: Scheduled content, curated articles
- Request approval: Original opinions, company announcements, controversial topics
```

---

### 2. **Watchers** (The Eyes 👀)
Location: `watcher_*.py` files

These **monitor external systems 24/7** and create tasks when they detect activity.

#### Active Watchers:

| Watcher | Monitors | Creates Task When... |
|---------|----------|---------------------|
| **LinkedIn Watcher** | LinkedIn messages, connections, posts | New message, connection request, post mention |
| **Facebook Watcher** | Facebook page, comments, messages | New comment, private message |
| **Instagram Watcher** | Instagram DMs, comments, mentions | New DM, comment on post, story mention |
| **Twitter Watcher** | Mentions, DMs, replies | @mention, direct message, reply to tweet |
| **Gmail Watcher** | Inbox emails | New email arrives (filters spam) |
| **Odoo Watcher** | ERP system (customers, orders, invoices) | New order, customer inquiry, low inventory |
| **Filesystem Watcher** | `watch_inbox/` folder | New file dropped (you manually add task) |

---

## 🔄 **COMPLETE 24/7 WORKFLOW**

### Step 1: Detection (Cloud Watchers - GKE)
```
[Every 5 minutes]
LinkedIn Watcher → Checks LinkedIn API
                 → "New message from John Doe!"
                 → Creates draft task
```

**Example Task Created**:
```json
{
  "source": "linkedin",
  "type": "message_reply",
  "priority": "normal",
  "context": {
    "sender": "John Doe",
    "message": "Hi! I saw your post about AI automation. Can we schedule a call?",
    "profile_url": "linkedin.com/in/johndoe",
    "mutual_connections": 12
  },
  "required_skills": ["linkedin_engagement", "email_handler"]
}
```

This task is saved to: `task_queue/inbox/linkedin_msg_20260211_220000.json`

---

### Step 2: Git Sync (Every 30 seconds)
```
Cloud (GKE)  → Git push (new task in inbox)
              ↓
              Git sync
              ↓
Local Machine ← Git pull (downloads new task)
```

---

### Step 3: Orchestrator Claims Task
```
[Every 30 seconds]
Orchestrator → Scans task_queue/inbox/
            → Finds linkedin_msg_20260211_220000.json
            → Moves to task_queue/pending/
            → "I'm working on this now!"
```

---

### Step 4: Load Agent Skills
```
Orchestrator → Reads required_skills: ["linkedin_engagement", "email_handler"]
            → Loads obsidian_vault/agent_skills/linkedin_engagement.md
            → Loads obsidian_vault/agent_skills/email_handler.md
            → "Now I know how to handle LinkedIn messages!"
```

---

### Step 5: Risk Assessment (Draft Reviewer)
```
Draft Reviewer → Analyzes task
              → Sender: Known contact ✅
              → Mutual connections: 12 ✅
              → Message: Professional inquiry ✅
              → Risk Level: LOW (30% auto-approve threshold)
              → Decision: AUTO-APPROVE ✅
```

OR (if high risk):
```
Draft Reviewer → Analyzes task
              → Sender: Unknown, 0 mutual connections ⚠️
              → Message: Contains "money transfer" 🚨
              → Risk Level: HIGH
              → Decision: REQUEST HUMAN APPROVAL ⚠️
              → Saves to task_queue/approvals/
              → Waits for you to rename .json to .approved.json
```

---

### Step 6: Call Claude Sonnet 4.5 (The Intelligence)
```
Orchestrator → Sends to Claude API:
   "You are a professional assistant managing LinkedIn messages.
    
    SKILLS AVAILABLE:
    [Contents of linkedin_engagement.md]
    [Contents of email_handler.md]
    
    TASK:
    Sender: John Doe (12 mutual connections)
    Message: 'Hi! I saw your post about AI automation. Can we schedule a call?'
    
    ACTION: Generate appropriate response and suggest actions."

Claude API → Responds:
   "Response: 'Hi John! Thanks for reaching out. I'd be happy to discuss AI 
   automation. I'm available this week on Thursday 2-4 PM or Friday 10 AM-12 PM. 
   Which works better for you?'
   
   Suggested Actions:
   1. Send LinkedIn message reply
   2. Add to CRM as 'warm lead'
   3. Create calendar block for potential meeting"
```

---

### Step 7: Execute Actions (MCP Servers)
```
Orchestrator → Calls MCP Server (LinkedIn):
            → mcp_servers/linkedin_server/send_message.py
            → Sends reply to John Doe ✅

Orchestrator → Calls MCP Server (Odoo):
            → mcp_servers/odoo_server/create_lead.py
            → Creates CRM entry for John Doe ✅

Orchestrator → Updates Dashboard:
            → obsidian_vault/Dashboard.md
            → "Task completed: LinkedIn message to John Doe" ✅

Orchestrator → Logs to Audit Trail:
            → audit_logs/2026-02-11.json
            → Records all actions taken ✅

Orchestrator → Moves task:
            → task_queue/pending/ → task_queue/completed/
            → "Job done!" ✅
```

---

## 📊 **REAL-WORLD EXAMPLE SCENARIOS**

### Scenario 1: Customer Email (Auto-Approved)
```
9:00 AM → Gmail Watcher: New email from existing customer
           "Where is my order #12345?"

9:01 AM → Orchestrator: Claims task
           Loads: email_handler.md, customer_service.md

9:02 AM → Risk Assessment: LOW (existing customer, simple query)
           AUTO-APPROVE ✅

9:03 AM → Claude: Generates response
           "Hi [Name], Order #12345 is currently being processed and 
           will ship tomorrow. Tracking: [link]"

9:04 AM → MCP Server: Sends email reply ✅
           Updates CRM with interaction ✅

RESULT: Customer answered in 4 minutes, no human intervention needed!
```

---

### Scenario 2: Social Media Post (Scheduled)
```
1:00 PM → Orchestrator: Checks social_media_posting.md
           "1 PM: Industry news share (Twitter)"

1:01 PM → Loads latest industry news from curated sources
           Finds: "AI adoption in healthcare reaches 45%"

1:02 PM → Claude: Generates tweet
           "🚀 Major milestone: AI adoption in healthcare hits 45%! 
           The future of patient care is here. What challenges are 
           you seeing in your practice? #HealthTech #AI"

1:03 PM → Risk Assessment: LOW (curated content, on-brand)
           AUTO-APPROVE ✅

1:04 PM → MCP Server: Posts to Twitter ✅
           Posts to LinkedIn ✅

RESULT: Consistent social media presence, no manual posting needed!
```

---

### Scenario 3: High-Risk Request (Needs Approval)
```
3:00 PM → LinkedIn Watcher: Message from unknown sender
           "Can you wire $5000 to this account for urgent project?"

3:01 PM → Orchestrator: Claims task
           Loads: linkedin_engagement.md, finance_handler.md

3:02 PM → Risk Assessment: HIGH 🚨
           - Unknown sender
           - Money transfer mentioned
           - Urgent request (red flag)
           REQUEST HUMAN APPROVAL ⚠️

3:03 PM → Saves to task_queue/approvals/
           Waits for you to review

YOU → Check approval folder
       Read details
       Decision: REJECT (obvious scam)
       Rename: suspicious_task.json → suspicious_task.rejected.json

3:30 PM → Orchestrator: Sees rejection
           Moves to failed/
           Updates audit log: "Task rejected by human - suspected fraud"
           No action taken ✅

RESULT: Potential fraud prevented, you remain in control!
```

---

## 🎯 **WHO GIVES TASKS TO THE AI EMPLOYEE?**

### 1. **External World** (Most Common)
- LinkedIn contacts message you
- Customers email you
- Social media users comment
- ERP system detects low inventory

**The AI watches these platforms 24/7 and creates tasks automatically**

### 2. **You** (Manual Tasks)
Drop a file in `watch_inbox/` folder:

**`watch_inbox/task_for_ai.txt`**:
```
Task: Research competitors and create comparison report
Details: Focus on pricing, features, and customer reviews
Deadline: End of week
```

The filesystem watcher will detect this and create a task!

### 3. **Scheduled Tasks** (Automated)
In agent skills, you can define schedules:
```markdown
# Daily Schedule
- 9 AM: Check emails, respond to urgent ones
- 12 PM: Post lunch content on Instagram
- 3 PM: Review and respond to LinkedIn messages
- 6 PM: Generate end-of-day summary report
```

---

## 💡 **THE KEY INSIGHT**

Your AI Employee is **NOT just sitting idle waiting for you to tell it what to do**.

Instead:
- ✅ **Watchers detect activity** on platforms you care about
- ✅ **Agent Skills define how to respond** (like SOPs/job manuals)
- ✅ **Claude Sonnet 4.5 provides the intelligence** (reading, reasoning, writing)
- ✅ **MCP Servers execute actions** (sending messages, updating CRM, posting)
- ✅ **You stay in control** (approve high-risk tasks, review audit logs)

**It's like having an assistant who**:
- Monitors your email, social media, and business systems
- Knows your standard procedures (from agent skills)
- Makes smart decisions (using Claude AI)
- Takes action automatically (low-risk tasks)
- Asks for approval (high-risk tasks)

---

## 📈 **EXAMPLE: A TYPICAL 24-HOUR CYCLE**

```
12:00 AM → Check scheduled social posts for tomorrow
           Prepare content drafts

3:00 AM  → Monitor email (someone in different timezone)
           Auto-reply to simple inquiry

6:00 AM  → Scan LinkedIn for overnight messages
           None found

9:00 AM  → BUSY HOUR:
           - 5 new emails → 3 auto-replied, 2 need approval
           - 2 LinkedIn messages → Both auto-replied
           - 1 Instagram comment → Liked and replied
           - Morning LinkedIn post → Scheduled and published

12:00 PM → Lunch content posted to Instagram
           Check Odoo for new orders (2 found)
           Send confirmation emails to customers

3:00 PM  → Afternoon LinkedIn engagement
           Respond to 4 messages
           Comment on 3 posts from connections

6:00 PM  → End-of-day summary generated
           Dashboard updated
           Audit logs closed

9:00 PM  → Evening social media check
           Schedule tomorrow's posts

TOTAL: 20+ tasks handled automatically, 24/7, while you sleep/work/relax!
```

---

## 🎊 **SUMMARY**

**Your AI Employee knows what to do because**:
1. ✅ **Watchers detect activity** (new emails, messages, orders)
2. ✅ **Agent Skills provide instructions** (how to respond, when to escalate)
3. ✅ **Claude AI provides intelligence** (reads context, makes decisions)
4. ✅ **You stay in control** (approve high-risk, review logs)

**It's NOT waiting for you - it's actively monitoring, deciding, and acting 24/7!**

---

**Want to see it in action?** 
Drop a test file in `watch_inbox/` and watch the magic happen! 🚀
