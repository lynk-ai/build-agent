# Content Rules — Placement, Clarity, Consistency

These rules govern every edit (`lynk-build`) and every audit (`lynk-evaluate`) of files inside `.lynk/`. Both skills enforce the same rulebook so a file passes evaluate if and only if it would have passed build.

The rules are prescriptive: each one says what good looks like and what the agent must do when it sees a violation. They complement the build: the specs under `references/docs/` say what the build validates; this rulebook covers what the build can't judge — placement, clarity, semantic correctness, and contradictions — plus the checks worth running locally before a commit ever reaches the backend.

## Rules at a glance

1. Single source of truth — one concept, one home
2. The right place is whatever the docs say — placement per the file-type spec
3. Misplaced content gets offered for relocation, not silently accepted
4. Every description and instruction must be meaningful and clear
5. Cross-file consistency — no contradictions
6. Reference & content integrity — names resolve (6a); nothing implied-but-undefined (6b)
7. Engine compatibility — SQL must run on the warehouse
8. Two SQL surfaces — authoring grammar vs. Lynk SQL query dialect
9. Domain coherence — a domain's content serves its team's agent
10. No raw SQL or formulas in prose — computation lives in schema
11. Entity keys must actually identify a row

`lynk-evaluate` tags each finding `local/content-rules-<N>` with the rule number. The **Quick check** at the end is the minimum coverage before saving (build) or closing an audit (evaluate).

---

## 1. Single source of truth

Each fact, definition, or rule lives in exactly **one** file. This is the layer's own design principle — "one concept, one home" (`references/docs/concepts/entity/README.md`, `references/docs/guides/where-knowledge-goes.md`): a quirk about orders lives on the `order` entity and nowhere else; every other mention points at that home instead of restating it.

When adding new content, first check whether it (or something equivalent) already exists somewhere in `.lynk/`. If it does:
- If the existing location is correct per Rule 2 → point at it (an `@` injection or a link — see `references/docs/reference/markdown-format.md`), do not duplicate.
- If the existing location is wrong per Rule 2 → relocate it (Rule 3), then add your new content to the correct file.

When auditing, flag any content that appears in two places (verbatim or near-verbatim) — even if both copies look correct individually. Two copies will drift; one of them ends up wrong.

**Severity: `warning`.** Duplicates will drift over time. If two copies *already contradict each other*, escalate as a Rule 5 contradiction (`needs-client-input`) — the contradiction is more urgent than the duplication.

**Content that several entities or domains need** is not a license to clone it. Give it one home and reference it: content shared across domains goes in the shared domain (typically `core`) or a root reference file (`references/docs/concepts/reference-files.md`), injected with `@` where needed. Note the root/domain glossary merge is *not* duplication — a domain key deliberately overriding a root key is expected behavior (`references/docs/concepts/glossary.md`).

---

## 2. The right place is whatever the docs say

Before placing any new content, read the relevant file-type spec under `references/docs/concepts/` and place per that spec. Never guess. Never rely on memory.

The file-type specs are the single source of truth for what goes where. This rulebook deliberately does not duplicate them — that would create drift. Two navigation aids:

- The placement decision itself — fact vs. word vs. number vs. procedure vs. behavior vs. orientation — is the placement table in `references/docs/guides/where-knowledge-goes.md`. Classify the content by kind and place it by row.
- If you're not sure which file-type spec applies, start at the docs index (`references/docs/SUMMARY.md`) and navigate from there.

---

## 3. Misplaced content gets offered for relocation, not silently accepted

This rule is **action protocol**, not a separate detection. Misplacement is detected by Rule 2; Rule 3 governs how the agent acts on what Rule 2 found. Findings stay tagged `content-rules-2`; the suggested-fix text cites Rule 3.

When you encounter content that doesn't belong where it is:

**In `lynk-build`** — call it out in the plan you present in Step 6, before any edit. Format: *"Found `<content>` in `<wrong_file>`. Per the `<file-type>` spec, it belongs in `<right_file>`. I'll move it as part of this edit."* Wait for user confirmation. Never move silently.

**In `lynk-evaluate`** — flag it as a finding under the `placement` check group with severity `warning` (or `error` if it changes agent behavior — e.g. a computation stranded in glossary prose means the agent re-derives it differently per question). Offer the move as a suggested fix.

Never assume the misplacement was intentional. The cost of a confirmation prompt is much smaller than the cost of an unexpected move.

---

## 4. Every description and instruction must be meaningful and clear

The agent reads descriptions to decide what to do — and in v2 they are doubly load-bearing: entities and skills are **lazy**, indexed by their frontmatter `name` and `description`, so a weak description doesn't just add noise, it makes the agent load the wrong things (`references/docs/concepts/entity/entity-md.md`, `references/docs/concepts/skill.md`).

**Reject these red flags. Severity: `warning` if business-critical (ENTITY.md / SKILL.md / POLICY.md frontmatter descriptions, feature / metric / relationship descriptions, glossary entries), otherwise `suggestion`:**

- **Tautological** — description repeats the name. `country_code: "country_code"`, `description: "the order entity"`.
- **Vague** — description gives no decision signal. `description: "metric data"`, `description: "customer information"`, `description: "session details"`.
- **Placeholder** — `TODO`, `tbd`, `xxx`, `FIXME`, `???`, `[fill in]`, `pending`, empty string on a required field.
- **Shifted-paste** — description matches a *different* field's or entity's name (typically from copy-pasting a row and forgetting to update the description).
- **Pasted fragment** — description reads like an instruction snippet rather than a description (`"see the customer entity for revenue"` is navigation, not a description).
- **Grain missing on an entity** — an entity description that can't say "one row per …" in its first line isn't describing an entity yet (`references/docs/guides/designing-entities.md`).
- **Scale missing on a ratio** — any ratio feature or metric must state its scale (`0–1` vs `0–100`) in the description, and every threshold that touches it must use that scale (`references/docs/concepts/entity/schema-yml/feature.md`, `references/docs/concepts/entity/schema-yml/metric.md`).

**What good looks like.** A good description tells the agent (a) what this thing represents and (b) when it applies — for entities, grain first:
> `description: A completed purchase transaction. One row per order. Use for revenue, order volume, purchase dates, and product-level sales.`

For behavioral prose (a policy) or reasoning prose (a skill), good looks like a rule the agent can follow without interpreting intent:
> *"When an answer includes a forward-looking projection, append the projections disclaimer."*

The `sql:` of a feature or metric must compute **exactly** what its description says — the agent reasons from the description, so a mismatch misleads every query. The build can't check this (`references/docs/concepts/entity/schema-yml/metric.md`); flag mismatches here, severity `warning`, escalating to `error` when the description would lead the agent to a wrong number (wrong filter, wrong scale, wrong grain).

---

## 5. Cross-file consistency — no contradictions

The same concept must mean the same thing everywhere it appears: `GLOSSARY.yml` (root and domain), `LYNK.md` (root and domain), `ENTITY.md` prose, `schema.yml` descriptions and filters, skills, and policies.

**Specific contradictions to watch for:**

- The glossary defines a term (e.g. `at_risk = NPS < 6 OR no login in 60 days`) but a feature `filter:` or a skill uses a different threshold.
- An `ENTITY.md` convention (e.g. *"exclude test accounts"*) that the entity's definitions don't enforce and other files don't honor.
- The root `LYNK.md` and a domain `LYNK.md` state incompatible rules. (Domain *extends* root by design — extension is fine, contradiction is not; `references/docs/concepts/lynk-md.md`.)
- Two files state different grains, fiscal calendars, or default filters for the same analysis.

**Not contradictions:** style differences (different phrasing of the same rule), and a domain glossary key overriding a root key — that merge is expected, the domain wins (`references/docs/concepts/glossary.md`). Only flag when the *meaning* differs where both copies are supposed to apply.

**When you find a contradiction:** in `lynk-build`, ask the user which version is canonical before editing. In `lynk-evaluate`, mark it `needs-client-input` rather than picking a side.

**Severity: `needs-client-input`.** The agent does not have authority to decide which definition is correct.

---

## 6. Reference & content integrity

Two shapes of the same problem — names without definitions, or definitions implied without names. The build validates the structured forms (`@` references, imports, `join_name`s, skill references to features and metrics — see the Validation sections of the specs); this rule exists so violations are caught *before* a commit, and so the un-validated forms (bare prose mentions) are caught at all.

**6a. Forward references — every name resolves.** Every entity, feature, metric, relationship, or glossary term *named* anywhere must resolve to a definition:

- `metric(<entity>.<name>)` in a feature's `sql:` or in a Lynk SQL snippet → the metric exists on that entity's `schema.yml`.
- A feature mentioned in prose (`use customer_lifetime_value for this`) → exists under that entity's `features:`.
- A `join_name` on a feature → a relationship of that name in the same `schema.yml`.
- An `@` reference (`@glossary.term.description`, `@customer.email.description`, `@/.lynk/…` file path) → resolves per `references/docs/reference/markdown-format.md`, within topology.
- An `imports:` path → defined on the identity parent (`references/docs/concepts/entity/schema-yml/identity-and-imports.md`).
- A key column referenced by a relationship step, feature expression, or query → **declared as a feature**. Keys are not features; an undeclared key is invisible outside the `keys:` block (`references/docs/concepts/entity/schema-yml/identity-and-imports.md`).

**Severity: `error`.** A broken structured reference fails the build; a broken prose mention silently misleads the agent.

**6b. Implied-but-undefined.** Content described in prose without a backing definition. Examples:
- `LYNK.md` says *"we report MRR weekly"* but no `mrr` metric exists anywhere.
- A skill's procedure references *"the high-value customer segment"* but no feature flags it.
- The glossary defines a term that no entity, feature, metric, or skill surfaces.

**Severity: `warning`.** The agent will be unable to answer cleanly when asked about something the prose says exists.

---

## 7. Engine compatibility — SQL must run on the warehouse

Every SQL expression in `.lynk/` compiles down to the user's warehouse dialect — Lynk intercepts only its own constructs (`metric()`, `USING('<join_name>')`, path references) and passes everything else through (`references/docs/api/lynk-sql.md`). So metric and feature `sql:`, `filter:` predicates, and relationship step conditions must all be valid in the warehouse engine the user runs.

**Detect the engine first.** The v2 layer does not declare the engine — `lynk.yml` carries only `schema_version`, `topology`, and `name` (`references/docs/concepts/lynk-yml.md`). Determine it from the user (ask once via `AskUserQuestion`) or from the data catalog via `lynk-sources`; record it for the session. Common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`. Never guess.

**Dialect-specific red flags:**
- `IFF` — Snowflake-flavored (BigQuery uses `IF`, Postgres `CASE WHEN`).
- `QUALIFY` — non-ANSI; supported on Snowflake, BigQuery, Databricks, and Redshift, but not Postgres.
- `SAFE_*` functions and backtick-quoted identifiers — BigQuery-only.
- `DATEADD` / `DATEDIFF` — argument order and unit syntax differ across BigQuery, Snowflake, and Postgres.
- Window-function syntax, `EXCEPT` vs `MINUS`, `LIMIT` placement — vary across engines.
- Implicit type coercion behavior differs (e.g. comparing string to integer); be explicit.

**Window functions — where they're allowed:** valid in a feature's `sql:` (a per-row value) and in Lynk SQL queries (including `QUALIFY` — `references/docs/api/lynk-sql.md`), but not in a metric's `sql:` — the spec defines that as an aggregation expression producing a single value across rows (`references/docs/concepts/entity/schema-yml/metric.md`), which a per-row window value is not.

**Reserved-word source columns must be quoted.** If a physical path in `sql:` ends in a SQL reserved word (e.g. `ORDER`, `ROW`, `VALUE`), quote that identifier — `maindb.public.orders."ORDER"`. Identifiers pass through unquoted, so an unquoted reserved word fails at query time. When a query errors with `unexpected '<WORD>'`, suspect a reserved-word column before suspecting the surrounding construct.

**In `lynk-build`** — write SQL using the detected engine's syntax from the start. When a portable form exists, prefer it over an engine-specific shortcut. Don't assume a dialect; if engine isn't yet detected, detect first.

**In `lynk-evaluate`** — scan every SQL expression against the detected engine and flag dialect-incompatible constructs. **Severity: `error`.** The SQL will fail at runtime, not at parse time, so the user won't see the issue until they run a query.

---

## 8. Two SQL surfaces — authoring grammar vs. Lynk SQL query dialect

Lynk has two SQL surfaces that look similar but apply in different contexts, and mixing them is the most common source of broken definitions and agent drift:

- **The authoring grammar** — the `sql:` / `filter:` fields inside `schema.yml`. Segment-counted path references (`order.net_amount` = entity-local, `maindb.public.orders.net_amount` = physical column), `metric()` / `first()` / `last()`, entity-qualified names, a single `join_name` binding every cross-entity reference, no templating of any kind. Spec: `references/docs/reference/sql-expressions.md`.
- **The Lynk SQL query dialect** — what the agent (or a user) writes against a built layer. Entities in `FROM`, feature names as columns, `metric(<entity>.<name>)` with an alias in the `SELECT` list, `USING('<join_name>')` for named relationships. `first()` / `last()` do **not** exist here — that's a documented pitfall. Spec: `references/docs/api/lynk-sql.md`.

This rulebook does not duplicate the SQL specs. Before writing or scanning any Lynk SQL, read:

- `references/docs/reference/sql-expressions.md` — the authoring grammar (paths, functions, join binding, filters)
- `references/docs/api/lynk-sql.md` — the query dialect (entity references, `metric()`, joins, supported statements, pitfalls)
- `references/docs/concepts/entity/schema-yml/relationships.md` — relationship step `sql:` (entity-relationship steps use `entity.feature` paths; table-relationship steps use physical columns)

**Surface violations to flag:** `first()` / `last()` in a query; a physical table in a query's `FROM` (bypasses the layer); a bare metric path where `metric()` is required; templating (`{{ }}`, `ref()`, macros) anywhere; a cross-entity reference in a metric's `sql:` (metrics are entity-local); an entity-relationship step joining on a physical column.

**In `lynk-build`** — read the docs above before writing any SQL; write canonical forms from the start. Do not rely on memory; the SQL surfaces have changed before and may again.

**In `lynk-evaluate`** — read the docs above before scanning, then flag any SQL that doesn't match what the current docs say is valid. **Severity: `error`** for surface violations (SQL the engine will not accept). **Severity: `warning`** for forms that may still execute but drift from canonical Lynk SQL. Cite the relevant doc path in the suggested fix.

The docs are the source of truth; on any disagreement between a file and the docs, the docs win.

---

## 9. Domain coherence — a domain's content serves its team's agent

A domain **is** an agent — one team's analytical surface, with its own vocabulary, entities, skills, and policies (`references/docs/concepts/domain/README.md`). Everything inside `domains/<name>/` must serve that team's agent: its entities answer that team's questions, its glossary speaks that team's language, its `LYNK.md` describes that team. Content useful to a different audience degrades this agent and is invisible to the agent that needs it — isolation is the design, and peers never reach each other (`references/docs/concepts/lynk-yml.md`, topology).

**Fix scopes** (when content fails the fit check):
- **Cross-domain** (several teams need it) → promote to the shared domain (typically `core`) or a root reference file, and reference it from where it's used. The every-agent test decides root vs. domain (`references/docs/guides/where-knowledge-goes.md`).
- **Belongs to a different single domain** (a finance rule in marketing's folder) → relocate to that domain. Remember peers can't reference each other — relocation, not a cross-reference, is the fix.
- **Speculative / nowhere yet** → flag and ask the user whether to keep, relocate, or remove.

**In `lynk-build`** — when adding to a domain, check the domain's `LYNK.md` and entity set and confirm the new content fits this team's agent. Surface any off-topic content you notice while reading and offer relocation in the same plan (Rule 3 protocol).

**In `lynk-evaluate`** — flag findings under the `domain-coherence` check group. Quote the offending content and the domain's `LYNK.md` framing (or its entity set, if no `LYNK.md` exists), and let the user judge.

**Severity: `warning`.** Escalate to **`needs-client-input`** when topical fit is genuinely ambiguous (the content could plausibly belong to two domains, or the domain has no `LYNK.md` to anchor the check) — the agent doesn't have authority to decide topical scope unilaterally.

---

## 10. No raw SQL or formulas in prose — computation lives in schema

Prose files — `LYNK.md`, `ENTITY.md`, `SKILL.md`, `POLICY.md`, glossary descriptions, reference files — must not *carry* computations. Skills use schema, they don't define it (`references/docs/concepts/skill.md`); the layer's own bar is explicit: no formula lives in glossary prose, and no raw SQL hides in `SKILL.md` or `POLICY.md` (`references/docs/guides/where-knowledge-goes.md`). The build cannot catch this — embedded SQL sails through validation, then rots silently when the schema or the warehouse changes, and formula prose makes the agent re-derive the computation slightly differently per question.

**What's a violation:**
- A glossary description carrying a formula (*"NDR = (starting ARR + expansion − contraction − churn) / starting ARR"*) — the **glossary shadow metric store** anti-pattern.
- A skill or policy step embedding warehouse SQL (*"compute at-risk MRR as `SELECT SUM(amount_cents)/100 FROM maindb.public.subscriptions WHERE …`"*) — the **skill-as-schema-smuggler** anti-pattern.
- An `ENTITY.md` or `LYNK.md` paragraph that defines a derivation instead of pointing at the feature or metric that owns it.

**What's fine:** naming defined computations. A skill saying *"start from `metric(subscription.mrr_at_risk)`"*, a glossary entry pointing at the two defined metrics to divide, an `@` injection of a definition's description — references by name are the intended pattern.

**Detection:** scan every prose surface for SQL keywords (`SELECT`, `FROM`, `WHERE`, `JOIN`, aggregate calls) and arithmetic formulas over column-like names. For each hit, check whether a schema definition (feature or metric) already owns that computation.

**Fix:** define the computation where it's validated — a feature or metric on the owning entity (or a skill *procedure* if it's genuinely multi-step reasoning, still referencing schema by name) — and have the prose point at it.

**Severity: `warning`** when the prose duplicates a computation that schema already defines (Rule 1 also applies — one home). **`error`** when the prose is the *only* place the computation exists: nothing validates it, and the agent must re-derive it.

A related prose failure with the same shape: **correctness by prose reminder** — a convention that must always hold (*"always exclude test accounts"*) enforced only by an `ENTITY.md` line. Prose is advisory; enforcement is structural — an upstream filtered view or a `filter:` on the affected definitions, with the prose line documenting *why* (`references/docs/guides/designing-entities.md`). Flag as `warning` with the structural fix suggested.

Tag findings `local/content-rules-10`.

---

## 11. Entity keys must actually identify a row

When an entity's `identity` is a physical table or view, `keys` is **required** and names the column(s) that *uniquely identify a row* — the grain contract is that each instance appears exactly once in the identity relation (`references/docs/concepts/entity/schema-yml/identity-and-imports.md`). When `identity` is another entity, `keys` is inherited and must **not** be re-authored. A composite key is valid; there is no keyless standalone entity.

The failure this rule catches is a **fabricated key**: a `keys` entry whose column(s) resolve fine (so Rule 6 passes) but aren't actually unique at the table's grain. This is common on event / fact tables with no single unique column — pressured to fill the required field, an agent may promote an arbitrary non-unique column (e.g. `interaction_element_id` on an events table) and rationalize it as "harmless." It isn't: a key that isn't unique is *worse* than a missing one — it's a false grain claim that silently corrupts dedup, joins, and distinct-count results downstream. The right key for such a table is a verified composite, or — if none exists — an honest escalation, never an arbitrary column. (If the rows aren't one-per-instance at all, the fix is upstream — a view or materialized table that creates the grain; Lynk never will: `references/docs/guides/designing-entities.md`.)

**In `lynk-build`** — source the key from real data: use the catalog's reported `keys`, or derive a candidate and verify it with a `COUNT(*)` vs `COUNT(DISTINCT keys)` query before committing it (build Step 5, capped at 3 candidate attempts, narrating each attempt). Never fabricate a key to satisfy the schema; if no candidate verifies unique, escalate the choice to the user rather than picking one.

**In `lynk-evaluate`** — flag a `keys` that has no uniqueness backing:
   - **Static suspicion — `needs-client-input`.** Uniqueness is a property of the data, so static analysis can only *suspect*. Raise it when: the catalog reports no `keys` for the identity table yet the entity declares one; or the entity's own description calls the source an event / log / activity stream (grains that rarely have a single unique column) and `keys` is a single non-id-looking column. Surface the candidate and the reason.
   - **Authoritative check — `error`.** Run `SELECT COUNT(*) AS rows, COUNT(DISTINCT <keys>) AS distinct_rows FROM <identity_table>` via `lynk-sources` (lynk-evaluate Step 7). `distinct_rows < rows` → the key is not unique → **error**. This confirms what Rule 6 can't: a declared, resolvable key that is nonetheless invalid.

Remember **keys are not features** (Rule 6a): a key column that any relationship step, expression, or query references must also be declared as a feature.

Tag findings `local/content-rules-11`.

---

## Quick check before saving / before closing an audit

For each file you touched (build) or read (evaluate), ask:

1. **Right place?** — Does each item match its file-type spec under `references/docs/concepts/`, per the placement table (Rule 2)?
2. **Clear and meaningful?** — Does each description tell the agent what this is and when it applies — grain-first for entities, scale stated for ratios (Rule 4)?
3. **Appears once?** — Scan related files for the same content; flag duplicates and point-don't-restate violations (Rule 1).
4. **Internally consistent?** — Do the definitions in this file agree with related files in meaning, not just in style (Rule 5)?
5. **All references resolve?** — Does every named feature, metric, entity, relationship, glossary term, `@` reference, and import resolve (Rule 6a)? Does every concept the prose implies have a backing definition (Rule 6b)? Is every key column that anything references also declared as a feature?
6. **Engine-compatible SQL?** — Does every SQL expression use only constructs valid in the detected warehouse engine (Rule 7)?
7. **Right SQL surface?** — Does every expression match its context — authoring grammar inside `schema.yml`, Lynk SQL query dialect in queries — per the docs linked from Rule 8?
8. **Domain coherent?** — Does everything in this domain serve this team's agent; is shared content promoted rather than cloned (Rule 9)?
9. **No computation in prose?** — Do glossary descriptions, `LYNK.md`, `ENTITY.md`, skills, and policies point at schema definitions rather than carrying formulas or raw SQL (Rule 10)?
10. **Keys real?** — Does every standalone entity's `keys:` actually identify a row — catalog-reported or verified unique — rather than a fabricated non-unique column (Rule 11)?

If the answer to any of these is "no" or "I'm not sure," the work isn't done.
