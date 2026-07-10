#!/bin/bash
# Prints a unique, sorted list of tags from all md files in the vault
# Usage: ./list_tags.sh

VAULT_ROOT="$(dirname "$0")/.."

# Privacy exclusions: the journal folder and files starting with _
GREP_EXCLUDES=(--exclude-dir='3 - Journal' --exclude='_*')

# Allowed file list: all md except the exclusions above and files with private: true
FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(
  grep -rLE '^private:[[:space:]]*true' "$VAULT_ROOT" --include="*.md" "${GREP_EXCLUDES[@]}" 2>/dev/null
)
[ ${#FILES[@]} -eq 0 ] && exit 0

{
  # Inline tags in text (#tag) — only at line start or after a space,
  # so link anchors and URL fragments aren't captured
  grep -hoE '(^|[[:space:]])#[א-תA-Za-z0-9_/-]+' "${FILES[@]}" 2>/dev/null \
    | sed -E 's/^[[:space:]]+//'

  # Frontmatter tags: parse only the tags block (inline array or dash list),
  # without capturing neighboring fields like subject/wiki_sources
  awk '
    function emit(t) {
      gsub(/^[[:space:]"'"'"']+|[[:space:]"'"'"']+$/, "", t)
      if (t != "") print "#" t
    }
    /^tags:/ {
      if (match($0, /\[[^]]*\]/)) {
        n = split(substr($0, RSTART + 1, RLENGTH - 2), a, ",")
        for (i = 1; i <= n; i++) emit(a[i])
        intags = 0
      } else intags = 1
      next
    }
    intags {
      if ($0 ~ /^[[:space:]]*-[[:space:]]*/) {
        line = $0
        sub(/^[[:space:]]*-[[:space:]]*/, "", line)
        emit(line)
      } else intags = 0
    }
  ' "${FILES[@]}"
} \
  | grep -E '^#[א-תA-Za-z]' \
  | grep -viE '^#[0-9a-f]{3}$|^#[0-9a-f]{6}$|^#[0-9a-f]*[0-9][0-9a-f]*$' \
  | sort -u
# Noise filtering: a tag must start with a letter (filters dates, numbers,
# dashes), and a hex run (a color code like #ffffff or #667eea) is not a tag
