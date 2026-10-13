# Digital Brain — An Agentic Obsidian Vault

A personal knowledge base that AI agents help maintain: one Obsidian vault, an AI-maintained wiki
of everything I watch and read, search by meaning in Hebrew and English, and a private folder no
agent can reach.

> **The core principle: I write my ideas; the agents read and enrich.**

This repo used to hold the whole system. It grew too long to read, so it's now split into six
small repos. Each one shows one idea that you can understand in a few minutes and copy on its own.
This page shows how they fit together.

## The pieces

| Repo | The idea |
|------|----------|
| [agentic-vault-skeleton](https://github.com/OferBlum/agentic-vault-skeleton) | The layout. One `AGENTS.md` for every agent, a three-file map so agents don't scan the vault, lazy-loaded skills, and a session cache |
| [vault-privacy-guard](https://github.com/OferBlum/vault-privacy-guard) | Privacy is a folder, not a flag. One policy file, enforced by a pre-tool hook in every agent runtime |
| [okf-frontmatter-standard](https://github.com/OferBlum/okf-frontmatter-standard) | Frontmatter with three closed axes (`type`, `subject`, `tags`) and a trust layer that separates generated from verified |
| [llm-wiki-youtube-transcript](https://github.com/OferBlum/llm-wiki-youtube-transcript) | The Karpathy method: an agent summarizes each source (YouTube, articles, PDFs) into a linked wiki page |
| [vault-semantic-search](https://github.com/OferBlum/vault-semantic-search) | Find notes by meaning across Hebrew and English, with a local index that never sees the private folder |
| [hermes-agent-layer](https://github.com/OferBlum/hermes-agent-layer) | A second agent runtime on the same vault, with no second copy of skills, memory or rules |

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

Every repo uses the same vault-relative layout (`0 - System/scripts/…`, `.claude/…`), so each
one drops onto the skeleton. None of them needs another to run. They duplicate a little code
instead of sharing a package, and
[ADR 0001](docs/adr/0001-showcase-repos-duplicate-code.md) explains why.

## Where to start

1. Start from **agentic-vault-skeleton**. Fill in `me.md` and run `claude` at the vault root.
2. Add **vault-privacy-guard** before you put anything private in the vault.
3. Add the rest in any order, as you need them.

The shared vocabulary (showcase repo, private folder, privacy guard, LLM wiki, OKF) is in
[CONTEXT.md](CONTEXT.md).

## License

MIT, see [LICENSE](LICENSE).
