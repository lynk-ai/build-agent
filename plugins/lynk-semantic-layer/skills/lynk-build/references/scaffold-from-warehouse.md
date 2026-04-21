# Scaffold or update an entity from a warehouse table

Follow `principles.md` for all guardrails (descriptions, PKs, mirroring,
destructive edits, credentials).

## Pre-flight

- **Source changed?** Ask the user to sync first: UI → bottom-left user icon
  → Account → "Sync schemas now".
- **Credentials** — confirm `.env` has `LYNK_API_KEY` (session JWT, expires)
  and `LYNK_API_BASE_URL` (default `https://dev.app.getlynk.ai`). If missing
  or stale, ask the user to copy a fresh key: UI → right-click → Inspect →
  Network → refresh → click any request → Headers → Authorization → copy
  without `Bearer `.
- Ask for: `key_source`, entity name, and (for new entities) primary key.

## Fetch

```bash
LYNK_API_KEY=$(grep '^LYNK_API_KEY=' .env | cut -d'=' -f2-)
LYNK_API_BASE_URL=$(grep '^LYNK_API_BASE_URL=' .env | cut -d'=' -f2-)
curl -s --ssl-no-revoke \
  -H "Authorization: $LYNK_API_KEY" \
  "$LYNK_API_BASE_URL/api/data-catalog/sources/{key_source}"
```

Response: `source.id`, `source.columns[]` (`name`, `type`, `dataType`).
`--ssl-no-revoke` is Windows-only.

## Write YAML

Schema: https://docs.getlynk.ai/file-types-reference/file-types/entity-yaml.md
Path: `.lynk/{domain}/entities/{name}.yml` (default domain = `default`).

- `key_source` = `source.id`.
- `keys` = user-confirmed PK or `[]`.
- One `type: field` per column; `data_type` mirrors API `type`.

## Update flow (source table changed)

1. Read existing YAML.
2. Fetch current schema.
3. Diff by `field` name:
   - **Added** — new `type: field` features. Ask user for descriptions.
   - **Removed** — impact-check per `principles.md`, then ask before deleting.
   - **Kept** — don't touch.
4. Preserve existing feature order; append new features at the end.
5. Report: N added, M removed, K impacts.
