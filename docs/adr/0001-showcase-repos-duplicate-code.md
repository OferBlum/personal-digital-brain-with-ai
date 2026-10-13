# Showcase repos duplicate code instead of sharing a package

The system is split into small showcase repos, one idea each, so a reader can grasp and copy any single idea without the rest. Almost every script imported a shared `vaultlib.py`, which imported `privacy_guard.py`. Rather than publish that as a shared package every repo depends on, each repo carries a trimmed copy of only the functions it uses, and the semantic index keeps its own positive allowlist instead of importing the guard.

We accepted the duplication because a shared package would force versioning and coordinated releases across every repo for a one-person system, and would make no repo readable or runnable on its own — the opposite of the reason for splitting.

## Consequences

- A fix to shared logic (e.g. frontmatter parsing) must be applied by hand in each repo that copied it.
- The OKF repo is the reference implementation of frontmatter parsing; other repos' copies follow it.
