# REST API

The Lynk REST API provides HTTP endpoints for managing your semantic layer and data catalog programmatically — running validity checks, registering schemas, syncing source metadata, and inspecting tables and columns without using the Lynk UI.

{% hint style="warning" %}
This reference is a work in progress. Endpoints, request/response shapes, and field semantics may change before general availability. Verify behavior against your tenant before depending on it in automation, and reach out to your Lynk account team for changes you spot.
{% endhint %}

---

## Base URL

```
https://app.getlynk.ai/api
```

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

Successful responses return JSON. The exception is `204 No Content` mutations (e.g. `PUT /integrations/data/schemas`), which return an empty body. Errors follow standard HTTP semantics:

| Status | Meaning |
|---|---|
| `200` | Success — body contains the operation's result. |
| `204` | Success — no body (used by mutations like `PUT /integrations/data/schemas`). |
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

### `PUT /integrations/data/schemas`

Registers one or more `DB.SCHEMA` scopes. Idempotent — re-adding an existing schema is a no-op.

**Headers:** `x-api-key`, `x-branch-name`, `x-domain-name`.

**Request body:**

```json
{
  "schemas": ["MAINDB.PUBLIC", "MAINDB.MARKETING"]
}
```

**Responses:**

`204 No Content` — registration succeeded (or was already present).

`422 Unprocessable Entity` — if the body is missing or malformed:

```json
{
  "detail": [
    { "type": "missing", "loc": ["body"], "msg": "Field required", "input": null }
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

## Related Reference

- [Lynk SQL](./lynk-sql.md) — the query syntax the agent uses, which you can also use directly.
- [Evaluations](../concepts/evaluations.md) — test cases that validate agent accuracy before pushing to production.
