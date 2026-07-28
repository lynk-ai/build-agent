---
description: Skills are lazy prose procedures for classes of analytical reasoning — how the agent thinks through an analysis, not what exists in the data.
icon: list-checks
---

# Skill

A lazy prose procedure for a class of analytical reasoning — root-cause analysis, churn investigation, pipeline review. Skills capture *how the agent thinks*, not *what exists in the data*.

## What it is

A skill is the runbook you'd hand a junior analyst for a recurring kind of analysis. It is verb-shaped — "how to investigate churn" — not noun-shaped. That distinction is the rule that keeps `skills/` from becoming a garbage drawer:

- A **fact** about an entity goes on the [entity](entity/README.md).
- A **way of reasoning** across an analysis goes in a skill.

Two further rules follow:

- **Skills don't define new schema.** If a skill needs a value the schema doesn't have, add a [feature](entity/schema-yml/feature.md) or [metric](entity/schema-yml/metric.md) — don't compute it inside the skill. Skills *use* features and metrics; they don't define them.
- **Skills don't compose with other skills.** A skill is an encapsulated procedure. It may inject content from entities, glossary terms, or supporting files via `@`, but skills don't merge or extend one another.

## Where it lives

A folder per skill inside a [domain](domain/README.md), with optional supporting files alongside the primary file:

```
.lynk/domains/<domain>/skills/<name>/
├── SKILL.md
└── examples/
    └── enterprise-churn-2024-q3.md
```

**Loaded lazily.** The agent indexes skills by their frontmatter `description` and loads a skill's body only when it's relevant to the question. Skills that don't apply stay unloaded — the brain is large, the agent's working memory is focused.

## Format

`SKILL.md` follows the shared [frontmatter contract](../reference/markdown-format.md#frontmatter-contract) — `name` (matching the folder), `description`, optional `enabled` — over a prose body.

The `description` is load-bearing: it's what the agent reads at index time to decide relevance. Write it so the agent can tell, from one line, whether a question calls for this skill.

The body is whatever helps the agent reason — procedures, decision trees, references to specific entities and metrics. Use the [`@` operator](../reference/markdown-format.md#references) to inject the exact definitions the procedure leans on, so the prose stays focused while the specifics are pulled in at load time.

## Examples

**Frontmatter and a short procedure.**

```markdown
---
name: pipeline-review
description: How to review sales pipeline health — stage coverage, aging, and slippage risk
enabled: true
---

# Pipeline Review

1. Coverage: compare open pipeline to quota by stage.
2. Aging: flag deals past the median days-in-stage for their stage.
3. Slippage: list deals whose close date moved more than once this quarter.
```

**A churn investigation skill (in the `core` domain) that injects definitions.** The `@` paths stay within `core`, the skill's own domain.

```markdown
---
name: churn-investigation
description: How to investigate customer churn — identify signals, segment by cohort, surface patterns
enabled: true
---

# Churn Investigation

When investigating churn, start with these signals:

1. Usage decline — see @customer.active_subscription_count.description
2. Pending cancellation — see @subscription.is_pending_cancellation.description
3. Support escalation — see @glossary.at_risk.description

Cohort the analysis by signup quarter. The team's working definition of churn
is in @glossary.logo_churn.description.

For a past investigation:
- @/.lynk/domains/core/skills/churn-investigation/examples/enterprise-churn-2024-q3.md
```

## Validation

- `SKILL.md` declares `name` and `description`; `name` matches the folder.
- A skill that references an undefined feature or metric fails — skills use schema, they don't define it.

## Related

- [Entity](entity/README.md) — where facts live, versus a skill's reasoning
- [Feature](entity/schema-yml/feature.md) · [Metric](entity/schema-yml/metric.md) — what skills use, not define
- [Policy](policy.md) — *how to operate*, versus a skill's *how to reason*
- [Markdown format](../reference/markdown-format.md) — the frontmatter contract and `@` operator
- Guides: [Placing knowledge in a layer](../guides/where-knowledge-goes.md)
