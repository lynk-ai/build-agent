---
name: lynk-ask
description: >
  Answer questions about the Lynk semantic layer, grounded in the docs — both
  Lynk concepts (primitives, file types, placement, syntax) and what's in a
  given `.lynk/` (instance lookups). Read-only: never edits, never calls the
  backend.

  Use for any Lynk question, even simple ones — Lynk blurs distinctions general
  analytics vocabulary misses (a `metrics:` metric is entity-local; a
  cross-entity aggregate is a feature calling `metric()`). Triggers: "metric
  vs. feature?", "what goes in ENTITY.md vs LYNK.md?", "where is Y defined?",
  "list features of X", "how do imports work?". Edits → `lynk-build`; quality →
  `lynk-evaluate`; validity → `lynk-validate`; sources → `lynk-sources`.
---

# lynk-ask

This skill answers questions about the Lynk semantic layer. It is read-only — it never writes to `.lynk/`, never calls the Lynk API. Two question shapes are in scope:

- **Instance** — "what's in my `.lynk/`?": entities, metrics, features, relationships, glossary, skills, policies, `LYNK.md` orientation.
- **Concept** — "what is X in Lynk?", "where does X belong?", "what's the difference between X and Y?".

Every answer must be grounded in the docs (and, for instance answers, the actual `.lynk/` files) — Lynk distinguishes primitives in ways general analytics vocabulary blurs (e.g., a *metric* under `metrics:` is entity-local, while a feature whose `sql` calls `metric()` exposes a cross-entity aggregate at row grain). Do not answer from prior knowledge alone.

## Steps

### 1. Read the docs tree and concepts page

Always do this **first**, before classification or `.lynk/` reads. All `references/…` paths in this skill resolve from the plugin root — `${CLAUDE_PLUGIN_ROOT}` when installed as a plugin, the repo root when working in this repo — not the user's CWD or the skill folder. Two reads:

1. Docs tree — `Read references/docs/SUMMARY.md`
2. Concepts grounding — `Read references/docs/concepts/README.md`

These two anchors and how to walk from the index to leaf pages are the doc-navigation convention written up in `references/docs/CLAUDE.md`.

This grounds every answer in correct Lynk vocabulary and gives you a map of doc pages to navigate to next. Skipping this step is what causes the most common failure mode for this skill — confidently confusing related primitives (e.g., treating a *metric feature* as a standalone *metric*) because general analytics vocabulary doesn't preserve Lynk's distinctions.

### 2. Classify the question

| Shape | Examples |
|---|---|
| **Instance** | "does X have Y?", "what metrics on X?", "where is Y defined?", "list features of X" |
| **Concept** | "what goes in ENTITY.md?", "metric vs. feature?", "skill vs. policy?", "where should X go?" |
| **Both** | "what is a cross-entity aggregate feature, and does my player have any?" |

If ambiguous, ask via `AskUserQuestion`.

### 3. Read the narrowest set of files

- **Concept** — from the docs tree (Step 1), `Read` only the narrowest leaf pages under `references/docs/` relevant to the question (file-type specs live under `concepts/`, e.g. `concepts/entity/schema-yml/metric.md`; cross-cutting rules under `reference/`). For placement questions ("what goes in X?", "where should Y live?"), the file-type spec is the canonical answer.
- **Instance** — list the layer with `find ./.lynk -type f | sort`, identify which file(s) own the artifact, and read only those. Entities live under `.lynk/domains/<domain>/entities/<entity>/` — note which domain owns the artifact, since each domain is its own agent and metric names are only unique per domain. For an entity question, read the entity's `schema.yml` plus its `ENTITY.md` (and anything the prose `@`-injects).
- **Both** — concept reads first (to ground vocabulary), then instance reads.

### 4. Answer precisely

- **Lead with disambiguation when the question uses an ambiguous term.** "Metric" can mean a standalone metric (under `metrics:`, entity-local) or a feature whose `sql` calls `metric()` across a relationship (under `features:`, row-grain). "Knowledge" can mean entity prose (`ENTITY.md`), team orientation (`LYNK.md`), or vocabulary (`GLOSSARY.yml`). A lead like "Yes — there's a metric called X" is wrong if X is actually a feature: it plants the wrong primitive in the user's head and reproduces the exact failure this skill exists to prevent. The lead sentence must name the *exact* primitive — e.g. "Yes — `total_games_played` is a *feature* on `player` that calls `metric(game.count_games)` across a relationship, not a standalone metric." (This metric-vs-feature distinction is specified in `references/docs/concepts/entity/schema-yml/metric.md` — cite it rather than restating placement from memory.)
- **For "no" / "missing" answers, scan the glossary and prose files before concluding.** If the same term shows up there (e.g. "PPG" defined in `GLOSSARY.yml` while there's no `points_per_game` metric on the entity), cite it and call out the gap explicitly: "the concept exists in your glossary as Z, but isn't modeled as a metric/feature/relationship." This is what makes the `lynk-build` handoff land — the user sees the modeling gap, not just an empty result.
- Use exact Lynk vocabulary throughout — even outside the lead. When primitives that are easy to confuse appear (metric vs. cross-entity aggregate feature, `ENTITY.md` prose vs. `LYNK.md` orientation, skill vs. policy), call out the distinction even if the user didn't ask for it.
- For instance answers, cite `file:line` paths and quote the relevant YAML or markdown.
- For concept answers, cite the doc path that anchors the definition (e.g. `references/docs/concepts/entity/schema-yml/metric.md`).
- If the answer is "no" / "not found" / "missing", say so directly — don't soften.

### 5. Offer the next action

- **Instance "no" / "missing"** → offer `lynk-build` to add it.
- **Concept answer with a natural follow-up** ("…and does my graph have one?") → offer to run an instance lookup (this skill).
- **User pivots to quality** ("is this metric well-defined?") → offer `lynk-evaluate`.
- **User pivots to backend validity or asks about the semantics build** ("did the build pass?", "is the layer ready?") → offer `lynk-validate`.
- **User pivots to source/schema** → offer `lynk-sources`.

Never edit files from this skill — edits belong in `lynk-build`, which has its own plan / confirm / write / evaluate flow that this skill should hand off to rather than bypass.

## Output Format

- Lead with the direct answer in one sentence — yes / no, the count, the name.
- Back it up with evidence: a YAML excerpt + file path for instance answers, or a quoted doc passage with its `references/docs/` path for concept answers.
- For "no" instance answers, state where the missing item *would* live if added, applying the same metric-vs-feature disambiguation as the lead (e.g., "no *feature* for total games played on `player` yet; a cross-entity count would live under `features:` as a `sql` that calls `metric(game.count_games)`, not under `metrics:` — metrics are entity-local; see `references/docs/concepts/entity/schema-yml/metric.md`").
- For primitive distinctions, show a short side-by-side before the answer.
- Use code blocks for YAML, SQL, and file paths.
- Always cite the doc path when leaning on a concept definition.
