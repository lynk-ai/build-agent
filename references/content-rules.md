# Content Rules — Placement, Clarity, Consistency

These rules govern every edit (`lynk-build`) and every audit (`lynk-evaluate`) of files inside `.lynk/`. Both skills enforce the same rulebook so a file passes evaluate if and only if it would have passed build.

The rules are prescriptive: each one says what good looks like and what the agent must do when it sees a violation.

## Rules at a glance

1. Single source of truth — each definition lives in exactly one file
2. The right place is whatever the docs say — placement per the file-type spec
3. Misplaced content gets offered for relocation, not silently accepted
4. Every description and instruction must be meaningful and clear
5. Cross-file consistency — no contradictions
6. Reference & content integrity — names resolve (6a); nothing implied-but-undefined (6b)
7. Engine compatibility — SQL must run on the warehouse
8. Lynk SQL syntax — examples vs feature definitions
9. Domain coherence — content scoped to a domain stays on-topic
10. Examples and evaluations must be valid, runnable, and self-consistent
11. Entity keys must actually identify a row
12. `related_sources` must not shadow — or be aggregated as — an entity

`lynk-evaluate` tags each finding `local/content-rules-<N>` with the rule number. The **Quick check** at the end is the minimum coverage before saving (build) or closing an audit (evaluate).

---

## 1. Single source of truth

Each instruction, definition, or rule lives in exactly **one** file.

When adding new content, first check whether it (or something equivalent) already exists somewhere in `.lynk/`. If it does:
- If the existing location is correct per Rule 2 → link to it from your edit's plan, do not duplicate.
- If the existing location is wrong per Rule 2 → relocate it (Rule 3), then add your new content to the correct file.

When auditing, flag any content that appears in two places (verbatim or near-verbatim) — even if both copies look correct individually. Two copies will drift; one of them ends up wrong.

**Severity: `warning`.** Duplicates will drift over time. If two copies *already contradict each other*, escalate as a Rule 5 contradiction (`needs-client-input`) — the contradiction is more urgent than the duplication.

**Scoping one file to several entities.** When content applies to a *set* of entities — not a single entity, and not the whole domain — scope one knowledge/task-instructions file to them with a list (`entity: [a, b, c]`) rather than cloning the content into each entity's files. The file loads when **any** listed entity is queried. This is the multi-entity home that avoids duplication; confirmed honored at runtime (see the file-type specs' frontmatter tables).

---

## 2. The right place is whatever the docs say

Before placing any new content, fetch the relevant file-type spec from `https://docs.getlynk.ai/file-types/` and place per that spec. Never guess. Never rely on memory.

The file-type specs are the single source of truth for what goes where. This rulebook deliberately does not duplicate them — that would create drift. If you're not sure which file-type spec applies to the content you're placing, start at the docs index (`https://docs.getlynk.ai/llms.txt`) and navigate from there.

---

## 3. Misplaced content gets offered for relocation, not silently accepted

This rule is **action protocol**, not a separate detection. Misplacement is detected by Rule 2; Rule 3 governs how the agent acts on what Rule 2 found. Findings stay tagged `content-rules-2`; the suggested-fix text cites Rule 3.

When you encounter content that doesn't belong where it is:

**In `lynk-build`** — call it out in the plan you present in Step 6, before any edit. Format: *"Found `<content>` in `<wrong_file>`. Per the `<file-type>` spec, it belongs in `<right_file>`. I'll move it as part of this edit."* Wait for user confirmation. Never move silently.

**In `lynk-evaluate`** — flag it as a finding under the `placement` check group with severity `warning` (or `error` if it changes agent behavior — e.g. a metric definition stranded in a knowledge file means the agent can't aggregate that metric). Offer the move as a suggested fix.

Never assume the misplacement was intentional. The cost of a confirmation prompt is much smaller than the cost of an unexpected move.

---

## 4. Every description and instruction must be meaningful and clear

The agent reads descriptions to decide what to do. A description that doesn't help the agent decide is worse than no description — it occupies space and creates noise.

**Reject these red flags. Severity: `warning` if business-critical (entity description, metric description, feature description used in queries), otherwise `suggestion`:**

- **Tautological** — description repeats the name. `country_code: "country_code"`, `description: "the order entity"`.
- **Vague** — description gives no decision signal. `description: "metric data"`, `description: "customer information"`, `description: "session details"`.
- **Placeholder** — `TODO`, `tbd`, `xxx`, `FIXME`, `???`, `[fill in]`, `pending`, empty string on a required field.
- **Shifted-paste** — description matches a *different* field's or entity's name (typically from copy-pasting a row and forgetting to update the description).
- **Pasted fragment** — description reads like an instruction snippet rather than a description (`"see the customer entity for revenue"` is navigation, not a description).
- **Empty on a business-critical element** — entity, metric, or feature used in evaluations or examples must have a description.

**What good looks like.** A good description tells the agent (a) what this thing represents and (b) when it applies. Example:
> `description: A completed purchase transaction. Use this entity for questions about revenue, order volume, purchase dates, and product-level sales.`

For an instruction (e.g. in task instructions), good looks like a clear rule the agent can follow without having to interpret intent:
> *"For revenue questions on the order entity, always exclude `is_test_order = true` rows. The default revenue metric is `sum_net_revenue`, not `sum_gross_revenue`."*

---

## 5. Cross-file consistency — no contradictions

The same concept must mean the same thing across glossary, knowledge, task instructions, examples, evaluations, and entity YAML.

**Specific contradictions to watch for:**

- Glossary defines a term (e.g. `at_risk = NPS < 6 OR no login in 60 days`) but a metric or task instruction filters by a different threshold.
- Knowledge file says one rule (e.g. *"exclude test accounts"*) but examples or evaluations don't apply the filter.
- Task instructions describe one SQL pattern; entity examples use a different pattern for the same question type.
- Two knowledge files (entity vs. domain) state different rules for the same entity.

**When you find a contradiction:** in `lynk-build`, ask the user which version is canonical before editing. In `lynk-evaluate`, mark it `needs-client-input` rather than picking a side.

**Severity: `needs-client-input`.** The agent does not have authority to decide which definition is correct.

**Style differences are not contradictions.** Different phrasing of the same rule is fine. Only flag when the *meaning* differs.

---

## 6. Reference & content integrity

Two shapes of the same problem — names without definitions, or definitions implied without names.

**6a. Forward references — every name resolves.** Every metric, feature, entity, or relationship *named* in markdown, examples, or `evaluations.yml` must resolve to a definition in some YAML.

Check for:
- A metric referenced as `METRIC('total_arr')` in an example → must exist in some entity's `metrics:`.
- A feature referenced in a knowledge file (`use the customer_lifetime_value field`) → must exist in the entity's `features:`.
- An entity referenced in a join, evaluation, or example (`FROM subscription`, `JOIN subscription`) → must have its own YAML.
- A `join_name` used in a feature → must exist in `entities_relationships.yml`.
- A feature used in **agent-generated SQL** (`expected_output`, entity `examples:`, task-instruction / knowledge SQL, any `SELECT` / `WHERE` / `GROUP BY`) must not only *exist* but be **queryable** — internal/private features (Rule 10) resolve only inside feature-definition `{…}` SQL and break the query if referenced in generated SQL.

**Severity: `error`.** A broken reference means the agent will fail to resolve a query — this is not a style issue.

**6b. Implied-but-undefined.** Content described in prose without a backing definition. Examples:
- A knowledge file says *"we report MRR weekly"* but no `mrr` metric exists.
- A task instruction references *"the high-value customer segment"* but no feature flags it.
- The glossary defines a term that no entity, metric, or feature surfaces.

**Severity: `warning`.** The agent will be unable to answer cleanly when asked about something the prose says exists.

**6c. Entity keys reference feature names.** Every entry in an entity's `keys:` must be the `name:` of a feature in that entity's `features:` — **not** a raw warehouse column. A raw-column key that shares a name with a feature (case-insensitively) makes the generated CTE project that column twice → `ambiguous column name` at query time. So: every key column needs a `field` feature, and `keys:` lists that feature's name (e.g. `keys: [vertical]` with a `vertical` feature on column `VERTICAL` — never `keys: [VERTICAL]`).

**Severity: `error`.** Dimensional queries on the entity fail at runtime (and backend `validate` does not catch it — only a query does).

> **Current engine caveat (confirmed live):** the consuming CTE still references key features by *column* name, so a feature-name key only resolves cleanly when the **feature name equals its column name** (`vertical`↔`VERTICAL`). If the key column's feature is *renamed* (e.g. feature `send_id` on column `ID`), keying on it (`keys: [send_id]`) breaks the entity at build time — surfacing either as `invalid identifier KEYS.ID`, or (once the build proceeds past keys) as **every derived feature on the entity** failing with `'<feature>' cannot be queried` and any relationship off the entity failing with `cannot be joined` — while plain 1:1 `field` features still resolve. The fix: give such key columns a feature whose name matches the column (e.g. an `id` feature on `ID`, keeping the descriptive `send_id` feature for metrics/joins) and key on that. Flag, don't silently leave a raw-column or renamed-feature key.

---

## 7. Engine compatibility — SQL must run on the warehouse

Every SQL snippet in `.lynk/` must be valid in the warehouse engine the user runs. That includes metric SQL, formula SQL, `first_last` filters, relationship joins, entity examples, and evaluation `expected_output`.

**Detect the engine first.** Read `.lynk/config.json` and look for an `engine`, `dialect`, or `warehouse` field. Common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`. If the field is missing, empty, or the file doesn't exist, ask the user — do not guess. Engine drives every check in this rule.

**Dialect-specific red flags:**
- `QUALIFY` and `IFF` — Snowflake-only.
- `SAFE_*` functions and backtick-quoted identifiers — BigQuery-only.
- `DATEADD` / `DATEDIFF` — argument order and unit syntax differ across BigQuery, Snowflake, and Postgres.
- Window-function syntax, `EXCEPT` vs `MINUS`, `LIMIT` placement — vary across engines.
- Implicit type coercion behavior differs (e.g. comparing string to integer); be explicit.

**Window functions — where they're allowed:** a window function (`ROW_NUMBER`, `RANK`, `LAG`, `OVER (PARTITION BY …)`) is valid in a `formula` feature's `sql:` (it produces a per-row value) and in `expected_output` queries, but **not** in a metric's `sql:`. Don't downgrade a legitimate ranking formula to a "query recipe" on the assumption that formulas can't hold windows — they can. (Verified at runtime; confirmed by the formula section of the entity-YAML docs.)

**Reserved-word source columns must be quoted.** If a field feature's `field:` is a SQL reserved word (e.g. `ORDER`, `ROW`, `VALUE`), quote it — `field: '"ORDER"'`. Identifiers pass through unquoted, so an unquoted reserved word fails to compile at query time (and `validate` won't catch it). When a build/eval query 502s with `unexpected '<WORD>'`, suspect a reserved-word column before suspecting the surrounding construct (e.g. a window function).

**In `lynk-build`** — write SQL using the detected engine's syntax from the start. When a portable form exists, prefer it over an engine-specific shortcut. Don't assume a dialect; if engine isn't yet detected, detect first.

**In `lynk-evaluate`** — scan every SQL snippet against the detected engine and flag dialect-incompatible constructs. **Severity: `error`.** The SQL will fail at runtime, not at parse time, so the user won't see the issue until they run a query.

---

## 8. Lynk SQL syntax — examples vs feature definitions

Lynk uses two SQL surfaces that look similar but apply in different contexts: **feature-definition `sql:`** (features referenced via `{feature_name}` curly braces, resolved by the Lynk engine at compile time) and **`expected_output` / task-instruction / knowledge SQL** (features as bare names — the SQL the agent should *generate*). Mixing them is the most common source of broken `expected_output` and agent drift.

This rulebook does not duplicate the SQL spec. Before writing or scanning Lynk SQL, fetch:

- `https://docs.getlynk.ai/api/lynk-sql.md` — entity references, `METRIC()`, joins, supported statements
- `https://docs.getlynk.ai/file-types/entity-yaml.md` — curly-brace rules in feature-definition `sql:` and metric-over-metric composition
- `https://docs.getlynk.ai/file-types/evaluations-yaml.md` — canonical `expected_output` syntax
- `https://docs.getlynk.ai/file-types/task-instructions-md.md` — SQL example conventions inside task-instructions markdown
- `https://docs.getlynk.ai/file-types/relationships-yaml.md` — relationship `sql:` syntax (`{source}.{field}` / `{destination}.{field}`)

**Private features are a surface violation in generated SQL.** Beyond the two-surface rule above, a generated-SQL snippet (`expected_output`, entity `examples:`, task-instruction / knowledge SQL) must reference only *queryable* features. Internal/private features — by this layer's convention, those whose `name:` begins with an underscore (`_is_…`, `_key`) — are valid **only** inside feature-definition `{…}` SQL; referencing them bare in generated SQL makes the engine fail to resolve the entity. See Rule 10 (point 3) for the detection recipe and fixes.

**In `lynk-build`** — fetch the docs above before writing any SQL; write canonical Lynk SQL from the start. Do not rely on memory; the SQL surface has changed before and may again.

**In `lynk-evaluate`** — fetch the docs above before scanning, then flag any SQL that doesn't match what the current docs say is valid. **Severity: `error`** for surface violations (SQL the engine will not parse). **Severity: `warning`** for forms that may still execute but drift from canonical Lynk SQL and risk causing the agent to reproduce the non-canonical pattern. Cite the relevant docs URL in the suggested fix.

The docs are the source of truth; on any disagreement between a YAML file and the docs, the docs win.

---

## 9. Domain coherence — content scoped to a domain stays on-topic

A file scoped to a named domain (`domain: "marketing"`, `domain: "finance"`, etc.) must (a) have a description of what the domain is about, and (b) hold only content topically aligned with that description. Both requirements — the structural one and the on-topic one — are spelled out in the [knowledge file spec](https://docs.getlynk.ai/file-types/knowledge-md) (Level 2). Apply per that spec; this rule covers only the action protocol when violations are found.

**Fix scopes** (when content fails the on-topic check):
- **Cross-domain** (applies in this domain *and* others) → relocate to `domain: "*"` so every domain inherits it.
- **Belongs to a different single domain** (a finance rule in a marketing file) → relocate to that domain's file.
- **Speculative / nowhere yet** → flag and ask the user whether to keep, relocate, or remove.

**In `lynk-build`** — when adding to a named-domain file, check the existing description and confirm the new content fits. Surface any off-topic sections you notice while reading and offer relocation in the same plan (Rule 3 protocol).

**In `lynk-evaluate`** — flag findings under the `domain-coherence` check group. Quote the offending section's heading and the domain description, and let the user judge.

**Severity: `warning`.** Escalate to **`needs-client-input`** when topical fit is genuinely ambiguous (the section could plausibly belong to two domains, or the description is too vague to anchor the check) — the agent doesn't have authority to decide topical scope unilaterally.

---

## 10. Examples and evaluations must be valid, runnable, and self-consistent

Examples and evaluations are the highest-leverage content in the layer: the agent reuses their shape as in-context patterns, so a broken or misleading one doesn't just fail its own case — it teaches the agent to generate the same broken SQL on live questions. This rule governs **every piece of agent-facing query SQL**:

- every entry under `examples:` in an entity YAML (`input` / `expected_output`),
- every test case in `evaluations.yml` (`input` / `expected_output`),
- every SQL example embedded in task-instruction and knowledge markdown.

Each one must satisfy **all five** of the following. `lynk-build` validates them **before writing** an example/evaluation; `lynk-evaluate` checks 1–3 and 5 statically (Step 6) and confirms 1–4 by execution (Step 7).

1. **Engine dialect (Rule 7).** Valid in the engine declared in `.lynk/config.json`; no constructs borrowed from another dialect.
2. **Lynk SQL surface (Rule 8).** Canonical generated-SQL form — bare entity in `FROM`, bare feature names in `SELECT` / `WHERE` / `GROUP BY`, `METRIC('name') AS alias` (every `METRIC()` aliased), and **no** `{curly_brace}` references (those belong only in feature-definition `sql:`).
3. **Every reference exists *and is queryable* (extends Rule 6a).** Every entity, feature, and metric named must resolve to a YAML definition **and** be referenceable in generated SQL. Not every declared feature is queryable: Lynk keeps *internal/private* features out of the query surface. By the convention this layer uses, a feature whose `name:` begins with an underscore (`_is_…`, `_key`, …) is internal — it resolves **only** inside feature-definition `{…}` SQL (metric / formula / `first_last` filter / join). Referencing one in generated SQL makes the engine fail to resolve the whole entity (observed: `Error during planning: table '<db>.<schema>.<entity>' not found`, or `Feature '_x' does not exist in entity '<e>'`).
   - **Static detection:** for each entity, collect the `name:` values that begin with `_`; flag any bare occurrence of one in agent-facing SQL (inside a `SELECT`, `WHERE`, `GROUP BY`, `IFF(...)`, or an aggregate argument). Mechanical — needs no warehouse.
   - **Authoritative check:** executing the SQL (`lynk-evaluate` Step 7). A private-feature reference fails at plan time even though a naive "is it declared?" check passes — which is why static reference-integrity (Rule 6a) alone is not enough. The docs do not currently document this public/private distinction, so runtime behavior and this convention govern; defer to the docs if they later specify which features are queryable.
   - **Fix:** replace the private reference with (a) the public column it mirrors, via its rollup/literal field (e.g. `LOWER(TRIM(sku_status)) = 'available to capture'` instead of `_is_sku_status_available_to_capture`); (b) a `METRIC()` that already encapsulates the flag; or (c) a newly-exposed **public** (non-`_`) field feature pointing at the same source column. **Severity: `error`** — the SQL will not run.
4. **Semantically correct — `input` ↔ `expected_output`.** The SQL answers the question the `input` asks: its filters, grouping, metric/dimension selection, and time window match the ask. **Severity: `warning`**, escalate to **`error`** when the SQL tests a different entity / metric / dimension than the `input` requests.
5. **No context contradiction (Rule 5).** The SQL honors the default filters, metric choices, ordering, and time windows the owning entity's and domain's task-instructions, knowledge, and glossary declare for that question type. A divergence is a Rule 5 contradiction — **needs-client-input** if the example may be intentionally testing the non-default path, otherwise **`error`**.

Tag findings `local/content-rules-10`, except use the more specific underlying rule when that is the precise cause — `-6` (missing reference), `-7` (dialect), `-8` (surface). A failure surfaced by execution also carries `local/examples-runtime` with the engine's `error_type` / `message`.

---

## 11. Entity keys must actually identify a row

Every entity's `keys` is **mandatory** and names the column(s) that *uniquely identify a row* — Lynk's granularity contract is that each instance appears exactly once in the `key_source`. One or more columns are allowed, so a composite key is valid; there is **no keyless entity**, and leaving `keys` empty fails validation.

The failure this rule catches is a **fabricated key**: a `keys` entry whose column(s) resolve fine (so Rule 6 passes) but aren't actually unique at the table's grain. This is common on event / fact tables with no single unique column — pressured to fill the mandatory field, an agent may promote an arbitrary non-unique column (e.g. `interaction_element_id` on an events table) and rationalize it as "harmless." It isn't: a key that isn't unique is *worse* than a missing one — it's a false grain claim that silently corrupts dedup, joins, and distinct-count results downstream. The right key for such a table is a verified composite, or — if none exists — an honest escalation, never an arbitrary column.

**In `lynk-build`** — source the key from real data: use the catalog's reported `keys`, or derive a candidate and verify it with a `COUNT(*)` vs `COUNT(DISTINCT keys)` query before committing it (build Step 5, capped at 3 candidate attempts, narrating each attempt). Never fabricate a key to satisfy the schema; if no candidate verifies unique, escalate the choice to the user rather than picking one.

**In `lynk-evaluate`** — flag a `keys` that has no uniqueness backing:
   - **Static suspicion — `needs-client-input`.** Uniqueness is a property of the data, so static analysis can only *suspect*. Raise it when: the catalog reports no `keys` for the source yet the entity declares one; or the entity's own description / knowledge calls the source an event / log / activity stream (grains that rarely have a single unique column) and `keys` is a single non-id-looking column. Surface the candidate and the reason.
   - **Authoritative check — `error`.** Run `SELECT COUNT(*) AS rows, COUNT(DISTINCT keys) AS distinct_rows FROM <key_source>` via the query engine (lynk-evaluate Step 7). `distinct_rows < rows` → the key is not unique → **error**. This confirms what Rule 6 can't: a declared, resolvable key that is nonetheless invalid.

Tag findings `local/content-rules-11`.

---

## 12. `related_sources` must not shadow — or be aggregated as — an entity

A `related_source` is **enrichment only**: a flat secondary table with no entity of its own, joined to pull a column or pick one row — never aggregated. Two failures fall under this rule, and both are silent: the YAML resolves, so Rules 2 and 6 pass, yet the model is wrong. The [entity-yaml spec](https://docs.getlynk.ai/file-types/entity-yaml.md) states both ("Only use `related_sources` for tables that are NOT the `key_source` of any entity"; metrics on a related_source are "No — promote the table to an entity instead"); this rule makes them a mechanical check.

**12a. The `related_source` table is also an entity's `key_source` (shadowing).** If a table is the `key_source` of any entity, reach it through `entities_relationships.yml` (a relationship + `source: <entity>` on the feature), never as a `related_source`. A related_source that shadows an entity forks the table into two parallel representations — the entity's metrics/features and the related_source's fields drift, and the agent can't use the entity's metrics through that path.

- **Static detection (mechanical, no warehouse):** for every table under any entity's `related_sources:`, grep for it as a `key_source`. If it appears, it's a violation. `! grep -rn "key_source:" .lynk/ | grep -i "<related_source_table>"`
- **Fix:** remove the `related_source`; add the relationship in `entities_relationships.yml`; repoint features that used the table to `source: <entity_name>` with the relationship's `join_name` (`field` / `first_last`), or to a `metric` feature if you were aggregating it (see 12b). **Severity: `error`.**

**12b. A `related_source` is being aggregated.** `related_sources` support only `field` and `first_last` features — never metrics. If any entity metric (or any `sql:`) counts / sums / averages a column sourced from a `related_source`, that table must be promoted to an entity with its own metrics, then chained in as a `metric` feature.

- **Static detection:** for each `related_source` on an entity, collect the `name:` of every `field` / `first_last` feature whose `source:` is that table; flag any entity `metrics:` `sql:` that references one of those `{names}` inside an aggregate (`COUNT` / `SUM` / `AVG` / …).
- **Fix:** create an entity whose `key_source` is the table, move the aggregation there as an entity metric, add a relationship, and pull the result onto the original entity as a `metric` feature. **Severity: `error`.**

Tag findings `local/content-rules-12`.

---

## Quick check before saving / before closing an audit

For each file you touched (build) or read (evaluate), ask:

1. **Right place?** — Does each item match the file-type spec from the docs (Rule 2)?
2. **Clear and meaningful?** — Does each description / instruction tell the agent what to do (Rule 4)?
3. **Appears once?** — Scan related files for the same content; flag duplicates (Rule 1).
4. **Internally consistent?** — Do the definitions in this file agree with related files in meaning, not just in style (Rule 5)?
5. **All references resolve?** — Does every named feature, metric, entity, or relationship exist in some YAML (Rule 6a)? Does every concept the prose implies have a backing definition (Rule 6b)? Does every `keys:` entry name a **defined feature** (not a raw warehouse column), with that feature's `name` equal to its column to dodge the `KEYS.<COL>` engine bug (Rule 6c)?
6. **Engine-compatible SQL?** — Does every SQL snippet use only constructs valid in the warehouse engine declared in `.lynk/config.json` (Rule 7)?
7. **Lynk SQL syntax correct for context?** — Does every SQL snippet match the canonical form specified in the docs linked from Rule 8 (`{feature_name}` references in feature-definition `sql:`; bare features, bare entities, and canonical `METRIC()` / join forms in `expected_output` and SQL examples)?
8. **Domain on-topic?** — For files scoped to a named domain: does the file have a domain description, and does each section fit it (Rule 9)?
9. **Examples & evaluations valid?** — For every entity `examples:` entry, every `evaluations.yml` case, and every SQL example in task-instructions / knowledge: right dialect, canonical surface, all references exist **and are queryable** (no private `_`-prefixed features in generated SQL), semantically answers its `input`, and contradicts no context default (Rule 10)?
10. **Keys real?** — Does every entity's `keys:` actually identify a row — catalog-reported or verified unique — rather than a fabricated non-unique column (Rule 11)?
11. **Related-sources legit?** — Is every `related_sources` table free of an entity `key_source` (not shadowing an entity) and never aggregated by a metric (Rule 12)?

If the answer to any of these is "no" or "I'm not sure," the work isn't done.
