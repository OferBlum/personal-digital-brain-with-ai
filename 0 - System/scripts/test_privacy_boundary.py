"""Synthetic privacy-boundary regressions; no real vault or provider calls."""
import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))


class PrivacyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='privacy-test-data-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.env = patch.dict(os.environ, {'VAULT_ROOT': str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)
        for name in ('privacy_guard', 'vaultlib', 'safe_input', 'embed_index', 'vsearch'):
            sys.modules.pop(name, None)
        self.G = importlib.import_module('privacy_guard')
        # Test the same denial logic under a synthetic name, never the real area.
        for name, value in (('PRIVATE_DIR', '9 - synthetic'), ('BLOCKED_DIRS', ('9 - synthetic',))):
            fixture_policy = patch.object(self.G, name, value)
            fixture_policy.start()
            self.addCleanup(fixture_policy.stop)
        self.V = importlib.import_module('vaultlib')
        self.S = importlib.import_module('safe_input')
        for folder in self.S.FOLDERS:
            (self.root / folder).mkdir()
        self.path = self.root / '2 - Notes' / 'test-data.md'

    def test_legacy_flag_is_ignored_by_guard_and_index(self):
        # Privacy is folder-only; the `private` property is kept but no longer enforced.
        self.path.write_text('---\nprivate: true\n---\nTEST DATA BODY\n')
        self.assertTrue(self.S.permitted('2 - Notes/test-data.md'))
        self.assertEqual(self.S.read('2 - Notes/test-data.md'), ({'private': True}, 'TEST DATA BODY\n'))
        self.assertFalse(self.V.is_forbidden(self.path))
        self.assertEqual(self.V.read_page(self.path)[1], 'TEST DATA BODY\n')
        self.assertIsNone(self.G.evaluate({'tool_input': {'file_path': str(self.path)}}))

    def test_malformed_headers_read_the_same_for_guard_index_and_vaultlib(self):
        cases = [
            '---\nprivate: false\nprivate: true\n---\n',
            '---\nprivate: true\nprivate: false\n---\n',
            '---\ntags: [broken\n---\n',
            '---\n- list instead of mapping\n---\n',
            '---\nprivate: false\n',
            '--- \nprivate: true\n---\n',
            '---\na: &flag false\nprivate: *flag\n---\n',
            '---\na: 1\na: 2\n---\n',
            '---\nx: {a: 1, a: 2}\n---\n',
            '---\nprivate: false\n' + ('x' * 70000) + '\n---\n',
        ]
        for number, header in enumerate(cases):
            with self.subTest(case=number):
                text = header + 'TEST DATA BODY\n'
                self.path.write_text(text)
                self.assertFalse(self.V.is_forbidden(self.path))
                self.assertIsNone(self.G.evaluate({'tool_input': {'file_path': str(self.path)}}))
                page = self.V.read_page(self.path)
                self.assertEqual(self.S.read('2 - Notes/test-data.md'), page)
                self.assertTrue(page[1].endswith('TEST DATA BODY\n'))
                if not page[0]:
                    # An unparsed header stays in the body, so a write-back loses nothing.
                    self.assertEqual(self.V.render_page(*page), text)

    def test_new_fields_are_never_written_above_a_broken_header(self):
        self.path.write_text('---\ntags: [broken\n---\nTEST DATA BODY\n')
        meta, body = self.V.read_page(self.path)
        self.assertTrue(self.V.has_broken_header(meta, body))
        with self.assertRaises(ValueError):
            self.V.render_page({'type': 'note'}, body)

    def test_public_empty_false_and_plain_headers_remain_readable(self):
        for header in ('---\n---\n', '---\nprivate: false\n---\n', '---\nprivate: true\n---\n',
                       '---\nprivate: "true"\n---\n', '---\nprivate: null\n---\n', ''):
            with self.subTest(header=header):
                self.path.write_text(header + 'TEST DATA PUBLIC BODY\n')
                self.assertTrue(self.S.permitted('2 - Notes/test-data.md'))
                self.assertEqual(self.S.read('2 - Notes/test-data.md')[1], 'TEST DATA PUBLIC BODY\n')
                self.assertEqual(self.V.read_page(self.path)[1], 'TEST DATA PUBLIC BODY\n')
    def test_default_and_explicit_vault_scans_never_list_vault_root(self):
        self.path.write_text('---\n---\nTEST DATA PUBLIC\n')
        malformed = self.path.with_name('malformed-test-data.md')
        malformed.write_text('---\na: 1\na: 2\n---\n' + 'TEST DATA BODY\n')
        private = self.root / self.G.PRIVATE_DIR
        private.mkdir()
        (private / 'synthetic.md').write_text('TEST DATA ONLY\n')
        real_scandir = os.scandir
        def deny_root_and_private(path='.', *args, **kwargs):
            p = Path(path)
            if p == self.root or private in (p, *p.parents):
                self.fail('listed forbidden fixture area')
            return real_scandir(path, *args, **kwargs)
        with patch('os.scandir', side_effect=deny_root_and_private):
            self.assertEqual(list(self.G.iter_vault_files()), [malformed, self.path])
            self.assertEqual(list(self.G.iter_vault_files(self.root)), [malformed, self.path])
            self.assertEqual(self.V.all_md_index(),
                             {'malformed-test-data': [malformed], 'test-data': [self.path]})

    def test_iterators_and_links_hide_symlinks_but_keep_malformed_headers(self):
        self.path.write_text('---\n---\nTEST DATA PUBLIC\n')
        malformed = []
        for folder in self.S.FOLDERS:
            path = self.root / folder / 'malformed-test-data.md'
            path.write_text('---\na: 1\na: [\n---\n' + 'TEST DATA BODY\n')
            malformed.append(path)
        link = self.path.with_name('linked-test-data.md')
        link.symlink_to(self.path)
        seen = [p for iterator in (self.V.iter_notes, self.V.iter_topics, self.V.iter_wiki_pages)
                for p, _, _ in iterator()]
        self.assertNotIn(link, seen)
        self.assertTrue(all(p in seen for p in malformed))
        index = {'malformed-test-data': malformed, 'linked-test-data': [link]}
        self.assertEqual(self.V.resolve_link('2 - Notes/malformed-test-data', index), ('ok', malformed[1]))
        self.assertEqual(self.V.resolve_link('malformed-test-data', index), ('ambiguous', None))
        self.assertEqual(self.V.resolve_link('linked-test-data', index), ('missing', None))
        self.assertEqual(self.V.resolve_link('2 - Notes/test-data'), ('ok', self.path))
        self.assertEqual(self.V.resolve_link('../outside/test-data'), ('missing', None))

    def test_symlink_allowed_root_is_not_listed_or_followed(self):
        outside = self.root / 'outside-test-data'
        outside.mkdir()
        (outside / 'visible.md').write_text('TEST DATA ONLY\n')
        notes = self.root / '2 - Notes'
        notes.rmdir()
        notes.symlink_to(outside, target_is_directory=True)
        real_scandir = os.scandir
        def spy(path='.', *args, **kwargs):
            if Path(path) in (notes, outside):
                self.fail('followed symlink directory')
            return real_scandir(path, *args, **kwargs)
        with patch('os.scandir', side_effect=spy):
            self.assertEqual(list(self.S.sources()), [])
            self.assertEqual(list(self.V.iter_notes()), [])
            self.assertEqual(self.V.all_md_index(), {})
        self.assertFalse(self.S.permitted('2 - Notes/visible.md'))
        with self.assertRaises(FileNotFoundError):
            self.V.read_page(notes / 'visible.md')

    def test_protected_path_is_refused_before_any_open_or_stat(self):
        private_path = self.root / self.G.PRIVATE_DIR / 'never-created-test-data.md'
        with patch('os.open', side_effect=AssertionError('protected filesystem touched')), \
             patch.object(Path, 'exists', side_effect=AssertionError('protected stat')):
            self.assertTrue(self.G.is_blocked(private_path))
            with self.assertRaises(FileNotFoundError):
                self.V.read_page(private_path)
            self.assertEqual(self.V.resolve_link(f'{self.G.PRIVATE_DIR}/never-created-test-data'),
                             ('missing', None))
    def test_backup_refuses_excluded_source_before_copy_or_creation(self):
        target = self.path.with_name('synthetic-target.md')
        target.write_text('SYNTHETIC BODY\n')
        self.path.symlink_to(target)
        with patch('shutil.copy2', side_effect=AssertionError('excluded source copied')):
            with self.assertRaises(FileNotFoundError):
                self.V.backup([self.path], 'fixture')
        self.assertFalse((self.root / '7 - Wikipedia' / '.backup').exists())

    def test_both_runtime_adapters_fail_closed_for_malformed_input(self):
        malformed = ('not json', 'null', '[]', '42', '{}',
                     '{"tool_input":null}', '{"tool_input":[]}',
                     '{"tool_input":{},"tool_input":{"path":"hidden"}}',
                     '{"tool_input":{"number":NaN}}')
        for text in malformed:
            with self.subTest(text=text):
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    self.assertEqual(self.G.run_claude(text), 2)
                    self.assertEqual(self.G.run_hermes(text), 0)
                self.assertEqual(json.loads(stdout.getvalue())['decision'], 'block')
                self.assertNotIn('hidden', stdout.getvalue() + stderr.getvalue())

    def test_hook_refuses_symlink_paths_without_disclosing_name(self):
        target = self.path.with_name('synthetic-target.md')
        target.write_text('TEST DATA SECRET\n')
        self.path.symlink_to(target)
        payload = {'tool_input': {'edits': [{'file_path': str(self.path)}]}}
        self.assertIsNotNone(self.G.evaluate(payload))
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(self.G.run_claude(json.dumps(payload)), 2)
            self.assertEqual(self.G.run_hermes(json.dumps(payload)), 0)
        self.assertEqual(json.loads(stdout.getvalue())['decision'], 'block')
        self.assertNotIn(self.path.name, stdout.getvalue() + stderr.getvalue())

    def test_builtin_selftest_matches_current_policy_and_restores_vault(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        original = self.G.VAULT
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(self.G.selftest(), 0)
        self.assertEqual(self.G.VAULT, original)
        self.assertNotIn('[FAIL]', stdout.getvalue())
    def seed_generation(self, schema=3, policy=None):
        I = importlib.import_module('embed_index')
        generation = 'a' * 32
        base = I.OUT / generation
        base.mkdir(parents=True)
        meta = {'schema': schema, 'model': 'LOCAL TEST DATA', 'dim': 2,
                'considered': {'2 - Notes/test-data.md': 'test-data-hash'}}
        if policy is not None:
            meta['privacy_policy'] = policy
        (base / 'meta.json').write_text(json.dumps(meta))
        (I.OUT / 'active.json').write_text(json.dumps({'generation': generation}))
        (base / 'chunks.jsonl').write_text(json.dumps({
            'path': '2 - Notes/test-data.md', 'text': 'OLD TEST DATA BODY',
            'body_hash': 'test-data-hash'}) + '\n')
        I.np.save(base / 'vectors.npy', I.np.array([[1., 0.]], dtype='float32'))
        return I, base

    def test_schema3_generation_rejected_before_cached_bodies_are_read(self):
        self.path.write_text('---\n---\n' + 'PUBLIC LOCAL TEST DATA ' * 12)
        I, base = self.seed_generation()
        search = importlib.import_module('vsearch')
        original = Path.read_text
        def deny_cache(path, *args, **kwargs):
            if path == base / 'chunks.jsonl':
                self.fail('legacy cached body was read')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', deny_cache):
            self.assertEqual(I.active(), (None, None))
            with self.assertRaises(SystemExit):
                search.load()
            with contextlib.redirect_stdout(io.StringIO()):
                I.status()
                I.audit()
                I.check()
                I.changes()
                from test_safe_index import StubOllama
                I.OLLAMA = StubOllama(self).url
                I.build()
        current, meta = I.active()
        self.assertIsNotNone(current)
        self.assertEqual(meta['schema'], 4)
        self.assertEqual(meta['privacy_policy'], 'folder-boundary-v1')
        self.assertNotIn('OLD TEST DATA BODY', (current / 'chunks.jsonl').read_text())

    def test_previous_policy_generation_is_opaque(self):
        self.path.write_text('---\nprivate: true\n---\nTEST DATA SECRET\n')
        schema = getattr(importlib.import_module('embed_index'), 'SCHEMA', 3)
        I, base = self.seed_generation(schema=schema, policy='strict-header-v1')
        search = importlib.import_module('vsearch')
        original = Path.read_text
        def deny_cache(path, *args, **kwargs):
            if path == base / 'chunks.jsonl':
                self.fail('cached body of newly excluded source was read')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', deny_cache):
            self.assertEqual(I.active(), (None, None))
            with self.assertRaises(SystemExit):
                search.load()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                I.changes()
                I.status()
                I.audit()
            self.assertNotIn(self.path.name, output.getvalue())

    def test_wrong_policy_and_cache_symlinks_fail_closed(self):
        self.path.write_text('TEST DATA PUBLIC\n')
        schema = getattr(importlib.import_module('embed_index'), 'SCHEMA', 3)
        I, base = self.seed_generation(schema=schema, policy='folder-only')
        self.assertEqual(I.active(), (None, None))
        (base / 'meta.json').write_text(json.dumps({
            'schema': 4, 'privacy_policy': 'strict-header-v1',
            'considered': {'2 - Notes/test-data.md': 'test-data-hash'}}))
        chunks = base / 'chunks.jsonl'
        chunks.unlink()
        chunks.symlink_to(self.path)
        self.assertEqual(I.active(), (None, None))

    def test_changes_never_discloses_removed_or_excluded_filenames(self):
        I = importlib.import_module('embed_index')
        output = io.StringIO()
        with patch.object(I, '_diff', return_value=(set(), {'2 - Notes/excluded-test-data.md'}, set())), \
             contextlib.redirect_stdout(output):
            I.changes()
        self.assertNotIn('excluded-test-data.md', output.getvalue())
        self.assertIn('1', output.getvalue())
    def test_reindex_wrapper_preserves_count_only_changes(self):
        import shutil
        import subprocess
        scripts = self.root / 'synthetic-scripts'
        scripts.mkdir()
        source = Path(__file__).resolve().parent / 'reindex.sh'
        shutil.copyfile(source, scripts / 'reindex.sh')
        (scripts / 'vault-python.sh').write_text(
            '#!/bin/bash\nif [ "${2:-}" = "--changes" ]; then\n'
            "  printf '+ 2 new eligible files\\n- 3 removed files\\n'\n"
            'else\n  printf "LOCAL TEST DATA BUILD\\n"\nfi\n')
        from test_safe_index import StubOllama
        result = subprocess.run(['bash', str(scripts / 'reindex.sh')],
                                env={**os.environ, 'OLLAMA_HOST': StubOllama(self).url},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('+ 2 new eligible files', result.stdout)
        self.assertIn('- 3 removed files', result.stdout)
        self.assertNotIn('1 new', result.stdout)
        self.assertIn('LOCAL TEST DATA BUILD', result.stdout)

    def test_index_build_refuses_symlink_output_before_writing(self):
        I = importlib.import_module('embed_index')
        destination = self.root / 'outside-test-data-cache'
        destination.mkdir()
        I.OUT.symlink_to(destination, target_is_directory=True)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            I.build()
        self.assertEqual(list(destination.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
