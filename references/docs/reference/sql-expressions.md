---
description: The reference grammar inside schema.yml sql fields — segment-count path resolution, the metric/first/last functions, filters, and join binding.
icon: brackets-curly
---

# SQL Expressions

The grammar for the `sql:` and `filter:` fields inside [`schema.yml`](../concepts/entity/schema-yml/README.md). It governs how a [feature](../concepts/entity/schema-yml/feature.md) or [metric](../concepts/entity/schema-yml/metric.md) references columns, other definitions, and related entities.

## What it is

When you author a feature or metric, its `sql:` field holds the expression that produces the value. That expression is mostly ordinary SQL, with one Lynk-specific rule: every reference inside it is a **path**, and the parser tells path types apart by counting segments.

This is the *authoring* grammar — the SQL you write inside `schema.yml`. It is distinct from the [Lynk SQL query dialect](../api/lynk-sql.md), which is what the agent emits to query a built layer. This page is about the former.

## Where it lives

Inside `.lynk/domains/<domain>/entities/<entity>/schema.yml`, in the `sql:` and `filter:` fields of features and metrics, and in the `sql:` field of [relationship](../concepts/entity/schema-yml/relationships.md) steps.

## Format

### The two reference forms

Every reference inside `sql:` is one of two things, distinguished by segment count:

| Segments | Form | Resolves to | Example |
|---|---|---|---|
| 4+ | Physical path | A column in the warehouse | `maindb.public.orders.net_amount` |
| 2 | Entity-local semantic path | A feature or metric on an entity **in this domain** | `order.net_amount` |

Anything else is SQL syntax around those references — formulas, function calls, `CASE WHEN`, casts.

**Expressions are literal SQL.** There is no templating of any kind — no variables, no macros, no `{{ … }}` or `{% … %}` syntax, no `ref()`. What you write is exactly what compiles.

A physical path inside `sql:` always names a **column** (4+ segments). A bare 3-segment table like `maindb.public.orders` is not a valid `sql:` reference — that 3-segment form belongs to [`identity:`](../concepts/entity/schema-yml/identity-and-imports.md), not to expressions.

**`sql` is same-domain only.** A semantic path may reference only entities in the *same* domain; it cannot name an entity in another domain. To use a value from another domain (e.g. `core`), [`import`](../concepts/entity/schema-yml/identity-and-imports.md) it onto this entity and reference it by its local name. Cross-domain composition is an `imports`/topology concern, not a `sql` one.

### References are always entity-qualified

Inside `sql:`, a reference to this entity's own feature is written `<entity>.<feature>` — `order.net_amount`, never a bare `net_amount`. Every name is qualified, so a reader of any expression knows exactly what each token refers to without outside context.

### Reaching across a boundary

A 2-segment path resolves to a *declared feature or metric* on the target entity — not to a raw warehouse column. You reach another entity only through its declared features and metrics; writing its physical path to dodge that is rejected — `maindb.public.customers.region` from an `order` feature fails even though the column exists. A value owned by another entity has exactly one form: that entity's feature or metric (`customer.region`), reached through a `join_name`. (When a 4+ segment physical column *is* legal instead, see [join binding](#join-binding).)

### Functions

| Function | Purpose |
|---|---|
| `metric(<entity>.<metric_name>)` | Invokes a [metric](../concepts/entity/schema-yml/metric.md) defined on an entity. The engine substitutes the metric's aggregation. |
| `first(<field>, order_by=<field>, offset=N)` | Picks a row from a `one_to_many` source ordered **ascending** by `order_by`; `offset` defaults to `0` — the **smallest** `order_by` (the first). |
| `last(<field>, order_by=<field>, offset=N)` | Picks a row ordered **descending** by `order_by`; `offset` defaults to `0` — the **largest** `order_by` (the most recent / highest). |

**`first()`/`last()` pick a single row, so the `order_by` must order deterministically** — break ties on a unique field and account for NULLs, or the chosen row is arbitrary and nothing errors.

A **feature** reference needs no wrapper — `customer.email` resolves directly. A **metric** is always invoked with `metric()` — write `metric(customer.total_arr)`, never bare `customer.total_arr` — so every aggregation is explicit in the expression.

`first()` and `last()` belong to this authoring grammar only — they do **not** exist in the [Lynk SQL](../api/lynk-sql.md) query dialect. At query time, use window functions and `QUALIFY` instead.

### Path shapes by context

The same segment count means different things in different fields — don't carry a shape from one context to another:

| Where | Segments | Means | Example |
|---|---|---|---|
| `identity:` | 3 | physical table | `maindb.public.customers` |
| `identity:` | 2 | another entity (extension) | `core.customer` |
| `sql:` / `filter:` | 2 | entity-local feature or metric | `order.net_amount` |
| `sql:` / `filter:` | 4+ | physical column | `maindb.public.orders.net_amount` |
| `imports:` | 3 | `domain.entity.name` | `core.customer.total_arr` |

### `filter`

**A `filter:` is grain-preserving: it narrows *source* rows before the `sql:` evaluates but never adds or drops the entity's own rows.** For an aggregation it limits which rows are aggregated; for a row-level feature it behaves like a join condition that nullifies non-matching rows rather than removing them. References in `filter` are entity-qualified, exactly like in `sql`, and bound by the same `join_name`.

### Join binding

When a feature's `sql:` or `filter:` references another entity, the feature declares a single `join_name` naming the [relationship](../concepts/entity/schema-yml/relationships.md) to traverse. That one `join_name` binds **every** cross-entity reference in the expression. For a multi-step relationship, the features and metrics of *any* entity along the path's steps are reachable.

A feature must declare a `join_name` **unless** its `sql` references only the entity's own `identity` source (physical columns) and/or its own features. This rule is the single source of truth for when a `join_name` is required.

What a `join_name` exposes depends on the relationship's type: a **table relationship** joins physical tables, so the expression may read their physical columns (4+ segment paths); an **entity relationship** joins entities, so it may read their features and metrics (2-segment paths), never raw columns. So a raw column is reachable only on the entity's own `identity` table or through a table relationship; another entity's value is always its feature or metric, reached through an entity relationship.

## Examples

**A formula over the entity's own features.** No `join_name`: every reference is local.

```yaml
- name: discount_value
  description: Amount discounted off this order, in USD
  sql: order.gross_amount - order.net_amount
  data_type: number
```

**A cross-entity reference with a function and a metric.** On Grove's `customer`, pulls a windowed value across a relationship and divides by a metric on the related entity.

```yaml
- name: latest_subscription_share
  description: The customer's most recent subscription MRR as a share of their total
  sql: last(subscription.mrr, order_by=subscription.started_at) / metric(subscription.total_mrr)
  data_type: number
  join_name: customer_to_subscription
```

```yaml
# Filtered cross-entity reference — only iOS purchases count
- name: ios_spend_usd
  description: Net USD revenue from this player's iOS purchases
  sql: metric(purchase.sum_net_revenue_usd)
  data_type: number
  join_name: player_to_purchase
  filter: purchase.store = 'ios'
```

## Validation

- A 2-segment path is resolved as an entity-local semantic path (`entity.thing`); a 4+ segment path as a physical column. An ambiguous or malformed path is rejected.
- Templating or variable syntax anywhere in `sql:` / `filter:` (`{{ }}`, `{% %}`, `ref()`, macros) is rejected — expressions are literal SQL.
- A reference that names an entity in another domain is rejected — `sql` is same-domain only; bring the value in via [`imports`](../concepts/entity/schema-yml/identity-and-imports.md) and reference its local name.
- Every reference must be reachable through the declared `join_name` — the local entity plus the join's step entities. A reference to an entity not on the path fails.
- A `join_name` is required unless the `sql`/`filter` references only the entity's own identity source and/or its own features. A missing required `join_name` fails.
- Cross-entity references must point at a *declared* feature or metric on the target — not a raw column.
- A metric is referenced with `metric(entity.metric_name)`; a bare metric path is rejected. A feature is referenced bare.
- A 4+ segment physical path may read a column only on the entity's own `identity` table or on a table reached through a **table relationship**. A raw column reached through an **entity relationship** (another entity's column) is rejected — reference that entity's feature or metric instead.

## Related

- [Feature](../concepts/entity/schema-yml/feature.md) — the fields that carry `sql`, `join_name`, and `filter`
- [Metric](../concepts/entity/schema-yml/metric.md) — entity-local aggregations and `metric()`
- [Relationships](../concepts/entity/schema-yml/relationships.md) — what `join_name` points at
- [Lynk SQL](../api/lynk-sql.md) — the query dialect (distinct from this authoring grammar)
