#!/usr/bin/env python3
"""Audit paper-link policy against all current BibTeX entries."""
from __future__ import annotations
import importlib.util
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = ROOT / 'scripts' / 'build.py'
spec = importlib.util.spec_from_file_location('pcdb_build', BUILD_PATH)
build = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(build)


def main() -> int:
    total = blocked_dois = safe_fallbacks = 0
    missing_links = []
    errors = []
    blocked_by_conference = Counter()
    for path in build.all_bib_files():
        conference = '' if build.is_survey_bib(path) else path.parent.name
        for entry in build.parse_bib_file(path):
            total += 1
            fields = entry['fields']
            doi = build.normalize_doi(fields.get('doi', ''))
            url = build.normalize_url(fields.get('url', ''))
            key = entry['key']
            primary = build.preferred_paper_url(doi, url, key)
            if doi and not build.doi_resolver_url(doi):
                blocked_dois += 1
                blocked_by_conference[conference or 'SURVEY'] += 1
                if primary:
                    safe_fallbacks += 1
            if primary and build.is_non_resolving_doi_url(primary):
                errors.append(f'{path.relative_to(ROOT)} :: {key}: unsafe non-resolving DOI URL: {primary}')
            if primary and not primary.lower().startswith(('http://', 'https://')):
                errors.append(f'{path.relative_to(ROOT)} :: {key}: unsupported URL scheme: {primary}')
            if not primary:
                missing_links.append(f'{path.relative_to(ROOT)} :: {key}')
    if errors:
        for error in errors:
            print('ERROR:', error, file=sys.stderr)
        print(f'Link audit failed with {len(errors)} unsafe link(s).', file=sys.stderr)
        return 1
    print(f'Link audit passed for {total} bibliography entries.')
    if blocked_dois:
        groups = ', '.join(f'{name}={count}' for name, count in sorted(blocked_by_conference.items()))
        print(f'Protected {blocked_dois} non-resolving/test-prefix DOI record(s); {safe_fallbacks} have safe fallback links. ({groups})')
    if missing_links:
        noun = 'entry' if len(missing_links) == 1 else 'entries'
        print(f'WARNING: {len(missing_links)} {noun} have no verified external link; titles remain intentionally unlinked:', file=sys.stderr)
        for item in missing_links:
            print('  ' + item, file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
