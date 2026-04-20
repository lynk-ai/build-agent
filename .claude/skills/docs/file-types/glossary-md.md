# Glossary File Reference

Glossary files define business-specific terms in plain English. They help the agent understand what users mean when they use terminology unique to your business or industry.

The glossary is not the place to define how metrics are calculated or which entity to query — that belongs in the entity YAML files, which are the source of truth for all data definitions. The glossary is purely about meaning in plain English.

---

## Frontmatter

```yaml
---
type: glossary
domain: "*"              # or a specific domain name
---
```

| Field | Values | Description |
|---|---|---|
| `type` | `glossary` | Identifies this as a glossary file |
| `domain` | `"*"`, `"default"`, `"marketing"`, etc. | Which domain this glossary applies to |

---

## Entry Format

Each entry is a YAML key-value pair immediately below the frontmatter block.

```yaml
---
type: glossary
domain: "*"
---

logo_churn:
  term: Logo Churn
  description: A customer who cancelled their subscription, counted as one regardless of their size. That means even a large enterprise counts as one churned logo, just like a small account.

at_risk:
  term: At Risk
  description: A customer we believe may churn. That means they are showing warning signs — low engagement, unresolved issues, or no recent activity.
```

| Field | Description |
|---|---|
| key (e.g., `arr`) | The lookup key — how the agent finds this entry |
| `term` | The human-readable term being defined |
| `description` | The definition — short, specific, and self-contained |

**Key naming:** Snake_case is conventional (e.g., `logo_churn`, `at_risk`) but not required. The agent uses the `term` and `description` fields — the key is just an internal identifier.

**Quoting keys with special characters:** Keys containing `%`, `+`, or other special YAML characters must be quoted (e.g., `"NPS%"`, `"CTR%"`).

---

## What Belongs in the Glossary

Terms that are **specific to your business** — words your users will type that have a particular meaning in your context, or that differ from their common industry definition.

**Business-specific terminology:**
```yaml
power_user:
  term: Power User
  description: A user who uses the product daily. That means they are highly engaged and rely on it as a core part of their workflow.

at_risk:
  term: At Risk
  description: A customer we believe may churn. That means they are showing at least one of the following warning signs - low engagement, unresolved issues, or no recent activity.

whale:
  term: Whale
  description: One of our highest-value accounts. That means we treat them as a strategic relationship with dedicated attention, not a standard self-serve customer.
```

**Terms your company uses differently from the industry norm:**
```yaml
activation:
  term: Activation
  description: A user who completed their first meaningful action in the product. That means simply signing up is not enough — they need to actually do something valuable.

conversion:
  term: Conversion
  description: A trial account that upgraded to a paid plan. That means a marketing click or a visit does not count as a conversion in our context.
```

**Status and segment labels users will reference:**
```yaml
active:
  term: Active
  description: A customer currently on a paid subscription. That means trial accounts are not active.

churned:
  term: Churned
  description: A customer whose subscription ended and was not renewed. That means they were once paying and are no longer.

trial:
  term: Trial
  description: An account exploring the product before committing to a paid plan. That means they are not yet a paying customer.
```

**What does NOT belong here:** common industry terms with standard definitions (MRR, GMV, ROAS), metric calculations, and anything that should be defined as a metric on an entity YAML.

---

## Domain-Specific Glossaries

You can scope a glossary to a specific domain. Named domains inherit from `domain: "default"` and can extend or override it. For the full inheritance model, see the [Domains reference](../concepts/domains.md).

---

## Best Practices

**Only add terms specific to your business.** If a term has a standard industry definition and you use it the same way, there's no value in adding it. Add it only if your definition differs, or if it's jargon unique to your company or industry.

**Write plain English definitions.** The glossary explains what things mean to a business user — not how they're calculated or which field to filter on. Calculations and metric definitions belong in entity YAML files.

**Lead with the precise definition, then explain the reasoning.** The first sentence should state exactly what the term means — the specific, unambiguous definition. The second sentence explains why it was defined that way, what it implies, or how it differs from a related term. This structure helps the agent understand both what to do and why, so it can apply the definition correctly in edge cases.

```yaml
# VAGUE
power_user:
  term: Power User
  description: A user who uses the product a lot.

# GOOD — precise definition first, reasoning second
power_user:
  term: Power User
  description: A user who uses the product daily. That means the user is highly engaged and relies on it as a core part of their workflow.
```

**Don't be circular.** A definition that says "NRR is net revenue retention" tells the agent nothing. Explain what the term actually means in your business context.

**Configure your clarification policy for unknown terms.** When a user references a term not in the glossary, the agent's behavior depends on your clarification policy. If no rule is configured, the agent may ask for clarification or attempt to interpret the term from conversation context. Add an explicit rule to your clarification policy for how the agent should handle unknown terms.

---

## Common Pitfalls

**Adding common industry terms.** If everyone in your industry already knows what a term means and you use it the same way, adding it to the glossary adds no value. Only add terms that are specific to your business or that you define differently.

**Circular definitions.** "Logo churn is when a logo churns" tells the agent nothing. The definition should explain what the term means in plain English — not restate the term.

**Relying on the glossary instead of defining a metric in the entity YAML.** Including a calculation in a glossary description is fine if it helps a non-technical person understand the term. But it is never enough on its own. If a term has a precise calculation, it must also be defined as a metric in the relevant entity YAML — that is the source of truth the agent uses. The glossary is a dictionary for business users; the YAML is what the agent actually queries against.

**Vague definitions.** "A customer who uses the product a lot" is not a definition. Be specific about what the term actually means in your business.

**Putting long explanations in the glossary.** If a term requires more than two sentences, it belongs in a knowledge file. The glossary is a quick lookup — long entries dilute it.

---

## When to Use This File

Add a glossary entry when a term meets one of these conditions:
1. It's specific to your business and wouldn't be understood by a general-purpose AI
2. Your company uses it differently than the industry standard
3. It's a status or segment label that users will reference by name

**Examples:**
- "Our team uses 'whale' to mean our top strategic accounts" → add a business-specific term
- "When users say 'active customer' they mean a paying customer, not a trial" → add a status definition
- "We define 'conversion' differently — it means a trial upgrading to paid, not a click" → add a term your company uses differently
- "The marketing team uses 'winback' constantly but it's not an industry-standard term" → add internal jargon the agent needs to recognize
- "The product domain uses 'activation' differently than the marketing domain" → create a domain-specific glossary entry

---

## When NOT to Use This File

- If it's a metric definition or KPI calculation → **entity YAML metrics** (that's the source of truth for how to query the data)
- If it's guidance on when to use an entity or metric → **entity knowledge file**
- If it's a SQL pattern, filter, or field convention → **task instructions file**
- If it's a data quality caveat or business rule → **knowledge file**
- If it's a common industry term your business uses in the standard way → don't add it at all

The glossary is for plain English meaning. Everything about how data is structured, calculated, or queried belongs in the YAML files.

---

## Full Examples

### Example 1 — Grove (B2B SaaS)

Grove sells subscription-based software to businesses. These terms appear frequently in internal conversations and reporting — without them, the agent will interpret "logo" literally and confuse revenue churn with account churn.

```yaml
---
type: glossary
domain: "*"
---

logo_churn:
  term: Logo Churn
  description: A customer who cancelled their subscription, counted as one regardless of their size. That means even a large enterprise counts as one churned logo, just like a small starter account.

revenue_churn:
  term: Revenue Churn
  description: The ARR we lost because a customer cancelled or downgraded. That means it is different from logo churn — a small customer cancelling has low revenue churn but still counts as one churned logo.

expansion:
  term: Expansion Revenue
  description: Additional ARR from an existing customer through an upsell, seat addition, or plan upgrade. That means it does not include revenue from new customers.

ndr:
  term: NDR
  description: Net Dollar Retention — the percentage of ARR retained from existing customers after accounting for churn, contraction, and expansion. That means an NDR above 100% means expansion is outpacing churn.

at_risk:
  term: At Risk
  description: A customer we believe may churn. That means they are showing warning signs — low NPS score, no active subscriptions, or no recent engagement — and should be flagged for account review.

power_user:
  term: Power User
  description: A user who uses the product daily and relies on it as a core part of their workflow. That means they are highly engaged and are the primary stakeholders to protect during renewal conversations.
```

---

### Example 2 — Bly (E-commerce)

Bly sells consumer goods direct-to-consumer online. These terms reflect how the marketing and growth teams talk about customers — they differ from standard industry definitions in a few key ways.

```yaml
---
type: glossary
domain: "*"
---

repeat_customer:
  term: Repeat Customer
  description: A customer who has placed more than one completed order with us. That means they came back after their first purchase, which is a strong signal of loyalty and the primary driver of LTV.

new_customer:
  term: New Customer
  description: A customer placing their very first completed order. That means they have no prior purchase history and are being acquired for the first time — trial carts and abandoned checkouts do not count.

vip:
  term: VIP
  description: A customer flagged as high-value in our system (the `vip` field is true). That means they have a long purchase history and high lifetime net revenue, and receive priority treatment in campaigns and support.

winback:
  term: Winback
  description: A lapsed customer who places a new completed order after going inactive. That means they were considered lost but re-engaged — either on their own or through a re-engagement campaign.

conversion:
  term: Conversion
  description: When a shopper completes a purchase — a `status = 'completed'` order. That means a click, a visit, or an abandoned cart does not count as a conversion in our context.
```

---

### Example 3 — Arcadia (Mobile gaming)

Arcadia is a casual mobile game monetized through in-app purchases. Gaming has industry-specific terminology where exact thresholds and edge cases matter. The cutoff between whale/dolphin/minnow, what counts as lapsed, and the precise definition of D7 all vary by company — without these entries, the agent will guess.

```yaml
---
type: glossary
domain: "*"
---

whale:
  term: Whale
  description: A player whose rolling 30-day spend exceeds $100. That means whales are a strategic retention segment — losing one whale has an outsized revenue impact compared to losing many casual players.

dolphin:
  term: Dolphin
  description: A paying player whose rolling 30-day spend is between $10 and $100. That means they contribute meaningfully to revenue but are managed at the segment level, not individually.

minnow:
  term: Minnow
  description: A paying player who has made at least one purchase but whose rolling 30-day spend is under $10. That means they count toward paying user conversion rates but have low individual LTV.

lapsed:
  term: Lapsed
  description: A player who has not opened the game in more than 30 days. That means lapsed players are distinct from churned — they are still targeted by re-engagement campaigns and may return.

d7_retention:
  term: D7 Retention
  description: The percentage of new players who return to play on exactly day 7 after their install date. That means day 0 is install day, and a player must be active on day 7 specifically — not just "within 7 days" — to count as retained.

arpdau:
  term: ARPDAU
  description: Average Revenue Per Daily Active User — total daily net revenue from purchases divided by the count of unique players who had a session that day. That means it measures revenue per engaged user, not per registered account.

soft_currency:
  term: Soft Currency
  description: In-game currency earned through gameplay, such as coins or gems earned from levels. That means it does not contribute to revenue figures — only real-money transactions are counted as revenue.

hard_currency:
  term: Hard Currency
  description: Premium in-game currency purchased with real money. That means it is the correct basis for all revenue and monetization analysis, even when players later spend it on virtual items within the game.
```
