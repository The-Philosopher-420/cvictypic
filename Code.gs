/*********************************************************************
 *  CVIČ TY PIČ – Google Apps Script (servuje appku + ukladá dáta do tabuľky)
 *  1) Nová Google tabuľka (sheets.new) → Rozšírenia → Apps Script.
 *  2) Do súboru Code.gs vlož TOTO (nahraď všetko).
 *  3) Vľavo „+“ → HTML → názov: index → vlož celý obsah súboru cvic-ty-pic.html.
 *  4) Nasadiť → Nová nasadenie → typ Webová aplikácia → Spustiť ako: Ja, Prístup: Ktokoľvek → Nasadiť.
 *     URL webovej aplikácie = appka. Otvor v Chrome/Safari, pridaj na plochu.
 *  5) Voliteľné: ANTHROPIC_KEY zapne chat, AI sync a fotky jedla pre všetkých.
 *  Po každej zmene kódu: Nasadiť → Spravovať nasadenia → ceruzka → Verzia: Nová → Nasadiť.
 *********************************************************************/
const ANTHROPIC_KEY = '';
const MODEL = 'claude-sonnet-5';   // ak by hlásil neznámy model, skús 'claude-sonnet-4-6'
const SECRET = 'cvictypic';        // heslo pre volania zvonka (verzia na GitHub Pages); pri servovaní zo skriptu netreba
const SHEET = 'kv';
const CHUNK = 45000;

function doGet(e){
  const q = (e && e.parameter) || {};
  if (q.a) return outJson(handle(q));                     // API pre appku hostovanú inde
  return HtmlService.createHtmlOutputFromFile('index')    // servuje appku
    .setTitle('Cvič ty pič')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
function doPost(e){ return outJson(handle(JSON.parse((e.postData && e.postData.contents) || '{}'))); }
function apiS(q){ q = q || {}; q.k = SECRET; return handle(q); }   // volania z appky cez google.script.run
function urlS(){ return ScriptApp.getService().getUrl(); }        // adresa appky pre tlačidlo „Odkaz pre kamošov“
function outJson(o){ return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function handle(q){
  try {
    if (q.a === 'ping') return { ok: true, auth: q.k === SECRET, chat: !!ANTHROPIC_KEY };
    if (q.k !== SECRET) return { error: 'zlé heslo' };
    if (q.a === 'get') return { value: kvGet(q.key) };
    if (q.a === 'set') { withLock(() => kvSet(q.key, String(q.value || ''))); return { ok: true }; }
    if (q.a === 'del') { withLock(() => kvDel(q.key)); return { ok: true }; }
    if (q.a === 'list') return { keys: kvAll().filter(r => r.key.indexOf(q.prefix || '') === 0).map(r => r.key) };
    if (q.a === 'getall') { const items = {}; kvAll().forEach(r => { if (r.key.indexOf(q.prefix || '') === 0) items[r.key] = r.value; }); return { items }; }
    if (q.a === 'chat') return chat(q);
    return { error: 'neznáma akcia' };
  } catch (err) { return { error: String(err) }; }
}
function sheet(){ const ss = SpreadsheetApp.getActiveSpreadsheet(); return ss.getSheetByName(SHEET) || ss.insertSheet(SHEET); }
function kvAll(){
  const sh = sheet(); const last = sh.getLastRow(); if (last < 1) return [];
  const v = sh.getRange(1, 1, last, Math.max(1, sh.getLastColumn())).getValues(); const rows = [];
  v.forEach((r, i) => { if (r[0]) rows.push({ row: i + 1, key: String(r[0]), value: r.slice(1).filter(x => x !== '').map(x => String(x).slice(1)).join('') }); });
  return rows;
}
function kvGet(key){ const r = kvAll().find(x => x.key === key); return r ? r.value : null; }
function kvSet(key, value){
  const sh = sheet(); const r = kvAll().find(x => x.key === key);
  const chunks = []; for (let i = 0; i < value.length; i += CHUNK) chunks.push('x' + value.slice(i, i + CHUNK)); // "x" = aby tabuľka nebrala text ako vzorec
  const rowVals = [key].concat(chunks.length ? chunks : ['x']);
  const row = r ? r.row : sh.getLastRow() + 1;
  if (sh.getMaxColumns() < rowVals.length) sh.insertColumnsAfter(sh.getMaxColumns(), rowVals.length - sh.getMaxColumns());
  if (r) sh.getRange(row, 1, 1, sh.getMaxColumns()).clearContent();
  sh.getRange(row, 1, 1, rowVals.length).setValues([rowVals]);
}
function kvDel(key){ const r = kvAll().find(x => x.key === key); if (r) sheet().deleteRow(r.row); }
function withLock(fn){ const l = LockService.getScriptLock(); l.waitLock(15000); try { fn(); } finally { l.releaseLock(); } }

function chat(q){
  if (!ANTHROPIC_KEY) return { error: 'server nemá API kľúč' };
  const res = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post', contentType: 'application/json',
    headers: { 'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01' },
    payload: JSON.stringify({ model: MODEL, max_tokens: q.max || 1000, system: q.system || '', messages: q.messages || [] }),
    muteHttpExceptions: true
  });
  const j = JSON.parse(res.getContentText());
  if (j.error) return { error: j.error.message };
  return { text: (j.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n') };
}

/* Denný AI sync – kredo + hodnotenie pre každý profil (Spúšťače → dailySync, časovač, denne) */
function dailySync(){
  if (!ANTHROPIC_KEY) return;
  const profiles = JSON.parse(kvGet('ctp:profiles') || '[]');
  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  profiles.forEach(p => {
    try {
      const d = JSON.parse(kvGet('ctp:d:' + p.id) || '{}');
      const res = chat({ system: 'Si drsný, vtipný, ale férový tréningový parťák v appke Cvič ty pič. Píšeš po slovensky, tykáš. Čierny humor, sarkazmus, nakopávanie – ale nikdy neurážaš vzhľad, váhu ani jedlo osoby. Odpovedáš IBA JSON.',
        messages: [{ role: 'user', content: summarize(p, d) + '\n\nVráť IBA JSON: {"credo":"1–2 vety, max 200 znakov, dnešné personalizované kredo","assess":"3–5 viet úprimné zhodnotenie a jedna konkrétna vec na tento týždeň"}' }], max: 600 });
      if (!res.text) return;
      const t = res.text.replace(/```json|```/g, '');
      const j = JSON.parse(t.slice(t.indexOf('{'), t.lastIndexOf('}') + 1));
      withLock(() => kvSet('ctp:ai:' + p.id, JSON.stringify({ credo: { d: today, text: j.credo }, assess: { d: today, text: j.assess } })));
    } catch (e) {}
  });
}
function summarize(p, d){
  const logs = (d.logs || []).slice(-3).map(l => l.date + ' ' + l.session + ': ' + (l.items || []).map(i => (i.nm || i.id) + ' ' + (i.sets || []).filter(s => s.r).map(s => s.w + '×' + s.r).join(',')).join('; ')).join('\n');
  let done = 0, skip = 0; Object.keys(d.checks || {}).forEach(w => Object.keys(d.checks[w]).forEach(k => { const v = d.checks[w][k]; if (v.s === 'done') done++; if (v.s === 'skip') skip++; }));
  const meals = (d.meals || []).slice(-5).map(m => m.d + ' ' + (m.name || '') + ' ' + Math.round((m.tot || {}).kcal || 0) + ' kcal').join('; ');
  return 'OSOBA: ' + p.name + ', ' + (p.bw || '?') + ' kg, cieľ: ' + (p.goalText || p.goal || '') + '\nTRÉNINGY: hotové ' + done + ', vynechané ' + skip + '\nPOSLEDNÉ MERANIA:\n' + (logs || '—') + '\nPOSLEDNÉ JEDLÁ: ' + (meals || '—') + '\nDnes: ' + new Date().toDateString();
}
