---
subject:
tags:
background: The vault's skill catalog + each skill's trigger — single source of truth for skill registration
private: false
created: 2026-07-08
---

# skills-index.md — The Skill Catalog

> A Layer 2 core file of [[AIOS]]. Single source of truth for the skill list. The skills themselves in `0 - System/SKILL-*.md` are **lazy-loaded** — only when the request matches (see [[CLAUDE]]). When a skill is ported to Hermes, that's the format (SKILL.md) and the source stays here.

## Knowledge & wiki maintenance

| Skill | When to trigger | Role |
|-------|-----------------|------|
| `SKILL-ingest` | "compile…" / a new source (URL, YouTube, raw) | Compile an external source into a wiki page + update manifest/index/log |
| `SKILL-resolve` | after every ingest | Update existing pages for contradictions/reinforcements/additions; updates last_compiled |
| `SKILL-crosslink` | after every ingest | Automatic [[wikilinks]] (dry-run → apply) |
| `SKILL-query` | a general question about the vault | Answer from the wiki with citations + offer to save new knowledge |
| `SKILL-lint` | "health check" | Validation: frontmatter, broken links, stale pages, missing sources |
| `SKILL-status` | "what's the wiki status?" / "what's pending?" | Health check: manifest, sources, compile state |

## Personal

| Skill | When to trigger | Role |
|-------|-----------------|------|
| `SKILL-journal-summary` | "summarize my week/journal" | Journal summary **on local Ollama only** — never through the Claude API or an external channel. Output: `2 - Notes/` with `private: true` |
| `SKILL-personal-stylist` | style / clothes / outfits | Outfit advice from the existing wardrobe; spots gaps; considers the weather |
| `SKILL-Nutrition-Advisor` | food / nutrition | Nutrition coach based on the profile, macro targets and the food bank |

## Investing

`SKILL-investment-agent` is the entry point; it routes to the sub-skills or handles it directly.

| Skill | When to trigger | Role |
|-------|-----------------|------|
| `SKILL-investment-agent` | investments / portfolio / stocks / "what about [ticker]?" | Investment desk head: quick-check, sizing, routing to sub-skills (IBKR + Playwright) |
| `SKILL-investment-fundamental` | routed from agent | Hedge-fund-style fundamental research: 5 layers, 26 dimensions |
| `SKILL-investment-graph` | routed from agent | Quantitative technical analysis: EMA, ATR, RSI, MACD, volume, patterns |
| `SKILL-investment-stop-loss` | a stop-loss request | Precise stop calculation: `Stop = Anchor − 1.5×ATR` (not percentages) |
| `SKILL-investment-deep-analyze` | "full analysis / deep dive" | Orchestrator: runs the three skills and synthesizes with a 14-point entry checklist |

## Notes

- MCP routing (IBKR/Gmail etc.) stays on the Claude Code side; Hermes reads outputs from the vault.
- Never invent subjects or tags not in SCHEMA. If none fits → leave empty.
- Links: [[me]] · [[vault-map]] · [[CLAUDE]]
