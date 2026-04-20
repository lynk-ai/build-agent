# Lynk plugin marketplace

A Claude Code plugin marketplace for the [Lynk](https://docs.getlynk.ai) semantic layer. Install it to get skills that help you **build**, **edit**, and **validate** a Lynk semantic graph in `.lynk/`.

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

The marketplace exposes one plugin, `lynk-semantic-layer`, which ships two skills:

- **`lynk-build`** — add or edit entities, metrics, features, relationships, glossary, task instructions, clarification policy, output format, knowledge files, and domains in `.lynk/`.
- **`lynk-validate`** — audit a semantic layer for correctness, completeness, and consistency. Produces a prioritized report of errors, warnings, and suggestions.

Both skills are model-invoked: just describe what you want in natural language (for example, "add a `points_per_game` metric to the player entity" or "validate my semantic layer") and Claude will pick the right skill.

Reference documentation is fetched on demand from [docs.getlynk.ai](https://docs.getlynk.ai), so the plugin stays small and always points at the latest docs.

## Updating

```
/plugin marketplace update lynk
```

## Repo contents

- `.claude-plugin/marketplace.json` — marketplace catalog.
- `plugins/lynk-semantic-layer/` — the distributed plugin (manifest + skills).
- `.claude/skills/skill-creator/` — internal dev tooling used when authoring skills in this repo. Not part of the marketplace.
