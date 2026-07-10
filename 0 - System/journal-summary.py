#!/usr/bin/env python3
"""
Journal Summary — Ollama Local Only
Summarizes the journal — runs strictly locally through Ollama.
The journal is the most private surface in the vault: it never goes through
a cloud model or any external channel.
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────
# Vault root: VAULT_ROOT env var, or the parent of this script's folder
# (the script lives in <vault>/0 - System/).
VAULT_PATH = os.environ.get("VAULT_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
JOURNAL_FOLDER = "3 - Journal"
NOTES_FOLDER = "2 - Notes"
OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_URL = "http://localhost:11434/api/generate"
SKILL_PATH = "0 - System/SKILL-journal-summary.md"
RATING_KEY = "day_rating"  # frontmatter key holding the daily 1-10 rating

# ── Load prompt from SKILL file ──────────────────────────
def load_prompt() -> str:
    skill_file = os.path.join(VAULT_PATH, SKILL_PATH)
    if not os.path.exists(skill_file):
        print("❌ SKILL-journal-summary.md not found")
        sys.exit(1)
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    if "## Ollama Prompt" not in content:
        print("❌ 'Ollama Prompt' section not found in SKILL-journal-summary.md")
        sys.exit(1)
    after_header = content.split("## Ollama Prompt")[1]
    parts = after_header.split("```")
    for part in parts:
        cleaned = part.strip()
        if cleaned and not cleaned.startswith("bash"):
            return cleaned
    print("❌ No prompt found")
    sys.exit(1)

# ── Helpers ─────────────────────────────────────────────
def get_journal_files(start_date: datetime, end_date: datetime) -> list:
    import glob
    journal_path = os.path.join(VAULT_PATH, JOURNAL_FOLDER)
    all_files = glob.glob(os.path.join(journal_path, "**/*.md"), recursive=True)
    result = []
    for f in sorted(all_files):
        filename = os.path.basename(f).replace(".md", "")
        try:
            file_date = datetime.strptime(filename, "%Y-%m-%d")
            if start_date <= file_date <= end_date:
                result.append(f)
        except ValueError:
            continue
    return result

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    lines = content.split("\n")
    clean = []
    in_block = False
    for line in lines:
        if "~~~dataview" in line or "```dataview" in line:
            in_block = True
        elif in_block and ("~~~" in line or "```" in line):
            in_block = False
        elif not in_block:
            clean.append(line)
    return "\n".join(clean).strip()

def call_ollama(prompt: str, system: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()["response"]

def save_summary(summary: str, start_date: datetime, end_date: datetime):
    notes_path = os.path.join(VAULT_PATH, NOTES_FOLDER)
    if not os.path.isdir(notes_path):
        print("❌ Notes folder not found")
        return
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    filename = f"Journal summary {start_str} to {end_str}.md"
    filepath = os.path.join(notes_path, filename)
    content = f"""---
subject:
tags: [journal-summary]
private: true
created: {datetime.now().strftime("%Y-%m-%d")}
---

# Journal summary — {start_str} to {end_str}

{summary}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved: {filename}")

# ── Main ────────────────────────────────────────────────
def main():
    if len(sys.argv) == 3:
        start = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        end = datetime.strptime(sys.argv[2], "%Y-%m-%d")
    elif len(sys.argv) == 2 and sys.argv[1] == "week":
        end = datetime.now()
        start = end - timedelta(days=7)
    elif len(sys.argv) == 2 and sys.argv[1] == "month":
        end = datetime.now()
        start = end - timedelta(days=30)
    else:
        print("Usage:")
        print("  python3 journal-summary.py 2026-04-01 2026-04-25")
        print("  python3 journal-summary.py week")
        print("  python3 journal-summary.py month")
        sys.exit(1)

    system_prompt = load_prompt()
    print(f"📖 Looking for journal entries from {start.date()} to {end.date()}...")
    files = get_journal_files(start, end)

    if not files:
        print("❌ No journal entries found in this range")
        sys.exit(1)

    print(f"✅ Found {len(files)} entries — processing each day separately...")

    # Process each day separately to avoid context window limits
    daily_summaries = []
    for f in files:
        date = os.path.basename(f).replace(".md", "")
        content = read_file(f)
        if not content.strip():
            continue
        print(f"  📅 Summarizing {date}...")
        day_prompt = f"Summarize the following day:\n\n## {date}\n{content}"
        day_summary = call_ollama(day_prompt, system_prompt)
        daily_summaries.append(f"### {date}\n{day_summary}")

    # Calculate average rating — read from frontmatter
    ratings = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            raw = fh.read()
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split("\n"):
                    if RATING_KEY in line and ":" in line:
                        val = line.split(":", 1)[1].strip()
                        try:
                            ratings.append(float(val))
                        except ValueError:
                            pass

    avg = f"{sum(ratings)/len(ratings):.1f}" if ratings else "not found"

    full_summary = "\n\n".join(daily_summaries)
    full_summary += f"\n\n---\n## Period summary\n- **Average rating:** {avg}"

    print("💾 Saving summary...")
    save_summary(full_summary, start, end)

if __name__ == "__main__":
    main()
