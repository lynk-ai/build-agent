#!/usr/bin/env python3
"""Generic Lynk API caller used by skills (lynk-validate and any future API skill).

Full endpoint reference: https://docs.getlynk.ai/api/rest-api

Reads `LYNK_API_TOKEN` and `LYNK_ENV` from `.env` at the current working
directory, then calls the Lynk backend and prints a structured JSON result
to stdout: `{url, method, env, status_code, body}`.

Base URL:
  - prod (default):  https://app.getlynk.ai/api
  - dev (LYNK_ENV=dev or --env dev):  https://dev.app.getlynk.ai/api

Usage:
  # Make an API call
  python scripts/lynk_api.py POST semantics/validate \
      --query scope=all \
      --query fail_on_warnings=false \
      --header x-branch-name=main \
      --header x-domain-name=default

  # Print canonical token-setup instructions (skills relay this verbatim)
  python scripts/lynk_api.py --print-setup

  # Save token to .env (also ensures .env is in .gitignore). Token is read
  # from the LYNK_API_TOKEN env var so it never lands in argv:
  LYNK_API_TOKEN=<token> python scripts/lynk_api.py --save-token
  # optionally also persist the env choice:
  LYNK_API_TOKEN=<token> LYNK_ENV=dev python scripts/lynk_api.py --save-token

Exit codes:
  0  Success (HTTP response received, or setup action completed)
  2  Configuration error (missing token, bad arg)
  3  Network / connection error
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_PROD = "https://app.getlynk.ai/api"
DEFAULT_DEV = "https://dev.app.getlynk.ai/api"

TOKEN_HELP = """LYNK_API_TOKEN is not set.

To set up your token:
  1. Open the Lynk app and click your avatar (bottom-left corner).
  2. Go to 'API tokens' and create a new token.
  3. If .env is not already in .gitignore, add it first — the token must not be committed.
  4. Save the token in .env at the project root:
       LYNK_API_TOKEN=<your-token>
  5. Optional: to call dev instead of prod, also add:
       LYNK_ENV=dev

Full API reference: https://docs.getlynk.ai/api/rest-api
"""


def load_dotenv(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (
                v.startswith("'") and v.endswith("'")
            ):
                v = v[1:-1]
            out[k] = v
    return out


def parse_kv(items: list[str] | None, label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            print(f"Bad {label} (expected key=value): {item}", file=sys.stderr)
            sys.exit(2)
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def try_json(s: str):
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return s


def ensure_env_gitignored(repo_root: str) -> bool:
    """Make sure `.env` is gitignored. Returns True if `.gitignore` was modified."""
    gi_path = os.path.join(repo_root, ".gitignore")
    lines: list[str] = []
    if os.path.exists(gi_path):
        with open(gi_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    if any(line.strip() in {".env", "/.env", "*.env"} for line in lines):
        return False
    block = ["", "# Lynk API token", ".env", ".env.*", "!.env.example"]
    sep = "" if (not lines or lines[-1] == "") else "\n"
    with open(gi_path, "a", encoding="utf-8") as f:
        f.write(sep + "\n".join(block) + "\n")
    return True


def upsert_env_var(env_path: str, key: str, value: str) -> str:
    """Insert or replace `KEY=value` in `.env`. Returns 'updated' or 'inserted'."""
    lines: list[str] = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    new_lines: list[str] = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(f"{key}={value}")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    return "updated" if found else "inserted"


def action_print_setup() -> int:
    print(TOKEN_HELP)
    return 0


def action_save_token() -> int:
    repo_root = os.getcwd()
    token = os.environ.get("LYNK_API_TOKEN")
    if not token:
        print(
            "save-token requires LYNK_API_TOKEN in the environment "
            "(e.g. `LYNK_API_TOKEN=<value> python scripts/lynk_api.py --save-token`).",
            file=sys.stderr,
        )
        return 2
    lynk_env = os.environ.get("LYNK_ENV")
    gitignore_changed = ensure_env_gitignored(repo_root)
    env_path = os.path.join(repo_root, ".env")
    summary: dict = {
        "action": "save-token",
        "env_path": env_path,
        "gitignore_added_env": gitignore_changed,
        "token_action": upsert_env_var(env_path, "LYNK_API_TOKEN", token),
    }
    if lynk_env:
        summary["lynk_env_action"] = upsert_env_var(env_path, "LYNK_ENV", lynk_env)
        summary["lynk_env_value"] = lynk_env
    print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Generic Lynk API caller.")
    p.add_argument(
        "method",
        nargs="?",
        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
        help="HTTP method (omit when using --save-token / --print-setup)",
    )
    p.add_argument("route", nargs="?", help="Path under /api/, e.g. semantics/validate")
    p.add_argument("--header", action="append", help="key=value, repeatable")
    p.add_argument("--query", action="append", help="key=value, repeatable")
    p.add_argument("--data", help="Request body (raw JSON string)")
    p.add_argument("--data-file", help="Path to file containing JSON body")
    p.add_argument(
        "--env", choices=["prod", "dev"], help="Override LYNK_ENV for this call"
    )
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument(
        "--print-setup",
        action="store_true",
        help="Print token-setup instructions and exit",
    )
    p.add_argument(
        "--save-token",
        action="store_true",
        help="Write LYNK_API_TOKEN (from env) to .env and ensure .gitignore protects it",
    )
    args = p.parse_args()

    if args.print_setup:
        return action_print_setup()
    if args.save_token:
        return action_save_token()

    if not args.method or not args.route:
        p.error("method and route are required (unless using --save-token / --print-setup)")

    env_file = load_dotenv(os.path.join(os.getcwd(), ".env"))
    token = env_file.get("LYNK_API_TOKEN") or os.environ.get("LYNK_API_TOKEN")
    if not token:
        print(TOKEN_HELP, file=sys.stderr)
        return 2

    env_choice = (
        args.env
        or env_file.get("LYNK_ENV")
        or os.environ.get("LYNK_ENV")
        or "prod"
    ).lower()
    base = DEFAULT_DEV if env_choice == "dev" else DEFAULT_PROD

    route = args.route.lstrip("/")
    url = f"{base}/{route}"
    qs = parse_kv(args.query, "query")
    if qs:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(qs)

    headers = {"x-api-key": token, "Accept": "application/json"}
    headers.update(parse_kv(args.header, "header"))

    if args.data and args.data_file:
        print("Pass either --data or --data-file, not both.", file=sys.stderr)
        return 2

    body_bytes: bytes | None = None
    if args.data:
        body_bytes = args.data.encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    elif args.data_file:
        with open(args.data_file, "rb") as f:
            body_bytes = f.read()
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(
        url, data=body_bytes, headers=headers, method=args.method
    )

    result = {
        "url": url,
        "method": args.method,
        "env": env_choice,
        "status_code": None,
        "body": None,
    }
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8")
            result["status_code"] = resp.status
            result["body"] = try_json(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        result["status_code"] = e.code
        result["body"] = try_json(raw)
    except urllib.error.URLError as e:
        result["error"] = f"Connection failed: {e.reason}"
        print(json.dumps(result, indent=2))
        return 3

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
