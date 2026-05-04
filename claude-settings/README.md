# claude-settings

Drop-in Claude Code configuration for customer repositories that use the Lynk semantic layer plugin.

## Current usage

These files are meant to be copied into the **customer repository's `.claude/` directory** (not this repo's). They configure Claude Code for the Lynk workflow: model, permission mode, status line, and the welcome banner.

```
<customer-repo>/
└── .claude/
    ├── settings.json
    └── statusline.sh
```

## Files

- `settings.json` — Claude Code settings (model, `auto` permission mode, status line command, Lynk welcome banner). The `statusLine.command` path is `.claude/statusline.sh`, which resolves correctly once copied into `.claude/`.
- `statusline.sh` — Status line script showing cwd, git branch, model, context %, and session cost. Must be executable (`chmod +x .claude/statusline.sh`).

## Install

From the customer repo root:

```sh
mkdir -p .claude
cp /path/to/build-agent/claude-settings/settings.json .claude/
cp /path/to/build-agent/claude-settings/statusline.sh .claude/
chmod +x .claude/statusline.sh
```
