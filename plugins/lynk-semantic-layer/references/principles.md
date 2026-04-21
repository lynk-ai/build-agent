# Principles for editing `.lynk/`

## Ask, don't assume

When a required input is missing or ambiguous, stop and ask. One extra question beats one wrong file.

## Never invent

- **Descriptions** — leave `description: ''` if the user didn't provide one. Don't infer from field names. On updates, ask the user for descriptions of newly-added fields before writing.
- **Primary keys** — never guess. Ask, or use `keys: []` as a placeholder.
- **Relationships / joins** — never infer. Ask for the join key and cardinality.
- **Metrics / SQL** — never author SQL the user didn't specify.

## Check quality, not just presence

A field isn't good just because it's non-empty. Flag or reject:

- Descriptions that repeat the field name (e.g. `country_code` → description `country_code`).
- Descriptions that are actually another column name (sign of a shifted spreadsheet paste).
- Placeholder text (`TODO`, `tbd`, `xxx`).
- Instruction or metadata fragments pasted in by mistake.
- One-word labels that restate the name without adding meaning or usage guidance.

In `lynk-build`: ask the user for a real description before writing. In `lynk-validate`: surface as a warning.

## Mirror, don't remap

When pulling types from an external source (e.g. the data-catalog API), copy `type` verbatim into `data_type`. Don't convert `string` to `datetime` for timestamp-looking columns unless the user asks.

## Scope to the request

Don't add sections the user didn't ask for. An "add entity" request writes the entity only — no metrics, relationships, or knowledge files unless requested.

## Credentials

- `LYNK_API_KEY` and `LYNK_API_BASE_URL` live in `.env` at the workspace root.
- Ensure `.env` is in `.gitignore`.
- Never echo the key in tool output or chat.

## Joins and relationships

- Never hardcode join SQL in `task_instructions`. Join definitions live in `.lynk/{domain}/entities_relationships.yml` or an entity's `related_sources`; task instructions may reference relationships by name only.
- See the Lynk docs (navigate from `https://docs.getlynk.ai/concepts/`) for the `entities_relationships.yml` vs `related_sources` distinction and the full join layout rules.

## Destructive edits

Before deleting or renaming anything in `.lynk/`, grep the whole layer for references (formula features, metric SQL, first_last features, `entities_relationships.yml`, `related_sources`, evaluations). Report every hit and ask how to proceed — remove dependents, rename, or abort.

## SQL must match the workspace engine

1. Read `.lynk/config.json` to determine the engine (e.g. `{"engine": "postgresql"}`). If missing, ask the user which engine the workspace targets.
2. Every SQL expression in `.lynk/` (entity metrics, formula features, metric / first_last filters, relationship join SQL) must be valid for that engine.
3. When validating, flag any engine-incompatible syntax.

## Lynk SQL call conventions

Call forms for `entity('name')`, `metric('name')`, `{feature_name}`, and the `{source}.{field}` / `{destination}.{field}` templates are specified in the Lynk docs (navigate from `https://docs.getlynk.ai/concepts/` to the lynk-sql reference).

**Docs correction:** the public lynk-sql reference sometimes shows `metric(name)` without quotes. That is incorrect — always pass a single-quoted string: `metric('name')`. Same for `entity('name')`.
