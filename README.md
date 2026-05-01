# Lynk plugin marketplace

A Claude Code plugin marketplace for the [Lynk](https://docs.getlynk.ai) semantic layer. Install it to get skills that help you **build**, **edit**, **evaluate**, and **validate** a Lynk semantic graph in `.lynk/`.

## Install

### From GitHub (recommended)

```
/plugin marketplace add lynk-ai/build-agent
/plugin install lynk-semantic-layer@lynk
```

### From a local clone

```
/plugin marketplace add .
/plugin install lynk-semantic-layer@lynk
```

## What's inside

The marketplace exposes one plugin, `lynk-semantic-layer`, which ships four skills:

- **`lynk-build`** — add or edit entities, metrics, features, relationships, glossary, task instructions, clarification policy, output format, knowledge files, and domains in `.lynk/`.
- **`lynk-evaluate`** — judge whether a semantic layer is good enough for the AI agent: description quality, cross-file consistency, content placement, reference integrity, and SQL dialect compatibility. Owns the fix-and-recheck loop (capped at 3 attempts) and chains the backend validity check from `lynk-validate`.
- **`lynk-validate`** — run the Lynk backend's formal validity check (`POST /api/semantics/validate`) against a committed branch. Surfaces schema errors, broken source-field references, and other server-side issues. Requires `LYNK_API_TOKEN` in `.env`.
- **`lynk-sources`** — manage data sources via the Lynk API: list schemas, add a schema, sync sources, fetch a source's columns, and reconcile entity YAMLs when source columns change (delegates writes to `lynk-build`).

All four skills are model-invoked: describe what you want in natural language (for example, "add a `points_per_game` metric to the player entity", "evaluate my semantic layer", "validate on the inquiries branch", or "sync sources — I added fields to orders") and Claude will pick the right skill.

Reference documentation is fetched on demand from [docs.getlynk.ai](https://docs.getlynk.ai), so the plugin stays small and always points at the latest docs.

## Updating

```
/plugin marketplace update lynk
```

## Repo contents

- `.claude-plugin/marketplace.json` — marketplace catalog.
- `plugins/lynk-semantic-layer/` — the distributed plugin (manifest + skills).
- `.claude/skills/skill-creator/` — internal dev tooling used when authoring skills in this repo. Not part of the marketplace.
