---
description: The required project settings file at the .lynk/ root — schema_version, topology, and name.
icon: gear
---

# lynk.yml

The required settings file at the project root. It governs how Lynk interprets the rest of the semantic layer — format version, domain topology, and the project name.

## What it is

`lynk.yml` holds settings *for* the semantic layer, not customer business content. Where [`LYNK.md`](lynk-md.md) and [`GLOSSARY.yml`](glossary.md) carry what the agent knows, `lynk.yml` carries the rules Lynk uses to read everything else: which format version the project targets, how its [domains](domain/README.md) may reference each other, and what to call the project.

It is the one place the project's **topology** is declared. Topology is the only architectural axis a customer can configure — everything else about how the layer composes is a fixed product property.

## Where it lives

One file, at the root of the `.lynk/` tree:

```
.lynk/lynk.yml
```

It is required. A project with no `lynk.yml` does not build.

## Format

| Field | Required | Type | Notes |
|---|---|---|---|
| `schema_version` | ✓ | string | Pins the project to a Lynk format version, so the format can evolve without breaking existing projects. |
| `topology` | – | object | The domain reference pattern. See below. Defaults to medallion with **no** shared domain — set `shared_domain` to enable cross-domain composition. |
| `name` | – | string | Human-readable project name. |

### `topology`

`topology` declares which [domains](domain/README.md) may reference which. It is the single authority for **every** cross-domain reference — structured composition (`identity:` and `imports:`) and file references alike (`@` injection, markdown links, and bare `/.lynk/…` paths in prose). It is enforced at build time: a reference the topology forbids is a build error.

```yaml
topology:
  pattern: medallion       # the default
  shared_domain: core      # the domain others may reference
```

| Field | Required | Type | Notes |
|---|---|---|---|
| `pattern` | – | string | `medallion`. Defaults to `medallion`. |
| `shared_domain` | – | string | Under `medallion`, the domain other domains may import from and reference. Conventionally `core`. **Optional — unset means there is no shared domain, so no cross-domain composition is allowed.** |

**By default there is no shared domain: until you set `shared_domain`, a domain may reference only its own files and the root reference files — no cross-domain composition at all.** Once a `shared_domain` is set under **medallion**, a domain may reference:

- its **own** files;
- the **root reference files** ([reference files](reference-files.md) at the `.lynk/` root, outside `domains/`, belonging to no domain);
- the **shared domain** (e.g. `core`).

Domains may **not** reference each other. So a `marketing` entity may declare `identity: core.customer` and import from it, or `@`-inject `/.lynk/domains/core/…`, but it cannot reach a `sales` peer; to share content across peers, promote it into the shared domain or a root reference file.

## Examples

**Version only.** Topology defaults to medallion with no shared domain — every domain is self-contained until a `shared_domain` is declared.

```yaml
# .lynk/lynk.yml
schema_version: "v2"
```

**Named project with an explicit topology.**

```yaml
# .lynk/lynk.yml
schema_version: "v2"
name: Grove
topology:
  pattern: medallion
  shared_domain: core
```

## Validation

- `lynk.yml` exists at the `.lynk/` root and declares `schema_version`. Missing or unreadable fails the build.
- `topology.pattern`, if set, is `medallion`; other values are rejected.
- The `shared_domain`, **if set**, names an existing domain under `domains/`. When unset there is no shared domain and no cross-domain composition is allowed.
- Cross-domain references that violate the declared topology are build errors; questionable-but-legal patterns surface as warnings.

## Related

- [Project](project.md) — what a project is and how it builds
- [Domain](domain/README.md) — domains and the cross-domain reference rules topology produces
- [Layout and naming](../reference/layout-and-naming.md) — where `lynk.yml` sits in the tree
