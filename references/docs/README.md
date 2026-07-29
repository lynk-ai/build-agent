---
description: Lynk is a semantic layer for AI — a brain organized by concept that teaches an agent how your business thinks.
icon: brain-circuit
layout:
  width: default
---

# Overview

A Lynk project is the business context an AI agent needs to answer data questions the way a senior insider would — your entities, metrics, vocabulary, and rules, encoded as files and organized by concept.

You are not configuring a system; you are teaching an agent how your business thinks. Lynk gives every piece of that knowledge one obvious home, so a builder opening a project recognizes the structure before reading a single file.

---

## The mental model

A Lynk project is **a brain organized by concept**. Six concept-shaped drawers hold what the agent needs:

| Drawer | What it holds |
|---|---|
| [`LYNK.md`](concepts/lynk-md.md) | **Orientation.** Who the business is, who a team is, how they think. |
| [`GLOSSARY.yml`](concepts/glossary.md) | **Vocabulary.** The terms a team uses and what they refer to. |
| [Domains](concepts/domain/README.md) | **The agents themselves.** One per team, one per audience. |
| [Entities](concepts/entity/README.md) | **What exists.** Customers, orders, campaigns. Each entity owns everything true about itself. |
| [Skills](concepts/skill.md) | **How to reason.** Procedures for recurring kinds of analysis. |
| [Policies](concepts/policy.md) | **Protocol.** How the agent operates and presents. |

Four ideas hold it together:

**Domains are agents.** Each domain is one team's analytical agent — marketing's agent, sales' agent, finance's agent. Each speaks that team's language and answers in that team's voice. A user always talks to one agent at a time. Designing a domain *is* designing an agent.

**Concepts are the unit of organization, not forms.** Everything true about orders — its definitions, its quirks, its conventions, its analytical patterns — lives in the orders entity. Not split across a knowledge file and an instructions file and a metrics file. One concept, one home.

**Some content is always loaded; some is loaded on demand.** Orientation, vocabulary, and policies are always in the agent's context. Entities and skills are lazy — the agent indexes them by description and loads only what a question needs.

**The shape never changes.** A project with one domain has the same shape as a project with twelve. Adding a domain is adding a folder, not a restructure.

---

## The `.lynk/` tree

The whole semantic layer lives under a `.lynk/` directory at your repo root. Up to three files sit at the root — `lynk.yml` is required; root `LYNK.md` and `GLOSSARY.yml` are optional. Domains hang off `domains/`, and shared [reference files](concepts/reference-files.md) can sit at the root alongside them.

```
.lynk/
├── lynk.yml            # project settings
├── LYNK.md             # who the business is
├── GLOSSARY.yml        # shared vocabulary
└── domains/
    ├── core/           # the shared domain others build on (set shared_domain in lynk.yml)
    │   ├── LYNK.md
    │   ├── GLOSSARY.yml
    │   ├── entities/
    │   │   └── customer/
    │   │       ├── ENTITY.md      # prose: quirks, conventions
    │   │       └── schema.yml     # structure: features, metrics, relationships
    │   ├── skills/
    │   └── policies/
    └── marketing/      # one team's agent
        ├── LYNK.md
        ├── entities/
        └── skills/
            └── attribution-analysis/
                └── SKILL.md
```

The smallest project worth querying is one domain with one entity and a `LYNK.md`. See [Layout and naming](reference/layout-and-naming.md) for the full tree and the rules.

---

## How a project is consumed

A Lynk project is a self-contained git repository — version-controlled, reviewable, editable in any IDE. Agents don't reason against in-progress edits. You push to a branch, the push triggers a build, the build validates the whole layer, and if it passes it deploys and becomes queryable. If it fails, the build is rejected and the last good build keeps serving. Answers are reproducible because they are bound to a specific build of a specific branch and domain.

See [Project](concepts/project.md) for the full lifecycle.

---

## Find your way

<table data-view="cards">
  <thead>
    <tr>
      <th>Start here</th>
      <th></th>
      <th data-card-target data-type="content-ref">Target</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>The project</strong></td>
      <td>The repo, the build lifecycle, branches</td>
      <td><a href="concepts/project.md">Project</a></td>
    </tr>
    <tr>
      <td><strong>Domains</strong></td>
      <td>Designing an agent for a team</td>
      <td><a href="concepts/domain/README.md">Domain</a></td>
    </tr>
    <tr>
      <td><strong>Entities</strong></td>
      <td>Modeling what exists — ENTITY.md + schema.yml</td>
      <td><a href="concepts/entity/README.md">Entity</a></td>
    </tr>
    <tr>
      <td><strong>Querying</strong></td>
      <td>The Lynk SQL dialect</td>
      <td><a href="api/lynk-sql.md">Lynk SQL</a></td>
    </tr>
  </tbody>
</table>

**Guides** — the judgment layer: how to decide, what good looks like, and the anti-patterns to avoid:

| If you're deciding… | Go to |
|---|---|
| Where a piece of knowledge belongs | [Placing knowledge in a layer](guides/where-knowledge-goes.md) |
| What becomes an entity, and its grain | [Choosing and shaping entities](guides/designing-entities.md) |
| How to model balances, windows, cohorts, KPIs | [Modeling metrics, time, and state](guides/metrics-time-and-state.md) |
| How many domains, what goes in core | [Designing domains](guides/designing-domains.md) |
| What loads when — @ vs link, splitting files | [Budgeting the agent's context](guides/context-engineering.md) |
| How to rename, deprecate, and change safely | [Evolving a live layer](guides/evolving-the-layer.md) |
| What a whole correct layer looks like | [Reading a complete layer](guides/complete-example.md) |

**Reference** — the shared mechanics every concept relies on:

| If you need… | Go to |
|---|---|
| The directory tree and naming rules | [Layout and naming](reference/layout-and-naming.md) |
| Frontmatter and the `@` injection operator | [Markdown format](reference/markdown-format.md) |
| The `sql:` grammar inside `schema.yml` | [SQL expressions](reference/sql-expressions.md) |
| Whether Lynk supports X — testing, parameters, templating, scheduling | [What Lynk doesn't do](reference/what-lynk-does-not-do.md) |
| The query dialect | [Lynk SQL](api/lynk-sql.md) |
