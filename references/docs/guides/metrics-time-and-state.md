---
description: How to place a computation — feature, metric, skill, or glossary term — and how to model balances, time windows, cohorts, and ratio KPIs correctly.
icon: timeline
---

# Modeling metrics, time, and state

Where each computation lives, and how time-varying state gets a grain it can be aggregated on correctly.

## When you need this

- You're defining "total MRR" and the source table holds historical and cancelled rows.
- Someone asks "MRR in March" or "NDR for the Q1 cohort" and you're unsure what to define versus what to query.
- A KPI divides one entity's aggregate by another's — ARPDAU, CAC — and has no obvious home.
- You're about to add `revenue_7d` next to an existing `revenue_30d`.
- The same rate comes out different depending on who computes it.

## The principle

Model state at the grain where it is true, and put each computation in the narrowest primitive that owns it. A balance like MRR is true *per subscription per month* — that grain must exist as physical rows before any metric can aggregate it, because Lynk cannot create a grain that doesn't exist. And definitions carry only what is always true: a window or segment that is a parameter of the question stays out of the schema and goes into query-time `WHERE`.

## Patterns

### Place the computation by its shape

Run this decision tree before writing anything:

- A row-grain value of one entity → a [feature](../concepts/entity/schema-yml/feature.md). Grove: `subscription.mrr`.
- An aggregate over an entity's own rows → a [metric](../concepts/entity/schema-yml/metric.md) on that entity: `subscription.total_mrr`.
- An aggregate consumed across an entity boundary → a feature wrapping the metric. Grove's `customer.total_mrr` is `sql: metric(subscription.total_mrr)` with `join_name: customer_to_subscription` — never a metric on the consuming entity, because metrics are entity-local.
- A way of computing — multi-step, opinionated — → a [skill](../concepts/skill.md).
- A word the team uses → a [glossary](../concepts/glossary.md) entry.

Deviate only at a domain boundary, where the move is an [import](../concepts/entity/schema-yml/identity-and-imports.md), not a new definition.

### Model semi-additive state on a snapshot entity

A balance — MRR, headcount, inventory — is semi-additive: it sums *within* one point in time, never across time. If `maindb.public.subscriptions` holds historical and cancelled rows, `SUM(subscription.mrr)` adds March's balance to February's; nothing errors, the number is just several times too large. **The snapshot grain must already exist upstream as a table or view — an entity's identity is never an inline query.** With `subscription_months` (one row per subscription per active month) in the warehouse, model it:

```yaml
identity: maindb.public.subscription_months   # a table or view, built upstream
keys:
  - subscription_id
  - month

features:
  # keys are not features — declare any key that joins or queries need.
  # subscription_id and customer_id are declared the same way as month.
  - name: month
    description: First day of the calendar month this row snapshots
    sql: maindb.public.subscription_months.month
    data_type: datetime
  - name: mrr
    description: This subscription's MRR during this month, in USD
    sql: maindb.public.subscription_months.mrr
    data_type: number

metrics:
  - name: sum_mrr
    description: Total MRR across the subscription-month rows in scope — always constrain to a single month
    sql: SUM(subscription_month.mrr)
    data_type: number
```

"MRR in March" is now query-time: `WHERE month = '2026-03-01'`. The same grain answers end-of-period and average-of-period balances, with no new definitions.

### Compute cohorts on the snapshot; canonicalize in a skill

**Aggregate *inside* each CTE, before any join — the shape that is correct by construction ([CTEs and subqueries](../api/lynk-sql.md#ctes-and-subqueries)).** NDR compares the same customers' MRR across two windows: compute each window in its own CTE at the snapshot grain, then join aggregate to aggregate.

```sql
WITH start_mrr AS (
  SELECT customer_id, metric(subscription_month.sum_mrr) AS mrr
  FROM subscription_month WHERE month = '2025-02-01' GROUP BY customer_id
), end_mrr AS (
  SELECT customer_id, metric(subscription_month.sum_mrr) AS mrr
  FROM subscription_month WHERE month = '2026-02-01' GROUP BY customer_id
)
SELECT SUM(e.mrr) / NULLIF(SUM(s.mrr), 0) AS ndr
FROM start_mrr s LEFT JOIN end_mrr e ON e.customer_id = s.customer_id
```

The window edges and who counts as "starting" are opinions, so this query lives in a Grove skill (say `ndr-analysis`) — the reproducible home of the computation. The glossary entry `ndr` stays one sentence of vocabulary and points at the skill.

### Give cross-entity ratio KPIs a skill, not a home they don't have

Arcadia's ARPDAU divides `metric(purchase.sum_net_revenue_usd)` by `metric(player.count_dau)`. Two entities' aggregates: not a metric (entity-local), not a feature (no row owns it). Don't invent a KPI entity — the schema has no primitive for this, by design. The pattern is a skill carrying the canonical Lynk SQL — one CTE per aggregate, joined on the shared key or date — with the glossary term defining the word. CAC-style ratios follow the same shape.

### Bake a time boundary only when it is a business definition

Arcadia bakes `duration_seconds > 5` into `player_to_meaningful_session` because the boundary *is* the definition of a meaningful session. "Last 30 days" is a parameter — it belongs in query-time `WHERE`, not in a definition. Bake when removing the filter changes what the word means; defer when it only changes which question was asked.

### Choose the filter mechanism by scope

| Mechanism | Scope | Reach for it when |
|---|---|---|
| `filter:` on a feature | one feature's source rows | the narrowing is part of this value's meaning — `player.ios_spend_usd` |
| `filter:` on a metric | one aggregate's rows | a differently-scoped aggregate is its own definition — `order.completed_revenue` |
| filtered relationship | every definition and query using the join | the narrowed set is itself a concept — `player_to_meaningful_session` |
| query-time `WHERE` | one query | the boundary is a parameter — dates, segments, "in March" |

## Anti-patterns

### Summing a balance across periods

```yaml
# wrong — subscription_months holds every month; this sums them all
- name: current_mrr
  description: Current total MRR, in USD
  sql: SUM(subscription_month.mrr)
  data_type: number
```

With twelve months of history the result is roughly 12× actual MRR — every month's balance added to every other's. It compiles and returns a number; the number is wrong. The fix is the snapshot pattern above: name the metric for what it computes, say in its description that time must be constrained, and pin the period at query time.

### Averaging per-row ratios across an entity boundary

The single-entity rule — a rate is a ratio of sums — is owned by [Metric](../concepts/entity/schema-yml/metric.md#computing-the-right-value). The cross-entity variant sneaks past it: aggregate a per-customer `refund_rate` feature on Bly's `customer`:

```yaml
# wrong — a customer with 1 order weighs the same as one with 1,000
- name: avg_refund_rate
  description: Company-wide refund rate, 0–1
  sql: AVG(customer.refund_rate)
  data_type: number
```

The number moves when the customer mix moves, not when refunds do. The company-wide rate is `order.refund_rate` — the metric on the entity whose rows carry both the numerator and the denominator.

### Measure explosion

```yaml
# wrong — near-duplicates the agent cannot tell apart
- name: revenue_7d
  description: Recent net revenue
  sql: SUM(order.net_amount)
  data_type: number
  filter: order.order_date >= CURRENT_DATE - INTERVAL '7 days'
  # …and revenue_30d, revenue_mtd, revenue_qtd, revenue_ytd
```

Every window multiplies the metric list, and the descriptions are indistinguishable — the agent's choice between them is a coin flip. The window is a parameter: keep the one canonical `sum_net_revenue` and put the window in query-time `WHERE`.

### Glossary-as-computation

```yaml
# wrong — the formula's only home is prose
ndr:
  name: NDR
  description: (starting MRR + expansion − contraction − churn) ÷ starting MRR, trailing 12 months, excluding new logos.
```

Prose is not executable. Each time the question comes up, the agent re-derives the CTEs slightly differently, and two askers get two numbers. The glossary defines words ([GLOSSARY.yml](../concepts/glossary.md)); the canonical query lives in a skill, and the glossary entry points at it.

## The bar

- Every metric aggregates only the entity it is defined on; every cross-boundary aggregate is a feature wrapping `metric()` with a `join_name`.
- Every balance-like value is modeled on a snapshot grain that physically exists, and its metric's description says how to constrain time.
- No definition encodes a parameter the question should supply; every baked filter is a business definition you can name.
- Every rate is a ratio of sums, computed on the entity that owns the rows.
- Any two metrics the agent must choose between are distinguishable from their names and descriptions alone, and every `sql` computes exactly what its description says.
- Every KPI built from two entities' aggregates has a skill holding its canonical Lynk SQL; the glossary term points at it.
- Query-time cross-grain math aggregates inside CTEs before joining.

## Related

- [Metric](../concepts/entity/schema-yml/metric.md) · [Feature](../concepts/entity/schema-yml/feature.md) · [Relationships](../concepts/entity/schema-yml/relationships.md)
- [Skill](../concepts/skill.md) · [GLOSSARY.yml](../concepts/glossary.md)
- [Lynk SQL](../api/lynk-sql.md) — query-time `WHERE`, CTEs, `metric()` · [SQL expressions](../reference/sql-expressions.md) — the authoring grammar
- Sibling: [Choosing and shaping entities](designing-entities.md)
