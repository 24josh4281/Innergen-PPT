#!/usr/bin/env python3
"""
PPT Master - Report Reference Learning Records

Index local PPTX structural candidates by content hash without copying client
text. Preserve actual review/correction evidence for reuse in later projects.
See docs/styles/innergen/report-diagrams-v30.md for the review contract.

Usage:
    python scripts/report_reference_learning.py scan --root INPUTS --output index.json
    python scripts/report_reference_learning.py record review.json --ledger reviews.jsonl
    python scripts/report_reference_learning.py recall --ledger reviews.jsonl --subject schedule

Examples:
    python scripts/report_reference_learning.py scan --root INPUTS --output OUTPUTS/reference-index.json

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parents[3]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from console_encoding import configure_utf8_stdio  # noqa: E402

VERSION = '30'
KEYWORDS = {
    'schedule': r'일\s*정|schedule|gantt',
    'procedure': r'추진\s*절차|프로세스|추진\s*방안|수행\s*절차|process',
    'detail': r'세부\s*현황|진행\s*현황|추진\s*현황|진척|이슈|status',
    'scope': r'수행\s*범위|과업\s*범위|컨설팅\s*범위|업무\s*범위|scope',
    'monitoring': r'모니터링|시나리오|산정식|감축량|monitoring',
}
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def digest(path: Path) -> str:
    """Hash content, not modification time."""
    with path.open('rb') as handle:
        result = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def repo_path(path: Path) -> str:
    """Store portable repository-relative paths where possible."""
    resolved = path.resolve()
    return resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else str(resolved)


def scan_deck(path: Path, sha: str) -> dict:
    """Read real slide order and structural counts; never persist source wording."""
    import posixpath

    candidates = []
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels}
        slides = presentation.findall(f'{P}sldIdLst/{P}sldId')
        for number, slide in enumerate(slides, 1):
            target = targets[slide.get(R + 'id')]
            part = target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/' + target)
            root = ET.fromstring(archive.read(part))
            # Source text is only an in-memory retrieval signal, not reusable facts.
            text = ' '.join(t.text or '' for t in root.iter(A + 't'))
            subjects = [key for key, pattern in KEYWORDS.items() if re.search(pattern, text, re.I)]
            if not subjects:
                continue
            counts = {kind: sum(1 for _ in root.iter(P + kind))
                      for kind in ('sp', 'pic', 'cxnSp', 'grpSp')}
            counts['tables'] = sum(1 for _ in root.iter(A + 'tbl'))
            candidates.append({'slide': number, 'part': part, 'subjects': subjects,
                               'counts': counts, 'status': 'xml_candidate_not_visually_reviewed'})
    return {'source': repo_path(path), 'sha256': sha, 'slide_count': len(slides), 'candidates': candidates}


def scan(source: Path, output: Path) -> dict:
    """Incrementally index changed sources and preserve old output on a read failure."""
    files = sorted(p for p in source.rglob('*.pptx') if not p.name.startswith('~$'))
    if not files:
        raise ValueError('No readable PPTX candidates in the requested root.')
    previous = json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
    old = {d['source']: d for d in previous.get('decks', [])} if previous.get('version') == VERSION else {}
    rows, changed = [], 0
    for path in files:
        sha = digest(path)
        cached = old.get(repo_path(path))
        if cached and cached['sha256'] == sha:
            rows.append(cached)
        else:
            rows.append(scan_deck(path, sha))
            changed += 1
    data = {'version': VERSION, 'root': repo_path(source),
            'status': 'structural_retrieval_index_not_design_or_content_validation', 'decks': rows}
    updated = data != previous
    if updated:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'files': len(rows), 'analyzed': changed, 'reused': len(rows) - changed, 'index_updated': updated}


def record(review_path: Path, ledger: Path) -> str:
    """Append a deduplicated evidence record, without asserting automated review."""
    row = json.loads(review_path.read_text(encoding='utf-8'))
    for name in ('source', 'source_sha256', 'subject', 'observation', 'adaptation',
                 'before', 'after', 'result', 'feedback'):
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise ValueError(f'Review requires nonempty {name}.')
    if row['subject'] not in KEYWORDS or row['result'] not in {'improved', 'unchanged', 'unresolved'}:
        raise ValueError('Unknown subject or result.')
    if type(row.get('slide')) is not int or row['slide'] < 1:
        raise ValueError('Review requires a positive slide number.')
    source = ROOT / row['source']
    if digest(source) != row['source_sha256']:
        raise ValueError('Reference source changed; reread the actual page before recording.')
    with zipfile.ZipFile(source) as archive:
        root = ET.fromstring(archive.read('ppt/presentation.xml'))
        if row['slide'] > len(root.findall(f'{P}sldIdLst/{P}sldId')):
            raise ValueError('Reference slide does not exist.')
    # Track concrete revisions independently of the declared human/agent review.
    for name in ('before', 'after'):
        artifact = ROOT / row[name]
        if not artifact.is_file():
            raise ValueError(f'{name} must identify an existing reviewed file.')
        row[name + '_sha256'] = digest(artifact)
    canonical = json.dumps(row, ensure_ascii=False, sort_keys=True)
    key = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    existing = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()
                if line.strip()] if ledger.exists() else []
    if any(v.get('record_sha256') == key for v in existing):
        return 'unchanged: review already recorded'
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps({'record_sha256': key, **row}, ensure_ascii=False) + '\n')
    return 'recorded: declared review with source and before/after hashes'


def recall(ledger: Path, subject: str, limit: int) -> dict:
    """Retrieve relevant prior reviews only while their source/output evidence is current."""
    if not ledger.exists():
        return {'reviews': [], 'stale': 0, 'status': 'no_previous_reviews_start_with_reference_reading'}
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()]
    selected, stale, hashes = [], 0, {}
    for row in reversed(rows):
        if row['subject'] != subject:
            continue
        valid = True
        for name, expected in [('source', 'source_sha256'), ('after', 'after_sha256')]:
            path = ROOT / row[name]
            if str(path) not in hashes:
                try:
                    hashes[str(path)] = digest(path)
                except OSError:
                    hashes[str(path)] = None
            if hashes[str(path)] != row[expected]:
                valid = False
        if not valid:
            stale += 1
            continue
        selected.append(row)
        if len(selected) == limit:
            break
    return {'reviews': selected, 'stale': stale,
            'status': 'declared_reviews_reassess_fit_for_current_project_not_automatic_rules'}


def main(argv: list[str] | None = None) -> int:
    """Run explicit local indexing or evidence recording."""
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    indexing = commands.add_parser('scan')
    indexing.add_argument('--root', type=Path, required=True)
    indexing.add_argument('--output', type=Path, required=True)
    review = commands.add_parser('record')
    review.add_argument('review', type=Path)
    review.add_argument('--ledger', type=Path, required=True)
    retrieve = commands.add_parser('recall')
    retrieve.add_argument('--ledger', type=Path, required=True)
    retrieve.add_argument('--subject', choices=sorted(KEYWORDS), required=True)
    retrieve.add_argument('--limit', type=int, default=3)
    args = parser.parse_args(argv)
    try:
        if args.command == 'scan':
            result = scan(args.root, args.output)
        elif args.command == 'record':
            result = record(args.review, args.ledger)
        else:
            if not 1 <= args.limit <= 20:
                raise ValueError('Recall limit must be between 1 and 20.')
            result = recall(args.ledger, args.subject, args.limit)
        print(json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else result)
        return 0
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f'Reference record error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
