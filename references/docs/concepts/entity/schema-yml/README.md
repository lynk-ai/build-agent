---
description: schema.yml is the structured definition of an entity — identity, keys, imports, features, metrics, and relationships.
icon: file-code
---

# schema.yml

The structured side of an [entity](../README.md). It defines what the entity *is* and what the agent can query on it — [identity](identity-and-imports.md), keys, [imports](identity-and-imports.md), [features](feature.md), [metrics](metric.md), and [relationships](relationships.md).

## What it is

`schema.yml` is what the agent reads to compose SQL: the columns and derivations it can select ([features](feature.md)), the aggregations it can apply ([metrics](metric.md)), and the paths it can traverse to other entities ([relationships](relationships.md)). Where [`ENTITY.md`](../entity-md.md) is prose the agent reads to understand the entity, `schema.yml` is structure the agent queries.

Everything rests on one rule: **grain is preserved by construction.** The entity always has exactly one row per base instance — `one_to_many` and `many_to_many` sources are handled through aggregation in [metrics](metric.md) or row-selection in [features](feature.md), never through references that would multiply rows. Joins default to LEFT; a [relationship](relationships.md) step can set its own `join_type` when needed.

## Where it lives

One per entity, alongside `ENTITY.md`:

```
.lynk/domains/<domain>/entities/<entity>/schema.yml
```

## Format

The top-level fields:

```yaml
identity: maindb.public.customers   # required — a physical table OR another entity
keys:                               # required when identity is a physical table; inherited otherwise
  - id

features: [...]
metrics: [...]
table_relationships: [...]
entity_relationships: [...]
imports: [...]                    # only when identity points at another entity
```

| Field | Required | Type | Page |
|---|---|---|---|
| `identity` | ✓ | path | [identity and imports](identity-and-imports.md) |
| `keys` | conditional | list | required when `identity` is a physical table; inherited when it's another entity — [identity and imports](identity-and-imports.md) |
| `imports` | – | object | only valid when `identity` is another entity — [identity and imports](identity-and-imports.md) |
| `features` | – | list | [feature](feature.md) |
| `metrics` | – | list | [metric](metric.md) |
| `table_relationships` | – | list | [relationships](relationships.md) |
| `entity_relationships` | – | list | [relationships](relationships.md) |

**One namespace.** Feature, metric, and relationship `name`s are unique within an entity, combined — a feature and a metric can't both be called `total_points`. The single namespace makes every reference unambiguous.

Expressions inside `sql:` and `filter:` follow the [SQL expressions](../../../reference/sql-expressions.md) grammar.

## Examples

**A standalone entity with one feature and one metric.**

```yaml
identity: maindb.public.orders
keys:
  - order_id

features:
  - name: net_amount
    description: Order total after discounts and refunds, in USD
    sql: maindb.public.orders.net_amount
    data_type: number

metrics:
  - name: count_orders
    description: Count of orders
    sql: COUNT(*)
    data_type: number
```

**An entity with a relationship feeding a cross-entity feature.** Grove's `customer` pulls total MRR from its subscriptions.

```yaml
identity: maindb.public.customers
keys:
  - id

features:
  # keys are not features — declared here because the relationship below joins on it
  - name: id
    description: Unique customer identifier
    sql: maindb.public.customers.id
    data_type: number

  - name: company_name
    description: The customer's company name
    sql: maindb.public.customers.company_name
    data_type: string

  - name: arr
    description: Annual recurring revenue for this customer, in USD
    sql: maindb.public.customers.arr
    data_type: number

  # cross-entity: pulled from subscription across the relationship, so it's a feature
  - name: total_mrr
    description: Total MRR across this customer's active subscriptions
    sql: metric(subscription.total_mrr)
    data_type: number
    join_name: customer_to_subscription

metrics:
  # local: aggregates this entity's own rows, so it's a metric
  - name: total_arr
    description: Total ARR across customers
    sql: SUM(customer.arr)
    data_type: number

entity_relationships:
  - name: customer_to_subscription
    description: Subscriptions belonging to this customer
    entity: subscription
    cardinality: one_to_many
    steps:
      - target: subscription
        join_type: left
        sql: customer.id = subscription.customer_id
```

Both sides of the step's join are declared features — `id` above, and `customer_id` on `subscription`'s own `schema.yml`. [Keys are not features](identity-and-imports.md#identity-and-keys); a step that references an undeclared column fails the build.

## Validation

- `identity` is present and valid; `keys` are authored when `identity` is a physical table — see [identity and imports](identity-and-imports.md#validation).
- The field tables are exhaustive — an unknown key anywhere in `schema.yml` (a `tags:`, `meta:`, or `time_grain:` carried over from another tool) fails the build. There is no dimension/measure split and no time grain on a metric; time grouping is a query-time `GROUP BY`.
- `name`s are unique across features, metrics, and relationships combined.
- Every feature and metric `sql` resolves to real columns **and compiles at the Lynk build** — the authoritative surface, not a raw-warehouse check (which is only a proxy and can be false-green). Unbacked columns or fabricated values fail the build.
- The feature/metric dependency graph is **acyclic** — no feature or metric may transitively depend on itself. A definition on entity A can reference one on B, and a definition on B can reference back into A — that's fine, as long as the *same* definition never reappears in the chain (`a.feature_a → b.feature_a → a.feature_a` is the illegal case). Break a cycle by sourcing the looping value from the entity's own columns.
- Each fact has **one home** — define it on the entity it belongs to and reference it elsewhere rather than restating it.
- Each sub-definition validates per its own page: [feature](feature.md#validation), [metric](metric.md#validation), [relationships](relationships.md#validation).

## Related

- [identity and imports](identity-and-imports.md) — what the entity is, and extending another entity
- [Feature](feature.md) · [Metric](metric.md) · [Relationships](relationships.md) — the sub-definitions
- [Entity](../README.md) — the folder and the `ENTITY.md` / `schema.yml` split
- [SQL expressions](../../../reference/sql-expressions.md) — the `sql:` grammar
