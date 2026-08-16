#!/usr/bin/env python3
"""Apply the paper-link reliability patch to PC_database."""
from __future__ import annotations
import ast
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD_BUILD_POLICY = 'NON_RESOLVING_DOI_PREFIXES = (\n    # Crossref documents 10.5555 as a test prefix.  Values under this prefix\n    # are sometimes used as publisher/database identifiers (notably by ACM\n    # DL), but doi.org resolution is not reliable enough to use as the site\'s\n    # primary link.  Prefer the BibTeX url field when it is available.\n    "10.5555/",\n)\n\n\ndef doi_resolver_url(doi: str) -> str:\n    """Return a doi.org URL only for DOI prefixes we treat as resolvable."""\n    normalized = (doi or \'\').strip()\n    if not normalized:\n        return \'\'\n    lowered = normalized.casefold()\n    if any(lowered.startswith(prefix) for prefix in NON_RESOLVING_DOI_PREFIXES):\n        return \'\'\n    return f"https://doi.org/{normalized}"\n\n\ndef preferred_paper_url(doi: str, url: str) -> str:\n    """Return the best external paper URL.\n\n    A normal DOI is preferred over ``url``.  For known non-resolving/test DOI\n    prefixes such as 10.5555, the BibTeX ``url`` is preferred instead so that\n    title clicks do not lead to a broken doi.org resolution.\n    """\n    return doi_resolver_url(doi) or url\n'
NEW_BUILD_POLICY = 'NON_RESOLVING_DOI_PREFIXES = (\n    # Crossref identifies these prefixes as test/unmaintained records rather\n    # than dependable publication identifiers. Never make doi.org the\n    # primary paper link for them; prefer a real URL or a DBLP record.\n    "10.5555/",\n    "10.88888/",\n    "10.50505/",\n)\n\n\ndef doi_resolver_url(doi: str) -> str:\n    """Return a doi.org URL only for DOI prefixes we treat as resolvable."""\n    normalized = (doi or \'\').strip()\n    if not normalized:\n        return \'\'\n    lowered = normalized.casefold()\n    if any(lowered.startswith(prefix) for prefix in NON_RESOLVING_DOI_PREFIXES):\n        return \'\'\n    return f"https://doi.org/{normalized}"\n\n\ndef dblp_record_url(key: str) -> str:\n    """Derive DBLP\'s persistent record URL from a DBLP-prefixed BibTeX key."""\n    normalized = (key or \'\').strip()\n    if not normalized.startswith(\'DBLP:\'):\n        return \'\'\n    path = normalized[len(\'DBLP:\'):].lstrip(\'/\')\n    if not path or any(ch.isspace() for ch in path):\n        return \'\'\n    return f"https://dblp.org/rec/{path}"\n\n\ndef is_non_resolving_doi_url(url: str) -> bool:\n    """Return whether URL is a doi.org link for a blocked DOI prefix."""\n    normalized = (url or \'\').strip()\n    match = re.match(r\'^https?://(?:dx\\.)?doi\\.org/(.+)$\', normalized, flags=re.IGNORECASE)\n    if not match:\n        return False\n    doi = normalize_doi(match.group(1))\n    return bool(doi) and not doi_resolver_url(doi)\n\n\ndef preferred_paper_url(doi: str, url: str, key: str = \'\') -> str:\n    """Return the safest available external paper URL.\n\n    Normal publication DOIs remain the first choice. For known\n    test/unmaintained DOI prefixes, use a non-DOI ``url`` when available.\n    A ``url`` that merely points back to the same non-resolving doi.org record\n    is rejected. Finally, DBLP-prefixed keys provide a stable metadata-page\n    fallback for legacy entries without usable DOI/URL metadata.\n    """\n    resolver = doi_resolver_url(doi)\n    if resolver:\n        return resolver\n    normalized_url = (url or \'\').strip()\n    if normalized_url and not is_non_resolving_doi_url(normalized_url):\n        return normalized_url\n    return dblp_record_url(key)\n'
OLD_APP = "  function paperPrimaryUrl(p) {\n    // DOI is the canonical title link whenever it is available.  Do not let a\n    // stale generated primaryUrl (for example a DBLP URL) override it.\n    if (p.doi) return `https://doi.org/${p.doi}`;\n    if (p.url) return p.url;\n    return '';\n  }\n"
NEW_APP = "  const NON_RESOLVING_DOI_PREFIXES = ['10.5555/', '10.88888/', '10.50505/'];\n\n  function paperDoiUrl(p) {\n    const doi = String(p?.doi || '').trim();\n    if (!doi) return '';\n    const lowered = doi.toLowerCase();\n    if (NON_RESOLVING_DOI_PREFIXES.some(prefix => lowered.startsWith(prefix))) return '';\n    return `https://doi.org/${doi}`;\n  }\n\n  function isNonResolvingDoiUrl(url) {\n    const value = String(url || '').trim();\n    const match = value.match(/^https?:\\/\\/(?:dx\\.)?doi\\.org\\/(.+)$/i);\n    if (!match) return false;\n    const doi = match[1].toLowerCase();\n    return NON_RESOLVING_DOI_PREFIXES.some(prefix => doi.startsWith(prefix));\n  }\n\n  function paperPrimaryUrl(p) {\n    // build.py computes primaryUrl using the same policy. Prefer it, but keep\n    // defensive fallbacks so cached/older JSON cannot reintroduce a broken\n    // test-prefix DOI link.\n    const generated = String(p?.primaryUrl || '').trim();\n    if (generated && !isNonResolvingDoiUrl(generated)) return generated;\n    const doiUrl = paperDoiUrl(p);\n    if (doiUrl) return doiUrl;\n    const url = String(p?.url || '').trim();\n    if (url && !isNonResolvingDoiUrl(url)) return url;\n    const key = String(p?.key || '').trim();\n    if (key.startsWith('DBLP:')) return `https://dblp.org/rec/${key.slice(5).replace(/^\\/+/, '')}`;\n    return '';\n  }\n"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one matching block, found {count}")
    return text.replace(old, new, 1)


def main():
    build_path = ROOT / 'scripts' / 'build.py'
    app_path = ROOT / 'site' / 'assets' / 'app.js'
    workflow_path = ROOT / '.github' / 'workflows' / 'pages.yml'
    audit_source = ROOT / '_link_patch_files' / 'scripts' / 'audit_links.py'
    test_source = ROOT / '_link_patch_files' / 'tests' / 'test_link_policy.py'
    audit_target = ROOT / 'scripts' / 'audit_links.py'
    test_target = ROOT / 'tests' / 'test_link_policy.py'
    required = [build_path, app_path, workflow_path, audit_source, test_source]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError('Missing required files: ' + ', '.join(missing))

    build = build_path.read_text(encoding='utf-8')
    app = app_path.read_text(encoding='utf-8')
    workflow = workflow_path.read_text(encoding='utf-8')
    build = replace_once(build, OLD_BUILD_POLICY, NEW_BUILD_POLICY, 'scripts/build.py URL policy')
    build = replace_once(build, "            primary_url = preferred_paper_url(doi, url)\n", "            primary_url = preferred_paper_url(doi, url, entry['key'])\n", 'scripts/build.py primary URL call')
    app = replace_once(app, OLD_APP, NEW_APP, 'site/assets/app.js primary-link policy')
    app = replace_once(app, "    const doi = p.doi ? externalLink(`https://doi.org/${p.doi}`, 'DOI') : '';\n", "    const doiUrl = paperDoiUrl(p);\n    const doi = doiUrl ? externalLink(doiUrl, 'DOI') : '';\n", 'site/assets/app.js DOI action')
    workflow = replace_once(workflow, "        run: python3 -m py_compile scripts/build.py scripts/validate.py\n", "        run: python3 -m py_compile scripts/build.py scripts/validate.py scripts/audit_links.py\n", 'workflow syntax check')
    workflow = replace_once(workflow, "      - name: Validate BibTeX data\n        run: python3 scripts/validate.py\n\n", "      - name: Validate BibTeX data\n        run: python3 scripts/validate.py\n\n      - name: Audit paper links\n        run: python3 scripts/audit_links.py\n\n", 'workflow link audit')

    ast.parse(build, filename='scripts/build.py')
    ast.parse(audit_source.read_text(encoding='utf-8'), filename='scripts/audit_links.py')
    ast.parse(test_source.read_text(encoding='utf-8'), filename='tests/test_link_policy.py')
    for source, target in ((audit_source, audit_target), (test_source, test_target)):
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise RuntimeError(f"Refusing to overwrite existing {target.relative_to(ROOT)}")

    node = shutil.which('node')
    temp = ROOT / '.link-policy-check.tmp.js'
    if node:
        try:
            temp.write_text(app, encoding='utf-8')
            subprocess.run([node, '--check', str(temp)], check=True)
        finally:
            temp.unlink(missing_ok=True)

    build_path.write_text(build, encoding='utf-8')
    app_path.write_text(app, encoding='utf-8')
    workflow_path.write_text(workflow, encoding='utf-8')
    audit_target.write_bytes(audit_source.read_bytes())
    test_target.parent.mkdir(parents=True, exist_ok=True)
    test_target.write_bytes(test_source.read_bytes())
    print('Paper-link reliability patch applied successfully.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
