import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).with_name('sync_skills_to_hermes.py')
def load():
    spec=importlib.util.spec_from_file_location('sync_skills',SCRIPT)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class SyncTest(unittest.TestCase):
    def test_malformed_metadata_is_read_like_any_text(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'source.md'
            for header in ('invalid: [','a: &flag false','a: 1\na: 2'):
                with self.subTest(header=header):
                    text='---\n'+header+'\n---\nSYNTHETIC BODY\n'
                    p.write_text(text)
                    self.assertEqual(m.read_permitted_text(p),text)

    def test_legacy_privacy_flag_is_ignored(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'source.md'
            for value in ('true','null','0','"false"'):
                with self.subTest(value=value):
                    p.write_text('---\nprivate: '+value+'\n---\nSYNTHETIC BODY\n')
                    self.assertTrue(m.read_permitted_text(p).endswith('SYNTHETIC BODY\n'))

    def test_only_selected_source_is_generated(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); src=root/'0 - System'; src.mkdir()
            target=src/'hermes-skills'
            (src/'SKILL-query.md').write_text('# SKILL — Query\n\nQuery instructions\n')
            config={'SKILL-query.md':{'slug':'wiki-query','category':'knowledge','tags':['wiki'],'desc':'Query.'},'SKILL-status.md':{'slug':'wiki-status','category':'knowledge','tags':['wiki'],'desc':'Status.'}}
            with patch.object(m,'VAULT',root),patch.object(m,'SKILLS_SRC',src),patch.object(m,'HERMES_SKILLS',target),patch.object(m,'CONFIG',config):
                self.assertEqual(m.main(['--only','wiki-query','--apply']),0)
                self.assertTrue((target/'knowledge/wiki-query/SKILL.md').is_file())
                self.assertFalse((target/'knowledge/wiki-status').exists())
                self.assertEqual(m.main(['--only','wiki-query','--check']),0)
                self.assertEqual(m.main(['--only','missing-skill','--apply']),2)

if __name__=='__main__': unittest.main()
