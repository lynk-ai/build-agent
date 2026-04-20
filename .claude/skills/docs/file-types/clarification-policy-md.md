# Clarification Policy File Reference

A clarification policy file tells the agent when to proceed with a default assumption and when to ask a clarifying question. It controls how the agent handles ambiguous or vague user requests.

---

## Frontmatter

```yaml
---
type: behavior
kind: clarification_policy
domain: "*"                # or a specific domain name
---
```

| Field | Values | Description |
|---|---|---|
| `type` | `behavior` | Identifies this as a behavior file |
| `kind` | `clarification_policy` | Marks this as a clarification policy file |
| `domain` | `"*"`, `"default"`, `"marketing"`, etc. | Which domain(s) this applies to |

---

## Default Behavior

If no clarification policy file is configured, Lynk applies its built-in clarification policy — a sensible default shared across all Lynk customers. Adding a clarification policy file overrides that default for your project. You are not starting from scratch — you are customizing on top of an existing baseline.

---

## What Goes in a Clarification Policy

**When to proceed** — cases where the agent should make a default assumption and state it, rather than asking. Define a default for time period and granularity so the agent knows what to assume when the user doesn't specify.

**When to ask** — when the question is ambiguous or too broad to answer directly. This covers both cases: a question where a parameter needs clarifying, and a question so open-ended there's no single right path. In both cases, the agent asks one focused question and suggests up to 3 concrete options grounded in real data.

**Response tone** — how the agent should sound when asking or stating an assumption.

---

## Custom Domains

A `marketing` domain clarification policy applies only to marketing-domain queries. Policies not defined in a custom domain fall back to the `domain: "*"` file.

---

## Decision Framework

Use this to decide whether a given situation calls for a question or a default assumption:

| Ambiguity | Stakes | What to do |
|---|---|---|
| High — question could mean meaningfully different things | High — wrong assumption changes the answer significantly | Ask a focused question, offer up to 3 concrete options |
| High | Low — any reasonable interpretation gives a similar answer | Proceed with the most common interpretation; state the assumption at the end |
| Low — intent is clear | High — the stakes matter but the interpretation is obvious | Proceed and state the assumption clearly inline |
| Low | Low | Proceed silently |

**What counts as high ambiguity:** multiple metrics could answer the question (ARR vs. MRR vs. cash), multiple entities could be relevant, or scope is underspecified ("how are we doing?").

**What counts as high stakes:** the answer will be used for a business decision, presented to leadership, or the wrong assumption would look like a data error.

---

## Best Practices

**Define your time period and granularity defaults.** These are the most common sources of ambiguity in data questions. Decide what the agent should assume when neither is specified and write it down.

**Reserve questions for genuinely vague questions.** Ask only when a question could be interpreted in multiple meaningfully different ways. When asking, always suggest up to 3 concrete options — this helps users choose quickly rather than re-explain.

**Match the decision framework to your audience.** Technical users (analysts, data engineers) tolerate more defaults and fewer questions. Non-technical users (marketing, executives) benefit from the agent being more explicit about assumptions.

**Keep it general.** Clarification policy is not the place for entity-specific SQL rules, filter defaults, or metric definitions. Those belong in task instructions and entity knowledge files.

---

## Common Pitfalls

**Putting SQL or filter rules here** — rules like "always filter to active customers" or "use net_amount for revenue" belong in task instructions, not clarification policy. Clarification policy is about handling ambiguous inputs, not generating SQL.

**Putting entity or metric guidance here** — rules like "use this entity when..." or "this metric means..." belong in the entity knowledge file, not clarification policy.

**Over-specifying when to ask** — if everything triggers a clarification question, the agent becomes annoying. Reserve questions for cases where the ambiguity would genuinely lead to meaningfully different answers.

---

## When to Use This File

Create or update a clarification policy when a situation meets one of these conditions:
1. The agent should apply a default assumption when a question is ambiguous — time period, granularity, scope
2. You want to define when the agent should ask a clarifying question vs. proceed with an assumption
3. You want to configure how the agent handles unknown terms or underspecified requests

**Examples:**
- "When no time period is specified, default to the current quarter" → add a time period default
- "When no granularity is specified, default to weekly" → add a granularity default
- "When the user asks something vague that could go in several directions, ask and offer options" → define when-to-ask behavior with examples

---

## When NOT to Use This File

- If you want SQL rules, filters, or field choices for a specific entity → **task instructions file**
- If you want to define what an entity or metric means, or when to use it → **entity knowledge file**
- If you want to define business terms → **glossary file**
- If you want to control how responses are structured (tables, tone, data notes) → **output format file**

---

## Full Examples

### Example 1 — Grove (B2B SaaS)

The most common sources of ambiguity in Grove queries are the revenue metric (ARR vs. MRR vs. cash collected) and vague scope questions ("how are we doing?" could mean revenue, churn, or both). The default time period is current quarter; the default granularity is monthly.

```markdown
---
type: behavior
kind: clarification_policy
domain: "*"
---

## When to Proceed
- When no time period is specified, default to the current fiscal quarter and mention it at the end of the answer
- When no granularity is specified, default to monthly breakdowns and mention it

## When to Ask
When the question is ambiguous or too broad to answer directly, ask one focused question and suggest up to 3 concrete options grounded in real data.

Ask when "revenue" is mentioned without a qualifier — ARR, MRR, and cash collected are meaningfully different and the wrong choice misleads decision-making.

Examples:
- User: "How are we doing?"
  AI: "Happy to dig in. What would you like to look at?
       1. ARR and growth vs. last quarter
       2. Active customer count and churn rate
       3. NDR trends over the last 6 months"

- User: "Why are we losing customers?"
  AI: "Worth digging into. Which angle do you want to start with?
       1. Logo churn rate by customer tier this quarter
       2. Revenue churn by plan type over the last 6 months
       3. Recently churned accounts and their last NPS score"

- User: "What's our revenue?"
  AI: "Are you looking for ARR (annual recurring revenue), MRR (monthly recurring), or cash collected this period?"

## Response Tone
- When asking: one line, direct, no preamble
- When stating an assumption: mention it at the end of the answer, not the beginning
```

---

### Example 2 — Bly (E-commerce), marketing domain

Marketing results at Bly are highly date-sensitive — a campaign that looked good over 28 days may look very different over 7 days. This policy always asks about time period for channel and campaign questions, and always asks about granularity when the user's question implies trend analysis.

```markdown
---
type: behavior
kind: clarification_policy
domain: "marketing"
---

## When to Proceed
- When a channel is specified clearly (e.g. "paid social performance"), proceed without asking about channel
- When a specific time period is stated (e.g. "last week", "this month"), proceed without asking about time

## When to Ask
When the question is ambiguous or too broad to answer directly, ask one focused question and suggest up to 3 concrete options grounded in real data.

Always ask about time period for campaign and channel questions — marketing results are highly sensitive to date range and defaulting silently can mislead.
Always ask about granularity when trend analysis is implied — daily vs. weekly tells very different stories in campaign data.

Examples:
- User: "Show me campaign performance"
  AI: "Which time period should I use — last 7 days, last 28 days, or this month?"

- User: "Is our marketing working?"
  AI: "Depends on what we're optimizing for. Which angle do you want to start with?
       1. Net revenue and order count by channel this month
       2. Repeat purchase rate from last quarter's cohort
       3. Conversion rate by channel over the last 28 days"

- User: "How are our top channels doing?"
  AI: "Two quick questions: which time period, and do you want to see revenue or order count? (The ranking can flip depending on which metric you use.)"

## Response Tone
- When asking: conversational but precise — briefly explain why you're asking
- When stating an assumption: lead with the answer, mention the assumption naturally inline
```

---

### Example 3 — Arcadia (Mobile gaming)

Arcadia metrics are sensitive to two dimensions users rarely specify: the player segment ("our players" could mean DAU, paying players, or whales — and revenue per player differs dramatically) and the retention window (D7 vs. D30 are not interchangeable). This policy always asks about segment for revenue and ARPDAU questions, and always clarifies retention window when "retention" is mentioned without a number.

```markdown
---
type: behavior
kind: clarification_policy
domain: "*"
---

## When to Proceed
- When a time period is specified (e.g. "yesterday", "last week", "Q1"), proceed without asking about time
- When a segment is specified clearly (e.g. "whales", "paying players", "all active players"), proceed without asking about segment
- For simple DAU or session count questions with no segment qualifier, default to all active players (last_session_at >= today - 7 days) and mention it

## When to Ask

**Always ask about player segment for revenue and ARPDAU questions.** "Our players" could mean all DAU, paying players only, or a specific segment. ARPDAU across all DAU is very different from ARPDAU across whales alone, and using the wrong group changes the answer by an order of magnitude.

**Always clarify the retention window when "retention" is mentioned without a number.** D7 and D30 retention tell different stories about game health, and the wrong assumption is directly misleading to live ops decisions.

When the question is too broad to answer directly, ask one focused question and suggest up to 3 concrete options grounded in real data.

Examples:
- User: "How are our players doing?"
  AI: "Happy to dig in. What would you like to look at?
       1. DAU and ARPDAU vs. the prior 7-day average
       2. D7 retention for this week's install cohort
       3. Whale count and spend_last_30_days_usd vs. prior week"

- User: "Show me whale performance this month"
  AI: "Which time period — the current month to date, the last 28 rolling days, or the last full calendar month?"

- User: "What's our retention?"
  AI: "Which retention window — D7 (day 7 return rate) or D30 (day 30 return rate)?"

## Response Tone
- When asking: one line, direct — mention why the distinction matters (e.g. "ARPDAU changes significantly depending on which player group you include")
- When stating an assumption: state it at the end of the answer, not before it
```
