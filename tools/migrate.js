#!/usr/bin/env node
/* =====================================================================
   MIGRÁCIA DÁT v1–v4 → v5 (schema_version 5), bez straty a bez hádania vlastníka
   Zdroje: --server <clone cvictypic-data> (kv/ctp__d__<user>.json + celá git história),
           --artifact <dir> (JSON hodnoty zo starého Claude artefaktu: art*_ctp_d_<user>.json)
   Výstup: --out <dir>: kv/ (v5 súbory), report.md, unclear.json, all-records.json
   Nič nemaže; nejasné záznamy iba označí (flag) a vypíše na rozhodnutie.
   Použitie: node tools/migrate.js --server ../cvictypic-data --artifact ../data-sources/old-artifact --out ../migration-out
   ===================================================================== */
const fs=require('fs'),path=require('path'),cp=require('child_process');
global.SCHEMA=5;
global.SES_META={UA:{n:'Upper A',grp:'upper'},LA:{n:'Lower A',grp:'lower'},UB:{n:'Upper B',grp:'upper'},LB:{n:'Lower B',grp:'lower'},K:{n:'Kardio'},X:{n:'Iný'}};
let _c=0;global.uid=()=>'m'+(Date.now().toString(36))+(++_c).toString(36);
const {legacyToWorkouts,mondayOf}=require('./legacy.js');
const args={};process.argv.slice(2).forEach((a,i,arr)=>{if(a.startsWith('--'))args[a.slice(2)]=arr[i+1]&&!arr[i+1].startsWith('--')?arr[i+1]:true;});
if(!args.out){console.error('chýba --out');process.exit(1);}
const OUT=path.resolve(args.out);fs.mkdirSync(OUT,{recursive:true});
const canon=v=>Array.isArray(v)?v.map(canon):(v&&typeof v==='object')?Object.fromEntries(Object.keys(v).filter(k=>!k.startsWith('_')).sort().map(k=>[k,canon(v[k])])):v;
const stable=v=>JSON.stringify(canon(v),null,1);
const norm=w=>{const o=canon(w);['updated','created','dev','src','deleted','moved_to','moved_from','conflict_dev','flag'].forEach(k=>delete o[k]);return o;};
const sig=w=>JSON.stringify(norm(w));
const readJ=f=>{try{return JSON.parse(fs.readFileSync(f,'utf8'));}catch(e){return null;}};
const userOfKey=f=>{const m=f.match(/ctp__d__([a-z0-9-]+)\.json$/);return m?m[1]:null;};

const sources=[];   // {name, user, data, kind}
const report=[];const R=(...a)=>report.push(...a);
R('# Migrácia dát → schéma 5','','Vygenerované: '+new Date().toISOString(),'');

/* ---------- 1. server (aktuálny stav) ---------- */
let profiles=null,seedState=null,serverUsers=[];
if(args.server){
 const kv=path.join(args.server,'kv');
 if(!fs.existsSync(kv)){console.error('server: chýba kv/ v '+args.server);process.exit(1);}
 const files=fs.readdirSync(kv).filter(f=>f.endsWith('.json'));
 R('## Zdroje','','### Server (kv/, aktuálny stav)');
 files.forEach(f=>{const j=readJ(path.join(kv,f));const u=userOfKey(f);
  if(f==='ctp__profiles.json'){profiles=j;R('- '+f+' – profily: '+(Array.isArray(j)?j.map(p=>p.id).join(', '):'?'));return;}
  if(f==='ctp__seed.json'){seedState=j;R('- '+f+' – stav seed importu: '+JSON.stringify(j));return;}
  if(u){serverUsers.push(u);sources.push({name:'server:'+f,user:u,data:j,kind:'server'});R('- '+f+' → '+u+': logs '+((j&&j.logs)||[]).length+', check-iny '+Object.values((j&&j.checks)||{}).reduce((n,b)=>n+Object.values(b).filter(v=>v&&v.s==='done').length,0)+', aktivity '+((j&&j.acts)||[]).length+', plán: '+(j&&j.plan&&Object.keys(j.plan).length?Object.keys(j.plan).join(','):'–')+', meals/health (ignorované): '+((j&&j.meals)||[]).length+'/'+Object.keys((j&&j.health)||{}).length);return;}
  R('- '+f+' – ignorované (nie tréningové dáta, ostáva na serveri)');});
}
/* ---------- 2. starý Claude artefakt ---------- */
if(args.artifact){
 R('','### Starý Claude artefakt (window.storage, byte-exact kópia)');
 fs.readdirSync(args.artifact).filter(f=>/^art\d+_ctp_d_[a-z0-9-]+\.json$/.test(f)).sort().forEach(f=>{const m=f.match(/^(art\d+)_ctp_d_([a-z0-9-]+)\.json$/);const j=readJ(path.join(args.artifact,f));sources.push({name:'artifact:'+f,user:m[2],data:j,kind:m[1]});R('- '+f+' → '+m[2]+': logs '+((j&&j.logs)||[]).length+', check-iny '+Object.values((j&&j.checks)||{}).reduce((n,b)=>n+Object.values(b).filter(v=>v&&v.s==='done').length,0));});
}
/* ---------- 3. git história servera – čo kedy zmizlo ---------- */
const history={}; // user -> id -> {first,last,lastSeenCommit,versions:Set(sig), sample}
if(args.server&&fs.existsSync(path.join(args.server,'.git'))){
 R('','### Git história cvictypic-data');
 const commits=cp.execSync('git log --format="%H|%cI" --reverse -- kv/',{cwd:args.server,encoding:'utf8'}).trim().split('\n').filter(Boolean).map(l=>{const [h,d]=l.split('|');return {h,d};});
 R('- commity dotýkajúce sa kv/: '+commits.length);
 const seenFiles=new Set();
 commits.forEach(c=>{let names=[];try{names=cp.execSync(`git ls-tree --name-only ${c.h} kv/`,{cwd:args.server,encoding:'utf8'}).trim().split('\n').filter(Boolean);}catch(e){}
  names.forEach(n=>{const u=userOfKey(n);if(!u)return;seenFiles.add(n);let txt='';try{txt=cp.execSync(`git show ${c.h}:${n}`,{cwd:args.server,encoding:'utf8',maxBuffer:64*1024*1024});}catch(e){return;}let j=null;try{j=JSON.parse(txt);}catch(e){return;}
   const {workouts,acts}=legacyToWorkouts(j,u,'history');history[u]=history[u]||{};
   [...workouts,...acts].forEach(w=>{const h=history[u][w.id]=history[u][w.id]||{first:c.d,versions:new Map()};h.last=c.d;h.lastCommit=c.h;const s=sig(w);if(!h.versions.has(s))h.versions.set(s,{at:c.d,rec:w});});});});
 Object.entries(history).forEach(([u,m])=>R('- '+u+': '+Object.keys(m).length+' rôznych id záznamov v histórii'));
}

/* ---------- 4. konverzia + zlúčenie podľa id ---------- */
const merged={}; // user -> id -> {rec, srcs:[], variants:[{src,rec}]}
const counts={before:{},after:{}}; // user -> exercise -> {sets, workouts}
function countInto(tbl,u,w){tbl[u]=tbl[u]||{};(w.entries||[]).forEach(e=>{const v=(e.sets||[]).filter(s=>s.r>0||s.w>0);if(!v.length)return;const c=tbl[u][e.exercise_id]=tbl[u][e.exercise_id]||{sets:0,workouts:0};c.sets+=v.length;c.workouts++;});if(w.src==='check'){const c=tbl[u]['(check-in)']=tbl[u]['(check-in)']||{sets:0,workouts:0};c.workouts++;}}
const acts={}; // user -> id -> rec
sources.forEach(s=>{if(!s.data)return;const {workouts,acts:ac}=legacyToWorkouts(s.data,s.user,s.kind);
 workouts.forEach(w=>{countInto(counts.before,s.user+' ('+s.name+')',w);merged[s.user]=merged[s.user]||{};const m=merged[s.user][w.id];if(!m){merged[s.user][w.id]={rec:w,srcs:[s.name],variants:[]};return;}m.srcs.push(s.name);if(sig(m.rec)!==sig(w)){if(s.kind==='server'){m.variants.push({src:m.srcs[0],rec:m.rec});m.rec=w;}else m.variants.push({src:s.name,rec:w});}});
 ac.forEach(a=>{acts[s.user]=acts[s.user]||{};if(!acts[s.user][a.id])acts[s.user][a.id]=a;});});
/* check-in, ku ktorému existuje meranie z iného zdroja (rovnaký user+dátum+typ) → vynechať (zostáva v histórii/zdroji) */
const shadowed=[];
Object.entries(merged).forEach(([u,m])=>{const measured=new Set(Object.values(m).filter(x=>x.rec.src!=='check'&&(x.rec.entries||[]).some(e=>e.sets.length)).map(x=>mondayOf(x.rec.date)+'|'+x.rec.session));Object.entries(m).forEach(([id,x])=>{if(x.rec.src==='check'&&measured.has((x.rec.week||mondayOf(x.rec.date))+'|'+x.rec.session)){shadowed.push(u+' '+x.rec.date+' '+x.rec.session+' ('+id+')');delete m[id];}});});

/* ---------- 5. nejasné záznamy (flag, nie rozhodnutie) ---------- */
const unclear=[];
function flag(u,id,type,note,proposal){const m=merged[u]&&merged[u][id];if(!m)return;m.rec.flag={type,note,proposal};unclear.push({user:u,id,date:m.rec.date,session:m.rec.session,type,note,proposal,summary:(m.rec.entries||[]).map(e=>e.exercise_id+' '+e.sets.map(s=>(s.w?s.w+'×':'')+s.r+(s.d?'↓':'')).join(',')).join('; ')});}
/* a) bloky z chatu (1. 9.) bez explicitného vlastníka – priradené heuristikou (váhy) → na potvrdenie */
Object.entries(merged).forEach(([u,m])=>Object.keys(m).forEach(id=>{if(/^seed-u[ab]-2026-08-2[14]$/.test(id))flag(u,id,'nejasný user','Blok z chatu 1. 9. bez mena (tvoj text „tu sú nejaké čo mám“), dátum 21. 8. odhadnutý. Priradené heuristikou: lat pulldown 45–50 kg (Matej 25–30 kg).','thephilosopher');}));
/* b) duplicitné zápisy (rovnaký user, dátum, typ; jeden je podmnožinou druhého) */
Object.entries(merged).forEach(([u,m])=>{const by={};Object.values(m).forEach(x=>{if(x.rec.src==='check')return;const k=x.rec.date+'|'+x.rec.session;(by[k]=by[k]||[]).push(x.rec);});Object.entries(by).forEach(([k,arr])=>{if(arr.length<2)return;arr.sort((a,b)=>sig(a).length-sig(b).length);const small=arr[0],big=arr[arr.length-1];const subset=(small.entries||[]).every(e=>{const be=(big.entries||[]).find(x=>x.exercise_id===e.exercise_id);return be&&e.sets.every((s,i)=>be.sets[i]&&be.sets[i].w===s.w&&be.sets[i].r===s.r);});flag(u,small.id,'duplikát?',`Rovnaký deň a typ ako ${big.id}${subset?' a je jeho podmnožinou (chyba duplikovania zápisu v starej verzii)':''}.`,subset?'označiť ako zmazaný (ponechať v zálohe)':'skontrolovať');});});
/* c) rozdielne verzie toho istého id v rôznych zdrojoch */
const infoVariants=[];
Object.entries(merged).forEach(([u,m])=>Object.entries(m).forEach(([id,x])=>{if(!x.variants.length)return;if(x.rec.src==='check'){infoVariants.push(`${u} · ${id}: server ${x.rec.date} vs. ${x.variants.map(v=>v.src.replace(/^artifact:/,'')+' '+v.rec.date).join(', ')} – check-in bez čísel, použitý serverový dátum`);return;}flag(u,id,'rozdielne verzie',`Zdroje ${x.srcs.join(' + ')} majú iný obsah; použitá serverová verzia, ostatné priložené ako variants v all-records.json.`,'skontrolovať');}));
/* d) záznamy, ktoré boli v git histórii a dnes na serveri nie sú */
const vanished=[];
const moved=[];
Object.entries(history).forEach(([u,m])=>Object.entries(m).forEach(([id,h])=>{const inFinal=merged[u]&&merged[u][id]||(acts[u]&&acts[u][id]);if(inFinal)return;const last=[...h.versions.values()].pop().rec;if(last.src==='check'&&merged[u]&&Object.values(merged[u]).some(x=>mondayOf(x.rec.date)===(last.week||mondayOf(last.date))&&x.rec.session===last.session))return;const elsewhere=Object.keys(merged).find(o=>o!==u&&merged[o][id]);if(elsewhere){moved.push(`${u} → ${elsewhere}: ${id} (${last.date} ${last.session})`);return;}vanished.push({user:u,id,first:h.first,last:h.last,rec:last});}));

/* ---------- 6. výstup v5 ---------- */
const kvOut=path.join(OUT,'kv');fs.rmSync(kvOut,{recursive:true,force:true});fs.mkdirSync(kvOut,{recursive:true});
const profOut=(Array.isArray(profiles)?profiles:[]).map(p=>({id:p.id,name:p.name,dia:!!p.dia,goalMonth:16,created:p.created||'',legacy:{bw:p.bw||0,h:p.h||0,age:p.age||0,sex:p.sex||'',exp:p.exp||'',goal:p.goal||'',goalText:p.goalText||''}}));
['thephilosopher','bocian','agiraa'].forEach(id=>{if(!profOut.find(p=>p.id===id)&&(merged[id]||serverUsers.includes(id)))profOut.push({id,name:id,dia:id==='thephilosopher',goalMonth:16});});
fs.writeFileSync(path.join(kvOut,'profiles.json'),stable({schema_version:5,profiles:profOut}));
const all={profiles:profOut,users:{}};
Object.keys(Object.assign({},merged,acts)).forEach(u=>{fs.mkdirSync(path.join(kvOut,u,'w'),{recursive:true});fs.mkdirSync(path.join(kvOut,u,'a'),{recursive:true});all.users[u]={workouts:[],activities:[],plan:null};
 Object.values(merged[u]||{}).forEach(x=>{x.rec.srcs=x.srcs;fs.writeFileSync(path.join(kvOut,u,'w',x.rec.id+'.json'),stable(x.rec));countInto(counts.after,u,x.rec);all.users[u].workouts.push(Object.assign({},x.rec,{variants:x.variants}));});
 Object.values(acts[u]||{}).forEach(a=>{fs.writeFileSync(path.join(kvOut,u,'a',a.id+'.json'),stable(a));all.users[u].activities.push(a);});
 const srv=sources.find(s=>s.kind==='server'&&s.user===u);
 if(srv&&srv.data&&srv.data.plan){const plan={schema_version:5,user_id:u,sessions:{},updated:Date.now(),src:'server:v4'};let any=false;['UA','LA','UB','LB'].forEach(k=>{if(Array.isArray(srv.data.plan[k])){plan.sessions[k]=srv.data.plan[k].map(x=>({id:String(x.id),nm:x.nm||'',sets:String(x.sets||''),drop:x.drop?1:0,pu:0,k:x.k||uid()}));any=true;}});if(any){fs.writeFileSync(path.join(kvOut,u,'plan.json'),stable(plan));all.users[u].plan=plan;}}
});
fs.writeFileSync(path.join(OUT,'all-records.json'),JSON.stringify(all,null,1));
fs.writeFileSync(path.join(OUT,'unclear.json'),JSON.stringify({unclear,vanished:vanished.map(v=>({user:v.user,id:v.id,first:v.first,last:v.last,date:v.rec.date,session:v.rec.session,summary:(v.rec.entries||[]).map(e=>e.exercise_id+' '+(e.sets||[]).map(s=>(s.w?s.w+'×':'')+s.r).join(',')).join('; ')}))},null,1));

/* ---------- 7. report ---------- */
R('','## Tabuľka migrácie (tréningy)','','| user | id | dátum | typ | cviky so sériami | zdroj(e) | poznámka |','|---|---|---|---|---|---|---|');
Object.entries(merged).sort().forEach(([u,m])=>Object.values(m).sort((a,b)=>a.rec.date<b.rec.date?-1:1).forEach(x=>{const w=x.rec;R(`| ${u} | ${w.id} | ${w.date} | ${w.session} | ${w.src==='check'?'check-in (bez čísel)':(w.entries||[]).filter(e=>e.sets.length).length} | ${x.srcs.join(' + ')} | ${w.flag?'**'+w.flag.type+'**':''}${x.variants.length?' rozdielne verzie':''} |`);}));
R('','### Aktivity (kardio – len história, mimo plánu)');Object.entries(acts).forEach(([u,m])=>Object.values(m).forEach(a=>R(`- ${u} · ${a.date} · ${a.kind}${a.min?' · '+a.min+' min':''} (${a.src})`)));
if(shadowed.length){R('','### Check-iny nahradené meraním (vynechané, nič sa nestráca – meranie je v tabuľke)');shadowed.forEach(s=>R('- '+s));}
R('','## Nejasné záznamy – na tvoje rozhodnutie','');if(!unclear.length)R('(žiadne)');unclear.forEach(x=>R(`- **${x.user} · ${x.date} ${x.session} · ${x.id}** – ${x.type}: ${x.note} Návrh: **${x.proposal}**. Obsah: ${x.summary||'(bez sérií)'}`));
if(infoVariants.length){R('','### Info · check-iny s rozdielnym dátumom v zdrojoch');infoVariants.forEach(x=>R('- '+x));}
if(moved.length){R('','### Info · záznamy presunuté medzi používateľmi (podľa histórie servera)');moved.forEach(x=>R('- '+x));}
R('','## Zmizli z histórie servera (dnes na serveri nie sú)','');if(!vanished.length)R('(nič – všetko, čo kedy bolo na serveri, tam je aj dnes)');vanished.forEach(v=>R(`- ${v.user} · ${v.rec.date} ${v.rec.session||('aktivita '+(v.rec.kind||''))} · ${v.id} · videné ${v.first.slice(0,10)} – ${v.last.slice(0,10)} · ${(v.rec.entries||[]).map(e=>e.exercise_id+' '+(e.sets||[]).map(s=>(s.w?s.w+'×':'')+s.r).join(',')).join('; ')||(v.rec.src==='check'?'(check-in bez čísel)':'('+(v.rec.min||0)+' min)')}`));
R('','## Validácia · počty sérií / tréningov per user per cvik','','### Pred (podľa zdroja)');
Object.entries(counts.before).sort().forEach(([k,ex])=>{R('','**'+k+'**');Object.entries(ex).sort().forEach(([e,c])=>R(`- ${e}: ${c.sets} sérií v ${c.workouts} tréningoch`));});
R('','### Po (v5, zlúčené)');
Object.entries(counts.after).sort().forEach(([k,ex])=>{R('','**'+k+'**');Object.entries(ex).sort().forEach(([e,c])=>R(`- ${e}: ${c.sets} sérií v ${c.workouts} tréningoch`));});
R('','### Rozdiely');
const sumBy=(tbl,pick)=>{const o={};Object.entries(tbl).forEach(([k,ex])=>{const u=k.split(' ')[0];o[u]=o[u]||{};Object.entries(ex).forEach(([e,c])=>{o[u][e]=o[u][e]||{sets:0,workouts:0};o[u][e].sets+=c.sets;o[u][e].workouts+=c.workouts;});});return o;};
const B=sumBy(counts.before),A=sumBy(counts.after);let diffs=0;
Object.keys(Object.assign({},B,A)).sort().forEach(u=>{Object.keys(Object.assign({},B[u]||{},A[u]||{})).sort().filter(e=>e!=='(check-in)').forEach(e=>{const b=(B[u]||{})[e]||{sets:0,workouts:0},a=(A[u]||{})[e]||{sets:0,workouts:0};if(b.sets!==a.sets||b.workouts!==a.workouts){diffs++;R(`- ${u} · ${e}: pred ${b.sets} sérií/${b.workouts} tr. (súčet zdrojov, duplicity medzi zdrojmi sa rátajú viackrát) → po ${a.sets}/${a.workouts}`);}});});
if(!diffs)R('(žiadne – súčty pred a po sedia)');else R('','Rozdiel = ten istý záznam bol vo viacerých zdrojoch (server + artefakt + história) a po zlúčení je raz. Záznam s iným obsahom je v „Nejasné“.');
fs.writeFileSync(path.join(OUT,'report.md'),report.join('\n')+'\n');
console.log('OK →',OUT,'| users:',Object.keys(merged).join(','),'| workouts:',Object.values(merged).reduce((n,m)=>n+Object.keys(m).length,0),'| unclear:',unclear.length,'| vanished:',vanished.length);
