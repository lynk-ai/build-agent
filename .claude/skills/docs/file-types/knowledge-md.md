# Knowledge File Reference

Knowledge files teach the agent what things mean — definitions, business rules, data quality notes, and context that shapes how it interprets a question.

---

## Frontmatter

```yaml
---
type: knowledge
domain: "default"        # required — "*", a domain name, or a list of domain names
entity: customer         # optional — omit for domain-wide knowledge
---
```

| Field | Values | Description |
|---|---|---|
| `type` | `knowledge` | Identifies this as a knowledge file |
| `domain` | `"*"`, `"default"`, `"marketing"`, or a list | Which domain(s) this file applies to |
| `entity` | entity name | Scopes to a specific entity. Omit for domain-wide files. |

---

## Scoping

Knowledge files are scoped by domain and optionally by entity — context compounds across levels. For the full inheritance model and override rules, see the [Domains reference](../concepts/domains.md).

---

## What Belongs in a Knowledge File

### Level 1: Business Knowledge (`domain: "*"`)

Business knowledge loads on every query across every domain. This is where you describe the business itself — what the company does, how it makes money, who the customers are, what the main products or services are. Any question the agent answers, in any domain, is grounded in this context. Include global conventions (currency, fiscal year, default exclusions) here too, but the business description is the foundation.

```markdown
---
type: knowledge
domain: "*"
---

## About the Business
Grove sells subscription-based software to companies. Revenue is subscription-based — customers
pay monthly or annually for platform access. The primary revenue metric is ARR. Customer segments
are SMB, Mid-Market, and Enterprise, defined by ARR thresholds. Customers can be active, in trial,
or churned. Growth comes from new logos, expansion (upsells and seat additions), and reduced churn.

## Fiscal Year
Fiscal year starts February 1. Q1 = Feb–Apr, Q2 = May–Jul, Q3 = Aug–Oct, Q4 = Nov–Jan.

## Global Conventions
- All revenue figures are in USD.
- Data refreshes daily at 06:00 UTC. Same-day figures may be incomplete until the refresh completes.
- Deleted and test accounts are excluded from all entity queries by default.

## Data Quality
- Accounts created before 2020-01-01 were migrated from a legacy CRM. Some fields (`industry`,
  `company_size`) may be null for these records.
- NPS scores are collected quarterly. The `nps_score` field reflects the most recent survey
  response, not a real-time value.
```

Business-level knowledge loads on every query across every domain — keep it focused. Business description, global conventions, and facts universally true across the company. If something only applies to one domain or entity, it belongs at a lower level.

---

### Level 2: Domain Knowledge (`domain: "marketing"`)

Domain knowledge loads for every query in the named domain. Use it to expand on the parts of the business that matter to this domain — specific products, business models, or company context that users in this domain reason about every day. Describe who uses this domain, what they care about, what business concepts are relevant to them and why, and how the agent should interact with them.

```markdown
---
type: knowledge
domain: "marketing"
---

## Who Uses This Domain
The marketing team — campaign managers, growth analysts, and the CMO.
Non-technical users: avoid referencing field names or table names in answers. Use plain language.
Example: say "customers acquired through paid search" not "`channel = 'paid_search'` and `status = 'active'`".

## What They Care About
CAC, ROAS, campaign performance, and channel attribution.
Do not surface subscription revenue metrics (ARR, churn, NDR) in this domain — redirect those
questions to the analytics team using the default domain.

## Attribution Convention
Attribution in this domain always uses last-click unless the user explicitly requests a different model.
Multi-touch attribution is not available — say so clearly if asked.

## Out of Scope
- ARR growth, logo churn, revenue churn, expansion → default domain
- User-level product engagement → product analytics domain
```

Keep domain knowledge focused on the audience and their conventions. Entity-specific rules belong in entity knowledge files — even when the entity is used in this domain.

---

### Level 3: Entity Knowledge (`domain: "default"` + `entity: customer`)

Entity knowledge loads when the agent identifies the query involves a specific entity. It is purely for interpretation — what the entity represents, what its fields and metrics mean from a business perspective, and how to read results correctly. Do not put SQL instructions here (those belong in task instructions). Do not define metrics or features here (those belong in the entity YAML).

The signal for needing entity knowledge: the agent correctly chose this entity but misunderstood how to use it, or misinterpreted the data it returned.

Good entity knowledge covers:
- **Aliases** — all the alternative names business users use to refer to this entity (e.g., 'account', 'client', 'company' for a customer entity)
- What the entity represents and when to use it vs. a related entity
- Cross-feature business rules — which metric to use for which type of question, and why the alternatives are wrong
- Non-obvious behavioral implications — e.g. "churned accounts are included by default, which is intentional"
- Known data quality issues and their scope
- What is in scope vs. out of scope for this entity

Individual field value definitions (what `status = 'active'` means, what each enum value represents) belong in the feature's `description` field in the entity YAML — not here. Entity knowledge is for rules and context that span multiple features or explain how the entity behaves as a whole.

```markdown
---
type: knowledge
domain: "default"
entity: customer
---

## Aliases
Business users refer to this entity as: account, client, company.

## What a Customer Is
A customer is any account with at least one completed paid transaction (`first_paid_at` is not null).
Free trial accounts are not customers by this definition — they exist in the entity but have not yet paid.
Churned accounts remain in the entity and are counted in totals unless explicitly filtered by `status`.
This is intentional — most churn and retention analysis requires access to churned records.

## Revenue Interpretation
`arr` is the primary revenue metric — use it for all revenue questions.
Do not use `total_paid` as a proxy for ARR. `total_paid` is a lifetime sum that includes one-time fees;
it overstates recurring revenue and breaks ARR-based analysis.

## Data Quality
- `company_size` and `industry` are sourced from the CRM and may lag behind the subscription
  system by 24–48 hours.
- Accounts that churned before 2021-06-01 may have `churn_reason = null` — the field was added
  after that date.
```

---

## Best Practices

**Be specific, not vague.** "Filter by `status = 'active'` for current customers" is specific. "Consider account status" is vague.

**Explain the why for non-obvious decisions.** If revenue includes refunds by default, say so and explain why. If a field is not real-time, say so and explain the implication.

**Match the level to the scope.** Business-level (`domain: "*"`) is for facts true everywhere. Domain-level is for audience and conventions. Entity-level is for data semantics. Don't put entity-specific rules in business knowledge or domain conventions in entity files.

**Treat business-level knowledge as the most carefully curated level.** It loads on every query in every domain. Every line you add is loaded unconditionally — keep it to facts that genuinely apply everywhere.

**Do not duplicate what is in the YAML.** The entity YAML has `description` fields on every feature — including what each field value means. Entity knowledge adds context that spans multiple features or explains how the entity behaves as a whole: cross-feature rules, non-obvious defaults, business rationale. If it's about one field, it probably belongs in the YAML.

**Short paragraphs, not walls of text.** The agent reads this to orient itself. Three focused bullet points outperform a five-paragraph essay.

**If a concept has a calculation, define it in the entity YAML.** Knowledge files explain what something means. The entity YAML defines how it's calculated. If a concept only exists in prose, the agent re-derives the SQL each time and may get it wrong. Define the metric or formula feature in the YAML first, then reference it by name in context files.

---

## Common Pitfalls

{% hint style="danger" %}
Avoid these common pitfalls when creating knowledge files.
{% endhint %}

**Putting SQL patterns in knowledge files.** SQL guidance belongs in task instructions — the agent does not apply knowledge file content when generating SQL. If you write "always filter deleted accounts" in a knowledge file, it may be ignored at query time.

**Writing vague statements.** "Consider account status" does not help. "Filter by `status = 'active'` to include only current paying customers" does. Be specific about field names, values, and conditions.

**Listing field value definitions in entity knowledge.** Documenting what `status = 'active'` or `status = 'churned'` means belongs in the feature's `description` in the entity YAML — not in an entity knowledge file. Entity knowledge is for cross-feature rules and entity-level business context. If the rule concerns a single field's values or definition, it belongs in the YAML.

**Domain-wide or business-level knowledge that's too long.** Domain knowledge (`domain: "default"`) loads on every query in that domain. Business knowledge (`domain: "*"`) loads on every query across every domain. If either grows into a wall of text, the agent's ability to extract relevant context degrades. Keep them lean — move entity-specific content into entity knowledge files.

**Missing documentation for complex entities.** If an entity has non-obvious fields, known data quality issues, or business rules that affect interpretation, those belong in entity knowledge — not left undocumented and discovered through wrong answers.

**Defining a metric in prose instead of the entity YAML.** Writing "ARPDAU is total daily net revenue divided by DAU" in a knowledge file describes the term — but doesn't ground it. If `arpdau` is defined as an entity metric in the YAML, the agent queries the pre-built metric directly. Prose descriptions inform the agent's reasoning; YAML metrics are what it actually queries against.

**Putting entity aliases in the entity YAML.** Aliases — the different names business users use to refer to an entity — belong in the entity knowledge file, not in the entity YAML. The entity YAML defines schema and calculation logic; the knowledge file is where the agent learns how users actually refer to entities in natural language.

---

## When to Use This File

Create or update a knowledge file when a situation meets one of these conditions:
1. The agent needs background context that can't be expressed as a metric, glossary term, or task instruction
2. There's a business rule, data caveat, or domain convention that affects how questions should be answered
3. You're scoping context to a specific domain or entity — not everything applies globally

Knowledge applies at three levels:

**Business level (`domain: "*"`) — applies to every query across all domains:**
- "What does this company do, who are its customers, how does it make money" → `domain: "*"` knowledge — this is the business description every agent answer is grounded in
- "All revenue figures are in USD, data refreshes daily at 6am UTC, and our fiscal year starts February 1" → `domain: "*"` knowledge
- "When 'revenue' is mentioned without qualification, it always means ARR — never MRR" → `domain: "*"` knowledge

**Domain level (`domain: "marketing"`) — applies to every query in this domain:**
- "This domain serves the marketing team — they care about CAC, ROAS, and campaign performance, not ARR or churn" → domain-level knowledge for the `marketing` domain
- "Users in this domain are non-technical — explain results in plain language, never reference field names" → domain knowledge
- "Attribution in this domain always uses last-click unless the user explicitly asks for a different model" → domain knowledge

**Entity level (`domain: "default"` + `entity: customer`) — applies when this entity is queried:**
- "Use the `customer` entity for questions about ARR, churn, and account health — not the `account` entity, which includes prospects" → entity knowledge on `customer`
- "`total_paid` includes one-time fees and should not be used as a proxy for ARR — use the `arr` feature instead" → entity knowledge on `customer`
- "This entity has a known data gap for March–April 2021 during the CRM migration — records from this period may be incomplete" → entity knowledge
- "The `status` field has four values: `active`, `churned`, `trial`, `paused` — a churned account is still included unless you filter by `status = 'active'`" → entity knowledge

---

## When NOT to Use This File

- If it's a SQL pattern, filter, field choice, or query convention → **task instructions file**
- If it's the definition of a metric or formula feature → **entity YAML**
- If it's a short term definition (one or two sentences) → **glossary file**
- If it's about how responses are formatted (table titles, tone, data notes) → **output format file**
- If it's about when to ask clarifying questions → **clarification policy file**

Quick test: SQL or query logic → task instructions. Metric or feature definition → entity YAML. Term definition → glossary. Communication style → behavior file.

---

## Full Examples

### Example 1 — Grove (B2B SaaS), business-level knowledge

This example shows a business-level knowledge file — business description and universally true facts, loaded on every query across every domain.

```markdown
---
type: knowledge
domain: "*"
---

## About Grove
Grove sells subscription-based software to companies. Revenue is entirely subscription-based —
customers pay monthly or annually for platform access. The business grows by acquiring new customers
(logos), expanding existing accounts (upsells and seat additions), and reducing churn. The primary
revenue metric is ARR. "Revenue" without qualification means ARR, not MRR. MRR = ARR / 12.

## Customer Lifecycle
Accounts move through three states: trial → active → churned.
A trial account is exploring the product before committing to a paid plan. An active account is paying.
A churned account cancelled and is no longer paying — it remains in the data and is counted in totals
unless explicitly filtered by status.
Growth comes from three levers: converting trials to paid (acquisition), growing existing accounts
via upsells and seat additions (expansion), and preventing active accounts from leaving (retention).
NDR (Net Dollar Retention) captures the combined effect of expansion and churn on existing revenue.

## Customer Tiers
Customers are segmented into three tiers by ARR: SMB (below $20K) → Mid-Market ($20K–$99K) →
Enterprise ($100K and above). Tier determines how accounts are prioritized for sales and customer
success. When a customer's ARR crosses a threshold, their tier updates automatically.

## Fiscal Year
Fiscal year starts February 1. Q1 = Feb–Apr, Q2 = May–Jul, Q3 = Aug–Oct, Q4 = Nov–Jan.

## Global Conventions
- All revenue figures are in USD.
- Data refreshes daily at 06:00 UTC. Same-day figures may be incomplete until the refresh completes.
- Deleted and test accounts are excluded from all entity queries by default.

## Data Quality
- Accounts created before 2020-01-01 were migrated from a legacy CRM. Some fields (`industry`,
  `company_size`) may be null for these records.
- NPS scores are collected quarterly. The `nps_score` field reflects the most recent survey
  response, not a real-time value.
```

---

### Example 2 — Bly (E-commerce), marketing domain knowledge

This example shows a domain-level knowledge file for Bly's marketing domain. It covers the business context relevant to this domain, who asks questions, what they care about, and the conventions the agent should follow.

```markdown
---
type: knowledge
domain: "marketing"
---

## Bly's Marketing Model
Bly sells consumer goods directly to shoppers online. Customers are acquired through paid and
organic channels — paid search, paid social, email, and direct. Each order is attributed to the
channel that drove the visit. The marketing team is responsible for new customer acquisition:
getting first-time buyers to place a completed order. CAC (cost to acquire a customer), ROAS
(return on ad spend), and channel conversion rate are the primary metrics the team optimizes.
A "conversion" in this domain means a first completed order — not a click or a visit.

## Customer Journey
Bly customers progress through value stages: new customer (first completed order) → repeat customer
(two or more completed orders) → VIP (flagged by lifetime net revenue and purchase history).
The marketing team's scope is acquisition — driving a visitor's first completed order. Everything
after that belongs to the analytics domain: repeat purchase rate, LTV, VIP conversion, and winback.
When a question touches retention or loyalty, redirect it.

## Who Uses This Domain
The marketing and growth team — campaign managers, paid acquisition analysts, and the CMO.
Non-technical users: avoid referencing field names or SQL conditions in answers. Use plain language.
Example: say "customers acquired through paid search" not "channel = 'paid_search' and status = 'completed'".

## What They Care About
New customer acquisition, channel performance, conversion rate, and return on ad spend.
Do not surface loyalty or retention metrics (repeat purchase rate, LTV, VIP status) in this domain
unless explicitly asked — redirect those questions to the analytics domain.

## Attribution Convention
Attribution in this domain always uses last-click unless the user explicitly requests a different model.
Multi-touch attribution is not available in the current data — say so clearly if asked, and do not
attempt to approximate it.

## Revenue Convention
Use net revenue (after discounts and refunds) for all revenue figures in this domain.
When showing channel revenue, always include order count alongside revenue — revenue alone can
be misleading if average order value differs significantly between channels.

## Out of Scope for This Domain
- Repeat purchase rate, LTV, and customer lifetime metrics → analytics domain
- Product catalog and inventory performance → merchandising domain
```

---

### Example 3 — Arcadia (Mobile gaming), `player` entity knowledge

This example shows the density of caveats needed for a gaming entity — multiple non-obvious definitions (active vs. lapsed), a spend field that intentionally excludes soft currency, a segment freshness lag, and a known data migration issue that affects cohort analysis.

```markdown
---
type: knowledge
domain: "default"
entity: player
---

## Aliases
Business users refer to this entity as: user, gamer, account.

## What a Player Is
A player is any registered account that has completed at least one game session.
Guest accounts and registered accounts with zero sessions are not counted as players.

## Activity Definitions
- **Active:** a player with a session in the last 7 days.
- **Lapsed:** a player with no session for 30 or more days.

Do not use `is_active` to determine activity — that field reflects a daily batch refresh and lags
actual session data by up to 24 hours. Use `last_session_at` for activity checks instead.

## Spend Fields
- `total_spend_usd` is a metric feature pulled from the `purchase` entity. It covers real-money
  in-app purchases (hard currency) only.
- Soft currency (coins, gems earned through gameplay or rewarded ads) is not included in
  `total_spend_usd` and has no USD value.
- For soft currency economy data, use the `economy_transaction` entity.

## Player Segment
- `player_segment` is a formula feature derived from `spend_last_30_days_usd` (rolling 30-day
  real-money spend).
- Segments are recalculated by a weekly batch job and may be up to **7 days stale**.
- The segment thresholds are: whale (>$100 rolling 30-day spend), dolphin ($10–$100), minnow
  (<$10 with at least one purchase), non-payer (no purchases).

## Known Data Issue — Pre-Migration Install Dates
Players who installed before **2022-03-01** have `install_date` set to 2022-03-01 — the migration
date, not their actual install date. This is a known data loss from the legacy system migration.

Do not use `install_date` for cohort analysis on players who may have installed before March 2022.
For those cohorts, use the `player_cohort` entity, which has corrected install date estimates from
the re-attribution pipeline.
```
