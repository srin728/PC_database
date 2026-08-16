'use strict';
const fs = require('fs');
const vm = require('vm');
const path = require('path');
vm.runInThisContext(fs.readFileSync(path.join(__dirname, '../site/assets/search-engine.js'), 'utf8'));
const E = global.PCSearchEngine;
const conferences = ['SODA','STOC','ICALP','IPEC','AAAI','ESA','STACS','FOCS'];
const years = Array.from({length:20}, (_,i)=>String(2006+i));
const tags = ['kernelization','treewidth','FPT','approximation','reconfiguration','lower bounds','graph algorithms'];
const words = ['parameterized','algorithm','vertex','cover','graph','kernel','exact','complexity','dynamic','programming','approximation','reconfiguration','structural'];
let seed=42; const rnd=()=>((seed=(1664525*seed+1013904223)>>>0)/2**32); const pick=a=>a[Math.floor(rnd()*a.length)];
const records=Array.from({length:10000},(_,i)=>({
  title:Array.from({length:8},()=>pick(words)).join(' '), authorText:`Author ${i%997} Researcher ${i%499}`,
  conference:pick(conferences), conferenceName:'Conference', collection:'conference', year:pick(years), key:`Key${i}`,
  tags:tags.filter(()=>rnd()<0.15)
}));
const index=E.build(records);
const opts={q:'parameterized algorithm', years:['2023','2024','2025'], conferences:['SODA','ICALP'], tags:['FPT']};
const baseline=()=>records.filter(p=>{
 const q=opts.q.toLowerCase(); if(q&&!E.searchableText(p).includes(q))return false;
 if(opts.years.length&&!opts.years.includes(String(p.year)))return false;
 if(opts.conferences.length&&!opts.conferences.includes(p.conference))return false;
 if(opts.tags.length&&!opts.tags.some(t=>(p.tags||[]).includes(t)))return false;
 return true;
});
for(let i=0;i<10;i++){baseline();E.query(index,opts);}
let t=process.hrtime.bigint(); for(let i=0;i<300;i++)baseline(); const oldMs=Number(process.hrtime.bigint()-t)/1e6;
t=process.hrtime.bigint(); for(let i=0;i<300;i++)E.query(index,opts); const newMs=Number(process.hrtime.bigint()-t)/1e6;
console.log(JSON.stringify({records:records.length,queries:300,linearMs:+oldMs.toFixed(1),indexedMs:+newMs.toFixed(1),speedup:+(oldMs/newMs).toFixed(1)}));
