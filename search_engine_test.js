'use strict';
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const code = fs.readFileSync(require('path').join(__dirname, '../site/assets/search-engine.js'), 'utf8');
vm.runInThisContext(code, { filename: 'search-engine.js' });
const E = global.PCSearchEngine;

function baseline(records, {q='', years=[], conferences=[], tags=[]}) {
  const needle = String(q).trim().toLowerCase();
  return records.map((p, id) => ({p, id})).filter(({p}) => {
    if (needle && !E.searchableText(p).includes(needle)) return false;
    if (years.length && (p.collection === 'survey' || !years.includes(String(p.year)))) return false;
    if (conferences.length && (p.collection === 'survey' || !conferences.includes(String(p.conference)))) return false;
    if (tags.length && !tags.some(tag => (p.tags || []).includes(tag))) return false;
    return true;
  }).map(x => x.id);
}

const conferences = ['SODA','STOC','ICALP','IPEC','AAAI'];
const years = ['2019','2020','2021','2022','2023','2024','2025'];
const tags = ['kernelization','treewidth','FPT','approximation','reconfiguration','lower bounds'];
const words = ['parameterized','algorithm','vertex','cover','graph','kernel','exact','complexity','dynamic','programming','approximation','reconfiguration'];

let seed = 123456789;
function rnd() { seed = (1103515245 * seed + 12345) >>> 0; return seed / 2**32; }
function pick(a) { return a[Math.floor(rnd()*a.length)]; }
function subset(a, p=0.25) { return a.filter(() => rnd() < p); }
function sentence(n=6) { return Array.from({length:n}, () => pick(words)).join(' '); }

const records = Array.from({length: 2500}, (_, i) => {
  const survey = rnd() < 0.06;
  const conf = survey ? '' : pick(conferences);
  const yr = pick(years);
  const ts = subset(tags, 0.22);
  return {
    title: sentence(5 + Math.floor(rnd()*4)),
    authorText: `Author ${i%137}, Researcher ${i%83}`,
    conference: conf,
    conferenceName: conf ? `${conf} Conference` : '',
    collection: survey ? 'survey' : 'conference',
    year: yr,
    key: `Key${i}`,
    tags: ts
  };
});

const index = E.build(records);

const queries = ['', 'pa', 'parameter', 'vertex cover', 'graph', 'Author 17', 'SODA', 'lower bounds', 'Key24', 'reconfiguration'];
for (let t = 0; t < 1200; t++) {
  const options = {
    q: pick(queries),
    years: subset(years, 0.12),
    conferences: subset(conferences, 0.12),
    tags: subset(tags, 0.10)
  };
  const want = baseline(records, options);
  const got = E.query(index, options);
  assert.deepStrictEqual(got, want, `Mismatch for ${JSON.stringify(options)}`);
}

// Edge cases: surveys are searchable by text/tag, but excluded by year/conference.
const surveyIndex = records.findIndex(p => p.collection === 'survey');
if (surveyIndex >= 0) {
  const p = records[surveyIndex];
  assert(E.query(index, {q: p.key}).includes(surveyIndex));
  assert(!E.query(index, {years:[p.year]}).includes(surveyIndex));
}

// Basic performance guard. This is deliberately generous to avoid flaky CI;
// it catches accidental O(N * text reconstruction) regressions in the engine.
const start = process.hrtime.bigint();
for (let i = 0; i < 300; i++) {
  E.query(index, {q:'parameterized', years:['2023','2024'], conferences:['SODA','ICALP'], tags:['FPT']});
}
const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;
assert(elapsedMs < 1500, `Search engine unexpectedly slow: ${elapsedMs.toFixed(1)} ms / 300 queries`);

console.log(`search_engine_test: OK (${records.length} records, 1200 equivalence cases, ${elapsedMs.toFixed(1)} ms / 300 queries)`);
