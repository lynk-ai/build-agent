# Output Format File Reference

An output format file tells the agent how to structure its responses — table titles, insights, disclaimers, data context, and tone. It controls what every answer looks like, not what the answer says.

---

## Frontmatter

```yaml
---
type: behavior
kind: output_format
domain: "*"                # or a specific domain name
---
```

| Field | Values | Description |
|---|---|---|
| `type` | `behavior` | Identifies this as a behavior file |
| `kind` | `output_format` | Marks this as an output format file |
| `domain` | `"*"`, `"default"`, `"marketing"`, etc. | Which domain(s) this applies to |

---

## Default Behavior

If no output format file is configured, Lynk applies its built-in output format — a sensible default shared across all Lynk customers. Adding an output format file overrides that default for your project. You are not starting from scratch — you are customizing on top of an existing baseline.

---

## What Goes in an Output Format File

**Tone** — how the agent should sound. Professional? Direct? Casual? Warm?

**Tables** — whether to add titles, captions, and what context to include below a table.

**Insights** — how many key takeaways to surface after data, and how to format them.

**Analysis** — whether to show percentage of total alongside absolute numbers, and what metadata to always include (filters applied, date range, known caveats).

**Examples** — annotated sample responses make the format concrete and testable.

---

## Custom Domains

A `marketing` domain output format file applies only to marketing-domain queries. Output format not defined in a custom domain falls back to the `domain: "*"` file.

---

## Best Practices

**Include annotated examples.** The most effective way to communicate output format is to show it. An example response is worth ten rules — the agent can infer format from a well-crafted example more reliably than from abstract instructions.

**Guide style, don't script every word.** Define the structure (title, insights, data notes) and the tone (direct, warm, formal). Leave the agent room to write naturally. Over-specified files produce formulaic responses that feel robotic.

**Define what metadata to always show.** Users shouldn't have to ask "what date range is this?" or "are trials included?" Decide once — filters applied, date range, key caveats — and put it in the format file.

**Keep tone instructions to one sentence per rule.** "Lead with the answer" is actionable. "Always be helpful, concise, professional, and engaging while avoiding unnecessary preamble" is not.

**Use domain-specific files for audiences that need different formats.** An executive audience and an analyst audience want different levels of detail. Define a domain-specific output format file rather than trying to handle both in one.

---

## Common Pitfalls

**Over-specifying every response** — very long, highly specific output format files produce rigid, formulaic responses. Guide style and structure — do not script every word.

**Putting SQL rules here** — SQL guidance belongs in task instructions. The agent does not apply output format rules when writing SQL.

**Putting business definitions here** — definitions belong in knowledge files. Output format files are purely about how responses are structured and presented.

---

## When to Use This File

Create or update an output format file when a situation meets one of these conditions:
1. Agent responses are inconsistent in structure and you want a standard format
2. A domain has different audience expectations — technical vs. non-technical, formal vs. casual
3. Every response should include specific elements regardless of the question (titles, data notes, insights)

**Examples:**
- "Answers should always end with a 'Data notes' section showing which filters were applied and what date range was used — users keep asking" → add a Data notes rule
- "Every table response needs a short title and 2–3 bullet insights below it — right now it's inconsistent" → define table and insights structure
- "The agent gives long, chatty responses — we want short and direct, lead with the answer" → set tone rules
- "The marketing domain should feel warmer and more exploratory; the analytics team wants precision and no filler" → create a domain-specific output format file
- "Responses should always show percentage of total alongside absolute numbers when showing a breakdown" → add an analysis rule

---

## When NOT to Use This File

- If you want to control what the agent *knows* (definitions, business rules, data caveats) → **knowledge file**
- If you want to control *when* the agent asks questions before answering → **clarification policy file**
- If you want SQL execution rules (filters, field choices, query patterns) → **task instructions file**
- If you want to define business terms the agent should recognize → **glossary file**

---

## Full Examples

### Example 1 — Grove (B2B SaaS), analytics team

Structured and information-dense. The Grove analytics team values precision — they always want to understand the scope and assumptions behind an answer.

```markdown
---
type: behavior
kind: output_format
domain: "*"
---

## Tone
- Professional and precise. No filler phrases. Lead with the answer.
- When the user's name is known, use it once — not repeatedly.

## Tables
- Always add a short title (up to 5 words) above the table
- Add 1–2 sentences of context below the title explaining what the data represents and any important scope
- After the table, include 2–3 key insights — each on its own line, starting with "→"
- Always show percentage of total alongside absolute numbers when the question is about a distribution

## Analysis
- End every response with a "Data notes" section (small text) covering:
  - Filters applied (e.g. active customers only, test accounts excluded)
  - Date range used
  - Any known caveats relevant to this answer (e.g. NPS scores updated quarterly)
- When a metric has multiple definitions (e.g. logo churn vs. revenue churn), state which one was used

## Examples

User: "Show me ARR by customer tier"
AI:
**ARR by Customer Tier — Current Quarter**
ARR across active Grove customers, segmented by the customer_tier formula (based on ARR thresholds).

| Customer Tier | ARR | % of Total |
|---|---|---|
| Enterprise | $1.8M | 61% |
| Mid-Market | $820K | 28% |
| SMB | $330K | 11% |

→ Enterprise accounts represent 61% of ARR while making up fewer than 20% of total active customers
→ SMB tier has the highest churn rate this quarter — worth monitoring expansion opportunities
→ Mid-Market ARR grew fastest quarter-over-quarter (+18%) driven by plan upgrades

_Data notes: ARR as of 2026-03-27. Active customers only (status = 'active'). Test and deleted accounts excluded. Customer tier based on ARR thresholds: Enterprise ≥ $100K, Mid-Market $20K–$99K, SMB < $20K._
```

---

### Example 2 — Bly (E-commerce), marketing and growth team

Conversational and action-oriented. The Bly growth team cares about what to do next, not just what the numbers say.

```markdown
---
type: behavior
kind: output_format
domain: "marketing"
---

## Tone
- Conversational but precise. Avoid jargon unless the user used it first.
- Lead with the most important number or finding, then explain.
- End with one clear next question the data raises — not a list of caveats.

## Tables
- Add a short title above every table (3–5 words)
- After the table, include 1–2 insights — short, specific, actionable
- Skip the "Data notes" section unless there's something the user needs to know to avoid misreading the data

## Analysis
- Always include percentage of total when showing channel or campaign breakdowns
- When showing trends, state the direction and magnitude in plain language ("up 12% week-over-week") — do not leave it to the user to calculate
- Use net_amount for all revenue figures. Round to the nearest whole number or meaningful decimal — don't show false precision.

## Examples

User: "How did our paid channels perform last week?"
AI:
**Paid Channel Performance — Last 7 Days**

| Channel | Orders | Net Revenue | % of Total Revenue |
|---|---|---|---|
| Paid Search | 2,140 | $94,200 | 42% |
| Paid Social | 1,380 | $58,600 | 26% |
| Email | 890 | $41,300 | 18% |

→ Paid social order volume is down 14% week-over-week despite similar spend — worth checking creative performance.

What do you want to dig into first — channel spend efficiency or specific campaign breakdown?
```

---

### Example 3 — Arcadia (Mobile gaming), live ops team

Numbers-first and comparison-oriented. The Arcadia live ops team makes daily decisions based on metric deltas — they need absolute numbers and prior-period comparisons in every response.

```markdown
---
type: behavior
kind: output_format
domain: "liveops"
---

## Tone
- Direct and numbers-first. Lead with the headline metric before any context.
- No filler phrases. No "Great question!" or preamble.
- Spell out ARPDAU (Average Revenue Per Daily Active User) on first mention in any session.

## Tables
- Add a short title above every table (3–5 words)
- For DAU, ARPDAU, and D7 retention, always show the prior 7-day average alongside the current value and a delta column
- Show WoW delta as a percentage with sign (e.g. +3.2% WoW or -1.8% WoW)
- Round percentages to one decimal place

## Analysis
- For key metrics (DAU, ARPDAU, D7 retention), always include WoW comparison — live ops makes decisions relative to prior performance
- State direction and magnitude explicitly ("up 8% WoW") — do not leave it to the reader to calculate
- If a metric moved more than 10% in either direction, flag it explicitly with one sentence of context explaining what may have caused it

## Examples

User: "How did yesterday perform?"
AI:
**Daily Performance — 2026-03-26**

| Metric | Yesterday | Prior 7-day avg | WoW Delta |
|---|---|---|---|
| DAU | 142,300 | 138,800 | +2.5% |
| ARPDAU (Average Revenue Per DAU) | $0.38 | $0.41 | -7.3% |
| D7 Retention | 22.4% | 23.1% | -0.7pp |

ARPDAU dropped -7.3% WoW despite stable DAU — worth checking whether the paying player mix shifted or whether a whale segment had lower spend yesterday.

_Figures as of 06:00 UTC. DAU = players with last_session_at >= yesterday UTC midnight. D7 retention reflects the install cohort from 7 days ago. Revenue filtered to purchase_currency = 'USD'._
```
