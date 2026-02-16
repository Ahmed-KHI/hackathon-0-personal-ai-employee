# Social Post Approval Checklist - Brand Voice Validation

**Purpose**: Validate social media posts against brand guidelines before publishing.

**CRITICAL**: Every social media post MUST pass this checklist. Claude should create approval requests citing specific checklist items.

---

## Pre-Publishing Checklist

### 1. Brand Voice Compliance ✅

**Professional Tone:**
- [ ] Language is professional yet approachable
- [ ] No slang, jargon, or overly casual language
- [ ] Appropriate for business decision-makers
- [ ] Matches voice in Company_Handbook.md

**Authentic & Humble:**
- [ ] No bragging or self-promotion
- [ ] Focus on value delivered, not just achievement
- [ ] Acknowledges team/partners/customers where relevant
- [ ] Shows genuine passion, not manufactured excitement

**Value-Focused:**
- [ ] Provides insight or learning
- [ ] Not just announcing, but explaining "why it matters"
- [ ] Offers actionable takeaway for readers
- [ ] Aligns with audience's business interests

---

### 2. Content Quality Standards ✅

**Accuracy:**
- [ ] All facts verified against vault documents
- [ ] Numbers/metrics are correct (revenue, milestones, dates)
- [ ] No exaggerations or "marketing fluff"
- [ ] Claims can be substantiated if challenged

**Clarity:**
- [ ] Message is clear and concise
- [ ] Avoids ambiguity or confusion
- [ ] Structure: Hook → Context → Value → CTA
- [ ] Readable at 8th-grade level (Flesch-Kincaid standard)

**Length:**
- [ ] Twitter: 200-250 characters (leaves room for retweets)
- [ ] LinkedIn: 150-300 words (optimal engagement)
- [ ] Facebook: 200-400 characters (stops at "See More" if longer)
- [ ] Instagram: Caption under 2,200 chars, focus on first 125

---

### 3. Legal & Compliance ✅

**No Sensitive Information:**
- [ ] No customer names without permission
- [ ] No confidential project details
- [ ] No unreleased product information
- [ ] No financial data not yet public

**No Controversial Topics:**
- [ ] Avoids politics, religion, divisive issues
- [ ] No comments on competitors (positive or negative)
- [ ] No industry gossip or speculation
- [ ] Professional, neutral stance

**Attribution:**
- [ ] Quotes are properly attributed
- [ ] Images have usage rights
- [ ] Third-party data is cited
- [ ] No copyright violations

---

### 4. Engagement Optimization ✅

**Call-to-Action (CTA):**
- [ ] Clear CTA present (contact, learn more, share, comment)
- [ ] CTA is actionable and specific
- [ ] Link is tested and working (if applicable)
- [ ] CTA aligns with business goals

**Hashtags:**
- [ ] 1-2 hashtags for Twitter (max 3)
- [ ] 3-5 hashtags for LinkedIn
- [ ] 5-10 hashtags for Instagram (max 30)
- [ ] Hashtags are relevant, not spammy
- [ ] Mix of broad and niche hashtags

**Visual Element:**
- [ ] Image/graphic suggested or attached (if platform supports)
- [ ] Visual is high quality (not pixelated or blurry)
- [ ] Visual adds value (not decorative filler)
- [ ] Alt text provided for accessibility

---

### 5. Timing & Frequency ✅

**Platform-Specific Timing:**
- [ ] LinkedIn: Weekday mornings (8-10 AM, Tuesday-Thursday optimal)
- [ ] Twitter: Weekdays 12-3 PM or 5-6 PM
- [ ] Facebook: Weekdays 1-3 PM
- [ ] Instagram: Weekdays 11 AM - 1 PM

**Frequency Limits:**
- [ ] Twitter: Max 5 posts/day
- [ ] LinkedIn: Max 1-2 posts/day (3/week minimum)
- [ ] Facebook: Max 1-2 posts/day
- [ ] Instagram: Max 1-2 posts/day

**Rate Limiter Check:**
- [ ] Not exceeding daily/weekly platform limits
- [ ] Checking watcher state files for recent post count
- [ ] Spacing posts at least 2-4 hours apart (same platform)

---

### 6. Risk Assessment ✅

**Controversy Risk: LOW/MEDIUM/HIGH**
- LOW: Routine business updates, tips, milestones
- MEDIUM: Industry opinions, trend commentary
- HIGH: Anything mentioning competitors, controversial topics

**Approval Requirement:**
- [ ] LOW risk: Can auto-approve if all other checks pass
- [ ] MEDIUM risk: Requires manager/CEO approval
- [ ] HIGH risk: Requires CEO + legal review

**Reputational Impact:**
- [ ] Post reflects well on company brand
- [ ] No potential for misinterpretation
- [ ] Aligns with long-term brand strategy
- [ ] Won't cause customer/partner concern

---

## Approval Request Template

When creating approval request, Claude should output:

```markdown
## Social Post Approval Request

**Platform:** [LinkedIn/Twitter/Facebook/Instagram]
**Post Type:** [Milestone/Update/Insight/Promotion]
**Risk Level:** [LOW/MEDIUM/HIGH]

### Proposed Content
[Full post text here]

### Checklist Results
✅ Brand Voice: PASS
✅ Content Quality: PASS
✅ Legal/Compliance: PASS
✅ Engagement Optimization: PASS
⚠️ Timing: REVIEW NEEDED (posting outside optimal window)
✅ Risk Assessment: LOW

### Concerns/Notes
- [Any items that need human review]
- [Explanation of any warnings]

### Recommendation
[APPROVE / REVIEW / REJECT]

**To Approve:** Move to /Approved
**To Reject:** Move to /Rejected with feedback
**To Revise:** Edit this file and move back to /Pending_Approval
```

---

## Integration with Platform Skills

After passing checklist, use platform-specific skills:
- [twitter_skills.md](twitter_skills.md) for Twitter posts
- [linkedin_skills.md](linkedin_skills.md) for LinkedIn posts
- [facebook_skills.md](facebook_skills.md) for Facebook posts
- [instagram_skills.md](instagram_skills.md) for Instagram posts

---

**This checklist is authoritative. No social post should bypass these checks.**
