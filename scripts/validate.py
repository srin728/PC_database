#!/usr/bin/env python3
"""Repository-level validation for BibTeX data used by the GitHub Pages build."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = ROOT / 'scripts' / 'build.py'
spec = importlib.util.spec_from_file_location('pcdb_build', BUILD_PATH)
build = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(build)


def main() -> int:
    conference_names = build.load_json(build.DATA_DIR / 'conferences.json', {})
    files = build.all_bib_files()
    errors: list[str] = []
    entry_count = 0
    conference_folders = set()

    for path in files:
        if not build.is_survey_bib(path):
            conference_folders.add(path.parent.name)
        try:
            entries = build.parse_bib_file(path)
            entry_count += len(entries)
        except Exception as exc:
            errors.append(str(exc))

    coverage_overrides = build.load_json(build.DATA_DIR / 'coverage.json', {})
    defined_sources = set(conference_folders) | (set(coverage_overrides) if isinstance(coverage_overrides, dict) else set())
    missing = build.missing_conference_definitions(defined_sources, conference_names)
    if missing:
        print(
            'WARNING: conference folders missing from data/conferences.json: ' + ', '.join(missing),
            file=sys.stderr,
        )

    if errors:
        print('BibTeX validation failed:', file=sys.stderr)
        for error in errors:
            print(f'  - {error}', file=sys.stderr)
        return 1

    print(f'Validated {entry_count} BibTeX entries across {len(files)} files.')
    if missing:
        print('Validation succeeded with conference-name warnings.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
