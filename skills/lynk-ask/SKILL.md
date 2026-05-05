---
name: lynk-ask
description: >
  Answer questions about the Lynk semantic layer — what's in `.lynk/`
  (instance lookups) and Lynk concepts themselves (primitives, file types,
  placement). Read-only: never edits, never calls the backend.

  Use this skill for any question about Lynk or `.lynk/`, even simple ones.
  Lynk distinguishes primitives that general analytics vocabulary blurs —
  e.g. a *metric* under `metrics:` is not a *feature of type metric* under
  `features:`. Don't answer from prior knowledge; run this skill so the
  answer is doc-grounded.

  Instance triggers: "does the player have a metric for total games played?",
  "what metrics does X have?", "list features of X", "where is Y defined?",
  "what's the SQL for X?", "how many entities do I have?". Concept triggers:
  "what is a knowledge file?", "metric vs. metric feature?", "formula vs.
  metric feature?", "where should glossary terms go?", "what is a
  clarification policy?".

  For edits use `lynk-build`; for quality `lynk-evaluate`; for backend
  checks `lynk-validate`.
---

# lynk-ask-semantics

This skill answers questions about the Lynk semantic layer. It is read-only — it never writes to `.lynk/`, never calls the Lynk API. Two question shapes are in scope:

- **Instance** — "what's in my `.lynk/`?": entities, metrics, features, relationships, glossary, context files.
- **Concept** — "what is X in Lynk?", "where does X belong?", "what's the difference between X and Y?".

Every answer must be grounded in the docs (and, for instance answers, the actual `.lynk/` files) — Lynk distinguishes primitives in ways general analytics vocabulary blurs (e.g., a *metric* under `metrics:` vs. a *feature of type metric* under `features:`). Do not answer from prior knowledge alone.

## Steps

### 1. Read the docs tree and concepts page

Always do this **first**, before classification or `.lynk/` reads. Two fetches:

1. Docs tree — `WebFetch https://docs.getlynk.ai/llms.txt`
2. Concepts grounding — `WebFetch https://docs.getlynk.ai/concepts.md`

This grounds every answer in correct Lynk vocabulary and gives you a map of doc pages to navigate to next. Skipping this step is what causes the most common failure mode for this skill — confidently confusing related primitives (e.g., treating a *metric feature* as a standalone *metric*) because general analytics vocabulary doesn't preserve Lynk's distinctions.

### 2. Classify the question

| Shape | Examples |
|---|---|
| **Instance** | "does X have Y?", "what metrics on X?", "where is Y defined?", "list features of X" |
| **Concept** | "what is a knowledge file?", "metric vs. metric feature?", "where should X go?" |
| **Both** | "what is a metric feature, and does my player have any?" |

If ambiguous, ask via `AskUserQuestion`.

### 3. Read the narrowest set of files

- **Concept** — from the docs tree (Step 1), `WebFetch` only the `concepts/<concept>` or `file-types/<type>` pages relevant to the question. For placement questions ("what goes in X?", "where should Y live?"), the file-type spec is the canonical answer.
- **Instance** — list the layer with `find ./.lynk -type f | sort`, identify which file(s) own the artifact, and read only those. For an entity question, that's the entity YAML plus its knowledge / task-instructions files.
- **Both** — concept reads first (to ground vocabulary), then instance reads.

### 4. Answer precisely

- **Lead with disambiguation when the question uses an ambiguous term.** "Metric" can mean a standalone metric (under `metrics:`) or a metric feature (under `features:` with `type: metric`). "Knowledge" can mean entity, domain, or business knowledge. A lead like "Yes — there's a metric called X" is wrong if X is actually a metric feature: it plants the wrong primitive in the user's head and reproduces the exact failure this skill exists to prevent. The lead sentence must name the *exact* primitive — e.g. "Yes — `total_games_played` is a metric *feature* on `player`, not a standalone metric."
- **For "no" / "missing" answers, scan the glossary and knowledge files before concluding.** If the same term shows up there (e.g. "PPG" defined in glossary while there's no `points_per_game` metric on the entity), cite it and call out the gap explicitly: "the concept exists in your glossary as Z, but isn't modeled as a metric/feature/relationship." This is what makes the `lynk-build` handoff land — the user sees the modeling gap, not just an empty result.
- Use exact Lynk vocabulary throughout — even outside the lead. When primitives that are easy to confuse appear (metric vs. metric feature, formula feature vs. metric feature, knowledge vs. task-instructions), call out the distinction even if the user didn't ask for it.
- For instance answers, cite `file:line` paths and quote the relevant YAML or markdown.
- For concept answers, cite the doc URL that anchors the definition.
- If the answer is "no" / "not found" / "missing", say so directly — don't soften.

### 5. Offer the next action

- **Instance "no" / "missing"** → offer `lynk-build` to add it.
- **Concept answer with a natural follow-up** ("…and does my graph have one?") → offer to run an instance lookup (this skill).
- **User pivots to quality** ("is this metric well-defined?") → offer `lynk-evaluate`.
- **User pivots to backend validity** → offer `lynk-validate`.

Never edit files from this skill — edits belong in `lynk-build`, which has its own plan / confirm / write / evaluate flow that this skill should hand off to rather than bypass.

## Output Format

- Lead with the direct answer in one sentence — yes / no, the count, the name.
- Back it up with evidence: a YAML excerpt + file path for instance answers, or a quoted doc passage with URL for concept answers.
- For "no" instance answers, state where the missing item *would* live if added (e.g., "no metric for total games played on player; it would go under `player.yml → metrics:`").
- For primitive distinctions, show a short side-by-side before the answer.
- Use code blocks for YAML, SQL, and file paths.
- Always cite the docs URL when leaning on a concept definition.
