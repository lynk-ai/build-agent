#!/usr/bin/env bash
# Claude Code statusline: cwd, git branch, model, context %, session cost.
# Parses the input JSON with bash regex (no jq) so this works on Windows
# Git Bash too, where jq isn't shipped.

INPUT=$(cat)

c() { printf '\033[%sm' "$1"; }
RESET=$'\033[0m'

# Echo the first "key":"..." string value found in $INPUT.
# Unescapes JSON \\ -> \ so Windows paths like "C:\\Users\\Tom" come out
# as C:\Users\Tom.
js() {
  if [[ "$INPUT" =~ \"$1\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    local val=${BASH_REMATCH[1]}
    val=${val//\\\\/\\}
    printf '%s' "$val"
  fi
}

# Echo the first "key": <number> found in $INPUT.
jn() {
  if [[ "$INPUT" =~ \"$1\"[[:space:]]*:[[:space:]]*(-?[0-9]+(\.[0-9]+)?) ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
  fi
}

cwd=$(js current_dir)
[[ -z "$cwd" ]] && cwd=$(js cwd)
display_name=$(js display_name)

# .model.id — search inside the "model": { ... } object to avoid matching
# any other "id" key that might appear elsewhere in the JSON.
model_id=""
if [[ "$INPUT" =~ \"model\"[[:space:]]*:[[:space:]]*\{([^}]*)\} ]]; then
  model_obj=${BASH_REMATCH[1]}
  if [[ "$model_obj" =~ \"id\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    model_id=${BASH_REMATCH[1]}
    model_id=${model_id//\\\\/\\}
  fi
fi

cost=$(jn total_cost_usd)
[[ -z "$cost" ]] && cost=0
ctx_pct=$(jn used_percentage)

# .rate_limits as an object => subscription session (suppress cost).
on_subscription=""
if [[ "$INPUT" =~ \"rate_limits\"[[:space:]]*:[[:space:]]*\{ ]]; then
  on_subscription="yes"
fi

display_cwd="$cwd"
if [[ -n "$HOME" && "$cwd" == "$HOME"* ]]; then
  display_cwd="~${cwd#"$HOME"}"
elif [[ -n "$USERPROFILE" && "$cwd" == "$USERPROFILE"* ]]; then
  # Windows: Claude Code passes paths like C:\Users\tom\..., HOME in Git Bash
  # is /c/Users/tom, so HOME doesn't match. USERPROFILE does. Quote the
  # pattern so backslashes aren't treated as glob escapes.
  display_cwd="~${cwd#"$USERPROFILE"}"
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
