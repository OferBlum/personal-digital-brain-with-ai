"""Isolated privacy regression tests for the folder boundary; never point these at the real vault."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from privacy_guard import PRIVATE_DIR, is_blocked  # noqa: E402


class StubOllama:
    """Local stand-in for the embedding service, so the real CLI runs end to end."""

    def __init__(self, test):
        import http.server
        import threading

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                payload = json.dumps({'embeddings': [[1.0, 0.0] for _ in data['input']]}).encode()
                self.send_response(200); self.end_headers(); self.wfile.write(payload)

            def log_message(self, *args): pass

        server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        test.addCleanup(server.server_close)
        test.addCleanup(server.shutdown)
        self.url = f'http://127.0.0.1:{server.server_port}'


class FolderBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name) / 'fixture'
        (self.root / '2 - Notes').mkdir(parents=True)
        (self.root / PRIVATE_DIR / 'journal').mkdir(parents=True)
        self.secret = self.root / PRIVATE_DIR / 'journal' / 'day.md'
        self.secret.write_text('---\nbackground: diary\n---\n' + 'semantic alpha secret diary ' * 12)
        self.note = self.root / '2 - Notes' / 'safe.md'
        self.note.write_text('---\nbackground: test\n---\n' + 'safe semantic alpha ' * 12)
        self.env = {**os.environ, 'VAULT_ROOT': str(self.root), 'OLLAMA_HOST': 'http://127.0.0.1:9'}

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args], env=self.env,
                              capture_output=True, text=True)

    def fresh_index_module(self):
        import importlib
        for name in ('privacy_guard', 'vaultlib', 'safe_input', 'embed_index'):
            sys.modules.pop(name, None)
        return importlib.import_module('embed_index')

    def test_private_folder_never_listed_or_opened_in_any_mode(self):
        import builtins
        import io
        touched = []
        real_scandir, real_open, real_io_open = os.scandir, builtins.open, io.open

        def spy_scandir(path='.', *a, **kw):
            if is_blocked(path): touched.append(('list', str(path)))
            return real_scandir(path, *a, **kw)

        def spy_open(file, *a, **kw):
            if is_blocked(file): touched.append(('open', str(file)))
            return real_open(file, *a, **kw)

        def spy_io_open(file, *a, **kw):
            if is_blocked(file): touched.append(('open', str(file)))
            return real_io_open(file, *a, **kw)

        with patch.dict(os.environ, self.env):
            index = self.fresh_index_module()
            with patch('os.scandir', side_effect=spy_scandir), \
                 patch('builtins.open', side_effect=spy_open), \
                 patch('io.open', side_effect=spy_io_open), \
                 patch.object(index, 'embed', side_effect=lambda texts: index.np.eye(len(texts), 2, dtype='float32')):
                paths = [index.V.rel(p) for p, _, _ in index.collect()]
                for action in (index._diff, index.status, index.check, index.changes, index.build):
                    action()
                index.V.all_md_index()
        self.assertEqual(paths, ['2 - Notes/safe.md'])
        self.assertEqual(touched, [])

    def test_retired_flag_is_indexed_and_private_folder_is_not(self):
        flagged = self.root / '2 - Notes' / 'flagged.md'
        flagged.write_text('---\nprivate: true\n---\n' + 'semantic alpha flagged ' * 12)
        self.env['OLLAMA_HOST'] = StubOllama(self).url
        result = self.cli('embed_index.py')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        hit = self.cli('vsearch.py', 'semantic alpha', '--json')
        self.assertEqual(hit.returncode, 0, hit.stderr)
        self.assertEqual(sorted(json.loads(hit.stdout)), ['2 - Notes/flagged.md', '2 - Notes/safe.md'])
        chunks = (self.root / 'vector-out').rglob('chunks.jsonl')
        self.assertNotIn('diary', ''.join(c.read_text() for c in chunks))
        for option in ('--status', '--changes', '--check', '--audit'):
            out = self.cli('embed_index.py', option)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertNotIn('day.md', out.stdout + out.stderr)
            self.assertNotIn(PRIVATE_DIR, out.stdout + out.stderr)

    def test_symlink_into_private_folder_is_refused(self):
        link = self.root / '2 - Notes' / 'link.md'
        link.symlink_to(self.secret)
        with patch.dict(os.environ, self.env):
            index = self.fresh_index_module()
            paths = [index.V.rel(p) for p, _, _ in index.collect()]
            self.assertFalse(index.S.permitted('2 - Notes/link.md'))
        self.assertEqual(paths, ['2 - Notes/safe.md'])

    def test_search_only_returns_paths_and_drops_deleted_notes(self):
        self.env['OLLAMA_HOST'] = StubOllama(self).url
        self.assertEqual(self.cli('embed_index.py').returncode, 0)
        names = self.cli('vsearch.py', 'semantic alpha')
        self.assertEqual(names.stdout.strip(), '2 - Notes/safe.md')
        self.assertNotIn('safe semantic alpha', names.stdout)
        self.assertNotIn('background', names.stdout)
        self.note.unlink()
        hit = self.cli('vsearch.py', 'semantic alpha', '--json')
        self.assertEqual(json.loads(hit.stdout), [], hit.stderr)

    def test_failure_never_publishes_partial_or_old_chunks(self):
        out = self.root / 'vector-out'
        out.mkdir()
        (out / 'meta.json').write_text('{"model":"legacy"}')
        (out / 'chunks.jsonl').write_text('{"path":"2 - Notes/safe.md","text":"OLD SECRET"}\n')
        self.assertNotEqual(self.cli('embed_index.py').returncode, 0)
        result = self.cli('vsearch.py', 'secret', '--json')
        self.assertNotIn('OLD SECRET', result.stdout + result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((out / 'active.json').exists())

    def test_failed_update_preserves_atomic_pointer(self):
        stub = StubOllama(self).url
        self.env['OLLAMA_HOST'] = stub
        self.assertEqual(self.cli('embed_index.py').returncode, 0)
        pointer = (self.root / 'vector-out' / 'active.json').read_bytes()
        self.note.write_text('a revised semantic note ' * 10)
        self.env['OLLAMA_HOST'] = 'http://127.0.0.1:9'
        self.assertNotEqual(self.cli('embed_index.py').returncode, 0)
        self.assertEqual((self.root / 'vector-out' / 'active.json').read_bytes(), pointer)
        # The previous generation keeps serving; the note is still inside the boundary.
        self.env['OLLAMA_HOST'] = stub
        result = self.cli('vsearch.py', 'semantic', '--json')
        self.assertEqual(json.loads(result.stdout), ['2 - Notes/safe.md'], result.stderr)


if __name__ == '__main__':
    unittest.main()
