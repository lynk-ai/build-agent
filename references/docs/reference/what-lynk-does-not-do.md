---
description: The boundaries in one place — testing and evaluations, metric parameterization, templating, tags, scheduling, cross-domain queries — what Lynk doesn't do by design, what's planned, and what belongs upstream, with the supported alternative for each.
icon: ban
---

# What Lynk doesn't do

Every boundary of the model, in one place. Each entry states whether the
boundary is **by design**, **planned**, or **upstream's job** — and the
supported way to get the outcome. The owning page carries the full rule;
this page exists so "does Lynk support X?" has one home.

## By design

These are the model's load-bearing decisions. They will not change; asking
for them differently means using the supported alternative.

- **Metrics take no arguments.** No parameters, no per-call filters, no date
  ranges — `metric(entity.metric_name)` is the entire call. A parameter of
  the question goes in query-time `WHERE`; a different business definition is
  a second metric with its own `filter:`. → [Metric](../concepts/entity/schema-yml/metric.md)
- **No templating.** No Jinja, no variables, no macros anywhere in `sql:` —
  expressions are literal. → [SQL expressions](sql-expressions.md)
- **No unknown YAML keys.** The field tables are exhaustive; `tags:`,
  `meta:`, `time_grain:` or any other carried-over key fails the build.
  → [schema.yml](../concepts/entity/schema-yml/README.md)
- **No time grains on metrics.** Time grouping happens at query time via
  `GROUP BY`/`WHERE`, never in the definition. → [Metric](../concepts/entity/schema-yml/metric.md)
- **No query-backed identity.** An entity roots in a warehouse **table or
  view** (3 segments) or another entity — never an inline SQL query. If the
  grain doesn't exist, create a view or materialize a table upstream.
  → [Identity](../concepts/entity/schema-yml/identity-and-imports.md)
- **No same-domain imports.** Two entities in one domain are always
  independent; extension (`identity: <domain>.<entity>` + `imports`) is
  cross-domain only and requires a configured `shared_domain`.
  → [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md)
- **No renaming imports.** An imported definition keeps its name; expose a
  different name via a local feature whose `sql` references the import.
  → [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md)
- **No policy inheritance or merging.** Policies are per-domain; overriding
  a Lynk default fully replaces it. Share behavior across domains with a
  reference file injected via `@`. → [Policy](../concepts/policy.md)
- **No structured glossary pointers.** A term carries no link field to an
  entity or metric — its description prose must stand on its own.
  → [GLOSSARY.yml](../concepts/glossary.md)
- **No cross-domain queries.** A query runs against one domain of one build;
  cross-domain composition is a modeling decision (promote to the shared
  domain), not a query-time mode. → [Lynk SQL](../api/lynk-sql.md)
- **No writes from the query surface.** Lynk SQL is read-only — a single
  `SELECT`; the agent never creates tables or modifies data.
  → [Lynk SQL](../api/lynk-sql.md)

## Planned, not yet available

- **Evaluations — testing expected query results.** The build validates
  *structure* (definitions compile, references resolve), never result
  values. Tooling that asserts expected outputs for metrics and queries is
  planned; today there is no test file type, assertion syntax, or testing
  folder. → [Project](../concepts/project.md) · [Lynk SQL](../api/lynk-sql.md)

## Upstream's job

- **Materialization and refresh scheduling.** The layer defines query-time
  semantics against tables that already exist; creating a grain (snapshot
  tables, views) and refreshing it on a schedule happens upstream — dbt, a
  scheduled job, the warehouse itself.
  → [Modeling metrics, time, and state](../guides/metrics-time-and-state.md)
- **Storing data.** A project points at warehouse tables; it never contains
  or copies them. → [Project](../concepts/project.md)

## Related

- [Project](../concepts/project.md) — what a project is and is not
- [Metric](../concepts/entity/schema-yml/metric.md) · [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md) · [Policy](../concepts/policy.md) · [GLOSSARY.yml](../concepts/glossary.md) — the owning specs
- [SQL expressions](sql-expressions.md) · [Lynk SQL](../api/lynk-sql.md) — the grammars whose boundaries appear above
