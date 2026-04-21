# Scaffold or update an entity from a warehouse table

Follow `../../../references/principles.md` for all guardrails (descriptions, PKs, mirroring, destructive edits, credentials).

This flow spans two phases of `SKILL.md`:

- **§Pre-flight** and **§Fetch** run **before** Step 5 (Plan and confirm).
- **§Write YAML** runs **during** Step 6 (Execute).
- **§Update flow** splits the same way — read + diff before plan, write after confirm.

The fetched schema and proposed YAML layout must appear in the plan the user confirms.

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
- `keys` = user-confirmed PK, or `[]` if the user hasn't confirmed (per `principles.md` §Never invent).
- One `type: field` feature per column; `data_type` mirrors the API `type` verbatim (per `principles.md` §Mirror, don't remap).
- Descriptions only if the user supplied them (per `principles.md` §Never invent).

## Update flow (source table changed)

1. **Read** existing YAML (pre-plan).
2. **Fetch** current schema per §Fetch (pre-plan).
3. **Diff** by `field` name and include the diff in the plan:
   - **Added** — new `type: field` features. Ask the user for descriptions before writing.
   - **Removed** — impact-check per `../../../references/principles.md` §Destructive edits, then ask before deleting.
   - **Kept** — don't touch.
4. **After** the user confirms, write YAML (execute phase). Preserve existing feature order; append new features at the end.
5. **Report**: N added, M removed, K impacts.
