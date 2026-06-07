---
name: lynk-evaluate
description: >
  Evaluate the Lynk semantic layer in `.lynk/` — judge whether it is good enough
  for the AI agent to use, not just whether the YAML parses. Checks description
  quality, cross-file consistency, content placement, reference integrity, and
  SQL dialect compatibility against the user's warehouse engine.

  Use this skill whenever the user asks to evaluate, audit, review, assess, or
  diagnose the semantic layer or any part of it. Trigger on phrases like
  "evaluate the semantics", "is this good enough for the agent", "audit my
  entities", "check description quality", "any contradictions in my context",
  "will my SQL run on Snowflake", "will this work on BigQuery", "review the
  glossary", "check my evaluations against instructions", "evaluate player",
  "is the semantic layer well structured", or any request to assess the quality
  of files inside `.lynk/`.
---

# lynk-evaluate-semantics

## Steps

### 1. Determine what to evaluate

If the user has **not** specified what to evaluate, use the `AskUserQuestion` tool to ask them. Before presenting options, check git history to surface recently edited artifacts:

```
! git log --oneline --diff-filter=M --name-only -20 -- .lynk/ | head -40
```

Use that output to identify the last 3 distinct `.lynk/` artifacts that were modified (entity YAML, knowledge file, task instructions, glossary, evaluations, etc.). Strip the domain path and file extension to present a clean artifact name (e.g., `player entity`, `nba_glossary`, `evaluations`).

Present these options to the user:
- **Option 1** — Last edited artifact (e.g., `player entity`)
- **Option 2** — Second-to-last edited artifact
- **Option 3** — Third-to-last edited artifact
- **Option 4** — Evaluate the entire semantic graph end-to-end

If git history doesn't yield 3 distinct artifacts, fill remaining slots with sensible defaults (e.g., the glossary, evaluations, or the largest entity in the domain).

Once the user selects, continue to Step 2 with the chosen target.

---

### 2. Locate the target files

Scan the semantic layer file tree:

```
! find ./.lynk -type f | sort
```

Based on the user's selection, identify the relevant files:

| Evaluation target | Files to read |
|---|---|
| Specific entity | Entity YAML + its knowledge file + its task instructions file + domain knowledge + domain task instructions + glossary |
| Entity + related entities | Same as above, but for the seed entity AND every entity it is related to (via `entities_relationships.yml`) |
| Glossary | The glossary file only |
| Full semantic graph | All entity YAMLs + all knowledge/task instruction files + glossary + domain context + evaluations + relationships |
| Evaluations | `evaluations.yml` + all entity YAMLs (to verify references) |

If the user asked about a **specific metric, feature, or relationship** on an entity, still evaluate the full entity context — but lead your response with the specific item they asked about.

---

### 3. Read the target files

Read only the files identified in Step 2. For entity evaluation, read in this order:
1. Entity YAML
2. Entity knowledge file
3. Entity task instructions file
4. Domain knowledge + domain task instructions
5. Glossary

For multi-entity evaluation (seed + related), read `entities_relationships.yml` first to determine the related entity set, then read each entity's files.

---

### 4. Read the relevant docs and detect the SQL engine

- **Always fetch `https://docs.getlynk.ai/llms.txt` first** to see the doc tree — the placement check (Rule 2 of `references/content-rules.md`) in Step 6 depends on knowing what file-type specs exist. Then `WebFetch` only the `concepts/<concept>` and `file-types/<type>` pages relevant to the targets in Step 2. (The doc-navigation convention is in `references/lynk-docs.md`.)
- **Detect the engine.** Read `.lynk/config.json` and look for an `engine`, `dialect`, or `warehouse` field. Common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`. If the field is missing, empty, or the file doesn't exist, ask the user via `AskUserQuestion` — do not guess. Record the dialect; every SQL check in Step 6 keys off it.

---

### 5. Run the backend validity check

Run the `lynk-validate` flow — its **steps 1–5** (branch detection, dirty-tree handling, origin check, token check, API call) — **without producing validate's report**. Capture the raw issue list for merging into the unified report in Step 7.

If validate skips (no token, user cancelled at the dirty-tree prompt, or branch not on origin), record the skip reason as one of: `no token`, `user cancelled`, `branch not on origin`. **Do not abort the evaluation** — local checks in Step 6 still run regardless.

---

### 6. Evaluate locally

For each finding, record: **severity** (error / warning / needs-client-input / suggestion), **location** (file + field or feature name), **what's wrong**, **how to fix it**.

Apply these check groups against the target files:

- **Content rules** — apply every rule in `references/content-rules.md` (Rules 1–12; the rule index is at the top) against the target files, and tag each finding `local/content-rules-<N>` with its rule number. The Quick check at the bottom of `content-rules.md` is the minimum coverage — skip nothing.
- **YAML & SQL structure** — required fields present, `{}` placeholders in metric SQL, `METRIC()` wrapping where required, no aggregates inside formula features, no circular formula dependencies, no duplicate feature / metric / relationship keys.
- **Examples & evaluations quality** — covers every `examples:` entry in entity YAMLs, every `evaluations.yml` case, **and** every SQL example in task-instruction / knowledge markdown; the agent learns its query patterns from all three, so a broken one teaches a broken pattern. Four sub-checks (detection detail lives in the cited rules):
  - **Validity & queryability** [`local/content-rules-10`] — apply Rule 10 (dialect, canonical surface, references exist *and are queryable* — the mechanical `_`-prefix scan is in the rule). **Severity: `error`.**
  - **Input ↔ expected_output coherence** [`local/examples-quality`] — the SQL's filters, grouping, metric/feature selection, and time window match what the `input` asks (Rule 10 point 4). **Severity: `warning`**, escalate to **`error`** when the divergence changes which entity / metric / dimension is tested.
  - **Description ↔ test alignment** [`local/examples-quality`] — the `description` states what the case actually tests. **Severity: `warning`**. Pure description red flags (tautological, placeholder) belong under Rule 4.
  - **Default-filter consistency** [`local/content-rules-5`] — every default filter the task-instructions declare for that question type appears in `expected_output` (Rule 5). **needs-client-input** if the omission might be intentional, otherwise **`error`**.

When examples and task instructions disagree on the *intended* behavior, mark it **needs-client-input** rather than picking a side (see Rule 5 of `content-rules.md`).

---

### 7. Optionally execute every example and evaluation (gated, calls query-engine)

Some failures only surface when the SQL actually runs — a column the engine doesn't expose, a relationship that doesn't resolve, a metric whose `sql:` produces a warehouse error, or a **private `_`-prefixed feature** referenced in generated SQL (Rule 10 point 3), which passes a naive "is it declared?" check but fails at plan time. The static checks in Step 6 catch what's reasonably checkable from the YAML alone (including the mechanical `_`-prefix scan); this step is the **authoritative confirmation** — it executes each `expected_output` against the warehouse. Scope: every entry under `examples:` in entity YAMLs and every `evaluations.yml` test case. SQL examples embedded in task-instruction / knowledge markdown often carry placeholders (`<company>`, a `dimension` stand-in) and are covered by the Step 6 static Rule 10 check rather than executed here; run one only if you substitute realistic literals first.

**Key-uniqueness probe (Rule 11).** This same gated, warehouse-calling pass is also where a *suspected* fabricated key gets confirmed. When the user opts in (any answer but **Skip**), then for each in-scope entity that Step 6 flagged `needs-client-input` under Rule 11 — or whose source the catalog reports no `keys` for — delegate to `lynk-sources` to run `SELECT COUNT(*) AS rows, COUNT(DISTINCT keys) AS distinct_rows FROM <key_source> LIMIT 1`. `distinct_rows < rows` → the declared key doesn't uniquely identify a row → **error**, tagged `local/content-rules-11`; quote both counts in the finding. This is the authoritative confirmation of the Rule 11 static suspicion (Step 6 can only suspect; uniqueness is a property of the data).

**Ask the user first** via `AskUserQuestion`:

> *"Run every example and evaluation against the warehouse via `query-engine/query` (with `LIMIT 1` so each call is fast)? Yes / Yes, evaluations only / Yes, examples only / Skip."*

This is opt-in. Never run it without asking — it dispatches real queries to the warehouse and takes seconds to tens of seconds per call.

**If the user opts in,** for each `expected_output` in scope:

1. **Apply `LIMIT 1`.** If the SQL already has a `LIMIT`, leave it; if it has none, append `LIMIT 1`. Do not wrap the query in a subquery — subqueries change the `semantics_used` shape returned by the engine and complicate error reporting.
2. **Delegate to `lynk-sources`** with the "Run Lynk SQL" action (`POST query-engine/query`, body is the SQL as a JSON-encoded string — see lynk-sources Step 3 for invocation, and `references/rest-api.md` for the full endpoint shape). Use the same branch and domain `lynk-evaluate` is operating on.
3. **Record the outcome:**
   - `200` → **pass**. Optionally capture `metadata.query_metadata.semantics_used` so the report can compare resolved entities / features against what the case claims to test (a case named "tests refund metric" whose `semantics_used.metrics` doesn't include the refund metric is a real finding).
   - `422` with `error_type: SemanticsConsumptionError` → **error**, tagged `local/examples-runtime`. Surface the `message` verbatim ("Feature 'X' does not exist in entity 'Y'") and quote the offending SQL line.
   - `500` with `error_type: InternalError` and `message: "SQL error: ParserError(...)"` → **error**, tagged `local/examples-runtime`. Quote the parser message.
   - `500` with bare `"Request failed"` and no `detail` envelope → **needs-client-input**, tagged `local/examples-runtime`. The branch's semantic layer is itself in a broken state; running examples isn't meaningful until the underlying layer validates. Recommend running `lynk-validate` on the same branch first.
4. **Cap the dispatch.** If more than ~30 queries are in scope, re-prompt the user to narrow scope ("Run all 87, or only the ones in the entity we're evaluating?"). Don't silently dispatch 100+ warehouse calls.

Merge runtime findings into the Step 8 report alongside the static ones — same severity tiers, separate source tag (`local/examples-runtime`).

If the user picks **Skip** or the step was bypassed (no examples / no evaluations in scope), record the skip reason and continue to Step 8.

---

### 8. Produce the evaluation report

Merge the backend issues from Step 5 with the static local findings from Step 6 and the runtime findings from Step 7 (if that step ran) into one unified report. Each issue carries a source tag so the user knows where it came from.

**If the user asked about a specific metric / feature / relationship:** lead with a focused section on that item — its evaluation result, issues, and suggested fixes — before the broader entity report.

**Report structure:**

```
## Evaluation Report — [Target Name] (engine: [dialect]) · Backend: [ok | <n> errors, <m> warnings | skipped: <reason>]

### Summary
[1-2 sentences: overall health, number of issues by severity, dialect applied, backend status]

### Errors (must fix)
- **[Location]** [backend/<scope>/<category> | local/<check-group>]: [What's wrong] → [How to fix]

### Warnings (should fix)
- **[Location]** [backend/... | local/...]: [What's wrong] → [How to fix]

### Needs client input
- **[Location]** [local/...]: [Conflict between instructions and examples / unresolvable intent] → [What you need from the user]

### Suggestions (nice to have)
- **[Location]** [local/...]: [What could be improved] → [Suggested improvement]

### What looks good
- [Bullet list of things that are well-modeled — be specific]
```

**Source tag values.** Every finding carries one tag so the user can tell at a glance where it came from — the backend API, a local rule, a content-quality check, or the runtime execution. Five shapes:

- `backend/<scope>/<category>` — raised by the `lynk-validate` API call in Step 5. `<scope>` is `entity` / `relationship` / `context`; `<category>` is `schema` / `semantic`.
- `local/content-rules-<N>` — raised by a content rule in Step 6; `<N>` is the rule number (see the rule index at the top of `references/content-rules.md`). Note: Rule 3 is action protocol, not a detection — misplacement findings get tagged `content-rules-2` and cite Rule 3 in the suggested fix.
- `local/yaml-sql-structure` — raised by the structural validation group in Step 6 (required fields, `{}` placeholders, `METRIC()` wrapping, no aggregates in formulas, no circular formulas, no duplicate keys).
- `local/examples-quality` — raised by the examples & evaluations quality group in Step 6 for the *semantic-alignment* sub-checks (input ↔ expected_output coherence, description ↔ test alignment). The same group's validity & queryability sub-check is tagged `local/content-rules-10`, and its default-filter-consistency sub-check is tagged `local/content-rules-5`.
- `local/examples-runtime` — raised by the optional runtime-execution pass in Step 7 (the `expected_output` SQL didn't execute against the warehouse). Carries the `error_type` and `message` from the engine response.

When the backend was skipped, the summary's `Backend:` field reads `skipped: <reason>` and the report contains only `[local/...]` issues. Mention the skip reason explicitly in the Summary paragraph so the user knows backend issues weren't checked.

If no issues are found in a severity tier, omit that section entirely.

---

### 9. Offer fixes and re-evaluate (bounded loop, hard cap 3)

If the report has errors or warnings, this skill — **and only this skill** — drives the fix-and-recheck loop. Build's Step 8 and validate's Output Format defer here; never run a parallel fix loop in those skills.

For each iteration (max 3):

1. **Offer fixes via `AskUserQuestion`:**
   - If errors exist: single option `Fix all <N> errors and ask about warnings`, plus `Stop — accept remaining issues`.
   - If only warnings exist: present them as `multiSelect: true` so the user picks which to fix. Include `Stop`.
   - Suggestions are never auto-fixed; mention them but don't include in the offer.

2. **If the user opts in:** delegate the edits to `lynk-build` Steps 6–7 (plan and confirm, then execute). Build re-reads the relevant docs as part of its normal flow, so every fix attempt stays doc-grounded.

3. **Re-check locally:** re-run **Steps 3 and 6 only** (re-read the edited files; re-do local checks). Skip Step 4 (engine/docs unchanged), Step 5 (backend won't see uncommitted changes), and Step 7 (don't re-dispatch warehouse calls inside the loop — runtime issues that were already reported will still be reported on commit, and running mid-loop would burn the user's warehouse credits per iteration).

4. **Repeat** with the iteration number in the prompt (`Attempt 2 of 3 — <N> issues remain. Fix? Stop?`). **After iteration 3, exit unconditionally** even if issues remain. Tell the user: *"Reached the 3-attempt cap. <N> issues remain — fix manually, or re-run `lynk-evaluate` to start a fresh loop."* This cap is non-negotiable; it prevents runaway loops if the agent can't converge.

5. If the user picks **Stop** at any iteration, exit immediately and leave the remaining issues in the final report.

**Backend re-check (post-loop).** If Step 5 reported backend issues *and* any fixes were applied during the loop, ask the user once: *"Commit your fixes and re-run the backend check?"*. If yes, run the full `lynk-validate` flow (it handles commit-and-push and the API call). Otherwise, leave the original backend findings in the report annotated `(initial check; may be stale after local fixes)`.

**Runtime re-check (post-loop).** If Step 7 ran and reported `local/examples-runtime` issues *and* fixes were applied, ask the user once: *"Re-run the affected examples / evaluations against the warehouse to confirm they now execute?"*. If yes, re-dispatch only the previously-failing queries — not the full set.

For **full graph evaluation**, group findings by entity/file rather than by severity tier, so the user can focus on one entity at a time.

For **evaluations evaluation**, group findings by evaluation name and add a coverage summary at the top showing entity distribution.

---

## Output Format

- Always state the detected engine on the summary line so the user knows which dialect rules were applied.
- Use code blocks when quoting YAML field names, feature names, or SQL snippets.
- Reference exact file paths so the user can navigate directly.
- Be specific about locations — say `player.yml → feature: career_points → metric: nonexistent_metric` not just "a feature has an issue".
- Lead with the most important findings; don't bury critical errors at the bottom.
- If you find issues in the files, offer to fix them — but only after completing the full report.
