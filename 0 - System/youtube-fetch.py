#!/usr/bin/env python3
"""
YouTube Fetch — Downloads transcripts from youtube_queue.md into raw/
"""

import os
import sys
import re
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌ Missing dependency: pip install youtube-transcript-api")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────
# Vault root: VAULT_ROOT env var, or the parent of this script's folder
# (the script lives in <vault>/0 - System/).
VAULT_PATH = os.environ.get("VAULT_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
QUEUE_PATH = "7 - Wikipedia/raw/youtube_queue.md"
RAW_FOLDER = "7 - Wikipedia/raw"

# Queue section markers
PENDING_MARKER = "Pending"
COMPILED_MARKER = "Compiled"

# ── Helpers ─────────────────────────────────────────────
def extract_video_id(url: str) -> str:
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id: str) -> str:
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "he", "iw"])
        return " ".join([t.text for t in fetched])
    except Exception as e:
        print(f"  ⚠️ No transcript found: {e}")
        return None

def parse_queue(queue_path: str):
    with open(queue_path, "r", encoding="utf-8") as f:
        content = f.read()
    pending = []
    in_pending = False
    for line in content.split("\n"):
        if PENDING_MARKER in line:
            in_pending = True
            continue
        if COMPILED_MARKER in line:
            in_pending = False
            continue
        if in_pending and "http" in line:
            urls = re.findall(r'https?://[^\s\)\]|]+', line)
            tags = re.findall(r'#\w+', line)
            if urls:
                pending.append({
                    "url": urls[0],
                    "tags": tags,
                    "line": line
                })
    return pending, content

def mark_as_compiled(content: str, original_line: str, page_name: str) -> str:
    # Extract a clean URL from the pending line (no table pipes / extra spaces)
    url_match = re.search(r'https?://[^\s\)\]|]+', original_line)
    url = url_match.group(0) if url_match else original_line.strip()
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_row = f"| {url} | [[{page_name}]] | {date_str} |"

    # Remove the line from the "Pending" section
    content = content.replace(original_line, "")

    # Inject a valid table row right after the separator row (| --- | --- | --- |)
    # under the "## Compiled" heading — so the row lands at the top of the table,
    # not before the heading.
    lines = content.split("\n")
    out = []
    in_compiled = False
    inserted = False
    for line in lines:
        out.append(line)
        if line.strip().startswith(f"## {COMPILED_MARKER}"):
            in_compiled = True
        elif in_compiled and not inserted and re.match(r'\s*\|\s*-{3,}', line):
            out.append(new_row)
            inserted = True
    if not inserted:
        # fallback: if no table was found under "Compiled", append at the end
        out.append(new_row)
    return "\n".join(out)

# ── Main ────────────────────────────────────────────────
def main():
    queue_full_path = os.path.join(VAULT_PATH, QUEUE_PATH)
    raw_full_path = os.path.join(VAULT_PATH, RAW_FOLDER)

    if not os.path.exists(queue_full_path):
        print(f"❌ Not found: {queue_full_path}")
        sys.exit(1)

    pending, queue_content = parse_queue(queue_full_path)

    if not pending:
        print("✅ No pending videos in the queue")
        sys.exit(0)

    print(f"📺 Found {len(pending)} pending videos...")

    for video in pending:
        url = video["url"]
        tags = video["tags"]
        video_id = extract_video_id(url)

        if not video_id:
            print(f"  ❌ Could not extract a video ID from: {url}")
            continue

        print(f"  ⬇️ Downloading transcript: {video_id}...")
        transcript = get_transcript(video_id)

        if not transcript:
            continue

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"youtube-{video_id}-{date_str}.md"
        filepath = os.path.join(raw_full_path, filename)

        tags_str = "\n  - ".join(tags) if tags else ""
        file_content = f"""---
subject:
tags:
  - learning
  - {tags_str}
private: false
type: youtube
youtube_id: {video_id}
youtube_url: {url}
fetched: {date_str}
---

# Transcript — {video_id}

{transcript}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)

        print(f"  ✅ Saved: {filename}")

        # The final page name is only decided at compile time (in Claude Code),
        # so a placeholder is injected that clearly must be replaced with a link
        # to the wiki page that gets created.
        queue_content = mark_as_compiled(queue_content, video["line"], "⚠️ update page name")

    with open(queue_full_path, "w", encoding="utf-8") as f:
        f.write(queue_content)

    print("\n✅ Done — now Claude Code will compile the new files in raw/")

if __name__ == "__main__":
    main()
