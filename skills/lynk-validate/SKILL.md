---
name: lynk-validate
description: >
  Run the Lynk backend's semantics build (`POST /api/semantics/builds`) to
  confirm the layer in `.lynk/` on a committed branch is valid — returning a
  build object (`status: valid|invalid`) with any schema errors, broken source
  references, or warehouse-query rejections.

  Use when the user wants to validate the layer or confirm a build. The endpoint
  is "builds", so also trigger on "the build", "the semantics build", "did the
  build pass". Triggers: "validate the semantic layer", "is my .lynk valid",
  "validate on dev", "any schema errors", "force a rebuild". For content quality
  (not validity), use `lynk-evaluate`.
---

# lynk-validate

## Steps

### 1. Determine the branch

The Lynk backend validates against the **committed remote branch**. Default to the current local branch:

```
! git rev-parse --abbrev-ref HEAD
```

If the user specified a branch ("validate on `main`", "validate the inquiries branch"), use that instead. If the result is `HEAD` (detached) or empty, default to `main`.

### 2. Check the working tree against the remote

The backend reads `origin/<branch>`, so uncommitted local changes won't be seen. Check status and ahead-of-remote commits in `.lynk/`:

```
! git status --porcelain -- .lynk/
! git log origin/<branch>..HEAD --oneline -- .lynk/
```

If there are local changes inside `.lynk/` (uncommitted or unpushed):

- Show a short summary (`git diff --stat -- .lynk/` plus the ahead-of-remote commits).
- Ask via `AskUserQuestion` how to proceed:
  - **Commit and push, then validate** — ask for a commit message, then `git add .lynk/ && git commit -m "<msg>" && git push origin <branch>`. **Stage only `.lynk/`** — never `git add -A`, to avoid pulling in `.env` or unrelated work.
  - **Validate the remote branch as-is** — proceed without committing; warn that local changes will not be reflected in the report.
  - **Cancel** — stop here.

### 3. Confirm the branch exists on origin

```
! git ls-remote --exit-code --heads origin <branch>
```

If the branch is missing on origin, ask the user whether to push it (`git push -u origin <branch>`) or pick a different branch.

### 4. Confirm the API token is set

The skill calls `${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py`, which reads `LYNK_API_TOKEN` from `.env` at the user's project root (CWD). If the token is missing, the script will exit with setup instructions on stderr — you can also fetch them on demand:

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" --print-setup
```

Always invoke the script with its absolute path via `${CLAUDE_PLUGIN_ROOT}` — when the plugin is installed via the marketplace, the script lives inside the plugin's install dir, not the user's repo. A bare `scripts/lynk_api.py` resolves against the user's CWD and fails. The `"$(command -v python3 || command -v python)"` prefix picks whichever Python interpreter the user has — macOS Homebrew ships only `python3`, some Windows installs only `python`, and the picker tolerates both.

Ask the user via `AskUserQuestion` how to proceed:

- **Set up the token now** — relay the script's setup instructions to the user verbatim, then ask them to paste the token directly in chat (not into a shell command). Once they paste it, persist it via the script — which handles `.env` writing **and** `.gitignore` protection in one step:
  ```
  ! LYNK_API_TOKEN='<paste>' "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" --save-token
  ```
  Add `LYNK_ENV=dev` to the env (before the Python invocation) if the user said "use dev". Re-run Step 5 once the script returns. *Note: the token will appear in shell history once — the user can rotate it after if concerned.*

- **Skip backend validation** — record the outcome `Backend validation not performed — no API token configured.` and jump to Step 6 to emit the skip outcome.

Future API-driven skills should reuse the same `--print-setup` / `--save-token` handshake — token plumbing lives in the script, not in each skill.

### 5. Call the builds API

**Status-only questions first** ("is the latest build green?", "when did it last pass?") — when the user wants the current verdict *without* triggering a build, use the read-only `GET semantics/builds/latest-successful --query branch=<branch>`: it returns the most recent **successful** build for the branch (or `404` if none exists yet). Report from that and stop. Fall through to the `POST` below to validate the *current* commit, or when no successful build exists yet.

Otherwise, build and validate the current commit with the shared script:

```
! "$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/lynk_api.py" POST semantics/builds \
    --branch <branch> \
    --query branch=<branch> \
    --query force=false \
    --header x-domain-name=default
```

Branch goes in the **query string** (`?branch=...`) — that's what the endpoint reads. Passing `--branch <branch>` too keeps the script's auto-set `x-branch-name` header consistent with the URL (the header itself is ignored by this endpoint but harmless).

If the user said "validate on dev" or "validate on prod", append `--env dev` or `--env prod` to override `LYNK_ENV` for this single call.

The script prints `{url, method, env, status_code, body}`. When you need the full response schema, read `references/rest-api.md` in this repo — that is the canonical endpoint reference. Do not fetch the public docs site for API details; the REST API spec is intentionally not published there.

**Three status codes carry a build object** — 200, 422, 409 — and the rest of the skill (Step 6) treats all three as success-for-reporting paths, just reading the build out of the right spot:

- **`200 OK`** → fresh build, layer is **valid**. `body.status == "valid"`. `body.validation_issues` is normally empty, but a valid build with **warnings** still lists them here — always read the array rather than assuming it's empty, and surface any warnings (they carry `severity: warning`, not `error`).
- **`422 Unprocessable Entity`** → fresh build, layer is **invalid**. Build object sits at the **root** of the body (not under `detail`, unlike the old `/validate` endpoint). `body.status == "invalid"`, issues at `body.validation_issues`.
- **`409 Conflict`** → **not an error.** A build for the branch's current `commit_sha` already exists, and `force=false` told the backend to return the cached build instead of rebuilding. **The cached build is wrapped under `body.detail`** — read `body.detail.status`, `body.detail.validation_issues`, and `body.detail.finished_at` (surface this as a cache timestamp in the report). This is the normal path when the user re-runs validate without pushing new commits. The cache key is the commit, not the warehouse state — if the user suspects the cached verdict is stale (sources were re-synced, columns changed without a new commit), re-call with `--query force=true` to bypass the cache.

**Three are pure errors:**

- **`5xx` / connection error (script exit 3)** → quote the message; suggest retry. A nonexistent branch currently surfaces as `500` with an empty body.
- **`401` / `403`** → auth failed; ask the user to verify the token in `.env` and check it isn't expired.
- **`404`** → wrong route or environment — and the API-drift signal. Show the URL called, then fetch the service spec to check whether the path moved: `GET semantics/openapi.json` and compare your route against its `paths`. If the spec shows a different path, that's the change — surface it and reconcile `references/rest-api.md`. (Consult the spec only here, on failure — not on every call.)

### 6. Produce the validation report

**Where the issue list lives:** `body.validation_issues` on `200` / `422`; `body.detail.validation_issues` on `409` (the cached path). Same per-issue shape in both.

**Per-issue fields:**

- `entity_name`, `scope` (`entity` / `relationship` / `context`), `severity` (`error` / `warning`)
- `category` — `schema` (declarative checks: missing descriptions, malformed YAML, broken refs) or `warehouse` (the backend ran a test query against the warehouse and the engine rejected it). The category telegraphs *how* the issue was found, which is useful in the fix: a `warehouse` issue is almost always a column / type drift between the YAML and the actual table; a `schema` issue is something you can fix from reading the YAML alone.
- `message`, `suggestion`
- `description` — populated for `category: warehouse` errors with the rendered SQL the backend ran, the compiled warehouse query, and the engine's error verbatim. Multi-kB per issue, so **don't paste it inline**. Reference it in the report (e.g. *"Engine error trace available in `description`"*) and surface it only if the user asks for it.
- `location.file_path`, `location.line_number`

Group by severity, then by file. Sort errors before warnings.

```
## Validation Report — branch `<branch>` (env: <prod|dev>)<cache_note>

### Summary
Status: <valid|invalid> · Errors: <n> · Warnings: <n>

### Errors (must fix)
- **<file_path>:<line_number>** [<scope>/<category>]: <message>
  Suggestion: <suggestion>   *(omit line if suggestion is null)*
  *Engine error trace available — ask for `description` to see the rendered SQL and warehouse error.*   *(only for `category: warehouse` with non-null `description`)*

### Warnings (should fix)
- ...

### What looks good
- (only when status is valid)
```

`<cache_note>` is empty for `200`/`422` (fresh build). For `409`, render ` · cached result from <body.detail.finished_at>` so the user knows the build wasn't re-run; mention in the Summary paragraph that `--query force=true` will rebuild if they suspect the cache is stale.

If multiple issues land in the same file, list them under one heading for that file.

**Skipped runs.** If the API call was skipped (no token, user cancelled at the dirty-tree prompt, branch not on origin), do **not** produce the full report. Emit a single line instead:

```
## Validation Report — branch `<branch>` (env: <prod|dev>)
Backend validation skipped: <reason>.
```

Reasons: `no API token configured`, `user cancelled`, `branch not on origin`. This makes the skip state explicit so callers — including `lynk-evaluate` — can detect and merge it cleanly.

## Output Format

- Always state the branch and environment in the summary line.
- Use exact `file_path:line_number` so the user can click through (omit `:line_number` if null).
- Quote the API's `message` and `suggestion` verbatim — don't paraphrase backend output.
- **When running standalone**, if the report contains errors, offer to fix them via `lynk-build` — but only after the full report. **When invoked from inside `lynk-evaluate`** (validate's steps 1–5 only, no report), do **not** offer fixes here; evaluate owns the fix loop.
