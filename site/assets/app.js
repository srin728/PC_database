(() => {
  'use strict';

  const app = document.getElementById('app');
  const loading = document.getElementById('loading');
  const nav = document.getElementById('site-nav');
  const navToggle = document.getElementById('nav-toggle');
  const brandTitle = document.getElementById('brand-title');

  const state = { data: null };

  const esc = (value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const enc = (value = '') => encodeURIComponent(String(value));

  function externalLink(url, label) {
    if (!url) return '';
    return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
  }

  function route() {
    const raw = location.hash.replace(/^#/, '') || 'home';
    const [path, queryString = ''] = raw.split('?');
    const parts = path.split('/').filter(Boolean).map(decodeURIComponent);
    return { page: parts[0] || 'home', arg: parts[1] || '', params: new URLSearchParams(queryString) };
  }

  function setCurrentNav(page) {
    [...nav.querySelectorAll('a')].forEach(a => {
      const target = a.getAttribute('href').replace('#', '');
      if (target === page || (page === 'year' && target === 'years') || (page === 'conference' && target === 'conferences') || (page === 'tag' && target === 'tags')) {
        a.setAttribute('aria-current', 'page');
      } else {
        a.removeAttribute('aria-current');
      }
    });
  }

  function sortPapers(papers) {
    return [...papers].sort((a, b) =>
      Number(b.year) - Number(a.year) ||
      a.conference.localeCompare(b.conference) ||
      a.title.localeCompare(b.title)
    );
  }

  function allRecords() {
    return [...(state.data.papers || []), ...(state.data.surveys || [])];
  }

  function paperPrimaryUrl(p) {
    if (p.url) return p.url;
    if (p.doi) return `https://doi.org/${p.doi}`;
    return '';
  }

  function paperCard(p) {
    const primary = paperPrimaryUrl(p);
    const title = primary ? `<a href="${esc(primary)}" target="_blank" rel="noopener noreferrer">${esc(p.title)}</a>` : esc(p.title);
    const tags = (p.tags || []).map(t => `<a class="tag" href="#tag/${enc(t)}">${esc(t)}</a>`).join('');
    const doi = p.doi ? externalLink(`https://doi.org/${p.doi}`, 'DOI') : '';
    const source = p.sourcePath ? `<a href="${esc(p.sourcePath)}" target="_blank" rel="noopener noreferrer">Source .bib</a>` : '';
    const raw = p.bibtex ? `<button type="button" class="copy-bib" data-bib-id="${esc(p.id)}">Copy BibTeX</button>` : '';
    const actions = [doi, source, raw].filter(Boolean).join('');
    const bibliographicMeta = p.collection === 'survey'
      ? `<span>Survey</span><span>${esc(p.year)}</span>`
      : `<span><a href="#conference/${enc(p.conference)}">${esc(p.conference)}</a></span><span><a href="#year/${enc(p.year)}">${esc(p.year)}</a></span>`;

    return `<article class="paper-card">
      <h3 class="paper-title">${title}</h3>
      <p class="paper-authors">${esc(p.authorText || 'Unknown author')}</p>
      <div class="paper-meta">
        ${bibliographicMeta}
        ${p.pages ? `<span>pp. ${esc(p.pages)}</span>` : ''}
        <span>${esc(p.key)}</span>
      </div>
      ${tags ? `<div class="tag-list" aria-label="Tags">${tags}</div>` : ''}
      ${actions ? `<div class="paper-actions">${actions}</div>` : ''}
    </article>`;
  }

  function paperList(papers) {
    if (!papers.length) return '<div class="empty-state">No papers match this view.</div>';
    return `<div class="paper-list">${papers.map(paperCard).join('')}</div>`;
  }

  function breadcrumbs(items) {
    return `<nav class="breadcrumbs" aria-label="Breadcrumb">${items.map((item, i) =>
      i === items.length - 1 ? esc(item.label) : `<a href="${esc(item.href)}">${esc(item.label)}</a> / `
    ).join('')}</nav>`;
  }

  function stats() {
    const f = state.data.facets;
    return `<div class="stats-grid">
      <div class="stat-card"><span class="stat-value">${f.paperCount}</span><span class="stat-label">conference papers</span></div>
      <div class="stat-card"><span class="stat-value">${f.yearCount}</span><span class="stat-label">years</span></div>
      <div class="stat-card"><span class="stat-value">${f.conferenceCount}</span><span class="stat-label">conferences</span></div>
      <div class="stat-card"><span class="stat-value">${f.tagCount}</span><span class="stat-label">tags</span></div>
    </div>`;
  }

  function renderHome() {
    const { site, papers, surveys = [], news, sourceUpdates, facets } = state.data;
    const latestPapers = sortPapers(papers).slice(0, site.homeRecentPapers || 12);
    const updates = [
      ...(news || []).map(n => ({...n, kind: 'news'})),
      ...(sourceUpdates || []).map(u => ({
        date: u.date,
        title: u.collection === 'survey'
          ? `Survey bibliography update${u.year ? `: ${u.year}` : ''}`
          : `Bibliography update: ${u.conference} ${u.year || ''}`.trim(),
        text: `${u.paperCount} entr${u.paperCount === 1 ? 'y' : 'ies'} currently in ${u.file}.`,
        kind: 'source'
      }))
    ].sort((a,b) => String(b.date).localeCompare(String(a.date))).slice(0, site.homeRecentUpdates || 8);

    const years = facets.years.slice(0, 6).map(y => `<a class="nav-card" href="#year/${enc(y.value)}"><strong>${esc(y.value)}</strong><span>${y.count} papers</span></a>`).join('');
    const conferences = facets.conferences.slice(0, 8).map(c => `<a class="nav-card" href="#conference/${enc(c.value)}"><strong>${esc(c.value)}</strong><span>${esc(c.label || c.value)} · ${c.count} papers</span></a>`).join('');

    app.innerHTML = `
      <section class="hero">
        <p class="eyebrow">Conference-paper bibliography</p>
        <h1>${esc(site.siteTitle)}</h1>
        <p class="hero-subtitle">${esc(site.siteSubtitle)}</p>
        <div class="notice" aria-label="Scope notice">
          <ul>
            <li><strong>The main database contains conference papers only.</strong> Survey papers are maintained separately and are excluded from the year and conference counts.</li>
            <li>The database is intended primarily for <strong>tracking research trends</strong> in parameterized complexity.</li>
            <li>If you notice a missing paper or incorrect metadata, <strong>please contact the maintainers.</strong></li>
          </ul>
        </div>
        <form class="search-hero" id="home-search">
          <input name="q" type="search" autocomplete="off" placeholder="Search titles, authors, tags, conferences…" aria-label="Search bibliography">
          <button class="button" type="submit">Search</button>
        </form>
        ${stats()}
      </section>

      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">Browse</p><h2>Recent years</h2></div><a href="#years">All years</a></div>
        <div class="card-grid">${years || '<div class="empty-state">Add BibTeX files to begin.</div>'}</div>
      </section>

      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">Browse</p><h2>Conferences</h2></div><a href="#conferences">All conferences</a></div>
        <div class="card-grid">${conferences || '<div class="empty-state">No conferences yet.</div>'}</div>
      </section>

      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">Separate collection</p><h2>Surveys</h2></div><a href="#surveys">Browse surveys</a></div>
        <a class="nav-card survey-card" href="#surveys"><strong>${surveys.length} survey paper${surveys.length === 1 ? '' : 's'}</strong><span>Kept separate from the conference and year views.</span></a>
      </section>

      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">News</p><h2>Latest updates</h2></div></div>
        <div class="news-list">${updates.length ? updates.map(u => `<article class="news-item"><time>${esc(u.date)}</time><h3>${esc(u.title)}</h3><p>${esc(u.text || '')}</p></article>`).join('') : '<div class="empty-state">No updates yet.</div>'}</div>
      </section>

      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">Newest bibliography entries</p><h2>Recent papers</h2></div><a href="#search">Open search</a></div>
        ${paperList(latestPapers)}
      </section>`;

    document.getElementById('home-search')?.addEventListener('submit', e => {
      e.preventDefault();
      const q = new FormData(e.currentTarget).get('q')?.toString().trim() || '';
      location.hash = `#search?q=${enc(q)}`;
    });
  }

  function renderYears() {
    const { facets } = state.data;
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Years'}])}
      <section class="page-intro"><p class="eyebrow">Browse</p><h1>By year</h1><p>Select a year to see papers grouped by conference.</p></section>
      <div class="card-grid">${facets.years.map(y => `<a class="nav-card" href="#year/${enc(y.value)}"><strong>${esc(y.value)}</strong><span>${y.count} papers · ${y.conferences} conferences</span></a>`).join('') || '<div class="empty-state">No years yet.</div>'}</div>`;
  }

  function renderYear(year) {
    const papers = state.data.papers.filter(p => String(p.year) === String(year));
    const groups = new Map();
    papers.forEach(p => { if (!groups.has(p.conference)) groups.set(p.conference, []); groups.get(p.conference).push(p); });
    const body = [...groups.entries()].sort(([a],[b]) => a.localeCompare(b)).map(([conf, list]) => `
      <section class="subgroup">
        <div class="subgroup-heading"><h3><a href="#conference/${enc(conf)}">${esc(conf)}</a></h3><span class="group-count">${list.length} papers</span></div>
        ${paperList(sortPapers(list))}
      </section>`).join('');
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Years',href:'#years'},{label:year}])}
      <section class="page-intro"><p class="eyebrow">Year</p><h1>${esc(year)}</h1><p>${papers.length} conference papers in the database.</p></section>
      ${body || '<div class="empty-state">No papers for this year.</div>'}`;
  }

  function renderConferences() {
    const { facets } = state.data;
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Conferences'}])}
      <section class="page-intro"><p class="eyebrow">Browse</p><h1>By conference</h1><p>Select a conference to see its papers grouped by year.</p></section>
      <div class="card-grid">${facets.conferences.map(c => `<a class="nav-card" href="#conference/${enc(c.value)}"><strong>${esc(c.value)}</strong><span>${esc(c.label || c.value)} · ${c.count} papers</span></a>`).join('') || '<div class="empty-state">No conferences yet.</div>'}</div>`;
  }

  function renderSurveys() {
    const surveys = sortPapers(state.data.surveys || []);
    const groups = new Map();
    surveys.forEach(p => { if (!groups.has(p.year)) groups.set(p.year, []); groups.get(p.year).push(p); });
    const body = [...groups.entries()].sort(([a], [b]) => Number(b) - Number(a)).map(([year, list]) => `
      <section class="subgroup">
        <div class="subgroup-heading"><h3>${esc(year)}</h3><span class="group-count">${list.length} paper${list.length === 1 ? '' : 's'}</span></div>
        ${paperList(sortPapers(list))}
      </section>`).join('');
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Surveys'}])}
      <section class="page-intro"><p class="eyebrow">Separate collection</p><h1>Surveys</h1><p>Survey papers are listed separately and do not contribute to the Years or Conferences views or their counts.</p></section>
      ${body || '<div class="empty-state">No survey papers yet. Add BibTeX files under <code>bib/survey/</code> or use <code>bib/survey.bib</code>.</div>'}`;
  }

  function renderConference(conference) {
    const papers = state.data.papers.filter(p => p.conference === conference);
    const label = state.data.conferenceNames[conference] || conference;
    const groups = new Map();
    papers.forEach(p => { if (!groups.has(p.year)) groups.set(p.year, []); groups.get(p.year).push(p); });
    const body = [...groups.entries()].sort(([a],[b]) => Number(b)-Number(a)).map(([year, list]) => `
      <section class="subgroup">
        <div class="subgroup-heading"><h3><a href="#year/${enc(year)}">${esc(year)}</a></h3><span class="group-count">${list.length} papers</span></div>
        ${paperList(sortPapers(list))}
      </section>`).join('');
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Conferences',href:'#conferences'},{label:conference}])}
      <section class="page-intro"><p class="eyebrow">Conference</p><h1>${esc(conference)}</h1><p>${esc(label)} · ${papers.length} papers.</p></section>
      ${body || '<div class="empty-state">No papers for this conference.</div>'}`;
  }

  function renderTags() {
    const tags = state.data.facets.tags;
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Tags'}])}
      <section class="page-intro"><p class="eyebrow">Browse</p><h1>Tags</h1><p>Tags come from the BibTeX <code>keywords</code> or <code>tags</code> field.</p></section>
      <div class="tag-cloud">${tags.map(t => `<a class="tag" href="#tag/${enc(t.value)}">${esc(t.value)} <span class="tag-count">${t.count}</span></a>`).join('') || '<div class="empty-state">No tags yet.</div>'}</div>`;
  }

  function renderTag(tag) {
    const papers = allRecords().filter(p => (p.tags || []).some(t => t.toLowerCase() === tag.toLowerCase()));
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Tags',href:'#tags'},{label:tag}])}
      <section class="page-intro"><p class="eyebrow">Tag</p><h1>${esc(tag)}</h1><p>${papers.length} matching papers.</p></section>
      ${paperList(sortPapers(papers))}`;
  }

  function searchableText(p) {
    return [p.title, p.authorText, p.conference, p.conferenceName, p.collection === 'survey' ? 'survey' : '', p.year, p.key, ...(p.tags || [])].join(' ').toLowerCase();
  }

  function renderSearch(params) {
    const { facets } = state.data;
    const initial = {
      q: params.get('q') || '',
      year: params.get('year') || '',
      conference: params.get('conference') || '',
      tag: params.get('tag') || ''
    };

    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'Search'}])}
      <section class="page-intro"><p class="eyebrow">Find papers</p><h1>Search</h1><p>Free-text and tag search include the separate survey collection. Year and conference filters apply only to conference papers.</p></section>
      <form class="search-panel" id="search-form">
        <input id="search-q" name="q" type="search" autocomplete="off" value="${esc(initial.q)}" placeholder="Title, author, tag, key…" aria-label="Search text">
        <select id="search-year" name="year" aria-label="Filter by year"><option value="">All years</option>${facets.years.map(x => `<option value="${esc(x.value)}" ${String(x.value)===initial.year?'selected':''}>${esc(x.value)}</option>`).join('')}</select>
        <select id="search-conference" name="conference" aria-label="Filter by conference"><option value="">All conferences</option>${facets.conferences.map(x => `<option value="${esc(x.value)}" ${x.value===initial.conference?'selected':''}>${esc(x.value)}</option>`).join('')}</select>
        <select id="search-tag" name="tag" aria-label="Filter by tag"><option value="">All tags</option>${facets.tags.map(x => `<option value="${esc(x.value)}" ${x.value===initial.tag?'selected':''}>${esc(x.value)}</option>`).join('')}</select>
      </form>
      <div class="results-bar"><span id="result-count"></span><button class="clear-button" id="clear-search" type="button">Clear filters</button></div>
      <div id="search-results"></div>`;

    const form = document.getElementById('search-form');
    const resultCount = document.getElementById('result-count');
    const results = document.getElementById('search-results');

    function update(pushHash = true) {
      const fd = new FormData(form);
      const q = (fd.get('q') || '').toString().trim().toLowerCase();
      const year = (fd.get('year') || '').toString();
      const conference = (fd.get('conference') || '').toString();
      const tag = (fd.get('tag') || '').toString();
      const filtered = sortPapers(allRecords().filter(p => {
        if (q && !searchableText(p).includes(q)) return false;
        if (year && (p.collection === 'survey' || String(p.year) !== year)) return false;
        if (conference && (p.collection === 'survey' || p.conference !== conference)) return false;
        if (tag && !(p.tags || []).includes(tag)) return false;
        return true;
      }));
      resultCount.textContent = `${filtered.length} result${filtered.length === 1 ? '' : 's'}`;
      results.innerHTML = paperList(filtered);
      bindCopyButtons();
      if (pushHash) {
        const out = new URLSearchParams();
        if (fd.get('q')) out.set('q', fd.get('q'));
        if (year) out.set('year', year);
        if (conference) out.set('conference', conference);
        if (tag) out.set('tag', tag);
        history.replaceState(null, '', `#search${out.toString() ? `?${out}` : ''}`);
      }
    }

    form.addEventListener('input', () => update(true));
    document.getElementById('clear-search').addEventListener('click', () => { form.reset(); update(true); });
    update(false);
  }

  function renderAbout() {
    const { site, generatedAt } = state.data;
    const contact = site.contactUrl ? `<p>${externalLink(site.contactUrl, 'Contact / report an omission')}</p>` : '<p>Set <code>contactUrl</code> in <code>data/site.config.json</code> to add a public contact link.</p>';
    app.innerHTML = `${breadcrumbs([{label:'Home',href:'#home'},{label:'About'}])}
      <section class="page-intro"><p class="eyebrow">About</p><h1>Scope and maintenance</h1><p>This is a curated conference bibliography for research substantially related to parameterized complexity.</p></section>
      <div class="about-grid">
        <article class="about-card"><h3>Scope</h3><p>The main bibliography contains papers accepted to international conferences. Survey papers may be maintained in a separate collection; they are excluded from the Years and Conferences views and counts. The site is designed for overviewing research activity and trends, not for replacing publisher pages, DBLP, or archival repositories.</p>${contact}</article>
        <article class="about-card"><h3>Metadata</h3><p>Entries are generated from BibTeX files. Tags are curator-supplied through <code>keywords</code> or <code>tags</code>. Paper text and abstracts are not copied into this site by default.</p></article>
        <article class="about-card"><h3>Copyright and links</h3><p>The site stores bibliographic metadata and links to external paper pages. Copyright in linked papers remains with the respective authors and/or publishers. Reuse of third-party metadata should follow the terms of its original source.</p></article>
        <article class="about-card"><h3>LLM disclosure</h3><p>This website was developed with assistance from a generative AI / large language model. LLM-assisted collection or classification may also be used during maintenance, but maintainers should verify inclusion decisions and bibliographic metadata.</p></article>
      </div>
      <p class="section" style="color:var(--muted);font-size:13px">Database generated: ${esc(generatedAt)}.</p>`;
  }

  function bindCopyButtons() {
    document.querySelectorAll('.copy-bib').forEach(btn => {
      btn.addEventListener('click', async () => {
        const paper = allRecords().find(p => p.id === btn.dataset.bibId);
        if (!paper?.bibtex) return;
        try {
          await navigator.clipboard.writeText(paper.bibtex);
          const old = btn.textContent; btn.textContent = 'Copied';
          setTimeout(() => { btn.textContent = old; }, 1200);
        } catch (_) {
          window.prompt('Copy BibTeX:', paper.bibtex);
        }
      });
    });
  }

  function render() {
    const r = route();
    setCurrentNav(r.page);
    nav.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');
    switch (r.page) {
      case 'home': renderHome(); break;
      case 'years': renderYears(); break;
      case 'year': renderYear(r.arg); break;
      case 'conferences': renderConferences(); break;
      case 'conference': renderConference(r.arg); break;
      case 'surveys': renderSurveys(); break;
      case 'tags': renderTags(); break;
      case 'tag': renderTag(r.arg); break;
      case 'search': renderSearch(r.params); break;
      case 'about': renderAbout(); break;
      default: location.hash = '#home'; return;
    }
    bindCopyButtons();
    window.scrollTo({top: 0, behavior: 'instant'});
  }

  navToggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(open));
  });

  window.addEventListener('hashchange', render);

  fetch('data/publications.json', {cache: 'no-cache'})
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(data => {
      state.data = data;
      document.title = data.site.siteTitle;
      brandTitle.textContent = data.site.shortTitle || data.site.siteTitle;
      loading.hidden = true;
      app.hidden = false;
      render();
    })
    .catch(err => {
      loading.innerHTML = `<strong>Could not load the generated bibliography.</strong><br><small>${esc(err.message)}. Run <code>python scripts/build.py</code> before publishing.</small>`;
    });
})();
