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

All endpoints accept `x-branch-name` and `x-domain-name` headers; pass them on every call. Add `--env dev` if the user said "on dev". For full request/response schemas, fetch `https://docs.getlynk.ai/api/data-catalog` on demand via `WebFetch`.

```
! python scripts/lynk_api.py GET integrations/data/schemas \
    --header x-branch-name=<branch> --header x-domain-name=default

! python scripts/lynk_api.py PUT integrations/data/schemas \
    --header x-branch-name=<branch> --header x-domain-name=default \
    --data '{"schemas":["MAINDB.PUBLIC"]}'

! python scripts/lynk_api.py GET data-catalog/sources \
    --header x-branch-name=<branch> --header x-domain-name=default

! python scripts/lynk_api.py GET data-catalog/sources/<key_source> \
    --header x-branch-name=<branch> --header x-domain-name=default

! python scripts/lynk_api.py POST data-catalog/sources/sync \
    --header x-branch-name=<branch> --header x-domain-name=default
```

`<key_source>` is the `id` field returned by the list-sources call (format: `DB.SCHEMA.TABLE`).

### 4. Interpret the response

The script prints `{url, method, env, status_code, body}`. Present results to the user concisely; consult `docs.getlynk.ai/api/data-catalog` for field-level detail when needed.

- **List schemas** — show how many are registered, grouped by `DB`.
- **Add schemas** — confirm what was registered. The call is idempotent; re-adding an existing schema is a no-op, not an error.
- **List sources** — paginated; use `--query page=N` for further pages. For large tenants, filter client-side by what the user asked about.
- **Fetch source fields** — show the column list; this is the canonical truth for that source.
- **Sync sources** — surface the diff stats verbatim. If `fieldsDeleted > 0`, recommend the reconcile flow (Step 5) before further modeling.
- **401 / 403** — token issue; route to `lynk-validate` Step 4 token-handshake (`--print-setup`, `--save-token`).
- **404** on a `<key_source>` — that `id` isn't in the list-sources response; the user may need to sync first.
- **4xx / 5xx otherwise** — quote the body's error message verbatim.

If the response shape is unexpected, show the raw body and ask how to proceed instead of guessing.

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
