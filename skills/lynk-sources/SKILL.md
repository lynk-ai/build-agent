---
name: lynk-sources
description: >
  Inspect the Lynk data catalog via the API and run ad-hoc Lynk SQL: list
  schemas and sources (tables), fetch a source's columns, sync the catalog to
  the warehouse, and reconcile entity `schema.yml` when source columns change.
  Read-and-API-only — hands off any `.yml` edits to `lynk-build`.

  Use to: list schemas/tables, model a new table (fetch its columns first),
  sync sources, refresh columns after a warehouse schema change, clean up after
  a dropped column, or run/test a Lynk SQL query. Triggers: "what tables do I
  have", "add the orders table", "sync sources", "columns changed", "run this
  query".
---

# lynk-sources

This skill owns the warehouse-facing workflow: it lists schemas and sources, fetches a source's columns, syncs the catalog, reconciles entity `schema.yml` files when source columns change, and runs ad-hoc Lynk SQL against the semantic layer. Other skills delegate to it whenever they need the warehouse side of the layer — `lynk-build` calls it before modeling a new table and to validate that referenced columns exist; `lynk-evaluate` flags a suspicious key and points here for warehouse confirmation (evaluate itself never queries). The data-catalog REST API is the transport; the workflow logic (reconcile flow, hand-off to `lynk-build` when columns drop, SQL execution) is what makes this a skill rather than a thin API wrapper.

## Steps

### 1. Determine the action

Classify the user's request to one of these actions:

| User intent | Action | Method | Route |
|---|---|---|---|
| "list schemas", "what schemas do I have" | List schemas | `GET` | `integrations/data/schemas` |
| "list tables", "list sources", "what tables do I have" | List sources | `GET` | `data-catalog/sources` |
| "what fields does X have", "show me the columns of X" | Fetch source fields | `GET` | `data-catalog/sources/<id>` |
| "sync sources", "the columns changed", "I added fields to X", "add the orders table" | Sync sources | `POST` | `data-catalog/sources/sync` |
| "X dropped column Y, clean up the entity" | Reconcile entity | — | combo: sync + fetch fields + hand off to `lynk-build` |
| "run this SQL", "test this query", "does this lynk SQL execute", "paste a SQL and run it" | Run Lynk SQL | `POST` | `query-engine/query` |

Routes above are bare — no `/api/` prefix, no leading `/`. The script prepends `/api/` itself, and a leading `/` gets mangled into a Windows path by Git Bash. `references/rest-api.md` shows full path-prefixed forms for documentation only — never pass those to the script.

If unclear, use `AskUserQuestion` to disambiguate. **These are the only supported operations** — if a request maps to none of them, tell the user it isn't a declared operation and stop; never hand the script an undeclared route. The error-time spec fetch in Step 4 is for diagnosing drift on a *declared* route (did its path or params change?), not for discovering new endpoints to call. **Note**: a *schema* is a `DB.SCHEMA` scope (e.g., `MAINDB.PUBLIC`); a *source* is a single table inside that scope, with `id = DB.SCHEMA.TABLE` (e.g., `MAINDB.PUBLIC.ORDERS`).

### 2. Confirm the API token

If `.env` does not have `LYNK_API_TOKEN` set, run:

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" --print-setup
```

Always invoke the script with its absolute path via `${CLAUDE_PLUGIN_ROOT}` — the script lives inside the plugin's install dir, not the user's repo, so a bare `scripts/lynk_api.py` won't resolve. The `"$(command -v python3 || command -v python)"` prefix picks whichever Python interpreter the user has, since some envs ship only one of the two binary names.

Ask the user via `AskUserQuestion`: **Set up the token now** (relay the script output, ask user to paste token in chat, then `LYNK_API_TOKEN='<paste>' "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" --save-token`) or **Skip** (exit with `Operation not performed — no API token configured.`).

### 3. Run the call

Use the method and route from the table in Step 1 — exactly as written, with no `/api/` and no leading `/`. Add `--env dev` if the user said "on dev". Branch and domain are resolved by the script (current git branch, `default` domain) — pass `--branch` or `--domain` only to override.

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" <METHOD> <route>
```

Concrete examples:

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" GET data-catalog/sources
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" GET data-catalog/sources/ANALYTICS.LYNK_VIEWS.ORDERS
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" POST data-catalog/sources/sync
```

**Run Lynk SQL** uses `--data` to pass the query — the body must be a JSON-encoded **string**, not an object. Single-quote the outer shell argument so the inner double quotes survive intact:

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" POST query-engine/query --data '"SELECT lead_id FROM lead LIMIT 1"'
```

For queries that span lines or contain special characters, write them to a file first and use `--data-file`:

```
! printf '%s' '"SELECT r.region_name, metric(o.total_revenue) AS total_revenue FROM orders o JOIN region r ON r.region_code = o.region_id WHERE o.created_date >= '"'"'2026-01-01'"'"' GROUP BY 1 LIMIT 1"' > /tmp/q.json
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" POST query-engine/query --data-file /tmp/q.json
```

If you don't know the request/response schema for the chosen route, read `references/rest-api.md` in this repo — that is the canonical endpoint reference for these skills. Do not fetch the public docs site for API details; the REST API spec is intentionally not published there.

`<id>` (used by the fetch-fields and per-source routes) is the `id` field returned by the list-sources call (format: `DB.SCHEMA.TABLE`).

### 4. Interpret the response

The script prints `{url, method, env, branch, domain, status_code, body}`. Present results to the user concisely. When you need field-level detail and the action table didn't fully cover it, read the relevant section of `references/rest-api.md`.

- **List schemas** — show how many are registered, grouped by `DB`.
- **List sources** — paginated (default 20 per page). The response carries `total_records`, `total_pages`, `current_page`, and the rows under `assets`. Page with `--query current_page=N`, and pull more per call with `--query items_per_page=150` (150 is the max). For large tenants, raise `items_per_page` and loop `current_page` up to `total_pages`, or filter by what the user asked about.
- **Fetch source fields** — show the table `description`, the catalog `keys`, the column count, and the column list; this is the canonical truth for that source. The `description`, `keys`, and count are what `lynk-build` needs to ground a new model and choose the entity key (`lynk-build` Step 5), so surface them, not just the columns. An empty `keys: []` means the catalog knows of no primary key — call that out, since it drives `lynk-build`'s key-verification loop.
- **Sync sources** — surface the diff stats verbatim. If `fieldsDeleted > 0`, recommend the reconcile flow (Step 5) before further modeling. If `sourcesCreated > 0` *or* the sync added new fields to an existing source, **actively offer to model the new content** via `lynk-build` using `AskUserQuestion` — don't just report it as informational. List the new sources / columns explicitly so the user can pick which to model now. If the user said "add the orders table", treat that as standing consent to model immediately and hand the column list off to `lynk-build`.
- **Run Lynk SQL** — on `200`, show row count and the first few rows; offer to show `metadata.query_metadata.rendered_sql` (the warehouse SQL the engine emitted) and `semantics_used` (which entities / features / metrics / relationships the engine resolved) when the user is debugging *why* a query returned what it did. On `422`, parse `detail`: if it's an array (FastAPI input error), the body shape was wrong — verify you JSON-encoded the SQL string; if it's an object with `error_type: SemanticsConsumptionError`, surface the `message` verbatim and point the user at the entity / feature it names. On `500`, parse `detail.error_type`: `InternalError` with `SQL error: ParserError(...)` is a Lynk-SQL syntax issue (quote the parser message); a bare `"Request failed"` string with no `detail` envelope means the branch's semantic layer is in a broken state — recommend running `lynk-validate` on the same branch before retrying.
- **401 / 403** — token issue; route to `lynk-validate` Step 4 token-handshake (`--print-setup`, `--save-token`).
- **404** on a `<id>` — that `id` isn't in the list-sources response; the user may need to sync first.
- **4xx / 5xx otherwise** — quote the body's error message verbatim.
- **Suspected API drift** — on a `404` (route not found) or a `422` that looks like a *param/shape* mismatch rather than a semantics error, fetch the service spec and compare: `GET <service>/openapi.json` (e.g. `data-catalog/openapi.json`, `query-engine/openapi.json`) resolves through the same script. Diff the route and query params you sent against the spec's `paths`; if they differ, that's the change — surface it and reconcile `references/rest-api.md` to the spec. Consult the spec only on such failures, never on every call.

If the response shape is unexpected, show the raw body and ask how to proceed instead of guessing.

### 5. Reconcile entity schema.yml on source change

When source columns change in the warehouse, entity `schema.yml` files that reference them silently break — features whose `sql` reads a dropped physical column will fail at query time, features and metrics that compose from those features will cascade, and relationship steps that join on them will stop resolving. This step closes that gap: detect the drift, walk the dependency tree, and hand the cleanup to `lynk-build`.

When the user said "I added/updated fields to X", "columns changed", or asked to clean up after a dropped column:

1. **Run sync first** (Step 3 sync action) so the catalog reflects the latest source state. If `body.fieldsDeleted > 0` you definitely need to reconcile; if 0 you may still want to surface added fields.
2. **Fetch current columns** (Step 3 fetch-fields action) for the affected source.
3. **Find affected schema.yml files** — entities rooted in this table (`identity:`) or reaching it through a physical path or table relationship:
   ```
   ! grep -lri "<id>" .lynk/ --include=schema.yml
   ```
   (`<id>` is the 3-segment `DB.SCHEMA.TABLE`; physical column references extend it to 4+ segments, so one case-insensitive grep catches identity, table-relationship targets, and column reads.)

   This physical-id grep does **not** catch cross-domain **extension** entities: an entity with `identity: <domain>.<entity>` plus `imports:` references the affected entity by entity-path, never by the physical table id (`references/docs/concepts/entity/schema-yml/identity-and-imports.md`). Once you know the removal list (step 4), grep each removed definition's entity-path (e.g. `core.customer.company_name`) across `.lynk/ --include=schema.yml` to find importers — they break by reference and must drop or replace the import in the same change.
4. **Diff** the fetched `columns[]` against the entity's features. Build a dependency tree of what each removed column impacts:
   - Features whose `sql` or `filter` references the removed physical column (4+ segment paths).
   - Features and metrics that compose from those features (entity-qualified references).
   - Relationship steps whose `sql` joins on removed columns, and features bound to them via `join_name`.
   - **Imported definitions** — any *other* entity whose `imports:` cherry-picks a feature or metric on this removal list (cross-domain extension); the importer breaks by reference until it drops or replaces the import (`references/docs/concepts/entity/schema-yml/identity-and-imports.md`).
   - **The `keys:` block** — if a removed column is a declared key (or part of a composite key), the entity's grain/identity contract breaks — more severe than a broken feature. Flag it prominently and treat re-establishing the grain (a new/composite key, or an upstream fix) as a prerequisite, not a routine removal.
   - Prose (`ENTITY.md`, skills) that `@`-injects or names the affected definitions.
5. **Show the dependency tree** to the user and confirm before any removals. **For new columns, actively offer to model them** via `lynk-build` using `AskUserQuestion` (e.g., *"3 new columns appeared in `inventory`: `restock_eta`, `supplier_tier`, `is_clearance`. Model them now as features? Yes / Defer / Skip the boolean"*). Don't just report new columns as informational — the user came here because of a source change, so offering to close the loop is the natural next step.
6. **Hand off the removal list to `lynk-build`** to execute the YAML edits. **Do not write .yml from this skill.** Build's own Step 8 will then run lynk-evaluate to surface any remaining issues.

## Output Format

- Always state the env (prod / dev) and branch on the summary line.
- For list and fetch responses, present results as compact bullet lists or tables grouped by schema or source.
- Quote API error messages verbatim — never paraphrase.
- For reconciliation, always show the full dependency tree before any removal, and always route writes through `lynk-build`.
