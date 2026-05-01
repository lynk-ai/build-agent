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

- **Always fetch `https://docs.getlynk.ai/llms.txt` first** to see the doc tree — the "right thing in the right file" check in Step 6 depends on knowing what file-type specs exist. Then `WebFetch` only the `concepts/<concept>` and `file-types/<type>` pages relevant to the targets in Step 2.
- **Detect the engine.** Read `.lynk/config.json` and look for an `engine`, `dialect`, or `warehouse` field. Common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`. If the field is missing, empty, or the file doesn't exist, ask the user via `AskUserQuestion` — do not guess. Record the dialect; every SQL check in Step 6 keys off it.

---

### 5. Run the backend validity check

Run the `lynk-validate` flow — its **steps 1–5** (branch detection, dirty-tree handling, origin check, token check, API call) — **without producing validate's report**. Capture the raw issue list for merging into the unified report in Step 7.

If validate skips (no token, user cancelled at the dirty-tree prompt, or branch not on origin), record the skip reason as one of: `no token`, `user cancelled`, `branch not on origin`. **Do not abort the evaluation** — local checks in Step 6 still run regardless.

---

### 6. Evaluate locally

For each finding, record: **severity** (error / warning / needs-client-input / suggestion), **location** (file + field or feature name), **what's wrong**, **how to fix it**.

Apply these check groups against the target files:

- **Content rules** — apply every rule in `references/content-rules.md` against the target files: single source of truth (Rule 1), correct placement per the docs (Rule 2), description clarity and red flags (Rule 4), cross-file consistency (Rule 5), and reference integrity (Rule 6). Use the rule numbers in the report's `local/<check-group>` tag — e.g. `local/content-rules-2` for a misplaced metric definition. The quick check at the bottom of `content-rules.md` is the minimum coverage; nothing in the target files should be skipped.
- **YAML & SQL structure** — required fields present, `{}` placeholders in metric SQL, `METRIC()` wrapping where required, no aggregates inside formula features, no circular formula dependencies, no duplicate feature / metric / relationship keys.
- **Engine compatibility** — for the engine detected in Step 4, scan every SQL snippet (metric SQL, formula SQL, `first_last` filters, relationship joins, entity examples, evaluation `expected_output`) for dialect-incompatible constructs. Examples: `QUALIFY` and `IFF` are Snowflake-only; `SAFE_*` and backtick identifiers are BigQuery-only; `DATEADD/DATEDIFF` syntax differs across BigQuery / Snowflake / Postgres.

When examples and task instructions disagree on the *intended* behavior, mark it **needs-client-input** rather than picking a side. (This is Rule 5 of `content-rules.md` applied at the cross-file level.)

---

### 7. Produce the evaluation report

Merge the backend issues from Step 5 with the local findings from Step 6 into one unified report. Each issue carries a source tag so the user knows where it came from.

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

Source tag values:
- `backend/<scope>/<category>` — from the API. `<scope>` is `entity` / `relationship` / `context`; `<category>` is `schema` / `semantic`.
- `local/content-rules-<N>` — from Step 6 content-rules application. `<N>` is the rule number from `references/content-rules.md` (1 single-source, 2 placement, 3 misplaced-relocation, 4 description-clarity, 5 consistency, 6 reference-integrity).
- `local/<check-group>` — from Step 6's other groups: `yaml-sql-structure`, `engine-compatibility`.

When the backend was skipped, the summary's `Backend:` field reads `skipped: <reason>` and the report contains only `[local/...]` issues. Mention the skip reason explicitly in the Summary paragraph so the user knows backend issues weren't checked.

If no issues are found in a severity tier, omit that section entirely.

---

### 8. Offer fixes and re-evaluate (bounded loop, hard cap 3)

If the report has errors or warnings, this skill — **and only this skill** — drives the fix-and-recheck loop. Build's Step 8 and validate's Output Format defer here; never run a parallel fix loop in those skills.

For each iteration (max 3):

1. **Offer fixes via `AskUserQuestion`:**
   - If errors exist: single option `Fix all <N> errors and ask about warnings`, plus `Stop — accept remaining issues`.
   - If only warnings exist: present them as `multiSelect: true` so the user picks which to fix. Include `Stop`.
   - Suggestions are never auto-fixed; mention them but don't include in the offer.

2. **If the user opts in:** delegate the edits to `lynk-build` Steps 6–7 (plan and confirm, then execute). Build re-reads the relevant docs as part of its normal flow, so every fix attempt stays doc-grounded.

3. **Re-check locally:** re-run **Steps 3 and 6 only** (re-read the edited files; re-do local checks). Skip Step 4 (engine/docs unchanged) and Step 5 — the backend won't see uncommitted changes, so re-running validate mid-loop would just return the same issues.

4. **Repeat** with the iteration number in the prompt (`Attempt 2 of 3 — <N> issues remain. Fix? Stop?`). **After iteration 3, exit unconditionally** even if issues remain. Tell the user: *"Reached the 3-attempt cap. <N> issues remain — fix manually, or re-run `lynk-evaluate` to start a fresh loop."* This cap is non-negotiable; it prevents runaway loops if the agent can't converge.

5. If the user picks **Stop** at any iteration, exit immediately and leave the remaining issues in the final report.

**Backend re-check (post-loop).** If Step 5 reported backend issues *and* any fixes were applied during the loop, ask the user once: *"Commit your fixes and re-run the backend check?"*. If yes, run the full `lynk-validate` flow (it handles commit-and-push and the API call). Otherwise, leave the original backend findings in the report annotated `(initial check; may be stale after local fixes)`.

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
