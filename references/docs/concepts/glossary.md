---
description: GLOSSARY.yml is the team's vocabulary — the terms they use and what they mean, always loaded and merged across scopes.
icon: book-a
---

# GLOSSARY.yml

The team's vocabulary, structured for the agent to read. Each entry is a term the team uses and what it means.

## What it is

When a user mentions a term in a question, the agent resolves it against the glossary to understand what they mean. When the agent writes an answer, it draws on the glossary for the names the team actually uses. The glossary is how the agent speaks the team's language.

**A glossary entry has no structured pointer to an entity or metric — the agent resolves a term only by reading its prose, so the description must stand on its own.** It is always loaded as part of orientation, and the agent reads the whole merged glossary to resolve each term.

A term that is really *a way of computing* — "customer health" combining engagement, payment, and support signals — usually wants to be a [skill](skill.md), not a glossary entry. The glossary defines what words mean; skills define how to reason.

## Where it lives

One `GLOSSARY.yml` at the project root, and optionally one inside each domain:

```
.lynk/GLOSSARY.yml                      # shared vocabulary
.lynk/domains/marketing/GLOSSARY.yml    # marketing's terms
```

## Format

A YAML file. Each top-level key is a term, in snake_case — the stable address the [`@` operator](../reference/markdown-format.md#references) points at (`@glossary.expansion.description`).

```yaml
expansion:
  name: Expansion
  description: Additional recurring revenue from an existing customer — upsells, seat growth, or plan upgrades. Counted separately from new-logo revenue.
```

| Field | Required | Type | Notes |
|---|---|---|---|
| key | ✓ | snake_case | The stable address. `@glossary.<key>` resolves here. |
| `name` | ✓ | string | The term as the team writes it. |
| `description` | ✓ | string | What the term means, in prose. Long forms, abbreviation expansions, and clarifying context all live here. |

**Composition merges across scopes.** The effective glossary in a domain is the root glossary merged with the domain's, with the **domain winning** on a key collision. A glossary reference never needs a domain prefix — it is already resolved against the merged result.

Lynk ships no default — the glossary is empty until you author it.

## Examples

**A single term.**

```yaml
active_customer:
  name: Active Customer
  description: A customer who has logged in within the last 90 days.
```

**A domain glossary (Grove, B2B SaaS) that overrides and extends the root.**

```yaml
logo_churn:
  name: Logo Churn
  description: A customer fully cancelling, counted as one lost logo regardless of contract size. Distinct from revenue churn, which weights by ARR.

ndr:
  name: NDR
  description: Net Dollar Retention. Revenue retained from existing customers over a period including expansion, contraction, and churn — excluding new logos.

at_risk:
  name: At Risk
  description: An active customer showing churn signals — declining usage, a pending cancellation, or an NPS detractor score in the last quarter.
```

## Validation

- Each entry declares `name` and `description`. A missing required field fails the build.
- Keys are snake_case. On a root/domain key collision, the domain entry wins (this merge is expected, not an error).

## Related

- [Domain → GLOSSARY.yml](domain/glossary.md) — the domain-scoped vocabulary that merges over this file
- [LYNK.md](lynk-md.md) — orientation, which the glossary is not
- [Skill](skill.md) — where *ways of computing* live, rather than the glossary
- Guides: [Placing knowledge in a layer](../guides/where-knowledge-goes.md) · [Modeling metrics, time, and state](../guides/metrics-time-and-state.md)
