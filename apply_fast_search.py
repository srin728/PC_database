#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
APP = ROOT / 'site' / 'assets' / 'app.js'
INDEX = ROOT / 'site' / 'index.html'
BUILD = ROOT / 'scripts' / 'build.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'pages.yml'


def replace_text_once(text: str, old: str, new: str, label: str) -> tuple[str, str]:
    if new in text:
        return text, f'[skip] {label}: already applied'
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one match, found {count}. The repository may have changed; no files were modified.')
    return text.replace(old, new, 1), f'[ok] {label}'


# Read all target files first. All transformations happen in memory so a
# mismatch cannot leave the repository half-patched.
texts = {
    APP: APP.read_text(encoding='utf-8'),
    INDEX: INDEX.read_text(encoding='utf-8'),
    BUILD: BUILD.read_text(encoding='utf-8'),
    WORKFLOW: WORKFLOW.read_text(encoding='utf-8'),
}
messages: list[str] = []

app = texts[APP]
app, msg = replace_text_once(app, "  const state = { data: null };", "  const state = { data: null, searchIndex: null };", 'search index state')
messages.append(msg)

old_searchable = """  function searchableText(p) {
    return [p.title, p.authorText, p.conference, p.conferenceName, p.collection === 'survey' ? 'survey' : '', p.year, p.key, ...(p.tags || [])].join(' ').toLowerCase();
  }

"""
new_searchable = """  function searchableText(p) {
    const engine = globalThis.PCSearchEngine;
    if (engine) return engine.searchableText(p);
    return [p.title, p.authorText, p.conference, p.conferenceName, p.collection === 'survey' ? 'survey' : '', p.year, p.key, ...(p.tags || [])].join(' ').toLowerCase();
  }

  function ensureSearchIndex() {
    if (state.searchIndex) return state.searchIndex;
    const engine = globalThis.PCSearchEngine;
    if (!engine) throw new Error('Search engine failed to load');

    const records = allRecords();
    const core = engine.build(records);
    const recordId = new Map(records.map((record, id) => [record, id]));
    const ranks = {};
    const orders = {};
    for (const mode of ['year-desc', 'year-asc', 'conference', 'title']) {
      const sorted = sortSearchPapers(records, mode);
      const order = new Uint32Array(sorted.length);
      const rank = new Int32Array(sorted.length);
      sorted.forEach((record, position) => {
        const id = recordId.get(record);
        order[position] = id;
        rank[id] = position;
      });
      orders[mode] = order;
      ranks[mode] = rank;
    }
    state.searchIndex = { ...core, ranks, orders };
    return state.searchIndex;
  }

  function sortSearchIds(ids, mode, index) {
    const selectedMode = index.ranks[mode] ? mode : 'year-desc';
    if (ids.length === index.records.length) return Array.from(index.orders[selectedMode]);
    const rank = index.ranks[selectedMode];
    return Array.from(ids).sort((a, b) => rank[a] - rank[b]);
  }

"""
app, msg = replace_text_once(app, old_searchable, new_searchable, 'indexed search helpers')
messages.append(msg)

# Replace renderSearch as one unit. If it is already the optimized version,
# leave it untouched; otherwise require the original markers exactly once.
if 'const PAGE_SIZE = 100;' in app and 'engine.query(index' in app:
    messages.append('[skip] optimized renderSearch: already applied')
else:
    start_marker = "  function renderSearch(params) {\n"
    end_marker = "\n  function renderAbout() {\n"
    start = app.find(start_marker)
    end = app.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError('renderSearch markers were not found; no files were modified.')
    new_render_search = r'''  function renderSearch(params) {
    const { facets } = state.data;
    const initial = {
      q: params.get('q') || '',
      years: params.getAll('year'),
      conferences: params.getAll('conference'),
      tags: params.getAll('tag'),
      sort: params.get('sort') || 'year-desc'
    };

    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Search'}])}
      <section class="page-intro"><p class="eyebrow">Find papers</p><h1>Search</h1><p>Free-text and tag search include the separate survey collection. Year and conference filters apply only to conference papers. Within each checkbox group, selections are combined with OR; different groups are combined with AND.</p></section>
      <form class="search-panel" id="search-form">
        <div class="search-query-row">
          <label class="search-query-label" for="search-q">Search text</label>
          <input id="search-q" name="q" type="search" autocomplete="off" value="${esc(initial.q)}" placeholder="Title, author, tag, key…">
        </div>
        <div class="filter-grid">
          ${filterCheckboxGroup('conference', 'Conference', facets.conferences, initial.conferences)}
          ${filterCheckboxGroup('year', 'Year', facets.years, initial.years)}
          ${filterCheckboxGroup('tag', 'Tag', facets.tags, initial.tags)}
        </div>
      </form>
      <div class="results-bar"><span id="result-count"></span><div class="results-controls"><label for="search-sort">Sort</label><select id="search-sort" name="sort" form="search-form"><option value="year-desc"${initial.sort === 'year-desc' ? ' selected' : ''}>Year: newest / proceedings order</option><option value="year-asc"${initial.sort === 'year-asc' ? ' selected' : ''}>Year: oldest / proceedings order</option><option value="conference"${initial.sort === 'conference' ? ' selected' : ''}>Conference / year / page</option><option value="title"${initial.sort === 'title' ? ' selected' : ''}>Title A–Z</option></select><button class="clear-button" id="clear-search" type="button">Clear filters</button></div></div>
      <div id="search-results"></div>`;

    const form = document.getElementById('search-form');
    const searchInput = document.getElementById('search-q');
    const sortSelect = document.getElementById('search-sort');
    const resultCount = document.getElementById('result-count');
    const results = document.getElementById('search-results');
    const index = ensureSearchIndex();
    const engine = globalThis.PCSearchEngine;
    const PAGE_SIZE = 100;
    const DEBOUNCE_MS = 180;
    let currentIds = [];
    let visibleCount = 0;
    let searchTimer = 0;
    let composing = false;

    function checkedValues(name) {
      return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map(input => String(input.value));
    }

    function readControls() {
      const rawQ = searchInput.value.trim();
      return {
        rawQ,
        q: rawQ.toLowerCase(),
        years: checkedValues('year'),
        conferences: checkedValues('conference'),
        tags: checkedValues('tag'),
        sortMode: sortSelect.value || 'year-desc'
      };
    }

    function writeHash(controls) {
      const out = new URLSearchParams();
      if (controls.rawQ) out.set('q', controls.rawQ);
      controls.years.forEach(year => out.append('year', year));
      controls.conferences.forEach(conference => out.append('conference', conference));
      controls.tags.forEach(tag => out.append('tag', tag));
      if (controls.sortMode !== 'year-desc') out.set('sort', controls.sortMode);
      history.replaceState(null, '', `#search${out.toString() ? `?${out}` : ''}`);
    }

    function updateResultCount() {
      const total = currentIds.length;
      const shown = Math.min(visibleCount, total);
      resultCount.textContent = total > shown
        ? `${total} result${total === 1 ? '' : 's'} · showing ${shown}`
        : `${total} result${total === 1 ? '' : 's'}`;
    }

    function appendNextBatch() {
      if (!currentIds.length) return;
      const list = document.getElementById('search-paper-list');
      const more = document.getElementById('search-more');
      if (!list || !more) return;
      const end = Math.min(visibleCount + PAGE_SIZE, currentIds.length);
      const html = currentIds.slice(visibleCount, end).map(id => paperCard(index.records[id])).join('');
      list.insertAdjacentHTML('beforeend', html);
      visibleCount = end;
      bindCopyButtons(list);
      const remaining = currentIds.length - visibleCount;
      more.innerHTML = remaining > 0
        ? `<button type="button" class="button" id="show-more-search">Show ${Math.min(PAGE_SIZE, remaining)} more</button>`
        : '';
      updateResultCount();
    }

    function resetResults() {
      visibleCount = 0;
      if (!currentIds.length) {
        results.innerHTML = '<div class="empty-state">No papers match this view.</div>';
        updateResultCount();
        return;
      }
      results.innerHTML = '<div class="paper-list" id="search-paper-list"></div><div id="search-more" style="margin-top:16px;text-align:center"></div>';
      appendNextBatch();
    }

    function update(pushHash = true) {
      const controls = readControls();
      const ids = engine.query(index, {
        q: controls.q,
        years: controls.years,
        conferences: controls.conferences,
        tags: controls.tags
      });
      currentIds = sortSearchIds(ids, controls.sortMode, index);
      resetResults();
      if (pushHash) writeHash(controls);
    }

    function scheduleTextSearch() {
      clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => update(true), DEBOUNCE_MS);
    }

    function updateSelectedCounts() {
      ['conference', 'year', 'tag'].forEach(name => {
        const count = form.querySelectorAll(`input[name="${name}"]:checked`).length;
        const badge = form.querySelector(`[data-selected-count="${name}"]`);
        if (badge) badge.textContent = count ? `${count} selected` : 'All';
      });
    }

    function filterOptions(input) {
      const groupName = input.dataset.filterSearch;
      const group = form.querySelector(`[data-filter-group="${groupName}"]`);
      if (!group) return;
      const q = input.value.trim().toLowerCase();
      let visible = 0;
      group.querySelectorAll('.filter-option').forEach(option => {
        const show = !q || (option.dataset.filterText || '').includes(q);
        option.hidden = !show;
        if (show) visible += 1;
      });
      const empty = group.querySelector('.filter-no-match');
      if (empty) empty.hidden = visible !== 0;
    }

    sortSelect.addEventListener('change', () => update(true));

    searchInput.addEventListener('compositionstart', () => { composing = true; });
    searchInput.addEventListener('compositionend', () => {
      composing = false;
      scheduleTextSearch();
    });
    searchInput.addEventListener('input', event => {
      if (composing || event.isComposing) return;
      scheduleTextSearch();
    });

    form.querySelectorAll('.filter-search-input').forEach(input => {
      input.addEventListener('input', () => filterOptions(input));
    });

    // Checkboxes emit both input and change in browsers. Listen only to change
    // so one click triggers exactly one indexed search.
    form.addEventListener('change', event => {
      if (!event.target.matches('input[type="checkbox"]')) return;
      clearTimeout(searchTimer);
      updateSelectedCounts();
      update(true);
    });

    results.addEventListener('click', event => {
      if (event.target.closest('#show-more-search')) appendNextBatch();
    });

    document.getElementById('clear-search').addEventListener('click', () => {
      clearTimeout(searchTimer);
      form.reset();
      sortSelect.value = 'year-desc';
      form.querySelectorAll('.filter-search-input').forEach(input => filterOptions(input));
      updateSelectedCounts();
      update(true);
    });

    updateSelectedCounts();
    update(false);
  }
'''
    app = app[:start] + new_render_search + app[end:]
    messages.append('[ok] optimized renderSearch')

old_bind = """  function bindCopyButtons() {
    document.querySelectorAll('.copy-bib').forEach(btn => {
      btn.addEventListener('click', async () => {
"""
new_bind = """  function bindCopyButtons(root = document) {
    root.querySelectorAll('.copy-bib').forEach(btn => {
      if (btn.dataset.copyBound === '1') return;
      btn.dataset.copyBound = '1';
      btn.addEventListener('click', async () => {
"""
app, msg = replace_text_once(app, old_bind, new_bind, 'idempotent copy-button binding')
messages.append(msg)

old_load = """      state.data = data;
      document.title = data.site.siteTitle;
"""
new_load = """      state.data = data;
      // Build the search index while the browser is idle so opening Search is
      // usually instant. Direct #search navigation still builds it on demand.
      const warmSearchIndex = () => {
        try { ensureSearchIndex(); } catch (_) { /* Search will report load errors on demand. */ }
      };
      if ('requestIdleCallback' in window) {
        window.requestIdleCallback(warmSearchIndex, { timeout: 2000 });
      } else {
        window.setTimeout(warmSearchIndex, 250);
      }
      document.title = data.site.siteTitle;
"""
app, msg = replace_text_once(app, old_load, new_load, 'idle search-index warmup')
messages.append(msg)
texts[APP] = app

index = texts[INDEX]
index, msg = replace_text_once(index, '  <script src="assets/app.js" defer></script>', '  <script src="assets/search-engine.js" defer></script>\n  <script src="assets/app.js" defer></script>', 'load search engine before app')
messages.append(msg)
texts[INDEX] = index

build = texts[BUILD]
build, msg = replace_text_once(build, "    for relative in ('assets/styles.css', 'assets/app.js'):", "    for relative in ('assets/styles.css', 'assets/search-engine.js', 'assets/app.js'):", 'cache-bust search engine')
messages.append(msg)
texts[BUILD] = build

workflow = texts[WORKFLOW]
old_workflow = """      - name: Build static site
        run: python3 scripts/build.py
"""
new_workflow = """      - name: Check Python syntax
        run: python3 -m py_compile scripts/build.py scripts/validate.py

      - name: Run Python unit tests
        run: python3 -m unittest discover -s tests -p 'test_*.py'

      - name: Validate BibTeX data
        run: python3 scripts/validate.py

      - name: Check JavaScript syntax
        run: |
          node --check site/assets/search-engine.js
          node --check site/assets/app.js

      - name: Test optimized search engine
        run: node tests/search_engine_test.js

      - name: Build static site
        run: python3 scripts/build.py
"""
workflow, msg = replace_text_once(workflow, old_workflow, new_workflow, 'CI search/regression checks')
messages.append(msg)
texts[WORKFLOW] = workflow

# Commit all transformed text only after every check succeeded.
for path, text in texts.items():
    path.write_text(text, encoding='utf-8')
for message in messages:
    print(message)
print('\nFast-search patch applied successfully.')
