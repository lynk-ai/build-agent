# Lynk docs — navigation guide

How skills should walk the Lynk docs at `https://docs.getlynk.ai`. The skills inline the specific URLs they fetch (so each step is atomic and self-contained); this file is the convention they follow.

## The two anchors

Skills ground themselves with two pages:

- **`llms.txt`** — the docs index. Lists every page available. Use it to discover the leaf URL you need.
- **`concepts.md`** — Lynk's core vocabulary (Entity, Feature, Metric, Relationship, Glossary, Domain, Context). Read it before answering or building anything that involves Lynk primitives.

Everything else is a leaf reached from the index.

## How to walk

1. **Start at the index.** Fetch `llms.txt` to see the current tree. Never guess a leaf path from memory.
2. **Pick the narrowest leaf** that answers your question (e.g., `file-types/entity.md`, `concepts/relationship.md`). Do not pre-fetch unrelated pages — context cost compounds.
3. **Fetch only that leaf.** If you need a second one, fetch it explicitly. No bulk traversal.

## When the docs move

Leaf URLs may change as docs evolve. If a fetch 404s:

1. Re-fetch `llms.txt` and find the new path.
2. Update the skill that pointed to the old path.
3. Do **not** hardcode workarounds or guess the new URL.

The two anchors (`llms.txt`, `concepts.md`) are stable — they're index pages, not leaves — so the skills inline them directly.
