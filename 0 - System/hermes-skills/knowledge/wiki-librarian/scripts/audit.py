"""Read-only, allowlisted librarian audit. No legacy vault module imports."""
from pathlib import Path
from contextlib import contextmanager
import os
import re
import stat
import unicodedata
import yaml

ALLOWED=('0 - System','1 - Topics','2 - Notes','7 - Wikipedia')

# Standalone copy of privacy_guard.split_header (0 - System/scripts); test_audit checks they match.
class HeaderLoader(yaml.SafeLoader):
    """SafeLoader without timestamps, so dates stay strings."""

HeaderLoader.yaml_implicit_resolvers={
    ch:[(tag,rx) for tag,rx in items if tag!='tag:yaml.org,2002:timestamp']
    for ch,items in yaml.SafeLoader.yaml_implicit_resolvers.items()}

HEADER_FENCE=re.compile(r'\A---[ \t]*\n(.*?)^---[ \t]*(?:\n|\Z)',re.S|re.M)

def split_header(text):
    """(meta, body); never a privacy signal. A malformed header reads as {} and stays in the body."""
    m=HEADER_FENCE.match(text)
    if not m: return {},text
    try:
        meta=yaml.load(m.group(1),Loader=HeaderLoader)
    except (yaml.YAMLError,RecursionError,ValueError):
        return {},text
    if meta is None: meta={}
    if not isinstance(meta,dict): return {},text
    return {unicodedata.normalize('NFC',str(k)):v for k,v in meta.items()},text[m.end():]

def permitted(root,path):
    root=Path(root); path=Path(path)
    try:
        rel=path.relative_to(root)
    except ValueError:
        return False
    if not rel.parts or rel.parts[0] not in ALLOWED or '..' in rel.parts:
        return False
    # Refuse nested vault copies and numbered policy areas before any stat/list.
    if any(re.match(r'^\d+\s*-\s*',part) for part in rel.parts[1:]):
        return False
    # Never follow symlinks, including directory symlinks.
    current=root
    for part in rel.parts:
        current=current/part
        if current.is_symlink(): return False
    return True

@contextmanager
def _stream(path):
    """Unbuffered, regular-file-only open; no parent symlinks or read-ahead."""
    path=Path(os.path.abspath(path))
    directory_fd=file_fd=None
    try:
        flags=os.O_RDONLY|os.O_NOFOLLOW
        directory_fd=os.open(path.anchor,flags|os.O_DIRECTORY)
        for component in path.parts[1:-1]:
            next_fd=os.open(component,flags|os.O_DIRECTORY,dir_fd=directory_fd)
            os.close(directory_fd); directory_fd=next_fd
        file_fd=os.open(path.name,flags|os.O_NONBLOCK,dir_fd=directory_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode): raise OSError('Unavailable input')
        stream=os.fdopen(file_fd,'rb',buffering=0); file_fd=None
        with stream: yield stream
    finally:
        if file_fd is not None: os.close(file_fd)
        if directory_fd is not None: os.close(directory_fd)

def read_public(root,path):
    """(meta, body) for a permitted path, or None. Only the path decides; see split_header."""
    path=Path(path)
    if not permitted(root,path): return None
    try:
        with _stream(path) as stream:
            text=stream.read().decode('utf-8-sig').replace('\r\n','\n')
    except (OSError,UnicodeError):
        return None
    return split_header(text)

# The audit never scans the vault root or executes legacy maintenance.
import argparse
import json
from datetime import date

META_NAMES={'index.md','log.md','validation_report.md','wiki_sources_issues.md'}
LINK=re.compile(r'(?<!!)\[\[([^\]]+)\]\]')

def paths(root):
    for folder in ('1 - Topics','2 - Notes','7 - Wikipedia'):
        base=root/folder
        if not permitted(root,base): continue
        if base.is_dir():
            for p in sorted(base.glob('*.md')):
                if not p.name.startswith('_') and permitted(root,p): yield p
    raw=root/'7 - Wikipedia'/'raw'
    if not permitted(root,raw): return
    for here,dirs,files in os.walk(raw,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not d.startswith('.') and permitted(root,Path(here)/d))
        for name in sorted(files):
            p=Path(here)/name
            if p.suffix=='.md' and permitted(root,p): yield p

def target_key(value):
    s=str(value).strip()
    if s.startswith('[[') and s.endswith(']]'): s=s[2:-2]
    return s.split('|',1)[0].split('#',1)[0].strip()

def audit(root):
    root=Path(root).absolute()
    documents={}
    for p in paths(root):
        data=read_public(root,p)
        if data is not None: documents[p.relative_to(root).as_posix()]=data
    stems={}
    for rel in documents:
        stems.setdefault(Path(rel).stem,[]).append(rel)
    def resolve(key):
        # No filesystem probes on link targets: resolve only the public catalog.
        if not key: return 'ok'
        p=Path(key)
        if p.is_absolute() or '..' in p.parts: return 'unavailable'
        if any(part not in ALLOWED for part in p.parts[:1]) and '/' in key:
            return 'unavailable'
        candidate=key if key.endswith('.md') else key+'.md'
        if '/' in key: return 'ok' if candidate in documents else 'unavailable'
        matches=stems.get(key[:-3] if key.endswith('.md') else key,[])
        return 'ok' if len(matches)==1 else 'ambiguous' if matches else 'unavailable'
    schema=read_public(root,root/'0 - System'/'SCHEMA.md')
    subjects=set()
    allowed_tags=None
    if schema:
        text=schema[1]
        def section(name):
            m=re.search(r'^##\s+'+re.escape(name)+r'[^\n]*\n(.*?)(?=^##\s|\Z)',text,re.M|re.S)
            return m.group(1) if m else ''
        subjects=set(re.findall(r'^-\s*\[\[([^\]]+)\]\]',section('subject'),re.M))
        allowed_tags=set(re.findall(r'`([^`]+)`',section('tags').split('###')[0]))
    pages={rel:data for rel,data in documents.items()
           if Path(rel).parent.as_posix()=='7 - Wikipedia'
           and Path(rel).name not in META_NAMES
           and data[0].get('type') not in ('report','index','log')}
    index=documents.get('7 - Wikipedia/index.md',({},''))[1]
    indexed={target_key(x) for x in LINK.findall(index)}
    issues=[]; warnings=[]; external=0; broken=0; ambiguous=0; source_issues=0
    for rel,(meta,body) in pages.items():
        if not meta and HEADER_FENCE.match(body): issues.append({'page':rel,'issue':'malformed_header'})
        for field in ('type','last_compiled','wiki_sources'):
            if field not in meta: issues.append({'page':rel,'issue':'missing_'+field})
        if meta.get('type')!='wiki-page': issues.append({'page':rel,'issue':'invalid_type'})
        if 'last_compiled' in meta:
            try: date.fromisoformat(str(meta['last_compiled']))
            except ValueError: issues.append({'page':rel,'issue':'invalid_last_compiled'})
        tags=meta.get('tags',[])
        if not isinstance(tags,list): issues.append({'page':rel,'issue':'tags_not_list'}); tags=[]
        if 'wiki' not in tags: warnings.append({'page':rel,'issue':'missing_wiki_tag'})
        if allowed_tags is not None:
            for tag in tags:
                if tag not in allowed_tags: warnings.append({'page':rel,'issue':'undeclared_tag','value':tag})
        sources=meta.get('wiki_sources',[])
        if not isinstance(sources,list): issues.append({'page':rel,'issue':'sources_not_list'}); sources=[]
        if not sources: warnings.append({'page':rel,'issue':'no_sources'})
        for source in sources:
            key=target_key(source)
            if key.startswith(('https://','http://')): external+=1; continue
            if resolve(key)!='ok':
                source_issues+=1
                warnings.append({'page':rel,'issue':'source_unavailable_or_ambiguous'})
        for entry in LINK.findall(body):
            key=target_key(entry)
            if key in subjects: continue
            status=resolve(key)
            if status=='unavailable': broken+=1; warnings.append({'page':rel,'issue':'body_target_unavailable'})
            elif status=='ambiguous': ambiguous+=1; warnings.append({'page':rel,'issue':'body_target_ambiguous'})
        if len(body.splitlines())>200: warnings.append({'page':rel,'issue':'long_page'})
    unindexed=sorted(rel for rel in pages if rel[:-3] not in indexed and Path(rel).stem not in indexed)
    for rel in unindexed: issues.append({'page':rel,'issue':'not_in_index'})
    return {'scope':'wiki-structural-read-only','counts':{
        'wiki_pages':len(pages),'structural_errors':len(issues),'warnings':len(warnings),
        'unindexed_pages':len(unindexed),'broken_body_links':broken,'ambiguous_body_links':ambiguous,
        'source_references_unavailable_or_ambiguous':source_issues,
        'external_source_references_unverified':external},'errors':issues,'warnings':warnings,
        'limitations':['Unavailable targets can be excluded or out-of-scope; no target names are disclosed.',
                       'External source reachability, semantic accuracy and legacy runtime jobs were not tested.',
                       'No vault files were changed.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault',required=True)
    args=parser.parse_args()
    print(json.dumps(audit(Path(args.vault)),ensure_ascii=False,indent=2))
