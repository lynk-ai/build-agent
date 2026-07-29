---
description: Policies are eager, always-apply behavioral commitments — output format, clarification behavior, and other rules for how the agent operates.
icon: scale-balanced
---

# Policy

An eager, always-apply behavioral commitment that governs how the agent operates and presents. Output format and clarification behavior are policies.

## What it is

Policies are eager prose rules for *how the agent behaves* — not what the data is, not how to reason through an analysis, but how to operate and present. The defining test: a policy is an **eager, always-apply behavioral commitment**. That rule is what keeps `policies/` coherent and stops it from becoming a catch-all.

Policies come in two layers that look identical structurally:

- **Lynk policies** — types Lynk defines and ships defaults for (`output-format` and `clarification` at launch, more over time). You override a default by creating a policy of that type; your file fully replaces Lynk's default.
- **Custom policies** — types you author for needs Lynk hasn't covered (compliance disclosures, regulatory caveats, team-specific behavior). No Lynk default — pure customer content.

The distinction matters at authoring time (am I overriding or extending?), not at runtime — the agent loads both the same way.

## Where it lives

A folder per policy inside a [domain](domain/README.md):

```
.lynk/domains/<domain>/policies/<name>/POLICY.md
```

## Format

`POLICY.md` follows the shared [frontmatter contract](../reference/markdown-format.md#frontmatter-contract) — `name` (matching the folder), `description`, optional `enabled` — over a prose body describing the behavior.

```markdown
---
name: output-format
description: How the agent presents query results to the user
enabled: true
---

# Output Format

When presenting query results:

- Lead with the answer, not the methodology.
- Show numbers with appropriate precision — never more decimal places than the data supports.
- For comparisons, always say which direction the change goes (up/down, gained/lost).
- When data is missing or partial, name it explicitly rather than presenting incomplete numbers as complete.
```

**Overriding a Lynk default fully replaces it — it does not merge.** Name the policy folder after the Lynk type (`output-format`, `clarification`) and your file becomes the whole policy; the default bullets are gone, not extended. Setting `enabled: false` on an override falls back to Lynk's default.

**Composition is per domain.** Policies don't merge across scopes. For behavior shared across domains, put the prose in a [reference file](reference-files.md) (outside `domains/`, reachable by every domain) and inject it from each domain's policy with an [`@` file reference](../reference/markdown-format.md#references); a policy can also inject from the shared `core` domain, per [topology](lynk-yml.md#topology).

**Naming collisions.** If Lynk later ships a policy type whose name you already use for a custom policy, the build surfaces a collision; rename your file or treat the new Lynk type as an override target.

## Examples

**A custom policy.**

```markdown
---
name: compliance-disclaimer
description: Required disclaimer appended to any answer involving financial projections
---

# Compliance Disclaimer

When an answer includes a forward-looking financial projection, append:
"Projections are estimates, not guarantees, and are not financial advice."
```

**A `sales`-domain clarification policy** overriding the Lynk default and referencing another policy in the same domain.

```markdown
---
name: clarification
description: When the agent asks a clarifying question before answering
enabled: true
---

# Clarification

Ask one clarifying question before answering when:

- a time range is implied but not stated ("recently", "lately");
- a metric name maps to more than one definition in the glossary;
- the question spans entities this domain doesn't contain.

Otherwise, state your assumption inline and proceed. For how to present the
answer once resolved, see @/.lynk/domains/sales/policies/output-format/POLICY.md.
```

## Validation

- `POLICY.md` declares `name` and `description`; `name` matches the folder.
- A custom policy whose name later collides with a new Lynk type surfaces a build collision.

## Related

- [Markdown format](../reference/markdown-format.md) — the frontmatter contract and `@` operator
- [Skill](skill.md) — *how to reason*, versus a policy's *how to operate*
- [LYNK.md](lynk-md.md) — identity and orientation, which is not protocol
- [Domain](domain/README.md) — the scope a policy applies within
- Guides: [Placing knowledge in a layer](../guides/where-knowledge-goes.md)
