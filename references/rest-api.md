# REST API

Internal reference for the Lynk REST API. Endpoints used by `lynk-sources`, `lynk-validate`, and `scripts/lynk_api.py`.

This file is intentionally not published on `docs.getlynk.ai` — the REST API is a skill-internal contract, not a user-facing surface. Keep it that way: customer-tenant identifiers, internal-only endpoints, and dev URLs all live here, not in public docs.

This reference is a work in progress. Endpoints, request/response shapes, and field semantics may change. Verify behavior against your tenant before depending on it in automation, and reach out to the platform team for changes you spot.

---

## Contents

Conventions (read once): [Base URL](#base-url) · [Authentication](#authentication) · [Standard request headers](#standard-request-headers) · [Response shape](#response-shape)

Endpoints:
- **Semantics** — `POST /semantics/builds` (used by `lynk-validate`, `lynk-evaluate`)
- **Integrations — Schemas** — `GET /integrations/data/schemas`
- **Data Catalog — Sources** — `GET /data-catalog/sources` · `GET /data-catalog/sources/{key_source}` · `POST /data-catalog/sources/sync` (used by `lynk-sources`, `lynk-build`)
- **Query Engine** — `POST /query-engine/query` (run Lynk SQL; used by `lynk-sources`, `lynk-evaluate`)
- [Related Reference](#related-reference)

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
| `422` | Request body or query failed validation. Body is `{detail: [{loc, msg, type, input}]}` for FastAPI input errors, or a domain-specific validation envelope (see `POST /semantics/builds`). |
| `5xx` | Server error — quote the message and retry. |

---

## Semantics

### `POST /semantics/builds`

Builds and validates the semantic layer on a committed branch against the Lynk backend. The backend pulls `origin/<branch>` at its current HEAD, parses every YAML / markdown file in `.lynk/`, runs a `LIMIT 0` probe against the warehouse for each feature, and returns a **build object** — a snapshot of the resolved semantic layer plus the validation issues the build surfaced. Surfaces schema errors (declarative checks against the YAML) and warehouse errors (engine rejected the test query).

**Builds are cached per `commit_sha`.** Until the branch advances, repeated calls with `force=false` return the cached build (HTTP `409`) rather than rebuilding. `force=true` discards the cache and rebuilds; use it when the *content of the warehouse* may have drifted (sources re-synced, columns added/dropped) without a new commit, since the cache key is the git commit, not the warehouse state.

**Headers:** `x-api-key`, `x-domain-name`. (`x-branch-name` is **not** read by this endpoint — branch comes from the query string. The header is harmless if sent.)

**Query parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `branch` | string | — (required) | The committed branch on origin to build. Must exist on `origin`; nonexistent branches currently return `500`. |
| `force` | boolean | `false` | When `true`, rebuild even if a build already exists for this `commit_sha`. When `false`, the backend returns the cached build with status `409` instead. |

**Request body:** none.

**Responses:**

There are three success-shaped paths — `200`, `422`, `409` — and each returns (or wraps) a **build object**. The client should treat all three as "I have a build result, surface its `status` and `validation_issues`."

`200 OK` — a fresh build completed and the layer is **valid**:

```json
{
  "id": "62f4aae1-fe8b-4613-a006-740a6e791af5",
  "tenant_id": "cae22df2-75e7-4250-8292-74c7e3eb1eba",
  "user_id": "U3D1r0DIU5XaroCwJZt57sZXju6Z",
  "user_email": "laila@getlynk.ai",
  "branch": "main",
  "commit_sha": "58ba295725ce636488c1c0729b92a8b1446fd559",
  "commit_date": "2026-06-07T10:58:00Z",
  "status": "valid",
  "error_message": null,
  "started_at": "2026-06-10T15:02:41.856101Z",
  "finished_at": "2026-06-10T15:02:50.245980Z",
  "created_at": "2026-06-10T15:02:41.856101Z",
  "updated_at": "2026-06-10T15:02:50.245980Z",
  "semantic_layer": { "entities": [...], "behavior_contexts": [...], "glossary_contexts": [...], "knowledge_task_contexts": [...], "instructions_task_contexts": [...] },
  "validation_issues": []
}
```

`422 Unprocessable Entity` — a fresh build completed and the layer is **invalid**. The build object sits at the **root of the body** (not wrapped in `detail` — that's the old `/validate` shape). `status` is `"invalid"`, and `validation_issues` is populated:

```json
{
  "id": "f0e71404-...",
  "branch": "poc__04-05-26",
  "commit_sha": "0ed9c8123fba085036344f21d6ed3f94e7ac47fc",
  "status": "invalid",
  "error_message": null,
  "semantic_layer": { "entities": [...] },
  "validation_issues": [
    {
      "entity_name": "activity_agg_daily",
      "related_entities": [],
      "items": [],
      "scope": "entity",
      "category": "warehouse",
      "severity": "error",
      "message": "Feature 'game_id' on entity 'activity_agg_daily' cannot be queried.",
      "suggestion": "Check that the feature's field/sql expression and any filter columns exist on the source table. If the feature is a formula or metric-feature, look at the features it transitively depends on — one of those may be the root cause.",
      "description": "### Query attempted\n\n```sql\nSELECT game_id FROM activity_agg_daily LIMIT 0\n```\n\n### Compiled warehouse query\n\n```sql\n...\n```\n\n### Engine error\n\n```\nExecutionError: ProgrammingError: ... column keys.game_id does not exist ...\n```",
      "location": {
        "file_path": ".lynk/default/entities/activity_agg_daily.yml",
        "line_number": null
      }
    }
  ]
}
```

`409 Conflict` — `force=false` and a build already exists for the branch's current `commit_sha`. The cached build is wrapped under `detail`. **It is not an error**; it's the normal idempotent path. The cached build carries its own `status` (could be `"valid"` or `"invalid"` — clients should always read it):

```json
{
  "detail": {
    "id": "53d43321-...",
    "branch": "main",
    "commit_sha": "58ba2957...",
    "status": "valid",
    "error_message": null,
    "finished_at": "2026-06-10T15:02:50Z",
    "semantic_layer": { ... },
    "validation_issues": []
  }
}
```

`500 Internal Server Error` — server-side failure. A branch that doesn't exist on origin currently surfaces here as well (empty body), as does any unexpected backend exception. Quote the message and retry.

**Build object fields:**

| Field | Type | Description |
|---|---|---|
| `id` | uuid | Build identifier (unique per build attempt). |
| `tenant_id` | uuid | Tenant the build belongs to. |
| `user_id`, `user_email` | string | Token owner that triggered the build. |
| `branch` | string | Branch the build ran against. |
| `commit_sha`, `commit_date` | string | The `origin/<branch>` HEAD commit at build time. |
| `status` | `"valid"` \| `"invalid"` | Whether the layer passed validation. `validation_issues` may still be non-empty when `valid` if there are only warnings. |
| `error_message` | string \| null | Catastrophic build failure (the build process itself crashed). For validation issues, see `validation_issues` — `error_message` is typically `null` even when `status: "invalid"`. |
| `started_at`, `finished_at`, `created_at`, `updated_at` | ISO-8601 UTC | Build timing. Use `finished_at` as the cache timestamp when reporting a `409` cached result. |
| `semantic_layer` | object | The fully resolved semantic layer the build produced (entities, contexts). Typically multi-hundred-kB; most clients ignore it. |
| `validation_issues` | array | The issues the build surfaced. Empty when `status: "valid"` with no warnings. |

**Validation issue fields:**

| Field | Type | Description |
|---|---|---|
| `entity_name` | string \| null | The entity the issue belongs to (null for relationship/context-level issues). |
| `related_entities` | string[] | Other entities involved (currently always empty in observed payloads). |
| `items` | array | Per-issue child items (currently always empty in observed payloads). |
| `scope` | `"entity"` \| `"relationship"` \| `"context"` | Which part of the layer the issue is about. |
| `category` | `"schema"` \| `"warehouse"` | `schema` = declarative check (missing description, malformed YAML, broken reference); `warehouse` = backend ran a `LIMIT 0` probe and the engine rejected it. The two split is useful in the fix path: `warehouse` issues are almost always YAML / table drift, while `schema` issues can be resolved from the YAML alone. (This replaces the prior `schema` / `semantic` split used by the legacy `/semantics/validate` endpoint.) |
| `severity` | `"error"` \| `"warning"` | Severity level. |
| `message` | string | Human-readable description of the issue. |
| `suggestion` | string \| null | A hint on how to fix the issue, when available. |
| `description` | string \| null | Rich markdown — present (and large, multi-kB) for `category: warehouse` errors. Contains three sections: `### Query attempted` (the Lynk SQL probe), `### Compiled warehouse query` (the engine-dialect SQL the backend ran), and `### Engine error` (the verbatim engine response, e.g. `column keys.game_id does not exist`). For other categories it is typically `null`. Clients should *not* paste it inline in summaries — surface its availability and render it only when the user asks. |
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
| `fieldsDeleted` | Columns removed. **If non-zero, downstream entity `schema.yml` files may reference columns that no longer exist** — check before further modeling. |
| `durationSeconds` | Wall time the sync took. |
| `message` | Human-readable summary. |

---

## Query Engine

Executes a Lynk SQL query against the semantic layer on a given branch + domain and returns rows from the warehouse. Used by `lynk-sources` for the "run this query" action and by `lynk-evaluate` for its warehouse probes (e.g. key uniqueness).

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

A bare `"Request failed"` 500 with no `detail` envelope means a backend exception the engine didn't translate — report it verbatim and check whether the branch's semantic layer itself is in a broken state (`POST /semantics/builds` on the same branch is a good next check).

**Caveats:**

- `SELECT * FROM <entity>` may return a generic 500 with no detail. Prefer explicit column lists — that's what canonical Lynk SQL looks like anyway.
- The endpoint runs the query against the actual warehouse on the branch — long queries take seconds to tens of seconds. For probe loops, wrap or append `LIMIT 1` so each call finishes fast.

---

## Related Reference

- [Lynk SQL](docs/api/lynk-sql.md) — the query syntax the agent uses, which you can also use directly.
