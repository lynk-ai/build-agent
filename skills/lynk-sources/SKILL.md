---
name: lynk-sources
description: >
  Manage data sources and schemas in your Lynk workspace via the API: list
  schemas, add a new schema, sync source-table metadata, fetch a source's fields,
  and reconcile entity YAMLs when source columns change.

  Use this skill whenever the user asks to: list schemas, see what tables/schemas
  exist, add a schema or table, sync sources, refresh source columns after a
  schema change, or clean up entity fields after a source update. Trigger
  phrases: "list schemas", "what schemas do I have", "add schema X", "add the
  orders table", "sync sources", "sync schemas", "I added fields to orders",
  "the source columns changed", "what fields does the orders table have",
  "clean up after the inquiries table dropped column referrer_id".

  This skill is read-and-API-only. When entity YAMLs need to be edited as a
  result (e.g., removing field features whose source column was dropped), it
  hands off to `lynk-build`.
---

# lynk-sources-semantics

## Steps

### 1. Determine the action

Classify the user's request to one of these actions:

| User intent | Action | Endpoint |
|---|---|---|
| "list schemas", "what schemas do I have" | List schemas | `GET /api/integrations/data/schemas` |
| "add schema X", "register the new schema" | Add schemas | `PUT /api/integrations/data/schemas` |
| "list tables", "list sources", "what tables do I have" | List sources | `GET /api/data-catalog/sources` |
| "what fields does X have", "show me the columns of X" | Fetch source fields | `GET /api/data-catalog/sources/<id>` |
| "sync sources", "the columns changed", "I added fields to X" | Sync sources | `POST /api/data-catalog/sources/sync` |
| "X dropped column Y, clean up the entity" | Reconcile entity | combo: sync + fetch fields + hand off to `lynk-build` |

If unclear, use `AskUserQuestion` to disambiguate. **Note**: a *schema* is a `DB.SCHEMA` scope (e.g., `MAINDB.PUBLIC`); a *source* is a single table inside that scope, with `id = DB.SCHEMA.TABLE` (e.g., `NETWORX_PROD.REPORTS.ACTIONS_ON_LEADS`).

### 2. Confirm the API token

The shared script `scripts/lynk_api.py` reads `LYNK_API_TOKEN` from `.env` at the project root. If missing, follow the same handshake `lynk-validate` uses:

```
! python scripts/lynk_api.py --print-setup
```

Ask the user via `AskUserQuestion`: **Set up the token now** (relay the script output, ask user to paste token in chat, then `LYNK_API_TOKEN='<paste>' python scripts/lynk_api.py --save-token`) or **Skip** (exit with `Operation not performed — no API token configured.`).

For branch-scoped operations, default to the current local branch (`! git rev-parse --abbrev-ref HEAD`); fall back to `main` if detached. Domain defaults to `default`.

### 3. Run the call

All endpoints accept `x-branch-name` and `x-domain-name` headers; pass them on every call. Add `--env dev` if the user said "on dev".

```
# List schemas → 200 {schemas: ["DB.SCHEMA", ...]}
! python scripts/lynk_api.py GET integrations/data/schemas \
    --header x-branch-name=<branch> --header x-domain-name=default

# Add schemas → 204 No Content. Body required: {schemas: ["DB.SCHEMA", ...]}.
# Idempotent — re-adding an existing schema also returns 204.
! python scripts/lynk_api.py PUT integrations/data/schemas \
    --header x-branch-name=<branch> --header x-domain-name=default \
    --data '{"schemas":["MAINDB.PUBLIC"]}'

# List sources (tables) → 200, paginated.
# {total_records, total_pages, current_page, assets: [{id, name, db, schema, keys, businessKeys, description, sourceType}]}
# id format: DB.SCHEMA.TABLE — that's the value to use as <key_source> below.
# Use --query page=N for pages beyond the first.
! python scripts/lynk_api.py GET data-catalog/sources \
    --header x-branch-name=<branch> --header x-domain-name=default

# Fetch one source's columns → 200
# {source: {id, name, db, schema, columns: [{name, description, type, dataType, nullable, defaultValue}]}}
# `type` is semantic (string / number / datetime / boolean / ...).
# `dataType` is engine-specific (TEXT / NUMBER / TIMESTAMP_NTZ / VARCHAR / ...).
! python scripts/lynk_api.py GET data-catalog/sources/<key_source> \
    --header x-branch-name=<branch> --header x-domain-name=default

# Sync sources → 200, synchronous (~10s for hundreds of tables). No body.
# {sourcesCreated, sourcesUpdated, sourcesDeleted, fieldsCreated, fieldsUpdated, fieldsDeleted, durationSeconds, message}
! python scripts/lynk_api.py POST data-catalog/sources/sync \
    --header x-branch-name=<branch> --header x-domain-name=default
```

### 4. Interpret the response

The script prints `{url, method, env, status_code, body}`.

- **List schemas (200)** — `body.schemas` is a flat list of `"DB.SCHEMA"` strings. Group them by `DB` for display and tell the user how many are registered.
- **Add schemas (204)** — empty body; report success with the schemas that were sent. If the user passed a schema that already exists, it's a no-op — clarify so they don't think a duplicate was created.
- **List sources (200)** — `body.assets[]` carries `id` (the `<key_source>`), `name`, `db`, `schema`, `keys`, `businessKeys`, `description`, `sourceType`. Use `body.total_pages` and `body.current_page` to decide whether to fetch more pages. For large tenants (200+ tables), filter client-side by `db` / `schema` based on what the user is asking about.
- **Fetch source fields (200)** — `body.source.columns[]` is the canonical column list. Each column has `name`, optional `description`, `type` (semantic), `dataType` (engine-specific), `nullable`, `defaultValue`. When grounding entity field features, prefer `dataType` for SQL casting and `type` for semantic intent.
- **Sync sources (200)** — surface the diff stats verbatim (e.g., *"212 tables synced; 2 fields created, 0 deleted"*). If `fieldsDeleted > 0`, immediately recommend the reconcile flow (Step 5) before any further modeling — entity features may point at deleted columns.
- **422 with `detail.[]` (FastAPI validation)** — quote the missing/invalid field path and adjust. For PUT schemas, `detail[0].loc=["body"]` with `msg="Field required"` means the `{schemas: [...]}` wrapper is missing.
- **401 / 403** — token issue; route to `lynk-validate` Step 4 token-handshake (`--print-setup`, `--save-token`).
- **404** on a source `<key_source>` — that `id` isn't in the list-sources response; the user may need to run sync first.

If the response shape is unexpected, show the raw body and ask the user how to proceed instead of guessing.

### 5. Reconcile entity YAML on source change

When the user said "I added/updated fields to X", "columns changed", or asked to clean up after a dropped column:

1. **Run sync first** (`POST /api/data-catalog/sources/sync`) so the catalog reflects the latest source state. If `body.fieldsDeleted > 0` you definitely need to reconcile; if 0 you may still want to surface added fields.
2. **Fetch current columns** via `GET /api/data-catalog/sources/<id>`.
3. **Find affected entity YAMLs** — entities sourcing from this table:
   ```
   ! grep -lrE "key_source:\s*<id>|source:\s*<id>" .lynk/
   ```
4. **Diff** the fetched `columns[]` against the entity's field features. Build a dependency tree of what each removed column impacts:
   - Field features whose `expression` references the removed column.
   - Formula features that compose from those field features.
   - Metrics that aggregate over removed features.
   - Relationships that join on removed columns.
   - Entity examples / evaluations referencing removed features or metrics.
5. **Show the dependency tree** to the user and confirm before any removals. New columns can be reported as informational — building features off them is a separate `lynk-build` request.
6. **Hand off the removal list to `lynk-build`** to execute the YAML edits. **Do not write .yml from this skill.** Build's own Step 8 will then run lynk-evaluate to surface any remaining issues.

## Output Format

- Always state the env (prod / dev) and branch on the summary line.
- For list and fetch responses, present results as compact bullet lists or tables grouped by schema or source.
- Quote API error messages verbatim — never paraphrase.
- For reconciliation, always show the full dependency tree before any removal, and always route writes through `lynk-build`.
