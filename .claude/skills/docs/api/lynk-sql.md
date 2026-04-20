# Lynk SQL

Lynk exposes a SQL interface for querying your semantic layer. The syntax is standard SQL with two additions: the `entity()` function for referencing entities, and the `metric()` function for applying predefined aggregation logic.

The agent uses this syntax internally when answering questions. As an engineer, you write it when authoring evaluation test cases — the `expected_output` field in an evaluation is a Lynk SQL query.

---

## `entity()`

`entity()` is used in the `FROM` clause to reference an entity. Think of it as the entity's table name.

```sql
SELECT
  company_name,
  plan_type,
  arr
FROM entity('customer')
WHERE status = 'active'
  AND is_test_account = false
ORDER BY arr DESC
```

One row is returned per entity instance — one row per customer in the example above. The field names in `SELECT` and `WHERE` are feature names as defined in the entity YAML, not raw warehouse column names.

---

## `metric()`

`metric()` applies a predefined metric from the entity's `metrics:` section. Use it like any aggregate function — `SUM()`, `COUNT()`, `AVG()` — but instead of writing the aggregation expression yourself, you reference the metric by name.

```sql
SELECT
  plan_type,
  metric(count_customers) AS customers,
  metric(total_arr)       AS arr
FROM entity('customer')
WHERE status = 'active'
  AND is_test_account = false
GROUP BY plan_type
ORDER BY arr DESC
```

`metric(total_arr)` here resolves to `SUM({arr})` as defined on the `customer` entity. The aggregation logic lives once in the entity definition and is reused in every query that references it.

When using `metric()`, apply `GROUP BY` to any non-aggregated features in the `SELECT` clause — same rule as standard SQL aggregate functions.

---

## Joining Entities

Join entities using the `JOIN` keyword. Lynk resolves the join using the relationship defined in `entities_relationships.yml`.

**Default join** — omit `ON` to use the default join for that entity pair:

```sql
SELECT
  c.company_name,
  c.plan_type,
  s.billing_cycle,
  s.status AS subscription_status
FROM entity('customer') c
JOIN entity('subscription') s
WHERE c.status = 'active'
  AND is_test_account = false
```

**Named join** — specify a join name with `ON` when more than one join path exists between two entities:

```sql
SELECT
  c.company_name,
  c.arr,
  metric(total_mrr) AS mrr_active
FROM entity('customer') c
JOIN entity('subscription') s ON customer_to_active_subscription
WHERE c.status = 'active'
  AND is_test_account = false
GROUP BY c.company_name, c.arr
```

The `ON` keyword here takes a join name — not a SQL expression. Join paths are defined in `entities_relationships.yml`. See [Relationships YAML Reference](../file-types/relationships-yaml.md) for how joins are defined and named.

`metric()` always applies to the main entity — the first entity in the `FROM` clause. Features from joined entities are accessed using standard dot notation (`s.billing_cycle`), but metrics are defined on the main entity only.

---

## Supported Statements

| Statement | Supported |
|---|---|
| `SELECT` | Yes |
| `FROM entity()` | Yes |
| `JOIN entity()` | Yes |
| `WHERE` | Yes |
| `GROUP BY` | Yes |
| `HAVING` | Yes |
| `ORDER BY` | Yes |
| `LIMIT` | Yes |
| CTEs (`WITH`) | No |
| DDL / DML | No |

CTEs are not supported by design. Aggregation logic belongs in entity metrics, not in the query layer — keeping it there makes it reusable and auditable across every query that touches that entity.

---

## Related Reference

- [Entities](../concepts/entities.md) — how entity metrics are defined
- [Relationships YAML Reference](../file-types/relationships-yaml.md) — how join paths are named and configured
- [Evaluations](../concepts/evaluations.md) — where `expected_output` queries are used
