(() => {
  'use strict';

  function searchableText(p) {
    return [
      p.title,
      p.authorText,
      p.conference,
      p.conferenceName,
      p.collection === 'survey' ? 'survey' : '',
      p.year,
      p.key,
      ...(p.tags || [])
    ].join(' ').toLowerCase();
  }

  function addPosting(map, key, id) {
    if (key === undefined || key === null || key === '') return;
    const k = String(key);
    let list = map.get(k);
    if (!list) {
      list = [];
      map.set(k, list);
    }
    list.push(id);
  }

  function freezePostings(map) {
    for (const [key, list] of map) map.set(key, Uint32Array.from(list));
    return map;
  }

  function trigramsForText(text) {
    const out = new Set();
    const words = String(text || '').match(/[0-9a-z\u0080-\uffff]+/gi) || [];
    for (const raw of words) {
      const word = raw.toLowerCase();
      if (word.length < 3) continue;
      for (let i = 0; i <= word.length - 3; i += 1) out.add(word.slice(i, i + 3));
    }
    return out;
  }

  function build(records) {
    const text = new Array(records.length);
    const years = new Map();
    const conferences = new Map();
    const tags = new Map();
    const trigrams = new Map();

    for (let id = 0; id < records.length; id += 1) {
      const p = records[id];
      const haystack = searchableText(p);
      text[id] = haystack;

      if (p.collection !== 'survey') {
        addPosting(years, p.year, id);
        addPosting(conferences, p.conference, id);
      }
      for (const tag of p.tags || []) addPosting(tags, tag, id);
      for (const gram of trigramsForText(haystack)) addPosting(trigrams, gram, id);
    }

    return {
      records,
      text,
      years: freezePostings(years),
      conferences: freezePostings(conferences),
      tags: freezePostings(tags),
      trigrams: freezePostings(trigrams),
      allIds: Uint32Array.from({ length: records.length }, (_, i) => i)
    };
  }

  function unionTwo(a, b) {
    if (!a || a.length === 0) return Array.from(b || []);
    if (!b || b.length === 0) return Array.from(a || []);
    const out = [];
    let i = 0;
    let j = 0;
    while (i < a.length && j < b.length) {
      const av = a[i];
      const bv = b[j];
      if (av === bv) {
        out.push(av); i += 1; j += 1;
      } else if (av < bv) {
        out.push(av); i += 1;
      } else {
        out.push(bv); j += 1;
      }
    }
    while (i < a.length) out.push(a[i++]);
    while (j < b.length) out.push(b[j++]);
    return out;
  }

  function unionSelected(map, values) {
    if (!values || values.length === 0) return null;
    const lists = [];
    for (const value of values) {
      const list = map.get(String(value));
      if (list && list.length) lists.push(list);
    }
    if (!lists.length) return [];
    lists.sort((a, b) => a.length - b.length);
    let out = Array.from(lists[0]);
    for (let i = 1; i < lists.length; i += 1) out = unionTwo(out, lists[i]);
    return out;
  }

  function intersectTwo(a, b) {
    if (!a || !b || a.length === 0 || b.length === 0) return [];
    const out = [];
    let i = 0;
    let j = 0;
    while (i < a.length && j < b.length) {
      const av = a[i];
      const bv = b[j];
      if (av === bv) {
        out.push(av); i += 1; j += 1;
      } else if (av < bv) {
        i += 1;
      } else {
        j += 1;
      }
    }
    return out;
  }

  function query(index, options = {}) {
    const q = String(options.q || '').trim().toLowerCase();
    const years = options.years || [];
    const conferences = options.conferences || [];
    const tags = options.tags || [];
    const constraints = [];

    const yearIds = unionSelected(index.years, years);
    if (yearIds !== null) constraints.push(yearIds);
    const conferenceIds = unionSelected(index.conferences, conferences);
    if (conferenceIds !== null) constraints.push(conferenceIds);
    const tagIds = unionSelected(index.tags, tags);
    if (tagIds !== null) constraints.push(tagIds);

    if (q) {
      const grams = [...trigramsForText(q)];
      for (const gram of grams) {
        const posting = index.trigrams.get(gram);
        if (!posting) return [];
        constraints.push(posting);
      }
    }

    constraints.sort((a, b) => a.length - b.length);
    let candidate;
    if (constraints.length) {
      candidate = Array.from(constraints[0]);
      for (let i = 1; i < constraints.length && candidate.length; i += 1) {
        candidate = intersectTwo(candidate, constraints[i]);
      }
    } else {
      candidate = Array.from(index.allIds);
    }

    // Trigrams are only a necessary condition. Verify against the exact old
    // substring semantics so the optimized engine cannot introduce false hits.
    if (q) candidate = candidate.filter(id => index.text[id].includes(q));
    return candidate;
  }

  globalThis.PCSearchEngine = Object.freeze({
    searchableText,
    trigramsForText,
    build,
    query,
    unionTwo,
    intersectTwo
  });
})();
