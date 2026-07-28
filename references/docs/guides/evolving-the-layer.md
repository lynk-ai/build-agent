---
description: How to change a live semantic layer — logging definition changes, renaming a shared feature or metric safely, deprecating with enabled false, and landing breaking changes across domains.
icon: timeline
---

# Evolving a live layer

Decide how to change a definition that others already rely on — without silently changing their answers.

## When you need this

- A metric's `sql` needs correcting and the numbers will move.
- You want to rename a feature or metric in a shared domain that other domains import.
- You're retiring or pausing an entity and aren't sure who references it.
- Someone asks "why is this number different from last month?"
- A breaking change in `core` has to land without stranding the leaf domains.

## The principle

The build validates the whole layer as one unit, so *structural* breakage — a dangling import, a reference to a disabled entity — surfaces at the next build, never at query time. What the build cannot see is *meaning*: a `sql` change under a stable name, a description drifting from its computation. So split the work accordingly: let the build catch structure — make breaks loud and fix them in the same change — and catch meaning yourself, with a changelog entry and a re-verified description on every consequential definition change.

## Patterns

### Keep a definition changelog

A metric's meaning can change even when its name doesn't — a denominator is corrected, a filter is added, a scale is fixed. When a number moves, the team needs to know why. Keep a short record of consequential definition changes: **what changed, when, and why.**

- It answers "why is this number different from last month?" without a forensic dig.
- It lets you re-run the value checks that guarded the old definition, so an already-fixed correctness bug doesn't silently regress.

A changelog is a maintenance record, not a schema primitive — keep it wherever the team already tracks change (a `CHANGELOG` file in the project, commit messages, or a supporting doc), close to the layer it describes. When Grove corrects `churn_rate` to exclude test accounts from the denominator, the entry says so — and next quarter, the check that caught the original bug can run again against the new definition.

### Rename with add → migrate → remove

There is no rename mechanism. [Imports are by reference](../concepts/entity/schema-yml/identity-and-imports.md), and an imported feature keeps its name — to expose one under a different name, you define a local feature whose `sql` references it. So renaming `total_arr` on `core.customer` breaks every extending entity's `imports` at their **next build** — loudly, not silently at query time. That's the safety net; work with it:

1. **Add** the new name on the parent (its `sql` can reference the old definition, so there's one computation).
2. **Migrate** consumers — point each importing entity and each `sql` reference at the new name.
3. **Deprecation window** — both names live; the changelog marks the old one deprecated.
4. **Remove** the old name. Any straggler you missed fails the next build, which is the point.

When Grove renames `core.customer.total_arr` to `arr_usd`, marketing's `customer` keeps building through steps 1–3 and its import line changes once, in a PR marketing can review.

### Deprecate with `enabled: false` — for drafts, not for hiding

`enabled: false` on an `ENTITY.md` disables the **whole entity** — `schema.yml` included — and every reference to it [fails the build like a reference to a missing entity](../reference/markdown-format.md#frontmatter-contract). That makes it the right tool for in-progress or experimental work: Arcadia can land a half-built `player_cohort_v2` with `enabled: false` and iterate without it being queryable or referenced.

It is the wrong tool for soft-hiding something others import — flipping the flag doesn't hide the entity, it breaks every consumer's build. To retire something shared, treat it as a removal: migrate importers first (previous pattern), then disable or delete.

### Coordinate breaking changes across domains

When a breaking change lands in the shared domain, make it in one PR and let the build enumerate the damage: [the build validates the entire semantic layer as one unit](../concepts/project.md#validation), so every leaf entity whose import or reference breaks fails *that* build, with the failures listed. Fix the leaf imports in the same PR. The layer is never deployed half-migrated — validation gates the deploy, and the previous good build keeps serving until the whole change passes.

## Anti-patterns

### Silent redefinition

**Wrong:** changing `churn_rate`'s `sql` — adding a filter, fixing a denominator — while its `name` and `description` stay as they were.

**Why it fails:** nothing errors. The build checks that the sql compiles and its columns resolve, not that it still computes what the description says. Every consumer's mental model is now wrong, dashboards shift with no recorded cause, and the description actively misleads the agent on every query ([Metric](../concepts/entity/schema-yml/metric.md) makes the description the agent's source of truth).

**Fix:** the changelog entry and the description update ship in the same edit as the `sql` change. If the description didn't need to change, say so explicitly in the changelog — that's the re-verification.

### The meaning-shift rename

**Wrong:** reusing an existing name for a different computation — repointing Bly's `sum_net_revenue` at `gross_amount` because "that's what the exec team means by revenue."

**Why it fails:** every existing query, feature `sql`, and import that references the name keeps compiling and now silently computes something else. A name in a live layer is a contract with everyone who ever read it.

**Fix:** a different computation gets a different name (`sum_gross_revenue`), a description that discriminates it from the old one, and — if the old one is retiring — the add → migrate → remove path.

### Disable-without-checking

**Wrong:** setting `enabled: false` on `core.customer` to "pause" it while other domains extend or reference it.

**Why it fails:** a disabled entity behaves exactly like a missing one — marketing's `identity: core.customer` and every `imports` line under it fail at their next build. You've turned a pause into an outage for every downstream domain.

**Fix:** enumerate importers and references first (the build will list them if you're unsure — disable on a branch and read the failures). Migrate them, then disable.

## The bar

- Every consequential definition change has a changelog entry: what changed, when, why.
- No `sql` change ships without its `description` re-verified against the new computation.
- Renames follow add → migrate → remove; no name is ever reused for a different computation.
- Before `enabled: false` or deletion on anything shared, importers are enumerated and migrated.

## Related

- [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md) — why imports break loudly and renames need the migration path
- [Project](../concepts/project.md) — the build/validate/deploy lifecycle that gates every change
- [Markdown format](../reference/markdown-format.md) — the `enabled` flag and what "disabled" means per primitive
- [Metric](../concepts/entity/schema-yml/metric.md) — the description–sql contract that silent redefinition violates
- [Budgeting the agent's context](./context-engineering.md) — deciding where layer content lives in the first place
