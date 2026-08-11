# Parameterized Complexity Conference Papers

A lightweight, mobile-friendly static bibliography for conference papers related to parameterized complexity. It is designed for GitHub Pages and uses no frontend framework, external font, or CDN dependency.

## Main features

- BibTeX is the source of truth.
- Bibliography files are organized by conference and year.
- Browse by **year**, **conference**, or **tag**.
- Maintain survey papers as a **separate collection** that is excluded from year/conference views and counts.
- Combined full-text/tag/year/conference search in the browser.
- A small **News / latest updates** area on the home page.
- Responsive layout for desktop and mobile.
- Theme colors are based on `#7a99cf` and `#0c7bbb`.
- Page-level `noindex` directives are included to keep the site out of search results as far as standard search-engine controls permit.
- No paper PDF or abstract is copied into the site by default.
- The site includes an explicit generative-AI / LLM disclosure.

## Repository layout

```text
.
├── bib/
│   ├── SODA/
│   │   ├── SODA_2023.bib
│   │   └── SODA_2024.bib
│   ├── ICALP/
│   │   └── ICALP_2024.bib
│   └── survey/
│       └── survey.bib
├── data/
│   ├── site.config.json
│   ├── conferences.json
│   └── news.json
├── site/
│   ├── index.html
│   ├── 404.html
│   ├── robots.txt
│   └── assets/
├── scripts/build.py
└── .github/workflows/pages.yml
```

The generated `_site/` directory is intentionally ignored by Git. GitHub Actions rebuilds it automatically.

## Adding papers

> **For routine bibliography updates, adding the `.bib` files is enough.** You do not need to edit or regenerate HTML, JSON, or other site files. Place each BibTeX file in the appropriate conference folder and push it to GitHub; the build process automatically updates the year, conference, tag, search, and recent-update views.

Put each conference's BibTeX files under `bib/<CONFERENCE>/` with names such as:

```text
bib/SODA/SODA_2023.bib
bib/SODA/SODA_2024.bib
bib/ICALP/ICALP_2024.bib
```

A paper can be tagged with either `keywords` or `tags`:

```bibtex
@inproceedings{SomeKey,
  author    = {Alice Author and Bob Author},
  title     = {A Parameterized Algorithm for an Example Problem},
  booktitle = {Proceedings of ...},
  year      = {2026},
  doi       = {10.xxxx/xxxxx},
  url       = {https://example.org/paper},
  keywords  = {FPT algorithms; kernelization; graph algorithms}
}
```

Comma and semicolon separators are both accepted for tags.

The conference abbreviation is inferred from the parent folder. The year is taken from the BibTeX `year` field and falls back to the filename if necessary.

### Survey papers

Survey papers can be kept separately in either of the following forms:

```text
bib/survey/survey.bib
```

or

```text
bib/survey.bib
```

Entries from these survey files are shown on the dedicated **Surveys** page. They are **not included in the Years or Conferences views, counts, or filters**. They remain available through free-text and tag search.

### DOI and URL normalization

The build script normalizes common TeX escapes in DOI/URL fields. In particular, an escaped underscore such as

```bibtex
doi = {10.1007/978-3-031-38906-1\_8}
```

is linked as

```text
https://doi.org/10.1007/978-3-031-38906-1_8
```

The malformed exported form `...-1/\_8` is also normalized to `...-1_8`, so the `.bib` file does not need to be edited manually for this case.

### DBLP author-name suffixes

DBLP sometimes appends a four-digit disambiguation identifier to an author name, for example `Lu Liu 0030`. The site removes this trailing four-digit identifier from the displayed author name, so it is shown as `Lu Liu`. The original BibTeX source entry is left unchanged.

### Per-paper BibTeX downloads

Each paper card's **Source .bib** link downloads a generated `.bib` file containing only that paper's single BibTeX entry. It no longer downloads the whole conference/year source file. The original conference-level files under `bib/` remain the source of truth.

## News and update history

Edit `data/news.json` for editorial announcements:

```json
[
  {
    "date": "2026-08-10",
    "title": "SODA 2025 added",
    "text": "Completed a first-pass screening of SODA 2025."
  }
]
```

The build script derives **Latest updates** from Git commits that changed files under `bib/`. Updates are grouped by commit and summarize added/removed BibTeX entries or metadata changes, so a single commit that updates many conference files appears as one maintenance event rather than many misleading file-level entries. If Git history is unavailable, the build falls back to per-file modification dates. The supplied GitHub Actions workflow uses `fetch-depth: 0` so the full update history is available during Pages builds.

## Conference display names

`data/conferences.json` maps folder abbreviations to full names. Unknown folders still work and are displayed using their folder name.

## Site title and contact link

Edit `data/site.config.json`:

```json
{
  "siteTitle": "Parameterized Complexity Conference Papers",
  "shortTitle": "PC Papers",
  "siteSubtitle": "A lightweight bibliography ...",
  "contactUrl": "https://github.com/USER/REPOSITORY/issues",
  "repositoryUrl": "https://github.com/USER/REPOSITORY",
  "includeRawBibTeX": false,
  "homeRecentPapers": 12,
  "homeRecentUpdates": 8
}
```

A GitHub Issues URL is a convenient choice for `contactUrl` because visitors can report omissions without publishing a personal email address.

Set `includeRawBibTeX` to `true` if you want every paper card to have a “Copy BibTeX” button. Keeping it `false` makes `publications.json` smaller; each card still provides a `Source .bib` download containing only that paper's single BibTeX entry.

## Theme colors

The design is controlled by CSS custom properties at the top of `site/assets/styles.css`:

```css
:root {
  --primary: #0c7bbb;
  --secondary: #7a99cf;
  /* ... */
}
```

Changing those variables is enough for most visual customization.

## Local preview

Build the static files:

```bash
python scripts/build.py
```

Then serve `_site/` locally, for example:

```bash
python -m http.server 8000 --directory _site
```

Open `http://localhost:8000/`.

## Deploying with GitHub Pages

1. Create a GitHub repository and copy these files into it.
2. Add your `.bib` files under `bib/`.
3. Push to the `main` branch.
4. In **Settings → Pages**, choose **GitHub Actions** as the source if GitHub does not select it automatically.
5. The included workflow builds and deploys the site.

No Node.js or package installation is required.

## Search-engine indexing

`site/index.html` and `site/404.html` contain:

```html
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet,noimageindex">
<meta name="googlebot" content="noindex,nofollow,noarchive,nosnippet,noimageindex">
```

`robots.txt` intentionally does **not** block crawling, because a crawler generally needs to read the HTML before it can observe a `noindex` directive. This is the standard architecture for asking compliant search engines not to index the site. No public-web mechanism can guarantee that every search engine, archive, or third-party index will honor the request.

If a URL was already indexed before `noindex` was added, removal can take time and may require a removal request through the relevant search-engine webmaster console.

## Copyright, metadata, and LLM use

This repository's website code is MIT-licensed. That license does **not** transfer rights to papers, publisher pages, or third-party metadata.

The default site deliberately stores only bibliographic metadata and outbound links. It does not reproduce paper PDFs or abstracts. If metadata is copied from DBLP, Crossref, publisher sites, or another source, verify and comply with that source's applicable terms/licence.

The website states that it was developed with assistance from generative AI / an LLM. If LLMs are later used to discover, classify, or tag papers, human verification is recommended before publishing entries.

## BibTeX parser notes

`scripts/build.py` uses a dependency-free parser that handles ordinary `@inproceedings`-style entries, nested braces, quoted values, and common LaTeX accents. If your database later depends heavily on BibTeX macros (`@string`), cross-references, or unusually complex TeX commands, replacing the parser with a dedicated BibTeX library would be safer.
