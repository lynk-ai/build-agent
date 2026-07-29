---
description: The frontmatter contract shared by every Markdown primitive, the reference grammar (@ injection, markdown links, bare paths), and how supporting files are organized.
icon: markdown
---

# Markdown Format

The shared rules for every Markdown file in a Lynk project: the frontmatter contract, the references that connect files (`@` injection, markdown links, and bare paths), and how supporting files are organized.

## What it is

Lynk's prose primitives — [`LYNK.md`](../concepts/lynk-md.md), [`ENTITY.md`](../concepts/entity/entity-md.md), [`SKILL.md`](../concepts/skill.md), [`POLICY.md`](../concepts/policy.md) — are Markdown files that share two mechanics:

- **Frontmatter** — a small, uniform YAML header. For the lazy-loaded primitives (entities and skills), the frontmatter is what the agent reads at index time to decide whether to load the file at all.
- **References** — `@` injection (eager content), plus markdown links and bare paths (navigation), connecting one file to another. File paths are absolute from the repo root (`/.lynk/…`).

Both are documented here once, so each primitive page can link here instead of repeating the rules.

## Where it lives

These rules apply to every `.md` primitive under `.lynk/` — root and domain `LYNK.md`, every `ENTITY.md`, `SKILL.md`, and `POLICY.md`. Paths and the overall tree are covered in [Layout and naming](./layout-and-naming.md).

## Format

### Frontmatter contract

`ENTITY.md`, `SKILL.md`, and `POLICY.md` carry the same frontmatter:

```yaml
---
name: orders                 # required — must match the folder name (charset per naming rules)
description: ...             # required — one-line summary
enabled: true               # optional — defaults to true
---
```

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | ✓ | string | Lowercase alphanumeric — entities use underscores; skills/policies may use hyphens or underscores. Must match the folder name (see [naming rules](./layout-and-naming.md#naming-rules)). |
| `description` | ✓ | string | One line. Load-bearing for lazy primitives — the agent indexes entities and skills by their `description` to decide relevance. |
| `enabled` | – | boolean | Defaults `true`. `false` removes the primitive from the build — see below. |

`LYNK.md` is the exception — it is pure prose with no required frontmatter. GitBook page frontmatter (`description`, `icon`) is separate from this contract and used only for the published docs site, not by the build.

**`enabled: false`** removes a primitive from the build without deleting it — for in-progress, deprecated, or experimental content. What "removed" means depends on the primitive:

- A [skill](../concepts/skill.md) is not loaded at all.
- An [entity](../concepts/entity/README.md) is disabled entirely. `enabled: false` on its `ENTITY.md` disables the **whole entity** — its `schema.yml` included — so it can't be queried, referenced, or imported. A reference to a disabled entity fails the build, exactly like a reference to one that doesn't exist.
- A [policy](../concepts/policy.md) that overrides a Lynk default falls back to Lynk's default.

### References

Files reference each other in three forms. All **file** paths are **absolute from the repo root, beginning `/.lynk/`** — there are no relative reference paths.

| Form | Syntax | What it does |
|---|---|---|
| `@` injection | `@glossary.mrr.description` · `@/.lynk/…` | Pulls content in and composes it into the prose, **eagerly** at load time. |
| Markdown link | `[text](/.lynk/…)` | A **navigation** target the agent can follow — not a substitution. |
| Bare path | `/.lynk/…` in prose | A navigation target written inline. |

**`@` injection** takes two path shapes:

*Conceptual paths* point at a primitive's field — usually `name` or `description` — and resolve in the host file's **own domain** (or the merged glossary):

```
@glossary.<term>.<field>          # the domain's merged glossary
@<entity>.<field>                 # an entity in the host file's domain
@<entity>.<sub>.<field>           # a feature/metric/relationship on that entity
```

The sub-primitive segment (`email` in `@customer.email.description`) is a feature, metric, or relationship name. Names are unique within an entity, so no type marker is needed.

*Whole-file injection* uses an absolute path:

```
@/.lynk/domains/core/entities/customer/ENTITY.md
@/.lynk/docs/onboarding.md
```

**`@` is eager; links and bare paths are not.** When the host file loads, everything it injects with `@` loads with it — the cost is the size of what's injected. Markdown links and bare paths don't inject anything; they're navigation the agent follows on demand. Keep host files lean and inject only what every use needs.

**Scope is topology-governed.** A file may reference its **own domain**, the **root [reference files](../concepts/reference-files.md)** (those at the `.lynk/` root, outside `domains/`), and — when a [shared domain](../concepts/lynk-yml.md#topology) is configured — that shared domain (conventionally `core`). With no shared domain set, a file reaches only its own domain and the root reference files. A reference to a peer domain fails the build. File references obey the same [topology](../concepts/lynk-yml.md#topology) as structured (`identity:`, `imports:`) references — topology is the single authority for what any file may reach.

### Supporting files

Beyond the required primary files, a primitive folder can hold any other files — examples, reference notes, longer instructions — organized however the author wants. They are not formal primitives; they are auxiliary content that a primary file injects with `@` when relevant.

```
.lynk/domains/core/entities/customer/
├── ENTITY.md
├── schema.yml
├── instructions/
│   └── closing-period.md
└── examples/
    └── refund-flows.md
```

## Examples

**Frontmatter only.** An entity with nothing worth flagging in prose: the frontmatter alone makes it loadable.

```markdown
---
name: subscription
description: Active and historical subscriptions. One row per subscription. Use for MRR, billing cycle, and cancellation analysis.
enabled: true
---
```

**Prose with injected supporting content.** Grove's `customer` entity injects a glossary term and a supporting file.

```markdown
---
name: customer
description: Grove accounts. One row per company. Use for ARR, churn, and plan-tier analysis.
enabled: true
---

# Customer

One row per company that has signed up. The team uses "customer" and "account" interchangeably.

**Conventions.** Most analyses exclude test accounts (`is_test_account = false`). "Churned" is defined in @glossary.logo_churn.description.

@/.lynk/domains/core/entities/customer/instructions/closing-period.md
```

## Validation

- `name` and `description` are present on every `ENTITY.md`, `SKILL.md`, and `POLICY.md`. A missing required field fails the build.
- `name` matches the folder name. Mismatches fail.
- Every reference resolves to an existing target — a known glossary term, a defined entity/feature/metric/relationship, or a real file. Dangling references fail.
- File reference paths are absolute (`/.lynk/…`); a relative reference path fails.
- References obey the project [topology](../concepts/lynk-yml.md#topology): a file may reach its own domain, the root reference files, and the shared domain when one is configured. A reference to a peer domain fails.
- A reference to a disabled entity fails the build (see `enabled`, above).
- Injection cycles fail the build — if A injects B and B injects A, the build rejects it rather than looping.

## Related

- [Layout and naming](./layout-and-naming.md) — the tree, folder rules, and the `enabled` flag
- [SQL expressions](./sql-expressions.md) — the reference grammar used inside `schema.yml` (a separate path syntax from `@`)
- [LYNK.md](../concepts/lynk-md.md) · [ENTITY.md](../concepts/entity/entity-md.md) · [Skill](../concepts/skill.md) · [Policy](../concepts/policy.md) — the primitives that use this contract
