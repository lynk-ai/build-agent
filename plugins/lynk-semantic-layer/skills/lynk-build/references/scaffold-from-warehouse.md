# Scaffold or update an entity from a warehouse table

Follow the Guardrails section in `../SKILL.md` for general rules (suggest-then-confirm, quality over presence, engine-aware SQL, scope to request).

This flow spans two phases of `SKILL.md`:

- **§Pre-flight** and **§Fetch** run **before** Step 5 (Plan and confirm).
- **§Write YAML** runs **during** Step 6 (Execute).
- **§Update flow** splits the same way — read + diff before plan, write after confirm.

The fetched schema and proposed YAML layout must appear in the plan the user confirms.

## Credentials

- `LYNK_API_KEY` and `LYNK_API_BASE_URL` live in `.env` at the workspace root.
- Ensure `.env` is in `.gitignore` before writing anything to it.
- Never echo the key in tool output or chat.

## Pre-flight (before plan & confirm)

- **Source changed?** Ask the user to sync first: UI → bottom-left user icon → Account → "Sync schemas now".
- **Credentials** — confirm `.env` has `LYNK_API_KEY` (session JWT, expires) and `LYNK_API_BASE_URL` (default `https://dev.app.getlynk.ai`). If missing or stale, ask the user to copy a fresh key: UI → right-click → Inspect → Network → refresh → click any request → Headers → Authorization → copy without `Bearer `.
- Ask for: `key_source`, entity name, and (for new entities) primary key.

## Fetch (before plan & confirm)

```bash
LYNK_API_KEY=$(grep '^LYNK_API_KEY=' .env | cut -d'=' -f2-)
LYNK_API_BASE_URL=$(grep '^LYNK_API_BASE_URL=' .env | cut -d'=' -f2-)
# On Windows, add --ssl-no-revoke if cert revocation checks fail.
curl -s \
  -H "Authorization: $LYNK_API_KEY" \
  "$LYNK_API_BASE_URL/api/data-catalog/sources/{key_source}"
```

Response: `source.id`, `source.columns[]` (`name`, `type`, `dataType`).

If curl returns 401 / 403 / any auth error, the session JWT has expired — ask the user to re-copy a fresh key per §Pre-flight, then retry. Do not echo the key to chat or tool output.

## Write YAML (during execute)

Fetch the entity-YAML spec on demand from the docs (navigate from `https://docs.getlynk.ai/concepts/` to the entity file-type spec). Then write to `.lynk/{domain}/entities/{name}.yml` (default domain = `default`) with:

- `key_source` = `source.id` (from the fetched response).
- `keys` = user-confirmed PK, or `[]` if the user hasn't confirmed.
- One `type: field` feature per column. **Mirror, don't remap:** copy the API `type` verbatim into `data_type`. Don't convert `string` to `datetime` for timestamp-looking columns unless the user asks.
- Descriptions: follow the Guardrails in `../SKILL.md` (suggest 1–2 options + "provide your own").

## Update flow (source table changed)

1. **Read** existing YAML (pre-plan).
2. **Fetch** current schema per §Fetch (pre-plan).
3. **Diff** by `field` name and include the diff in the plan:
   - **Added** — new `type: field` features. Follow the SKILL Guardrails for descriptions (suggest 1–2 options + "provide your own") before writing.
   - **Removed** — ask the user before deleting. Dependent formulas, metrics, first_last features, relationships, or evaluations may reference the removed field; git is the safety net if something breaks.
   - **Kept** — don't touch.
4. **After** the user confirms, write YAML (execute phase). Preserve existing feature order; append new features at the end.
5. **Report**: N added, M removed, K impacts.
