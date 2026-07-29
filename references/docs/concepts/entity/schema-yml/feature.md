---
description: A feature is a queryable, row-grain attribute of an entity — a column, a derivation, or a value pulled across a relationship.
icon: tag
---

# Feature

A queryable, row-grain attribute of an [entity](../README.md) — a column, a derivation, or a value pulled across a [relationship](relationships.md).

## What it is

Features answer *"what is this attribute?"* at the entity's grain — one value per entity instance. Use a feature for row-level values; use a [metric](metric.md) when you need an aggregation across rows.

A feature's `sql` can be a direct column read, a formula over other features, a function call, or a value pulled from a related entity. The expression follows the [SQL expressions](../../../reference/sql-expressions.md) grammar — segment-counted paths, `metric()` / `first()` / `last()`, and the join-binding rule.

## Where it lives

`.lynk/domains/<domain>/entities/<entity>/schema.yml`, under `features:`.

## Format

**For any ratio, state the scale (`0–1` vs `0–100`) in the `description`, and keep every threshold in that scale** — a `0–1` value compared against `>= 55` is always false, and nothing errors.

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | ✓ | string | Unique within the entity across features, metrics, and relationships. |
| `description` | ✓ | string | Load-bearing — the agent reasons from it, so the `sql` must produce **exactly** what it describes. |
| `sql` | ✓ | SQL expression | The expression after `SELECT` that produces this value. [SQL expressions](../../../reference/sql-expressions.md) grammar. |
| `data_type` | ✓ | `number` \| `string` \| `datetime` \| `boolean` | The type of the resulting value. |
| `join_name` | conditional | string | A [relationship](relationships.md) name. Required unless `sql`/`filter` reference only the entity's own identity source and/or its own features — you never need a `join_name` to "join" an entity to itself. Anything reached through a relationship needs one. |
| `filter` | – | SQL predicate | A WHERE clause that narrows source rows *before* the `sql` evaluates. Grain-preserving. |

The full rule for when `join_name` is required, and how one `join_name` binds every cross-entity reference in the expression, lives in [SQL expressions → join binding](../../../reference/sql-expressions.md#join-binding).

## Examples

**A formula over the entity's own features.** No `join_name`: every reference is local.

```yaml
- name: discount_value
  description: Amount discounted off this order, in USD
  sql: order.gross_amount - order.net_amount
  data_type: number
```

**A value pulled across a relationship, combined with a metric.** On Grove's `customer`, the latest subscription's MRR as a share of the customer's total.

```yaml
- name: latest_subscription_share
  description: The customer's most recent subscription MRR as a share of their total
  sql: last(subscription.mrr, order_by=subscription.started_at) / metric(subscription.total_mrr)
  data_type: number
  join_name: customer_to_subscription
```

A few more shapes, for reference:

```yaml
# Direct column read — physical column on the entity's own identity table (no join_name)
- name: net_amount
  description: Order total after discounts and refunds, in USD
  sql: maindb.public.orders.net_amount
  data_type: number

# Physical column across a TABLE relationship — order_items is a table, not an entity,
# so the join_name reaches its raw columns directly
- name: primary_category
  description: Category of this order's highest-value line item
  sql: last(maindb.public.order_items.category, order_by=maindb.public.order_items.item_total)
  data_type: string
  join_name: order_to_items

# Cross-entity reference — semantic path through an ENTITY relationship
- name: customer_email
  description: Email of the customer who placed this order
  sql: customer.email
  data_type: string
  join_name: order_to_customer

# Filtered cross-entity reference
- name: ios_spend_usd
  description: Net USD revenue from this player's iOS purchases
  sql: metric(purchase.sum_net_revenue_usd)
  data_type: number
  join_name: player_to_purchase
  filter: purchase.store = 'ios'
```

## Validation

- `name` is unique within the entity (features, metrics, and relationships share one namespace).
- The `sql` computes what the `description` says, and the feature **compiles and field-probes at the Lynk build** — the authoritative surface where every column must resolve to real data. A raw-warehouse check alone is a proxy; fabricated values or columns fail the build.
- `data_type` is one of `number`, `string`, `datetime`, `boolean`.
- `join_name` is required unless `sql`/`filter` reference only the entity's own identity source and/or own features; a missing required `join_name` fails.
- Every reference in `sql`/`filter` is reachable through the declared `join_name` (the local entity plus the join's steps); what each relationship type exposes is the [SQL expressions → join binding](../../../reference/sql-expressions.md#join-binding) rule.
- Grammar errors are detailed in [SQL expressions → validation](../../../reference/sql-expressions.md#validation).

## Related

- Parent: [schema.yml](README.md) · [Entity](../README.md)
- Siblings: [Metric](metric.md) · [Relationships](relationships.md)
- [SQL expressions](../../../reference/sql-expressions.md) — the `sql` grammar and join binding
- [Lynk SQL](../../../api/lynk-sql.md) — how features appear as columns at query time
- Guides: [Modeling metrics, time, and state](../../../guides/metrics-time-and-state.md)
