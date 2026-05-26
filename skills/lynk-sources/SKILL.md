---
name: lynk-sources
description: >
  Inspect the Lynk data catalog via the API and reconcile entity YAMLs when
  source columns change: list registered schemas, list sources (tables), fetch
  a source's columns, sync the catalog against the warehouse, and clean up
  entity field features whose source columns were dropped.

  Use this skill whenever the user asks to: list schemas, see what tables/
  schemas exist, model a new table (fetch its columns first), sync sources,
  refresh source columns after a warehouse schema change, or clean up entity
  fields after a source update.

  Trigger phrases: "list schemas", "what schemas do I have", "add the orders
  table", "sync sources", "I added fields to orders", "the source columns
  changed", "what fields does the orders table have", "clean up after the
  inquiries table dropped column referrer_id".

  This skill is read-and-API-only on the catalog side. It hands off to
  `lynk-build` for any `.yml` edits it surfaces (e.g., removing field
  features whose source column was dropped).
---

# lynk-sources-semantics

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

Routes above are bare — no `/api/` prefix, no leading `/`. The script prepends `/api/` itself, and a leading `/` gets mangled into a Windows path by Git Bash. `references/rest-api.md` shows full path-prefixed forms for documentation only — never pass those to the script.

If unclear, use `AskUserQuestion` to disambiguate. **Note**: a *schema* is a `DB.SCHEMA` scope (e.g., `MAINDB.PUBLIC`); a *source* is a single table inside that scope, with `id = DB.SCHEMA.TABLE` (e.g., `MAINDB.PUBLIC.ORDERS`).

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

If you don't know the request/response schema for the chosen route, read `references/rest-api.md` in this repo — that is the canonical endpoint reference for these skills. Do not fetch the public docs site for API details; the REST API spec is intentionally not published there.

`<key_source>` (used by the fetch-fields and per-source routes) is the `id` field returned by the list-sources call (format: `DB.SCHEMA.TABLE`).

### 4. Interpret the response

The script prints `{url, method, env, branch, domain, status_code, body}`. Present results to the user concisely. When you need field-level detail and the action table didn't fully cover it, read the relevant section of `references/rest-api.md`.

- **List schemas** — show how many are registered, grouped by `DB`.
- **List sources** — paginated; use `--query page=N` for further pages. For large tenants, filter client-side by what the user asked about.
- **Fetch source fields** — show the column list; this is the canonical truth for that source.
- **Sync sources** — surface the diff stats verbatim. If `fieldsDeleted > 0`, recommend the reconcile flow (Step 5) before further modeling. If `sourcesCreated > 0` *or* the sync added new fields to an existing source, **actively offer to model the new content** via `lynk-build` using `AskUserQuestion` — don't just report it as informational. List the new sources / columns explicitly so the user can pick which to model now. If the user said "add the orders table", treat that as standing consent to model immediately and hand the column list off to `lynk-build`.
- **401 / 403** — token issue; route to `lynk-validate` Step 4 token-handshake (`--print-setup`, `--save-token`).
- **404** on a `<key_source>` — that `id` isn't in the list-sources response; the user may need to sync first.
- **4xx / 5xx otherwise** — quote the body's error message verbatim.

If the response shape is unexpected, show the raw body and ask how to proceed instead of guessing.

### 5. Reconcile entity YAML on source change

When source columns change in the warehouse, entity YAMLs that reference them silently break — field features whose `expression` points at a dropped column will fail at query time, formula features that depend on those fields will cascade, and metrics that aggregate over them will produce wrong results. This step closes that gap: detect the drift, walk the dependency tree, and hand the cleanup to `lynk-build`.

When the user said "I added/updated fields to X", "columns changed", or asked to clean up after a dropped column:

1. **Run sync first** (Step 3 sync action) so the catalog reflects the latest source state. If `body.fieldsDeleted > 0` you definitely need to reconcile; if 0 you may still want to surface added fields.
2. **Fetch current columns** (Step 3 fetch-fields action) for the affected source.
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
5. **Show the dependency tree** to the user and confirm before any removals. **For new columns, actively offer to model them** via `lynk-build` using `AskUserQuestion` (e.g., *"3 new columns appeared in `inventory`: `restock_eta`, `supplier_tier`, `is_clearance`. Model them now as features? Yes / Defer / Skip the boolean"*). Don't just report new columns as informational — the user came here because of a source change, so offering to close the loop is the natural next step.
6. **Hand off the removal list to `lynk-build`** to execute the YAML edits. **Do not write .yml from this skill.** Build's own Step 8 will then run lynk-evaluate to surface any remaining issues.

## Output Format

- Always state the env (prod / dev) and branch on the summary line.
- For list and fetch responses, present results as compact bullet lists or tables grouped by schema or source.
- Quote API error messages verbatim — never paraphrase.
- For reconciliation, always show the full dependency tree before any removal, and always route writes through `lynk-build`.
