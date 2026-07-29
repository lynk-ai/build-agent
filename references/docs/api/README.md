---
description: The programmatic interfaces — the Lynk SQL query dialect and the REST endpoints for validation and catalog inspection.
icon: plug
---

# API Reference

**Interfaces for querying and inspecting your Lynk semantic layer.**

This section documents the programmatic interfaces exposed by Lynk — how to write queries against your semantic layer, and how to call Lynk's HTTP endpoints to validate the semantic layer and inspect the data catalog.

---

## What's in this section

| Page | What it covers |
|---|---|
| [Lynk SQL](lynk-sql.md) | The SQL dialect the agent uses internally — single-domain scope, entity references, `metric(<entity>.<metric_name>)`, joins (default, `USING('<join_name>')`, `USING(<common_feature_name>)`, `ON`), CTEs, supported statements |
| [REST API](rest-api.md) | HTTP endpoints for validating the semantic layer and inspecting the data catalog (tables and columns) |

---

**Where to go next:**
- Need to understand how entities and metrics are defined? → [Entity](../concepts/entity/README.md)
- Want the authoring grammar behind `sql:` fields? → [SQL expressions](../reference/sql-expressions.md)
