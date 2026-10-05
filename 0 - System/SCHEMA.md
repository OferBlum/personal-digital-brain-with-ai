# SCHEMA.md — Vault Schema

The single source of truth for the three axes that tag every file in the vault.
`0 - System/scripts/validate.py` enforces this file.

## The three axes

Each axis answers exactly one question, and only one:

| Axis | The question it answers | Closed? |
| --- | --- | --- |
| `subject` | which area of my life this belongs to | yes — only from the list below |
| `type` | what kind of object this is | yes — only from the list below |
| `tags` | what the file is for | a declared list, extended deliberately |

## The extension rule

**A new subject or tag goes into this file first, and only then gets used.**
No inventing one while writing — `validate.py` will fail, which is the point.

If no subject fits → leave `subject:` empty. That is correct and intended, not a gap:
a page about HNSW indexing is not a "life domain", and it is found through
`type` + `tags` + semantic search instead.

## subject

> **Replace these with your own life domains.** Each subject is a wikilink that topic hubs,
> notes and wiki pages attach to via the `subject:` frontmatter field. They are examples —
> the machinery matters, the vocabulary is yours.

- [[Investing]] — everything related to the stock market
- [[Obsidian]] — everything I learn about the Obsidian app
- [[Style]] — fashion and clothing
- [[Trips]] — nature and travel, places I want to visit or already have
- [[Books]] — books I read and what I learned from them
- [[Fitness]] — physical training and health
- [[Projects]] — ideas and projects I'm working on
- [[AI Courses]] — summaries and courses I take on AI
- [[Work]] — everything related to work

## type (8)

The axis OKF adds. Answers "what kind of object is this", not "what is it about":

- `wiki-page` — a compiled knowledge page in `7 - Wikipedia/`
- `note` — one of my own notes in `2 - Notes/`
- `topic-hub` — a topic page in `1 - Topics/`
- `template` — a template in `4 - Templates/`
- `checklist` — a checklist for a repeated process
- `report` — a report generated automatically by a script
- `index` — a catalog (`7 - Wikipedia/index.md`)
- `log` — an operations log (`7 - Wikipedia/log.md`)

`7 - Wikipedia/raw/` also contains `youtube` and `rtf` — those are **source** kinds, not
knowledge pages. `raw/` is immutable and never rewritten.

## tags (16)

**System & structure** — load-bearing; scripts emit these, don't rename them
`wiki` · `topic` · `index` · `log` · `report` · `cache` · `archive`

**Learning & AI**
`learning` · `ai` · `claude` · `obsidian`

**Content examples** — replace these with your own, the same way you replace subjects
`plan` · `idea` · `book` · `trip` · `work`

### Tag writing rules

- **No leading `#`** inside frontmatter. Write `ai`, never `#ai` — Obsidian Bases and Dataview
  treat those as two different tags, which splits every view that groups by `tags`.
- Lowercase.
- Space → underscore.

## The OKF v0.2 trust layer

Beyond the three axes, every file carries provenance. Absent keys have meaningful defaults —
writing a default out is churn, so don't:

| Key | Meaning | Default when absent |
| --- | --- | --- |
| `generated_by` | who produced it — `human:me`, `process:<name>`, or `<agent>/<version>` | — |
| `generated_at` | when it was produced | — |
| `verified` | `[{by, at}]` — who *reviewed* it. Write it only via `okf_verify.py` | **unverified** |
| `status` | `draft` / `stable` / `deprecated` | **`stable`** |
| `wiki_sources` | provenance links on compiled pages (this vault's OKF `sources`) | — |

`generated_by` and `generated_at` are **two flat keys, never a nested `generated:` map** —
Obsidian Properties renders only flat scalars and lists, so a nested map swallows both rows.

Also on every file: `background` (a one-line description that doubles as the cross-language
bridge for semantic search). There is no separate creation-date key — `generated_at` carries it.
`private` is retired: privacy is folder-only, so don't add the key (an existing `private: false`
is a harmless leftover).

## Running it

```bash
python3 "0 - System/scripts/validate.py"     # enforces this file
python3 "0 - System/scripts/okf_verify.py"   # stamps/audits the trust layer
bash    "0 - System/list_tags.sh"            # what is actually in the vault, for comparison
```
