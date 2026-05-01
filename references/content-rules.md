# Content Rules — Placement, Clarity, Consistency

These rules govern every edit (`lynk-build`) and every audit (`lynk-evaluate`) of files inside `.lynk/`. Both skills enforce the same rulebook so a file passes evaluate if and only if it would have passed build.

The rules are prescriptive: each one says what good looks like and what the agent must do when it sees a violation.

---

## 1. Single source of truth

Each instruction, definition, or rule lives in exactly **one** file.

When adding new content, first check whether it (or something equivalent) already exists somewhere in `.lynk/`. If it does:
- If the existing location is correct per Rule 2 → link to it from your edit's plan, do not duplicate.
- If the existing location is wrong per Rule 2 → relocate it (Rule 3), then add your new content to the correct file.

When auditing, flag any content that appears in two places (verbatim or near-verbatim) — even if both copies look correct individually. Two copies will drift; one of them ends up wrong.

**Severity: `warning`.** Duplicates will drift over time. If two copies *already contradict each other*, escalate as a Rule 5 contradiction (`needs-client-input`) — the contradiction is more urgent than the duplication.

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
- A metric referenced as `metric('total_arr')` in an example → must exist in some entity's `metrics:`.
- A feature referenced in a knowledge file (`use the customer_lifetime_value field`) → must exist in the entity's `features:`.
- An entity referenced in a join, evaluation, or example (`FROM entity('subscription')`) → must have its own YAML.
- A `join_name` used in a feature → must exist in `entities_relationships.yml`.

**Severity: `error`.** A broken reference means the agent will fail to resolve a query — this is not a style issue.

**6b. Implied-but-undefined.** Content described in prose without a backing definition. Examples:
- A knowledge file says *"we report MRR weekly"* but no `mrr` metric exists.
- A task instruction references *"the high-value customer segment"* but no feature flags it.
- The glossary defines a term that no entity, metric, or feature surfaces.

**Severity: `warning`.** The agent will be unable to answer cleanly when asked about something the prose says exists.

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

**In `lynk-build`** — write SQL using the detected engine's syntax from the start. When a portable form exists, prefer it over an engine-specific shortcut. Don't assume a dialect; if engine isn't yet detected, detect first.

**In `lynk-evaluate`** — scan every SQL snippet against the detected engine and flag dialect-incompatible constructs. **Severity: `error`.** The SQL will fail at runtime, not at parse time, so the user won't see the issue until they run a query.

---

## Quick check before saving / before closing an audit

For each file you touched (build) or read (evaluate), ask:

1. **Right place?** — Does each item match the file-type spec from the docs (Rule 2)?
2. **Clear and meaningful?** — Does each description / instruction tell the agent what to do (Rule 4)?
3. **Appears once?** — Scan related files for the same content; flag duplicates (Rule 1).
4. **Internally consistent?** — Do the definitions in this file agree with related files in meaning, not just in style (Rule 5)?
5. **All references resolve?** — Does every named feature, metric, entity, or relationship exist in some YAML (Rule 6a)? Does every concept the prose implies have a backing definition (Rule 6b)?
6. **Engine-compatible SQL?** — Does every SQL snippet use only constructs valid in the warehouse engine declared in `.lynk/config.json` (Rule 7)?

If the answer to any of these is "no" or "I'm not sure," the work isn't done.
