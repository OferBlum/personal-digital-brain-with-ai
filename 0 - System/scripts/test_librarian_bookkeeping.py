#!/usr/bin/env python3
"""Synthetic-only regressions: never execute a CLI against the live vault.

Default mode isolates bookkeeping behind a mock shared guard that refuses symlinks
and paths marked with deny().
BOOKKEEPING_REAL_GUARD=1 additionally exercises the completed shared guard,
with all of its root constants patched to the temporary fixture vault.
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unicodedata
import unittest
from unittest.mock import patch

import yaml

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).parent
TARGETS = (
    ("build_index", "INDEX"),
    ("build_manifest", "DOT"),
    ("build_manifest", "OLD"),
    ("append_log", "LOG"),
    ("validate", "SCHEMA"),
    ("validate", "REPORT"),
    ("wiki_sources_report", "REPORT"),
    ("fix_frontmatter", "INDEX"),
)


class BookkeepingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bookkeeping-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.v = types.ModuleType("vaultlib")
        for name, relative in (("VAULT", "."), ("WIKI", "7 - Wikipedia"),
                               ("RAW", "7 - Wikipedia/raw"), ("NOTES", "2 - Notes"),
                               ("TOPICS", "1 - Topics"), ("SYS", "0 - System")):
            setattr(self.v, name, self.root / relative)
            getattr(self.v, name).mkdir(parents=True, exist_ok=True)
        self.guards = []
        self.denied = set()
        self.backups = []
        self.v.nfc = lambda s: unicodedata.normalize("NFC", str(s))
        self.v.today = lambda: "2026-10-06"
        self.v.rel = lambda p: str(Path(p).relative_to(self.root))
        self.v.is_forbidden = self.guard
        self.v.backup = self.backup
        self.v.iter_wiki_pages = lambda: iter(())
        self.v.iter_notes = lambda: iter(())
        self.v.iter_topics = lambda: iter(())
        self.v.all_md_index = lambda: {}
        self.v.resolve_link = lambda inner, index: ("missing", None)
        self.v.has_broken_header = lambda meta, body: False
        self.v.render_page = lambda meta, body: "---\n" + yaml.safe_dump(meta, allow_unicode=True) + "---\n" + body
        self.real_guard = None
        if os.environ.get("BOOKKEEPING_REAL_GUARD") == "1":
            with patch.dict(sys.modules):
                sys.modules.pop("vaultlib", None)
                sys.path.insert(0, str(SCRIPTS))
                try:
                    import vaultlib
                    self.real_guard = vaultlib.is_forbidden
                    for name in ("VAULT", "WIKI", "RAW", "NOTES", "TOPICS", "SYS"):
                        p = patch.object(vaultlib, name, getattr(self.v, name))
                        p.start()
                        self.addCleanup(p.stop)
                finally:
                    sys.path.pop(0)

    def guard(self, path):
        path = Path(path)
        self.guards.append(path)
        if self.real_guard:
            return self.real_guard(path)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            return True
        if not path.is_relative_to(self.root):
            return True
        return path in self.denied

    def deny(self, path, text):
        """Make the shared guard refuse `path`. The real policy has no in-place marker, so a symlink."""
        if self.real_guard:
            destination = self.root / ("synthetic-" + path.name)
            destination.write_text(text, encoding="utf-8")
            if path.exists() or path.is_symlink():
                path.unlink()
            path.symlink_to(destination)
        else:
            path.write_text(text, encoding="utf-8")
            self.denied.add(path)

    def backup(self, paths, label):
        self.backups.append((tuple(paths), label))
        return self.root / ".backup" / label

    def load(self, name):
        spec = importlib.util.spec_from_file_location("fixture_" + name, SCRIPTS / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"vaultlib": self.v}), patch.object(sys, "argv", [name]):
            spec.loader.exec_module(module)
        return module

    def invoke(self, module, args=()):
        output = io.StringIO()
        with patch.object(sys, "argv", [module.__name__, *args]), contextlib.redirect_stdout(output):
            module.main()
        return output.getvalue()

    def args_for(self, name):
        return ["--op", "ingest", "--title", "fixture entry"] if name == "append_log" else []

    def test_append_log_preserves_exact_old_bytes_and_appends(self):
        module = self.load("append_log")
        old = b"---\r\ntype: log\r\n---\r\n# Wiki Log\r\n\r\n\r\n## historical first\r\nold content  \r\n\r\n"
        module.LOG.write_bytes(old)
        self.invoke(module, self.args_for("append_log"))
        actual = module.LOG.read_bytes()
        self.assertTrue(actual.startswith(old), "Every existing byte, including CRLF and whitespace, must remain untouched")
        self.assertEqual(actual.count(b"fixture entry"), 1)
        self.assertGreater(actual.index(b"fixture entry"), len(old))

    def test_manifest_drops_newly_private_mappings_preserves_other_history(self):
        module = self.load("build_manifest")
        source = self.v.RAW / "public-source.md"
        source.write_text("---\ntype: source\n---\npublic\n", encoding="utf-8")
        blocked = self.v.RAW / "restricted-source.md"
        self.deny(blocked, "synthetic body\n")
        page = self.v.WIKI / "public-page.md"
        page.write_text("---\ntype: wiki-page\n---\npublic\n", encoding="utf-8")
        private_page = self.v.WIKI / "restricted-page.md"
        self.deny(private_page, "synthetic body\n")
        records = [
            {"path": self.v.rel(source), "ingested": "2020-01-01", "pages_produced": [page.stem, private_page.stem]},
            {"path": self.v.rel(blocked), "ingested": "2021-01-01", "pages_produced": [page.stem]},
            {"path": "7 - Wikipedia/raw/missing-historical.md", "ingested": "2019-01-01", "pages_produced": ["missing-historical-page"]},
            {"path": "7 - Wikipedia/raw/history-with-no-pages.md", "ingested": "2018-01-01", "pages_produced": []},
        ]
        module.DOT.write_text(json.dumps(records), encoding="utf-8")
        clean = {"path": "7 - Wikipedia/raw/other-history.md", "ingested": "2017-01-01", "pages_produced": ["other-page"]}
        module.OLD.write_text(json.dumps({"sources": [clean]}), encoding="utf-8")
        output = self.invoke(module)
        result = json.loads(module.DOT.read_text(encoding="utf-8"))
        by_path = {e["path"]: e for e in result}
        self.assertNotIn(self.v.rel(blocked), by_path)
        self.assertEqual(by_path[self.v.rel(source)]["pages_produced"], [page.stem])
        for e in (records[2], records[3], clean):
            self.assertEqual(by_path[e["path"]], e, "Unrelated permitted history must survive, including records with no pages")
        self.assertNotIn(private_page.stem, output)
        self.assertNotIn(blocked.name, output)
        for paths, _ in self.backups:
            self.assertNotIn(module.DOT, paths, "Never copy stale excluded mappings into a fresh manifest backup")
        self.assertFalse(module.OLD.exists())

    def test_validate_does_not_emit_excluded_source_name(self):
        module = self.load("validate")
        blocked = self.v.RAW / "restricted-source.md"
        self.deny(blocked, "synthetic body\n")
        page = self.v.WIKI / "public-page.md"
        meta = {"type": "wiki-page", "tags": ["wiki"], "last_compiled": "2026-10-06", "wiki_sources": ["[[" + self.v.rel(blocked) + "]]" ]}
        self.v.iter_wiki_pages = lambda: iter([(page, meta, "public body")])
        output = self.invoke(module)
        self.assertNotIn(blocked.name, output + module.REPORT.read_text(encoding="utf-8"))

    def test_source_report_does_not_emit_excluded_source_name(self):
        module = self.load("wiki_sources_report")
        blocked = self.v.RAW / "restricted-source.md"
        self.deny(blocked, "synthetic body\n")
        page = self.v.WIKI / "public-page.md"
        self.v.iter_wiki_pages = lambda: iter([(page, {"wiki_sources": ["[[" + self.v.rel(blocked) + "]]" ]}, "public body")])
        output = self.invoke(module)
        self.assertNotIn(blocked.name, output + module.REPORT.read_text(encoding="utf-8"))

    def test_source_report_handles_excluded_resolver_status_without_target(self):
        module = self.load("wiki_sources_report")
        self.v.resolve_link = lambda inner, index: ("forbidden", None)
        result = module.classify(self.v.WIKI / "public-page.md", "[[restricted-source]]", {})
        self.assertIsNotNone(result)
        self.assertNotIn("restricted-source", str(result))

    def test_source_report_labels_url_and_nonmarkdown_as_unvalidated(self):
        module = self.load("wiki_sources_report")
        for entry in ("https://example.test/public", "[[7 - Wikipedia/raw/attachment.pdf]]"):
            with self.subTest(entry=entry):
                result = module.classify(self.v.WIKI / "public-page.md", entry, {})
                self.assertIn("not validated", str(result).lower())

    def test_append_log_rejects_excluded_page_reference(self):
        module = self.load("append_log")
        page = self.v.WIKI / "restricted-page.md"
        self.deny(page, "synthetic body\n")
        with self.assertRaises(SystemExit) as stopped:
            self.invoke(module, self.args_for("append_log") + ["--pages", page.stem])
        self.assertNotIn(page.stem, str(stopped.exception))
        self.assertEqual(self.backups, [])
        self.assertFalse(module.LOG.exists())

    def test_append_log_rejects_excluded_source_reference(self):
        module = self.load("append_log")
        source = self.v.RAW / "restricted-source.md"
        self.deny(source, "synthetic body\n")
        with self.assertRaises(SystemExit) as stopped:
            self.invoke(module, self.args_for("append_log") + ["--source", self.v.rel(source)])
        self.assertNotIn(source.name, str(stopped.exception))
        self.assertEqual(self.backups, [])
        self.assertFalse(module.LOG.exists())

    def test_manifest_reports_legacy_classification_limits_without_removing_history(self):
        module = self.load("build_manifest")
        records = [{"path": path, "ingested": "2017-01-01", "pages_produced": ["historical-page"]}
                   for path in ("https://example.test/public", "7 - Wikipedia/raw/attachment.pdf")]
        module.DOT.write_text(json.dumps(records), encoding="utf-8")
        output = self.invoke(module)
        self.assertEqual(json.loads(module.DOT.read_text(encoding="utf-8")), records)
        self.assertIn("not validated", output.lower())

    def test_targets_becoming_private_during_backup_are_not_written(self):
        for name, attr in (("build_index", "INDEX"), ("build_manifest", "DOT"), ("append_log", "LOG")):
            with self.subTest(cli=name):
                module = self.load(name)
                target = getattr(module, attr)
                target.write_text("[]" if name == "build_manifest" else "---\ntype: index\n---\npublic history\n", encoding="utf-8")
                blocked = "SYNTHETIC PRIVATE BODY\n"
                def change_privacy(paths, label):
                    self.deny(target, blocked)
                    return self.root / ".backup" / label
                self.v.backup = change_privacy
                with self.assertRaises(SystemExit):
                    self.invoke(module, self.args_for(name))
                self.assertEqual(target.read_text(encoding="utf-8"), blocked)

    def test_fix_frontmatter_apply_rechecks_page_before_write(self):
        module = self.load("fix_frontmatter")
        module.APPLY = True
        page = self.v.WIKI / "public-page.md"
        page.write_text("---\ntype: wiki-page\n---\npublic body\n", encoding="utf-8")
        self.v.iter_wiki_pages = lambda: iter([(page, {"type": "wiki-page"}, "public body")])
        blocked = "SYNTHETIC PRIVATE BODY\n"
        def change_privacy(paths, label):
            self.deny(page, blocked)
            return self.root / ".backup" / label
        self.v.backup = change_privacy
        with self.assertRaises(SystemExit):
            self.invoke(module)
        self.assertEqual(page.read_text(encoding="utf-8"), blocked)

    def test_fix_frontmatter_dry_run_does_not_write_or_backup_pages(self):
        module = self.load("fix_frontmatter")
        page = self.v.WIKI / "public-page.md"
        old = "---\ntype: wiki-page\n---\npublic body\n"
        page.write_text(old, encoding="utf-8")
        self.v.iter_wiki_pages = lambda: iter([(page, {"type": "wiki-page"}, "public body")])
        self.invoke(module)
        self.assertEqual(page.read_text(encoding="utf-8"), old)
        self.assertEqual(self.backups, [])

    def test_permitted_empty_targets_are_guarded_and_work(self):
        for name in ("build_index", "build_manifest", "append_log", "validate", "wiki_sources_report", "fix_frontmatter"):
            with self.subTest(cli=name):
                module = self.load(name)
                self.invoke(module, self.args_for(name))
                for cli, attr in TARGETS:
                    if cli == name:
                        self.assertIn(getattr(module, attr), self.guards)

    def check_blocked(self, name, attr, symlink=False):
        module = self.load(name)
        target = getattr(module, attr)
        original = "DO NOT READ SYNTHETIC BODY\n"
        if symlink:
            destination = self.root / "synthetic-destination.md"
            destination.write_text(original, encoding="utf-8")
            target.symlink_to(destination)
        else:
            self.deny(target, original)
        read_text, write_text = Path.read_text, Path.write_text
        def checked_read(path, *args, **kwargs):
            if path == target:
                raise AssertionError("CLI read blocked target body before checking shared guard")
            return read_text(path, *args, **kwargs)
        def checked_write(path, *args, **kwargs):
            if path == target:
                raise AssertionError("CLI overwrote blocked target before checking shared guard")
            return write_text(path, *args, **kwargs)
        output = io.StringIO()
        with patch.object(Path, "read_text", checked_read), patch.object(Path, "write_text", checked_write), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as stopped:
                self.invoke(module, self.args_for(name))
        self.assertNotEqual(stopped.exception.code, 0)
        self.assertNotIn(target.name, str(stopped.exception))
        self.assertNotIn(target.name, output.getvalue())
        self.assertEqual(self.backups, [], "Guard must run before copying or backing up any metadata")
        if not symlink and not self.real_guard:  # deny() is a symlink under the real guard
            self.assertIn(target, self.guards, "CLI must invoke the shared privacy guard")
        self.assertEqual(target.read_text(encoding="utf-8"), original)


for cli, attr in TARGETS:
    for symlink in (False, True):
        def case(self, cli=cli, attr=attr, symlink=symlink):
            self.check_blocked(cli, attr, symlink)
        setattr(BookkeepingTests, "test_" + cli + "_" + attr.lower() + ("_symlink" if symlink else "_private"), case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
