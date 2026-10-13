"""Structural checks on the librarian skill layout; not a test of LLM summary quality."""
from pathlib import Path
import re
import unittest

SKILL=Path(__file__).absolute().parents[1]
SYS=Path(__file__).absolute().parents[4]
REFERENCES=('ingest','resolve','crosslink','query','audit','files','source-summaries')
HEBREW=re.compile('[\u0590-\u05FF]')

class SkillLayout(unittest.TestCase):
    def test_every_routed_reference_exists(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
        routed=set(re.findall(r'`references/([\w-]+)\.md`',text))
        self.assertEqual(routed,set(REFERENCES))
        for name in REFERENCES:
            with self.subTest(reference=name):
                self.assertTrue((SKILL/'references'/f'{name}.md').is_file())

    def test_references_link_only_to_existing_siblings(self):
        for path in (SKILL/'references').glob('*.md'):
            text=path.read_text(encoding='utf-8')
            for name in re.findall(r'`([\w-]+)\.md`',text):
                if name in ('index','log','SKILL','AGENTS','CLAUDE'): continue
                with self.subTest(file=path.name,target=name):
                    self.assertIn(name,REFERENCES)

    def test_instructions_are_english(self):
        for path in [SKILL/'SKILL.md',*(SKILL/'references').glob('*.md')]:
            with self.subTest(file=path.name):
                self.assertIsNone(HEBREW.search(path.read_text(encoding='utf-8')))

    def test_legacy_subskills_are_gone(self):
        for name in ('ingest','resolve','crosslink','query','lint','status'):
            with self.subTest(skill=name):
                self.assertFalse((SYS/f'SKILL-{name}.md').exists())
                self.assertFalse((SYS/'hermes-skills'/'knowledge'/f'wiki-{name}').exists())

    def test_core_policy_markers(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
        for marker in ('One main summary per source','does not exist for this skill',
                       'review, status and query make no writes','vault-python.sh'):
            with self.subTest(marker=marker): self.assertIn(marker,text)

if __name__=='__main__': unittest.main()
