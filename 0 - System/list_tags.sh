#!/bin/bash
# Prints a unique, sorted list of tags from all md files in the vault
# Usage: ./list_tags.sh

VAULT_ROOT="$(dirname "$0")/.."

# Non-Latin letter range, built from UTF-8 bytes so this file stays pure ASCII.
# Here: Hebrew alef..tav (U+05D0-U+05EA). Replace with your own script's range.
# NOTE: do not swap this for [[:alpha:]] — BSD grep on macOS does not match
# non-ASCII letters through that class, which silently drops every such tag.
LETTERS="$(printf '\xd7\x90')-$(printf '\xd7\xaa')A-Za-z"

# Privacy exclusions: the journal folder and generated _ files (not secrets — just not tags)
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
  grep -hoE "(^|[[:space:]])#[${LETTERS}0-9_/-]+" "${FILES[@]}" 2>/dev/null \
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
  | grep -E "^#[${LETTERS}]" \
  | grep -viE '^#[0-9a-f]{3}$|^#[0-9a-f]{6}$|^#[0-9a-f]*[0-9][0-9a-f]*$' \
  | sort -u
# Noise filtering: a tag must start with a letter (filters dates, numbers,
# dashes), and a hex run (a color code like #ffffff or #667eea) is not a tag
