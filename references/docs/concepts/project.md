---
description: A Lynk project is a self-contained git repository — one repo, one customer — consumed as versioned, validated builds.
icon: box-archive
---

# Project

A Lynk project is a self-contained git repository: one repo, one project, one customer. It holds the entire semantic layer and is consumed as versioned, validated builds.

## What it is

A project is the unit of everything in Lynk. It contains the [domains](domain/README.md), [entities](entity/README.md), [skills](skill.md), and [policies](policy.md) that make up a customer's semantic layer. Multi-tenancy lives at the account level, not inside the project — a customer with genuinely independent business units (a holding company with separate analytics teams) has multiple projects, one per repo.

A project is **not**:

- the data warehouse — the layer points at tables, it doesn't contain them;
- the dashboard layer — skills describe reasoning, not pre-built charts;
- access control — governed elsewhere;
- the agent — the agent reads the project; it isn't part of it.

## Where it lives

A project is a git repository. The semantic layer lives under a `.lynk/` directory at the repo root, with `lynk.yml`, `LYNK.md`, and `GLOSSARY.yml` at the root of that tree, domains under `domains/`, and any shared [reference files](reference-files.md) at the root alongside them. The full shape is in [Layout and naming](../reference/layout-and-naming.md).

## Format

### Project settings

The project's settings live in [`lynk.yml`](lynk-yml.md) at the `.lynk/` root: `schema_version` (required), `topology`, and an optional `name`. These are settings *for* the semantic layer — they tell Lynk how to interpret the rest — not customer business content.

### Lifecycle

Projects are consumed as **versioned, validated builds**, never as live edits. The loop:

1. The customer edits the repo — locally, via the Lynk UI, or in a PR.
2. The customer pushes to a branch.
3. The push triggers a build.
4. The build validates the entire semantic layer.
5. If validation passes, the build deploys and becomes queryable.
6. If validation fails, the build doesn't deploy; the previous good build keeps serving.

Agents always reason against a deployed build of a specific branch — never against in-progress or unvalidated edits. When a user asks a question, that question is scoped to a branch's build and a single [domain](domain/README.md) inside it. The triple **domain + branch + build** addresses one queryable agent, which is why answers are reproducible.

The build validates *structure* — definitions compile, references resolve — never result values. Tooling that tests expected query results (evaluations) is planned, not yet available (see [Lynk SQL](../api/lynk-sql.md)).

### The minimum project

The smallest project that can be productively queried is one [domain](domain/README.md) with at least one [entity](entity/README.md), plus a `LYNK.md` with basic orientation. Below that, no agent has anything to reason about. Below-minimum projects pass validation with warnings; they just can't be queried usefully.

## Examples

**A single-domain project.**

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

**A project's `lynk.yml`.**

```yaml
# .lynk/lynk.yml
schema_version: "v2"
name: Grove
topology:
  pattern: medallion
  shared_domain: core
```

## Validation

The build validates the entire semantic layer as one unit; a project deploys only if validation passes. Validation covers, among other rules:

- `lynk.yml` exists and declares `schema_version`.
- Every primitive's `name` matches its folder (see [Layout and naming](../reference/layout-and-naming.md#validation)).
- Every cross-domain reference — in structured fields (`identity:`, `imports:`) and in `@`/file references — resolves and obeys the project [topology](lynk-yml.md#topology). (`sql:` is same-domain only, so it is never a cross-domain reference.)
- A project below the productive minimum (a domain, an entity, a `LYNK.md`) passes with **warnings**, not errors.

Each topic's own page lists the specific rules its build errors cite.

## Related

- [lynk.yml](lynk-yml.md) — the settings file
- [Domain](domain/README.md) — the agents a project contains
- [Entity](entity/README.md) — what a domain models
- [Layout and naming](../reference/layout-and-naming.md) — the on-disk shape
- Guides: [Evolving a live layer](../guides/evolving-the-layer.md)
