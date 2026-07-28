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
  glossary", "audit my skills and policies", "evaluate player",
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

Use that output to identify the last 3 distinct `.lynk/` artifacts that were modified. Collapse each path to its owning artifact — the entity, skill, or policy folder, or the `GLOSSARY.yml` / `LYNK.md` file — and present a clean artifact name (e.g., `player entity`, `core glossary`, `churn-investigation skill`).

Present these options to the user:
- **Option 1** — Last edited artifact (e.g., `player entity`)
- **Option 2** — Second-to-last edited artifact
- **Option 3** — Third-to-last edited artifact
- **Option 4** — Evaluate the entire semantic graph end-to-end

If git history doesn't yield 3 distinct artifacts, fill remaining slots with sensible defaults (e.g., the glossary, the root `LYNK.md`, or the largest entity in the domain).

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
| Specific entity | The entity's `schema.yml` + `ENTITY.md` (+ files its prose `@`-injects) + the domain's `LYNK.md` and `GLOSSARY.yml` + the root `LYNK.md` and `GLOSSARY.yml` |
| Entity + related entities | Same as above, but for the seed entity AND every entity its `entity_relationships:` target |
| Glossary | The root `GLOSSARY.yml` + the domain's (they merge; the domain wins on key collisions) |
| Skill or policy | The `SKILL.md` / `POLICY.md` + every definition it references (`@` paths, named features/metrics) |
| Full semantic graph | Everything under `.lynk/` — `lynk.yml`, root files, and every domain's entities, skills, and policies |

If the user asked about a **specific metric, feature, or relationship** on an entity, still evaluate the full entity context — but lead your response with the specific item they asked about.

---

### 3. Read the target files

Read only the files identified in Step 2. For entity evaluation, read in this order:
1. The entity's `schema.yml`
2. The entity's `ENTITY.md` (and anything it `@`-injects)
3. The domain's `LYNK.md` + the root `LYNK.md`
4. The domain's `GLOSSARY.yml` + the root `GLOSSARY.yml`
5. Skills and policies in the domain that reference the entity

For multi-entity evaluation (seed + related), read the seed's `entity_relationships:` in `schema.yml` first to determine the related entity set, then read each entity's files.

---

### 4. Read the relevant docs and detect the SQL engine

- **Always read `references/docs/SUMMARY.md` first** to see the doc tree — the placement check (Rule 2 of `references/content-rules.md`) in Step 6 depends on knowing what file-type specs exist. Then `Read` only the spec pages under `references/docs/concepts/` relevant to the targets in Step 2. (The doc-navigation convention is in `references/docs/CLAUDE.md`.) All `references/…` paths resolve from the plugin root — `${CLAUDE_PLUGIN_ROOT}` when installed as a plugin, the repo root when working in this repo — not the user's CWD.
- **Detect the engine.** The v2 layer does not declare the engine — `lynk.yml` carries only `schema_version`, `topology`, and `name`. Determine it from the user via `AskUserQuestion` (common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`) or from the data catalog via `lynk-sources` — do not guess. Record the dialect; every SQL check in Step 6 keys off it.

---

### 5. Run the backend validity check

Run the `lynk-validate` flow — its **steps 1–5** (branch detection, dirty-tree handling, origin check, token check, API call) — **without producing validate's report**. Capture the raw issue list for merging into the unified report in Step 7.

If validate skips (no token, user cancelled at the dirty-tree prompt, or branch not on origin), record the skip reason as one of: `no token`, `user cancelled`, `branch not on origin`. **Do not abort the evaluation** — local checks in Step 6 still run regardless.

---

### 6. Evaluate locally

For each finding, record: **severity** (error / warning / needs-client-input / suggestion), **location** (file + field or feature name), **what's wrong**, **how to fix it**.

Apply these check groups against the target files:

- **Content rules** — apply every rule in `references/content-rules.md` (Rules 1–11; the rule index is at the top) against the target files, and tag each finding `local/content-rules-<N>` with its rule number. The Quick check at the bottom of `content-rules.md` is the minimum coverage — skip nothing.
- **YAML & structure** — mirror the build's own validation locally so violations are caught *before* a commit (the authoritative rules live in the Validation sections of the specs under `references/docs/concepts/`): required fields present and **no unknown YAML keys** (the field tables are exhaustive — a `tags:` or `time_grain:` fails the build); `name`s unique within the entity across features, metrics, and relationships, and metric names unique across the **whole domain**; the feature/metric dependency graph acyclic; `join_name` present whenever `sql`/`filter` reaches beyond the entity's own identity source and features; entity-relationship steps targeting only entities (bridges modeled as entities) and joining only on **declared features** — keys are not features; `keys:` authored when `identity` is a physical table and *not* re-authored under extension; no templating anywhere in `sql:`. **Severity: `error`** (these fail the build). Tag `local/yaml-sql-structure`.

When two files disagree on the *intended* behavior (e.g. a skill's procedure vs. an `ENTITY.md` convention), mark it **needs-client-input** rather than picking a side (see Rule 5 of `content-rules.md`).

---

### 7. Optionally probe key uniqueness against the warehouse (gated, calls query-engine)

Key uniqueness is a property of the *data*, so Step 6 can only suspect a fabricated key (Rule 11 static suspicion) — this step is the **authoritative confirmation**. Scope: each in-scope entity that Step 6 flagged `needs-client-input` under Rule 11, or whose identity table the catalog reports no `keys` for.

**Ask the user first** via `AskUserQuestion`:

> *"Probe the declared keys of <N> entities against the warehouse (one fast `COUNT(*)` vs `COUNT(DISTINCT …)` query each)? Yes / Skip."*

This is opt-in. Never run it without asking — it dispatches real queries to the warehouse.

**If the user opts in,** for each entity in scope delegate to `lynk-sources` to run `SELECT COUNT(*) AS rows, COUNT(DISTINCT <keys>) AS distinct_rows FROM <identity_table> LIMIT 1` (composite keys → count the distinct concatenation). Use the same branch and domain `lynk-evaluate` is operating on.

- `distinct_rows == rows` → the key holds; note it as verified in the report.
- `distinct_rows < rows` → the declared key doesn't uniquely identify a row → **error**, tagged `local/content-rules-11`; quote both counts in the finding.
- A `4xx`/`5xx` from the engine → surface the error verbatim and recommend running `lynk-validate` on the branch; don't retry blindly.

If the user picks **Skip** or nothing is in scope, record the skip reason and continue to Step 8.

---

### 8. Produce the evaluation report

Merge the backend issues from Step 5 with the static local findings from Step 6 and the key-probe findings from Step 7 (if that step ran) into one unified report. Each issue carries a source tag so the user knows where it came from.

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

**Source tag values.** Every finding carries one tag so the user can tell at a glance where it came from — the backend API, a local rule, or the warehouse probe. Three shapes:

- `backend/<scope>/<category>` — raised by the `lynk-validate` API call in Step 5. `<scope>` is `entity` / `relationship` / `context`; `<category>` is `schema` (declarative YAML check) or `warehouse` (the backend ran a `LIMIT 0` probe and the engine rejected it). The `warehouse` category replaces the legacy `semantic` value — same tag shape, the enum just changed when validate moved to the builds endpoint.
- `local/content-rules-<N>` — raised by a content rule in Step 6 or the Step 7 key probe; `<N>` is the rule number (see the rule index at the top of `references/content-rules.md`). Note: Rule 3 is action protocol, not a detection — misplacement findings get tagged `content-rules-2` and cite Rule 3 in the suggested fix.
- `local/yaml-sql-structure` — raised by the structural validation group in Step 6 (required fields, no unknown keys, name uniqueness, acyclic dependencies, `join_name` rules, keys-are-not-features).

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

3. **Re-check locally:** re-run **Steps 3 and 6 only** (re-read the edited files; re-do local checks). Skip Step 4 (engine/docs unchanged), Step 5 (backend won't see uncommitted changes), and Step 7 (don't re-dispatch warehouse calls inside the loop — running mid-loop would burn the user's warehouse credits per iteration).

4. **Repeat** with the iteration number in the prompt (`Attempt 2 of 3 — <N> issues remain. Fix? Stop?`). **After iteration 3, exit unconditionally** even if issues remain. Tell the user: *"Reached the 3-attempt cap. <N> issues remain — fix manually, or re-run `lynk-evaluate` to start a fresh loop."* This cap is non-negotiable; it prevents runaway loops if the agent can't converge.

5. If the user picks **Stop** at any iteration, exit immediately and leave the remaining issues in the final report.

**Backend re-check (post-loop).** If Step 5 reported backend issues *and* any fixes were applied during the loop, ask the user once: *"Commit your fixes and re-run the backend check?"*. If yes, run the full `lynk-validate` flow (it handles commit-and-push and the API call). Otherwise, leave the original backend findings in the report annotated `(initial check; may be stale after local fixes)`.

**Key-probe re-check (post-loop).** If Step 7 ran and reported key-uniqueness errors *and* the keys were changed during the loop, ask the user once: *"Re-probe the affected entities' keys against the warehouse to confirm they now hold?"*. If yes, re-dispatch only the previously-failing probes — not the full set.

For **full graph evaluation**, group findings by entity/file rather than by severity tier, so the user can focus on one entity at a time.

---

## Output Format

- Always state the detected engine on the summary line so the user knows which dialect rules were applied.
- Use code blocks when quoting YAML field names, feature names, or SQL snippets.
- Reference exact file paths so the user can navigate directly.
- Be specific about locations — say `player/schema.yml → feature: career_points → sql references metric(game.nonexistent_metric)` not just "a feature has an issue".
- Lead with the most important findings; don't bury critical errors at the bottom.
- If you find issues in the files, offer to fix them — but only after completing the full report.
