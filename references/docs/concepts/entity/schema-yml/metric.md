---
description: A metric is an aggregation defined on the entity it aggregates — sum, count, average, conditional aggregates — invoked with metric().
icon: sigma
---

# Metric

An aggregation defined on an [entity](../README.md) — sum, count, average, conditional aggregate — anything that produces a single value across many rows.

## What it is

Where a [feature](feature.md) answers *"what is this attribute?"* at row grain, a metric answers *"across many rows of this entity, what's the aggregate?"*

A metric is **entity-local**. It is defined exactly once, on the entity whose rows it aggregates — `sum_net_revenue` lives on `order` because `order` is the entity whose rows it sums. Its `sql` references that entity's own features (entity-qualified) and **cannot** reference other entities; there is no `join_name` on a metric.

To use an aggregate across an entity boundary — `customer` wanting total revenue across all its orders — you don't define a metric on `customer`. You define a [feature](feature.md) on `customer` whose `sql` references the cross-entity metric path through a [relationship](relationships.md), and the engine handles the join and grain alignment. This keeps the agent's mental model simple: **metrics aggregate the current entity; everything else is a feature**, however it's computed underneath.

## Where it lives

`.lynk/domains/<domain>/entities/<entity>/schema.yml`, under `metrics:`.

## Format

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | ✓ | string | Unique across the **whole domain**, not just this entity — the domain's metric namespace is flat (see [Validation](#validation)). Also shares the entity's namespace with features and relationships. |
| `description` | ✓ | string | What the metric represents. The `sql` must compute **exactly** this — the agent reasons from the description, so a mismatch misleads every query. State the scale (e.g. `0–1` vs `0–100`) for any ratio. |
| `sql` | ✓ | aggregation expression | References this entity's features, entity-qualified. No cross-entity references. [SQL expressions](../../../reference/sql-expressions.md) grammar. |
| `data_type` | ✓ | `number` \| `string` \| `datetime` \| `boolean` | The type of the aggregated value. |
| `filter` | – | SQL predicate | A WHERE clause that narrows rows before the aggregation runs. |

### Invoking a metric

A metric is invoked with `metric(<entity>.<metric_name>)` — and that is the **entire** call. **A metric takes no arguments: no parameters, no per-call filters, no date ranges.** A differently-scoped aggregate is a *second* metric with its own `filter:`, or manual SQL at query time (see [Lynk SQL → CTEs](../../../api/lynk-sql.md#ctes-and-subqueries)).

- **Inside `schema.yml`** — a feature's `sql` can call `metric()` to compose with an aggregate (see [SQL expressions](../../../reference/sql-expressions.md#functions)).
- **At query time** — the agent writes `metric(<entity>.<metric_name>)` in Lynk SQL; when the entity is aliased, it uses the alias. Full rules in [Lynk SQL](../../../api/lynk-sql.md#metricentitymetric_name).

### Computing the right value

Two mistakes pass every structural check but still produce the wrong number, so they are called out here:

- **Aggregate ratios as a ratio of sums — never an average of per-row ratios.** A rate or percentage is `SUM(numerator) / NULLIF(SUM(denominator), 0)`. `AVG(per_row_pct)` weights every row equally and is wrong whenever the denominators differ — a career shooting % computed by averaging per-game percentages is off by exactly this.
- **State the scale and keep thresholds in it.** Say whether a ratio is `0–1` or `0–100` in the `description`, and write every comparison constant in that same scale. A `0–1` value compared against `>= 55` is always false.

## Examples

**A count.**

```yaml
- name: count_customers
  description: Count of customers
  sql: COUNT(*)
  data_type: number
```

**A conditional aggregate.** Counts churned customers without filtering the rest out.

```yaml
- name: churned_customers
  description: Count of customers who have churned
  sql: SUM(CASE WHEN customer.status = 'churned' THEN 1 ELSE 0 END)
  data_type: number
```

**An aggregate with a filter.** On Bly's `order`, revenue from completed orders only.

```yaml
- name: completed_revenue
  description: Net revenue from completed orders
  sql: SUM(order.net_amount)
  data_type: number
  filter: order.status = 'completed'
```

**A weighted ratio.** A percentage is a ratio of sums, not an average of per-row ratios.

```yaml
- name: completion_rate
  description: Share of orders completed, 0–1 (weighted by order count)
  sql: SUM(CASE WHEN order.status = 'completed' THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0)
  data_type: number
```

## Validation

- `name` is unique within the entity (features, metrics, and relationships share one namespace).
- `name` is unique across the **whole domain**, not just within its entity — a `player_game` and a `team_game` cannot both define a metric named `total_points`. References are always entity-qualified (`player_game.total_points`), so you'd expect that to disambiguate, but the domain's metric namespace is flat: the bare `name` must be globally unique. Give each a distinct name by prefixing its subject — `player_total_points`, `team_total_points`.
- The metric **compiles and field-probes at the Lynk build** — the authoritative surface where every column must resolve to real data. A raw-warehouse check alone is a proxy that can pass while the build fails; fabricated values or columns fail the build.
- Quality bars the build can't check — the `sql` matching the `description`, descriptions distinguishable enough for the agent to choose between similar metrics — live in [Modeling metrics, time, and state](../../../guides/metrics-time-and-state.md#the-bar).
- `sql` references only this entity's own features (entity-qualified); cross-entity references and `join_name` are not allowed on a metric.
- `data_type` is one of `number`, `string`, `datetime`, `boolean`.
- Grammar errors are detailed in [SQL expressions → validation](../../../reference/sql-expressions.md#validation).

## Related

- Parent: [schema.yml](README.md) · [Entity](../README.md)
- Siblings: [Feature](feature.md) — how cross-entity aggregates are exposed · [Relationships](relationships.md)
- [SQL expressions](../../../reference/sql-expressions.md) — `metric()` and the `sql` grammar
- [Lynk SQL](../../../api/lynk-sql.md) — invoking `metric()` at query time
- Guides: [Modeling metrics, time, and state](../../../guides/metrics-time-and-state.md)
