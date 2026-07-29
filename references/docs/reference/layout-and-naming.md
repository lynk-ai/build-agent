---
description: The .lynk/ directory tree, the rules for naming folders and files, and the settings that control how a project is built.
icon: folder-tree
---

# Layout and Naming

The on-disk shape of a Lynk project: where every file lives, how folders and primitives are named, and the settings that govern the build.

## What it is

A Lynk project is a self-contained git repository. Everything the agent reads lives under a single `.lynk/` directory at the repo root. The shape is uniform: the same layout describes a project with one domain and a project with twelve. Adding a domain is adding a folder, never a restructure.

The layout is built from a small set of primitives that all share one folder-shape — a folder per item, a primary file inside, standard frontmatter. A builder who learns the shape once uses it everywhere: [entities](../concepts/entity/README.md), [skills](../concepts/skill.md), and [policies](../concepts/policy.md) all follow it.

This page is the reference for the tree and the naming rules. Each primitive's own page covers what goes *inside* its files.

## Where it lives

The semantic layer lives under `.lynk/` at the repo root. The root of that tree holds up to three files — `lynk.yml` (required) plus an optional root `LYNK.md` and `GLOSSARY.yml`; domains hang off `domains/`, and shared [reference files](../concepts/reference-files.md) can sit at the root alongside them.

```
.lynk/
├── lynk.yml            # project settings (required)
├── LYNK.md             # root orientation (the business)
├── GLOSSARY.yml        # root vocabulary
└── domains/
    └── <domain>/       # one folder per domain — the domain name IS the folder name
        ├── LYNK.md
        ├── GLOSSARY.yml
        ├── entities/
        │   └── <entity>/
        │       ├── ENTITY.md
        │       └── schema.yml
        ├── skills/
        │   └── <skill>/
        │       └── SKILL.md
        └── policies/
            └── <policy>/
                └── POLICY.md
```

The domain is derived **from the path** — the folder name under `domains/` is the domain's name. There is no `domain:` field to set anywhere.

## Format

### The three root files

| File | Required | Role |
|---|---|---|
| `lynk.yml` | ✓ | Project settings — see below. Governs how Lynk interprets the rest. |
| `LYNK.md` | – | Root [orientation](../concepts/lynk-md.md): who the business is. Applies to every domain. |
| `GLOSSARY.yml` | – | Root [vocabulary](../concepts/glossary.md). Merged into every domain. |

### `lynk.yml` settings

`lynk.yml` holds the project settings — `schema_version` (required), `topology`, and an optional `name`. The fields are documented in full on the [lynk.yml](../concepts/lynk-yml.md) page.

### Naming rules

| Rule | Applies to | Detail |
|---|---|---|
| Lowercase, alphanumeric, underscores | Domain & entity folders; feature / metric / relationship names | `core`, `player_game`, `total_points`. These appear in `sql:` references. |
| Lowercase, alphanumeric, hyphens or underscores | Skill & policy folders | `churn-investigation`, `output-format`. |
| `name` matches the folder | Every primitive with frontmatter | The `name` in `ENTITY.md` / `SKILL.md` / `POLICY.md` frontmatter must equal the folder name. |
| Primary file is uppercase | Every primitive | `ENTITY.md`, `SKILL.md`, `POLICY.md`, `LYNK.md` — fixed names, uppercase. `schema.yml` and `GLOSSARY.yml` are fixed too. |
| No reserved names | Domains | `core` is the conventional shared domain under medallion, but it is a convention, not a requirement. |

### `enabled`

Every entity, skill, and policy carries an optional `enabled` flag (defaults to `true`) in its frontmatter that removes it from the build without deleting it — useful for in-progress or deprecated content. The flag is part of the shared frontmatter contract; see [Markdown format → frontmatter contract](./markdown-format.md#frontmatter-contract) for what "removed" means per primitive.

## Examples

**One domain, one entity.** The smallest project worth querying: a single domain with one entity and a root `LYNK.md`.

```
.lynk/
├── lynk.yml
├── LYNK.md
└── domains/
    └── core/
        └── entities/
            └── customer/
                ├── ENTITY.md
                └── schema.yml
```

**A shared `core` plus a team domain (Grove, B2B SaaS).** Marketing builds its agent on top of `core`, with `core` set as the medallion `shared_domain` (see the `lynk.yml` below).

```
.lynk/
├── lynk.yml
├── LYNK.md
├── GLOSSARY.yml
└── domains/
    ├── core/
    │   ├── LYNK.md
    │   ├── GLOSSARY.yml
    │   ├── entities/
    │   │   ├── customer/
    │   │   │   ├── ENTITY.md
    │   │   │   └── schema.yml
    │   │   └── subscription/
    │   │       ├── ENTITY.md
    │   │       └── schema.yml
    │   └── policies/
    │       └── output-format/
    │           └── POLICY.md
    └── marketing/
        ├── LYNK.md
        ├── GLOSSARY.yml
        ├── entities/
        │   └── customer/          # marketing's view of core.customer (identity)
        │       ├── ENTITY.md
        │       └── schema.yml
        └── skills/
            └── attribution-analysis/
                └── SKILL.md
```

```yaml
# .lynk/lynk.yml
schema_version: "v2"
name: Grove
topology:
  pattern: medallion
  shared_domain: core
```

## Validation

- `lynk.yml` exists at the `.lynk/` root and declares `schema_version`. A missing or unreadable `lynk.yml` fails the build.
- Every primitive's `name` frontmatter matches its folder name. Mismatches fail.
- Domain and entity folders — and feature / metric / relationship names — are lowercase alphanumeric with underscores. Skill and policy folders may also use hyphens.

Beyond the layout itself, the build also warns when the project is below the [project minimum](../concepts/project.md#the-minimum-project) (a domain, an entity, a root `LYNK.md`) and on [empty domains](../concepts/domain/README.md#validation).

## Related

- [Project](../concepts/project.md) — the repo, the build lifecycle, and branches
- [lynk.yml](../concepts/lynk-yml.md) — the settings file in full
- [Markdown format](./markdown-format.md) — the shared frontmatter contract and `@` injection
- [Domain](../concepts/domain/README.md) · [Entity](../concepts/entity/README.md) · [Skill](../concepts/skill.md) · [Policy](../concepts/policy.md)
