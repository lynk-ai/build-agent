# Building Lynk semantic graph
Lynk is an AI native data platform for managing data analytics AI agents. 
The product has two main layers - the semantic graph - which enables AI agents work with the company's data by modeling data for AI both from the schema and data aspect (yaml files) and the context aspect (markdown files).

## Goal
Our goal is to create and test skills for building and validating lynk semantic graph - so users can easily build and maintain their semantic graph. 

## Resources
1. Lynk docs are hosted at https://docs.getlynk.ai and are fetched on demand by the skills (via `WebFetch`). No local docs folder is kept in this repo.
2. /.lynk folder - a folder with an example for a real semantic layer build on lynk, on the data of the NBA.

## Marketplace layout
- Public skills are distributed as a Claude Code plugin marketplace defined in `.claude-plugin/marketplace.json`.
- The plugin `lynk-semantic-layer` (under `plugins/lynk-semantic-layer/`) ships two skills: `lynk-build` and `lynk-validate`.
- Register the marketplace locally with `/plugin marketplace add .` and install with `/plugin install lynk-semantic-layer@lynk`.
- `.claude/skills/skill-creator/` is internal dev tooling for authoring skills in this repo and is **not** part of the marketplace. 



