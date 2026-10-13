# Digital Brain

An agentic Obsidian vault, published as a set of small repos that each present one idea of the system.

## Language

**Showcase repo**:
A standalone repo that presents exactly one idea of the system, readable in minutes and copyable on its own. It may duplicate a little code instead of depending on another showcase repo.
_Avoid_: module, package, component

**Umbrella repo**:
The entry-point repo that links every showcase repo and shows how they compose into one vault.
_Avoid_: monorepo, main repo

**Private folder**:
The single vault folder that holds every private file, including the journal. Being inside it is the only thing that makes a file private.
_Avoid_: journal (as a synonym), private flag

**Privacy guard**:
The enforcement of the private-folder rule across every agent runtime, search tool and script, from one policy implementation.
_Avoid_: safety

**LLM wiki**:
The AI-maintained wiki of source summaries (the Karpathy method), together with every ingest source that feeds it. YouTube is one ingest source, not a separate wiki.
_Avoid_: wikipedia, YouTube wiki

**OKF**:
The frontmatter standard: three closed axes (`type`, `subject`, `tags`) whose vocabulary is declared in the schema before use, plus the trust layer (`generated_by`, `verified`, `status`).
_Avoid_: tags system, metadata

## Relationships

- The **Umbrella repo** links every **Showcase repo**; no **Showcase repo** requires another to run
- The **Privacy guard** enforces exactly one rule: nothing in the **Private folder** is reachable
- Every page of the **LLM wiki** carries **OKF** frontmatter

## Flagged ambiguities

- "safety" was used for the privacy repo — resolved: it is the **Privacy guard**, and covers nothing beyond the private-folder rule.
- "llm wiki" and the existing YouTube transcript repo — resolved: one **LLM wiki**, YouTube is an ingest source.
