# PC_database fast-search patch

This patch is designed for the current `srin728/PC_database` layout.

## What changes

- Builds an in-memory search index once (lazily / during browser idle time).
- Uses inverted indexes for Year / Conference / Tag filters.
- Uses a trigram posting-list index for free-text substring search.
- Intersects the shortest posting lists first, then verifies exact substring matches.
- Preserves the old search semantics: the optimized result set is checked against the exact `includes()` condition.
- Precomputes sort ranks for all four search sort modes.
- Debounces free-text input by 180 ms.
- Handles IME composition correctly (no search while text is being composed).
- Removes the old checkbox double-search caused by both `input` and `change` events.
- Renders only the first 100 search results, with a `Show 100 more` button.
- Makes Copy BibTeX binding idempotent when more results are appended.
- Warms the search index via `requestIdleCallback` when available.
- Adds cache busting for the new search engine script.
- Adds a randomized equivalence/performance test and runs it in GitHub Actions.

## Apply

Extract this ZIP at the repository root, so these files exist:

- `apply_fast_search.py`
- `site/assets/search-engine.js`
- `tests/search_engine_test.js`

Then run:

```bash
python3 apply_fast_search.py
```

The patcher is transactional for the existing text files: it validates every expected edit in memory before writing any of them. It is also idempotent, so running it twice is safe.

## Verify locally

```bash
node --check site/assets/search-engine.js
node --check site/assets/app.js
node tests/search_engine_test.js
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate.py
python3 scripts/build.py
```

The GitHub Actions workflow is also patched to run these checks before deployment.

## Test coverage included

`tests/search_engine_test.js` generates 2,500 synthetic bibliography records and compares the optimized search with the previous linear-scan semantics across 1,200 randomized combinations of:

- free-text query,
- multiple years,
- multiple conferences,
- multiple tags,
- surveys vs conference papers.

It also includes a generous performance regression guard.

`tests/search_engine_benchmark.js` is optional and prints an indicative local comparison. On the creation environment, 300 representative searches over 10,000 synthetic records took about 1,039 ms with repeated linear scans versus about 122 ms with the indexed engine (roughly 8.5x for the search-computation portion). Actual browser speedups vary by device and query selectivity; DOM pagination typically improves perceived responsiveness further.
