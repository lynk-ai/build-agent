---
description: The query dialect — warehouse SQL plus metric(<entity>.<name>) and USING('<join_name>'); entity references, joins, CTEs, windows, supported statements, pitfalls.
icon: database
---

# Lynk SQL

Lynk exposes a SQL interface for querying your semantic layer. The dialect is your warehouse's SQL with two engine-specific abstractions: `metric(<entity>.<name>)` for applying a pre-defined aggregation, and `USING('<join_name>')` for joining along a relationship defined in an entity's `schema.yml`. Everything else — `SELECT`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, CTEs, subqueries, window functions, every scalar and aggregate function your warehouse exposes — is standard SQL.

The agent uses this syntax internally when generating queries. As an engineer, you can also write it directly against a deployed build. (Evaluation tooling that consumes Lynk SQL as expected query outputs is planned, not yet available.)

---

## Single-domain scope

A query targets exactly one [domain](../concepts/domain/README.md). The domain is selected alongside the branch — in the UI, or carried on the connection. Every entity, feature, metric, and relationship the query references resolves within that one domain's world.

Cross-domain queries are not supported. A query that references an entity the active domain doesn't contain fails with a clear error rather than silently reaching into another domain. To combine concepts from different domains, model them in a shared domain (typically `core`) and query that domain — see [Domains](../concepts/domain/README.md).

---

## How it works

Lynk SQL is compiled into your warehouse's native SQL before execution. The engine resolves `metric()` calls to their aggregation expressions, expands `USING('<join_name>')` into the relationship's `ON` clause from `schema.yml`, and rewrites entity references to the underlying source tables. Everything else passes through to the warehouse.

Two consequences worth knowing:

- **The dialect is your warehouse's.** `FILTER (WHERE ...)` works on Postgres; `IFF()` and `QUALIFY` work on Snowflake; `PERCENTILE_CONT(...) WITHIN GROUP (...)` works on most modern warehouses. If your warehouse doesn't expose a function, neither does Lynk SQL.
- **Some constructs depend on how the engine emits SQL.** `WITH RECURSIVE`, for example, isn't supported on every engine because of how Lynk generates CTEs. If a construct fails compilation, fall back to a form the engine can express.

**Read-only.** Lynk SQL compiles to a single `SELECT` statement. `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and other DDL/DML are not supported.

---

## Entity references

Entities appear as identifiers in `FROM` and `JOIN` — no wrapper, no quoting. The engine resolves the entity to its underlying source table.

```sql
SELECT
  o.order_id,
  o.status,
  o.net_amount
FROM order o
WHERE o.status = 'completed'
ORDER BY o.order_date DESC
```

**Names in `SELECT` and `WHERE` are feature names from the entity's `schema.yml`, not raw warehouse columns — key columns included: `c.id` works only when `id` is a declared feature on `customer` ([keys are not features](../concepts/entity/schema-yml/identity-and-imports.md#identity-and-keys)).** One row is returned per entity instance — one row per order above. Aliases (`FROM order o`) work as in any SQL query.

---

## `metric(<entity>.<metric_name>)`

`metric()` applies a pre-defined [metric](../concepts/entity/schema-yml/metric.md) from an entity. The reference is entity-qualified — name the entity, then the metric. Use it anywhere a standard aggregate (`SUM`, `COUNT`, `AVG`) is legal — `SELECT`, `HAVING`, arithmetic expressions, CTEs, subqueries, window aggregates.

```sql
SELECT
  status,
  metric(order.count_orders)     AS count_orders,
  metric(order.sum_net_revenue)  AS sum_net_revenue
FROM order
WHERE order_date >= '2026-01-01'
GROUP BY status
ORDER BY sum_net_revenue DESC
```

**When the entity is aliased, the reference uses the alias:**

```sql
SELECT
  c.customer_tier,
  metric(c.total_arr) AS total_arr
FROM customer c
GROUP BY c.customer_tier
```

**Rules:**

- The argument is an entity-qualified metric path, unquoted: `metric(order.count_orders)`.
- When the entity carries an alias in the query, use the alias: `FROM customer c` → `metric(c.total_arr)`.
- Every `metric()` in the `SELECT` list must carry an alias: `metric(order.count_orders) AS count_orders`. Inside `HAVING`, `OVER(...)`, or a larger expression, no alias is needed — alias the surrounding select item instead.
- A metric is defined on the entity it aggregates. To aggregate from an entity other than the one you're selecting, push that aggregation into a CTE or subquery (see [CTEs and subqueries](#ctes-and-subqueries)).
- Apply `GROUP BY` to any non-aggregated features in the `SELECT` — same rule as standard SQL aggregates.

When the question needs the metric's logic over a filtered subset the metric definition doesn't capture, or combined with a non-aggregate expression, fall back to writing the aggregation manually.

---

## Joins

Lynk SQL supports the full set of standard SQL join types — `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL OUTER JOIN`, `CROSS JOIN`. Pick whichever the question requires. The join *condition* can be expressed in four forms:

| Form | Use when |
|---|---|
| `JOIN <entity>` (no `ON`, no `USING`) | The default relationship between the two entities is what you want. The engine uses the pair's single relationship, or the one marked `default: true` when several exist. |
| `JOIN <entity> USING('<join_name>')` | A named relationship exists in the entity's `schema.yml` and you want that specific one — typically because the pair has more than one relationship. |
| `JOIN <entity> USING(<common_feature_name>)` | Standard SQL: the two sides share a feature name and you want a join on equality of that column. The argument is an unquoted identifier, not a string literal. |
| `JOIN <entity> ON <expr>` | No relationship matches, you need extra predicates beyond the relationship's keys, or you're joining a CTE or subquery (where relationships don't apply). |

The two `USING` forms are distinguished by the argument: a **single-quoted string literal** names a relationship `join_name` from `schema.yml`; an **unquoted identifier** names a common column.

### Default join — no `ON`, no `USING`

When two entities have a single relationship defined (or one of several is marked `default: true`), join them by name alone. The engine fills in the `ON` clause from that relationship.

```sql
SELECT
  o.order_id,
  o.net_amount,
  c.email
FROM order o
LEFT JOIN customer c
WHERE o.status = 'completed'
```

### `USING('<join_name>')`

When the entity pair has more than one relationship, name the one you want with `USING()` and a string literal. The engine looks up the relationship by `join_name` and expands its `ON` clause at compile time.

```sql
SELECT
  p.player_id,
  s.duration_seconds
FROM player p
LEFT JOIN session s USING('player_to_meaningful_session')
WHERE p.country = 'US'
```

**Rules:**

- The `join_name` is a single-quoted string literal.
- This form is only valid for relationships predefined in `schema.yml`.
- `USING()` cannot be combined with additional predicates. `USING('rel') AND extra_predicate` is invalid — switch to a manual `ON` clause when you need extra filters baked into the join.

### `USING(<common_feature_name>)`

Standard SQL `USING` — the unquoted identifier names a feature that exists on both sides, and the engine joins on equality of that column.

```sql
SELECT
  p.player_id,
  s.duration_seconds
FROM player p
LEFT JOIN session s USING(player_id)
WHERE s.duration_seconds > 5
```

### `ON <expr>`

Use a manual `ON` clause when no relationship matches, when the join needs extra predicates, or when joining a CTE or subquery.

```sql
SELECT
  o.order_id,
  o.net_amount,
  c.email
FROM order o
LEFT JOIN customer c
  ON c.id = o.customer_id
 AND c.is_test_account = false
WHERE o.status = 'completed'
```

`ON` (or column-based `USING`) is the only join form available when one side is a CTE or subquery, since relationships are defined between entities, not against derived tables.

---

## CTEs and subqueries

CTEs (`WITH ... AS`) and subqueries are supported. Two situations make them useful:

1. **Applying a `metric()` to a filtered subset** the metric definition itself doesn't capture (e.g., the same metric over two distinct time windows in one query).
2. **Aggregating from an entity other than the one you're selecting** — isolate that entity in a CTE, aggregate there, and expose the value to the outer query.

```sql
WITH refunded AS (
  SELECT
    customer_id,
    metric(order.sum_net_revenue) AS refunded_revenue
  FROM order
  WHERE status = 'refunded'
    AND order_date >= '2026-01-01'
  GROUP BY customer_id
)
SELECT
  c.id,
  c.email,
  c.total_orders,
  r.refunded_revenue
FROM customer c
LEFT JOIN refunded r
  ON r.customer_id = c.id
```

Here `refunded` aggregates from `order` — a different entity than the `customer` we're selecting — and the outer query joins the result back by a plain `ON` clause.

**Joins to a CTE or subquery need a manual `ON` clause (or a column-based `USING(<column>)`): the relationship-name `USING('<join_name>')` and the no-clause default join work only between entities** — a derived table has no relationship to resolve.

Reach for a CTE when it earns its place — clearer grain transitions, isolating a filtered metric scope, or splitting a query into named stages. A CTE that exists because you *could* write one is just noise.

---

## Window functions and `QUALIFY`

Window functions are supported, and `metric()` can appear inside the window — both as the aggregated expression and inside `OVER (ORDER BY ...)`. The `QUALIFY` clause filters rows by a window function result, the way `HAVING` filters by an aggregate.

```sql
SELECT
  country,
  metric(player.count_players) AS count_players,
  DENSE_RANK() OVER (ORDER BY metric(player.count_players) DESC) AS country_rank
FROM player
GROUP BY country
QUALIFY country_rank <= 5
```

All standard window forms work: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `PERCENT_RANK`, `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`, aggregates as windows (`SUM(x) OVER (PARTITION BY ...)`), and `ROWS BETWEEN ... PRECEDING/FOLLOWING` frames.

---

## Set operations and subqueries

`UNION`, `UNION ALL`, `INTERSECT`, and `EXCEPT` are supported between any two Lynk SQL queries. Subqueries pass through as standard SQL — scalar subqueries in `SELECT`/`WHERE`/`HAVING`, `IN (subquery)`, and `EXISTS` / `NOT EXISTS`.

---

## SQL functions

Every scalar, aggregate, and window function your warehouse supports is available. Date math, string operations, conditional expressions, casts (`CAST`, `::`, `TRY_CAST`) — write them as you would in plain SQL. The engine only intercepts `metric()` and `USING('<join_name>')`; everything else passes through to the warehouse.

---

## Supported statements

| Statement | Supported |
|---|---|
| `SELECT` (incl. `DISTINCT`) | Yes |
| `FROM <entity>` | Yes |
| `JOIN <entity>` (default relationship) | Yes |
| `JOIN <entity> USING('<join_name>')` | Yes |
| `JOIN <entity> USING(<common_feature_name>)` | Yes |
| `JOIN <entity> ON <expr>` | Yes |
| `INNER` / `LEFT` / `RIGHT` / `FULL OUTER` / `CROSS JOIN` | Yes |
| `WHERE` | Yes |
| `GROUP BY` (including by position: `GROUP BY 1`) | Yes |
| `HAVING` (with `metric()` or raw aggregates) | Yes |
| `QUALIFY` (window-result filter) | Yes |
| `ORDER BY` (with `NULLS FIRST` / `NULLS LAST`) | Yes |
| `LIMIT` / `OFFSET` | Yes |
| CTEs (`WITH`) | Yes |
| `WITH RECURSIVE` | Engine-dependent |
| Subqueries (scalar, `IN`, `EXISTS`) | Yes |
| Window functions (`OVER`, `PARTITION BY`, `ROWS BETWEEN`) | Yes |
| Set operations (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`) | Yes |
| DDL / DML | No |

---

## Common pitfalls

**Querying across domains.** A query resolves within one domain. Referencing an entity the active domain doesn't contain fails — model shared concepts in `core` instead.

**Using raw warehouse table names.** Lynk SQL operates on entities. `FROM db_prod.core.orders` bypasses the semantic layer — write `FROM order` and let the engine resolve the table.

**Combining `USING('<join_name>')` with extra predicates.** `USING('rel') AND extra_predicate` is invalid. Switch to a manual `ON` clause when you need extra filters baked into the join.

**Using authoring-grammar functions.** `first()` and `last()` belong to the [`schema.yml` authoring grammar](../reference/sql-expressions.md#functions) and do not exist at query time — the engine intercepts only `metric()` and `USING('<join_name>')`; anything else passes through to the warehouse and fails. Use window functions and `QUALIFY` instead.

---

## Related reference

- [Metric](../concepts/entity/schema-yml/metric.md) — how metrics are defined and what `metric()` invokes
- [Feature](../concepts/entity/schema-yml/feature.md) — entity attributes referenced as columns
- [Relationships](../concepts/entity/schema-yml/relationships.md) — how `join_name` paths are defined and defaulted
- [SQL expressions](../reference/sql-expressions.md) — the authoring grammar inside `schema.yml` (distinct from this query dialect)
