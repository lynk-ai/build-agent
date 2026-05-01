---
name: lynk-validate
description: >
  Validate the Lynk semantic layer in `.lynk/` against the Lynk backend by calling
  `POST /api/semantics/validate`. Surfaces schema errors, broken source-field
  references, and other server-side validity issues for a given branch.

  Use this skill whenever the user asks to validate, run a backend check on, or
  verify the formal validity of the semantic layer. Trigger phrases: "validate
  the semantic layer", "run lynk validate", "is my .lynk valid", "check against
  the backend", "validate on branch X", "validate on dev", "are there any schema
  errors", "validate inquiries branch".

  For local content quality (description quality, cross-file contradictions,
  dialect compatibility), use `lynk-evaluate` instead — this skill only runs the
  backend API.
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

The skill calls `scripts/lynk_api.py`, which reads `LYNK_API_TOKEN` from `.env` at the project root. If the token is missing, the script will exit with setup instructions on stderr — you can also fetch them on demand:

```
! python scripts/lynk_api.py --print-setup
```

Ask the user via `AskUserQuestion` how to proceed:

- **Set up the token now** — relay the script's setup instructions to the user verbatim, then ask them to paste the token directly in chat (not into a shell command). Once they paste it, persist it via the script — which handles `.env` writing **and** `.gitignore` protection in one step:
  ```
  ! LYNK_API_TOKEN='<paste>' python scripts/lynk_api.py --save-token
  ```
  Add `LYNK_ENV=dev` to the env (before `python`) if the user said "use dev". Re-run Step 5 once the script returns. *Note: the token will appear in shell history once — the user can rotate it after if concerned.*

- **Skip backend validation** — record the outcome `Backend validation not performed — no API token configured.` and jump to Step 6 to emit the skip outcome.

Future API-driven skills should reuse the same `--print-setup` / `--save-token` handshake — token plumbing lives in the script, not in each skill.

### 5. Call the validate API

Run the shared script:

```
! python scripts/lynk_api.py POST semantics/validate \
    --query scope=all \
    --query fail_on_warnings=false \
    --header x-branch-name=<branch> \
    --header x-domain-name=default
```

If the user said "validate on dev" or "validate on prod", append `--env dev` or `--env prod` to override `LYNK_ENV` for this single call.

The script prints `{url, method, env, status_code, body}`. Interpret the response:

- **HTTP 200**, `body.status == "valid"` → success, no issues. `error_count` and `warning_count` are 0.
- **HTTP 200**, `body.status == "invalid"` or **HTTP 422** with `body.detail.status == "invalid"` → validation issues. The issue list is at `body.issues` (200) or `body.detail.issues` (422). Same shape either way.
- **HTTP 401 / 403** → auth failed. Ask the user to verify the token in `.env` and that it isn't expired.
- **HTTP 404** → wrong route or environment. Show the URL the script called.
- **HTTP 5xx** → backend issue. Quote the status and message; suggest retry.
- **Connection error** (script exit 3) → quote the error reason; check network or `LYNK_ENV`.

### 6. Produce the validation report

Each issue has: `entity_name`, `scope` (entity / relationship / context), `category` (schema / semantic), `severity` (error / warning), `message`, `suggestion`, `location.file_path`, `location.line_number`.

Group by severity, then by file. Sort errors before warnings.

```
## Validation Report — branch `<branch>` (env: <prod|dev>)

### Summary
Status: <valid|invalid> · Errors: <n> · Warnings: <n>

### Errors (must fix)
- **<file_path>:<line_number>** [<scope>/<category>]: <message>
  Suggestion: <suggestion>   *(omit line if suggestion is null)*

### Warnings (should fix)
- ...

### What looks good
- (only when status is valid)
```

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
