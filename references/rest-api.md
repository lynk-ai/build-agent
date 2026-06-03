# REST API

Internal reference for the Lynk REST API. Endpoints used by `lynk-sources`, `lynk-validate`, and `scripts/lynk_api.py`.

This file is intentionally not published on `docs.getlynk.ai` — the REST API is a skill-internal contract, not a user-facing surface. Keep it that way: customer-tenant identifiers, internal-only endpoints, and dev URLs all live here, not in public docs.

This reference is a work in progress. Endpoints, request/response shapes, and field semantics may change. Verify behavior against your tenant before depending on it in automation, and reach out to the platform team for changes you spot.

---

## Base URL

| Environment | Base URL | When |
|---|---|---|
| Production | `https://app.getlynk.ai/api` | Default — used unless the user says "on dev" |
| Development | `https://dev.app.getlynk.ai/api` | When the user says "on dev" or `LYNK_ENV=dev` is set |

The `scripts/lynk_api.py` script picks the URL automatically: prod by default, dev when `--env dev` is passed or `LYNK_ENV=dev` is in `.env`. Skills should pass `--env dev` only when the user explicitly asks for dev — never default to it.

All paths in this reference are relative to the base URL.

## Authentication

Every request must include a Lynk-issued API token:

```
x-api-key: <your token>
```

Generate a token in the Lynk app: click your avatar (bottom-left corner) → **API tokens** → **Create token**. Tokens are tenant-scoped and long-lived.

## Standard request headers

Most endpoints accept (and several require) two additional headers that scope the request to a specific branch and domain of your semantic layer:

| Header | Required | Description |
|---|---|---|
| `x-api-key` | yes | Authentication token (above). |
| `x-branch-name` | yes for branch-scoped operations | The semantic-layer branch the call applies to (e.g., `main`, `inquiries`). |
| `x-domain-name` | yes for domain-scoped operations | The semantic-layer domain (typically `default`). |

## Response shape

Successful responses return JSON. Errors follow standard HTTP semantics:

| Status | Meaning |
|---|---|
| `200` | Success — body contains the operation's result. |
| `401` / `403` | Token missing, invalid, or expired. |
| `404` | Route or resource not found — check the path and that the resource exists. |
| `422` | Request body or query failed validation. Body is `{detail: [{loc, msg, type, input}]}` for FastAPI input errors, or a domain-specific validation envelope (see `POST /semantics/validate`). |
| `5xx` | Server error — quote the message and retry. |

---

## Semantics

### `POST /semantics/validate`

Validates the semantic layer on a committed branch against the Lynk backend. Surfaces schema errors, broken source-field references, and other server-side validity issues.

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Query parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `scope` | string | `all` | What to validate. `all` validates the full graph. |
| `fail_on_warnings` | boolean | `false` | Whether to treat warnings as failures in the response status. |

**Request body:** none.

**Responses:**

`200 OK` — when the layer is valid:

```json
{
  "status": "valid",
  "error_count": 0,
  "warning_count": 0,
  "issues": []
}
```

`422 Unprocessable Entity` — when the layer has issues. The validation envelope is wrapped in `detail`:

```json
{
  "detail": {
    "status": "invalid",
    "error_count": 6,
    "warning_count": 0,
    "issues": [
      {
        "entity_name": "order",
        "related_entities": [],
        "scope": "entity",
        "category": "semantic",
        "severity": "error",
        "message": "Entity 'order': Feature 'lifetime_value' sources from 'lead' but it is not reachable.",
        "suggestion": "Available sources: MAINDB.PUBLIC.ORDERS, MAINDB.PUBLIC.CUSTOMERS, customer.",
        "location": {
          "file_path": ".lynk/default/entities/order.yml",
          "line_number": null
        }
      }
    ]
  }
}
```

**Issue object fields:**

| Field | Type | Description |
|---|---|---|
| `entity_name` | string \| null | The entity the issue belongs to (null for relationship/context-level issues). |
| `related_entities` | string[] | Other entities involved (e.g., for relationship issues). |
| `scope` | `"entity"` \| `"relationship"` \| `"context"` | Which part of the layer the issue is about. |
| `category` | `"schema"` \| `"semantic"` | Whether the issue is structural (YAML/syntax) or semantic (references/joins). |
| `severity` | `"error"` \| `"warning"` | Severity level. |
| `message` | string | Human-readable description of the issue. |
| `suggestion` | string \| null | A hint on how to fix the issue, when available. |
| `location.file_path` | string | Path to the offending file inside `.lynk/`. |
| `location.line_number` | integer \| null | Line in the file, when known. |

---

## Integrations — Schemas

A *schema* in this API is a `DB.SCHEMA` scope that the data catalog tracks (for example, `MAINDB.PUBLIC` or `MAINDB.SALES`). Adding a schema makes its tables available as sources to model entities against.

### `GET /integrations/data/schemas`

Lists every `DB.SCHEMA` scope currently registered for the tenant.

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Request body:** none.

**Response:**

`200 OK`:

```json
{
  "schemas": [
    "DBT_DB.PUBLIC",
    "MAINDB.PUBLIC",
    "MAINDB.SALES",
    "SNOWFLAKE.CORE"
  ]
}
```

---

## Data Catalog — Sources

A *source* is a single table inside a registered schema. Its `id` has the format `DB.SCHEMA.TABLE` and is the value used as `{key_source}` when fetching column-level details.

### `GET /data-catalog/sources`

Lists every source (table) the catalog currently tracks. Paginated.

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Query parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number for pagination. |

**Response:**

`200 OK`:

```json
{
  "total_records": 212,
  "total_pages": 11,
  "current_page": 1,
  "assets": [
    {
      "id": "MAINDB.PUBLIC.ORDERS",
      "name": "ORDERS",
      "db": "MAINDB",
      "schema": "PUBLIC",
      "keys": [],
      "description": "",
      "sourceType": "asset"
    }
  ]
}
```

**Asset object fields:**

| Field | Type | Description |
|---|---|---|
| `id` | string | Fully qualified table identifier — `DB.SCHEMA.TABLE`. Use this as `{key_source}` for column-level calls. |
| `name` | string | Bare table name. |
| `db` | string | Database name. |
| `schema` | string | Schema name (within `db`). |
| `keys` | string[] | Primary key columns, when known. |
| `description` | string | Free-text description of the table. |
| `sourceType` | string | Catalog source type (`asset` for warehouse tables). |

### `GET /data-catalog/sources/{key_source}`

Fetches the full column list and metadata for a single source.

**Path parameters:**

| Name | Type | Description |
|---|---|---|
| `key_source` | string | The `id` returned by `GET /data-catalog/sources` — `DB.SCHEMA.TABLE`. |

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Response:**

`200 OK`:

```json
{
  "source": {
    "id": "MAINDB.PUBLIC.ORDERS",
    "name": "ORDERS",
    "db": "MAINDB",
    "schema": "PUBLIC",
    "keys": [],
    "description": "",
    "sourceType": "asset",
    "columns": [
      {
        "name": "OrderId",
        "description": null,
        "type": "string",
        "dataType": "TEXT",
        "nullable": false,
        "defaultValue": null
      },
      {
        "name": "PlacedAt",
        "description": null,
        "type": "datetime",
        "dataType": "TIMESTAMP_NTZ",
        "nullable": true,
        "defaultValue": null
      }
    ]
  }
}
```

**Column object fields:**

| Field | Type | Description |
|---|---|---|
| `name` | string | Column name as it appears in the source. |
| `description` | string \| null | Catalog description, if set. |
| `type` | string | Semantic type — `string`, `number`, `datetime`, `boolean`, etc. |
| `dataType` | string | Engine-specific type — `TEXT`, `NUMBER`, `TIMESTAMP_NTZ`, `VARCHAR`, etc. Use this for SQL casting. |
| `nullable` | boolean | Whether the column accepts `NULL`. |
| `defaultValue` | any \| null | Default value, when defined. |

`404 Not Found` — if `{key_source}` isn't in the catalog (run `POST /data-catalog/sources/sync` first).

### `POST /data-catalog/sources/sync`

Refreshes the data catalog by reading the latest schema state from the warehouse — picks up newly added tables, dropped tables, and column changes. Synchronous; typically completes in ~10 seconds for hundreds of tables.

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Request body:** none.

**Response:**

`200 OK`:

```json
{
  "sourcesCreated": 0,
  "sourcesUpdated": 212,
  "sourcesDeleted": 0,
  "fieldsCreated": 2,
  "fieldsUpdated": 9315,
  "fieldsDeleted": 0,
  "durationSeconds": 10.23,
  "message": "Successfully synced 212 tables across 2 schemas"
}
```

**Diff stat fields:**

| Field | Description |
|---|---|
| `sourcesCreated` | New tables discovered since the last sync. |
| `sourcesUpdated` | Tables whose metadata or column definitions changed. |
| `sourcesDeleted` | Tables removed from the warehouse since the last sync. |
| `fieldsCreated` | Columns added across all tables. |
| `fieldsUpdated` | Columns whose type, nullability, or description changed. |
| `fieldsDeleted` | Columns removed. **If non-zero, downstream entity YAMLs may reference columns that no longer exist** — check before further modeling. |
| `durationSeconds` | Wall time the sync took. |
| `message` | Human-readable summary. |

---

## Query Engine

Executes a Lynk SQL query against the semantic layer on a given branch + domain and returns rows from the warehouse. Used by `lynk-sources` for the "run this query" action and by `lynk-evaluate` to execute every `examples:` and `evaluations.yml` test case end-to-end.

### `POST /query-engine/query`

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`, `Content-Type: application/json`.

**Request body:** a JSON-encoded **string** containing the Lynk SQL — not an object. The endpoint expects a bare string at the top level.

```json
"SELECT lead_id FROM lead LIMIT 1"
```

Wrapping the SQL in an object (`{"query": "..."}` or `{"sql": "..."}`) returns 422 with `loc: ["body"], type: "string_type"`.

**Responses:**

`200 OK` — the query executed successfully:

```json
{
  "data": [
    { "LEAD_ID": 18674481 }
  ],
  "metadata": {
    "execution_metadata": {
      "query_duration_ms": 4222,
      "executed_by": "",
      "executed_at": "2026-05-26T09:23:09.681924Z"
    },
    "query_metadata": {
      "rendered_sql": "WITH lynk__cte_lead AS (...) SELECT lead_id FROM lynk__cte_lead lead LIMIT 1",
      "semantics_used": {
        "entities":      ["lead"],
        "features":      [{ "name": "lead_id", "entity": "lead" }],
        "metrics":       [],
        "relationships": [],
        "sources":       ["networx_prod.reports.leads_story_view"]
      }
    }
  }
}
```

**Response object fields:**

| Field | Description |
|---|---|
| `data` | Array of row objects. Column names use the warehouse's casing (e.g., `LEAD_ID` on Snowflake). |
| `metadata.execution_metadata.query_duration_ms` | End-to-end wall time, ms. |
| `metadata.execution_metadata.executed_by` | Identity that ran the query (empty for API-token calls). |
| `metadata.execution_metadata.executed_at` | ISO-8601 UTC timestamp. |
| `metadata.query_metadata.rendered_sql` | The warehouse-dialect SQL the engine actually executed — useful when debugging why a Lynk SQL query returned unexpected rows. |
| `metadata.query_metadata.semantics_used` | Which entities, features, metrics, relationships, and source tables the engine resolved for this query. Use this to verify the query touched what you expected. |

`422 Unprocessable Entity` — body shape error or semantic-layer error (missing feature, unresolvable reference). Two sub-shapes:

```json
{
  "detail": [
    { "type": "string_type", "loc": ["body"], "msg": "Input should be a valid string", "input": { "query": "SELECT 1" } }
  ]
}
```

```json
{
  "detail": {
    "error_type": "SemanticsConsumptionError",
    "error_code": "42P01",
    "message": "SemanticsConsumptionError: Feature 'nonexistent_field' does not exist in entity 'lead'. Dependency path: lead.nonexistent_field"
  }
}
```

`500 Internal Server Error` — SQL parser errors or warehouse errors. Structured:

```json
{
  "detail": {
    "error_type": "InternalError",
    "error_code": "XX000",
    "message": "SQL error: ParserError(\"Expected: an SQL statement, found: SELEC at Line: 1, Column: 1\")"
  }
}
```

A bare `"Request failed"` 500 with no `detail` envelope means a backend exception the engine didn't translate — report it verbatim and check whether the branch's semantic layer itself is in a broken state (`POST /semantics/validate` on the same branch is a good next check).

**Caveats:**

- `SELECT * FROM <entity>` may return a generic 500 with no detail. Prefer explicit column lists in evaluations and examples — that's what canonical Lynk SQL looks like anyway.
- The endpoint runs the query against the actual warehouse on the branch — long queries take seconds to tens of seconds. For evaluation loops, wrap or append `LIMIT 1` so each test case finishes fast.

---

## Related Reference

- [Lynk SQL](./lynk-sql.md) — the query syntax the agent uses, which you can also use directly.
- [Evaluations](../concepts/evaluations.md) — test cases that validate agent accuracy before pushing to production.
