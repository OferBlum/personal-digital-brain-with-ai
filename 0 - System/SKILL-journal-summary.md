# SKILL — Journal Summary (Local/Ollama Only)

## Privacy Notice
This skill runs EXCLUSIVELY via Ollama locally.
Journal files NEVER leave the machine. Never use the Claude API for this skill.

## When to Use
When the user asks to summarize journal entries for specific days.
Examples:
- "Summarize my last week"
- "Summarize the month"
- "Summarize [date] to [date]"

## How to Run
```bash
cd /path/to/your/vault
python3 "0 - System/journal-summary.py" week
python3 "0 - System/journal-summary.py" month
python3 "0 - System/journal-summary.py" 2026-04-01 2026-04-25
```

## Output
Saved to `2 - Notes/` with `private: true`

## Ollama Prompt
```
You are a personal assistant that summarizes a personal journal.
Your task is to summarize the entries as what was done during the day, in chronological order.
Focus only on what actually happened.

For each day separately write:
### [date]
- **Tasks completed:** short list
- **Key moments:** short list
- **Insights:** short list if any
- A general summary of the day, following the order of the entry and the completed tasks and key moments
- **Day rating:** [the rating as recorded]

At the very end add:
## Period summary
- **Average rating:** compute the average of all ratings found

Write in the user's language only. Do not add emotional analysis.
```
