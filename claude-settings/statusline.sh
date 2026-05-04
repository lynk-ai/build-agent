#!/usr/bin/env bash
# Claude Code statusline: cwd, git branch, model, context %, session cost.

INPUT=$(cat)

c() { printf '\033[%sm' "$1"; }
RESET=$'\033[0m'

cwd=$(jq -r '.workspace.current_dir // .cwd // empty' <<< "$INPUT")
display_name=$(jq -r '.model.display_name // empty' <<< "$INPUT")
model_id=$(jq -r '.model.id // empty' <<< "$INPUT")
cost=$(jq -r '.cost.total_cost_usd // 0' <<< "$INPUT")
ctx_pct=$(jq -r '.context_window.used_percentage // empty' <<< "$INPUT")

display_cwd="$cwd"
if [[ -n "$HOME" && "$cwd" == "$HOME"* ]]; then
  display_cwd="~${cwd#$HOME}"
fi

version=$(grep -oE '[0-9]+-[0-9]+' <<< "$model_id" | head -1 | tr - .)
model_label="$display_name"
if [[ -n "$version" && "$display_name" != *"$version"* ]]; then
  model_label="$display_name $version"
fi

branch_field=""
if git_status=$(git -C "$cwd" status --porcelain=v2 --branch 2>/dev/null); then
  branch=$(awk '/^# branch.head/ {print $3}' <<< "$git_status")
  if [[ "$branch" == "(detached)" ]]; then
    branch=$(git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
  fi
  dirty=""
  if grep -qE '^[12u?]' <<< "$git_status"; then
    dirty="*"
  fi
  branch_field="$(c '35')🌿 ${branch}${dirty}${RESET}"
fi

if [[ -n "$ctx_pct" ]]; then
  pct_int=${ctx_pct%.*}
  pct_int=${pct_int:-0}
  filled=$(( (pct_int + 10) / 20 ))
  (( filled > 5 )) && filled=5
  (( filled < 0 )) && filled=0
  empty=$(( 5 - filled ))
  bar=""
  for ((i=0; i<filled; i++)); do bar+="▓"; done
  for ((i=0; i<empty;  i++)); do bar+="░"; done
  if   (( pct_int < 60 )); then ctx_color="32"
  elif (( pct_int < 85 )); then ctx_color="33"
  else                          ctx_color="31"
  fi
  ctx_field="$(c "$ctx_color")📊 ${pct_int}% [${bar}]${RESET}"
else
  ctx_field="$(c '90')📊 —${RESET}"
fi

cost_fmt=$(printf '%.2f' "$cost" 2>/dev/null || echo "0.00")

# Only show cost on API-key auth: subscription sessions get .rate_limits populated.
on_subscription=$(jq -r 'if (.rate_limits // null) != null then "yes" else empty end' <<< "$INPUT")

parts=()
parts+=("$(c '36')📁 ${display_cwd}${RESET}")
[[ -n "$branch_field" ]] && parts+=("$branch_field")
parts+=("$(c '34')🤖 ${model_label}${RESET}")
parts+=("$ctx_field")
[[ -z "$on_subscription" && "$cost_fmt" != "0.00" ]] && parts+=("$(c '32')💰 \$${cost_fmt}${RESET}")

out=""
for p in "${parts[@]}"; do
  if [[ -z "$out" ]]; then out="$p"; else out+="  $p"; fi
done
printf '%s' "$out"
