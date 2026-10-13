# Digital Brain — An Agentic Obsidian Vault

The biggest advantage of AI is also its weakness: it knows everything, so its answers don't always
fit **you**. My fix is a knowledge base with all of **my** data — my Obsidian vault. AI agents get
access to it and become an assistant that knows about me.

> **I write the ideas, the agents read and enrich.**

What it does:

- **A wiki** of summaries of everything I watch and read
- **Search by meaning**, in Hebrew and English
- **A private folder** that no agent can reach
- **Any agent** — the rules, skills and memory live in the vault, not in one AI tool

## The pieces

This repo used to hold the whole system, but it got too long to read. So I split it into six small
repos. Each one shows one idea, and you can copy it on its own:

| Repo | What it does |
|------|--------------|
| [agentic-vault-skeleton](https://github.com/OferBlum/agentic-vault-skeleton) | The layout. One `AGENTS.md` for every agent, a three-file map so agents don't scan the whole vault, skills that load only when needed, and a session cache |
| [vault-privacy-guard](https://github.com/OferBlum/vault-privacy-guard) | Privacy is a folder, not a flag. One policy file, and a hook that checks every tool call in every agent |
| [okf-frontmatter-standard](https://github.com/OferBlum/okf-frontmatter-standard) | The metadata on top of each note: three closed fields (`type`, `subject`, `tags`), plus a mark for what the AI wrote and what I checked |
| [llm-wiki-youtube-transcript](https://github.com/OferBlum/llm-wiki-youtube-transcript) | The Karpathy method: an agent turns each source (YouTube, articles, PDFs) into a linked wiki page |
| [vault-semantic-search](https://github.com/OferBlum/vault-semantic-search) | Find notes by meaning in Hebrew and English, with a local index that never sees the private folder |
| [hermes-agent-layer](https://github.com/OferBlum/hermes-agent-layer) | A second agent, Hermes, on the same vault — no second copy of skills, memory or rules |

## How they fit together

```text
                    agentic-vault-skeleton  (folders, AGENTS.md, map, cache)
                               │
     ┌─────────────────────────┼──────────────────────────┐
     ▼                         ▼                          ▼
 okf-frontmatter-standard   llm-wiki-youtube-transcript   vault-semantic-search
 (what every file says      (fills 7 - Wikipedia/,        (finds notes and wiki
  about itself)              every page OKF-tagged)        pages by meaning)
     │                         │                          │
     └──────────── vault-privacy-guard: every agent, every tool, every script
                   is kept out of the private folder ─────┘
                               │
               Claude Code ────┴──── hermes-agent-layer (Hermes)
```

All the repos use the same folder layout (`0 - System/scripts/…`, `.claude/…`), so each one drops
right onto the skeleton. None of them needs another one to run. They repeat a little code instead
of sharing a package — [ADR 0001](docs/adr/0001-showcase-repos-duplicate-code.md) explains why.

## Where to start

1. Start with **agentic-vault-skeleton**. Fill in `me.md` and run your agent at the vault root.
2. Add **vault-privacy-guard** before you put anything private in the vault.
3. Add the rest in any order, when you need them.

The words I use across the repos (showcase repo, private folder, privacy guard, LLM wiki, OKF) are
explained in [CONTEXT.md](CONTEXT.md).

## License

MIT, see [LICENSE](LICENSE).
