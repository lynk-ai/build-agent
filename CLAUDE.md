# Building Lynk semantic graph
Lynk is an AI native data platform for managing data analytics AI agents. 
The product has two main layers - the semantic graph - which enables AI agents work with the company's data by modeling data for AI both from the schema and data aspect (yaml files) and the context aspect (markdown files).

## Goal
Our goal is to create and test skills for building and validating lynk semantic graph - so users can easily build and maintain their semantic graph. 

## Resources
1. Lynk docs live in `references/docs/` — a local copy of the Lynk Semantics v2 docs, read directly by the skills (index: `references/docs/SUMMARY.md`, navigation guide: `references/docs/CLAUDE.md`).
2. /.lynk folder - a folder with an example for a real semantic layer build on lynk, on the data of the NBA.

## Marketplace layout
- Public skills are distributed as a Claude Code plugin marketplace defined in `.claude-plugin/marketplace.json`.
- The plugin `lynk-semantic-layer` (defined by `.claude-plugin/plugin.json` at the repo root, with its skills under `skills/`) ships five skills: `lynk-build`, `lynk-evaluate`, `lynk-validate`, `lynk-sources`, and `lynk-ask` (read-only Q&A on `.lynk/` instances and Lynk concepts). `lynk-sources` covers list/sync/fetch operations on the data catalog and reconciles entity YAMLs when source columns change. The shared script `scripts/lynk_api.py` is a generic Lynk API caller used by every API-driven skill; it reads `LYNK_API_TOKEN` and `LYNK_ENV` from `.env` at the project root, and exposes `--print-setup` and `--save-token` actions so each skill can reuse the same token/.env/.gitignore handshake without duplicating logic. `lynk-ask` is read-only and does not use the API script.
- Register the marketplace locally with `/plugin marketplace add .` and install with `/plugin install lynk-semantic-layer@lynk`.
- `.claude/skills/skill-creator/` is internal dev tooling for authoring skills in this repo and is **not** part of the marketplace. 



