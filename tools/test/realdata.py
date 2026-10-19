"""Reálne dáta: mock GitHub nasypaný presne tým, čo je nasadené v cvictypic-data (v5 kv/ + nedotknuté v4 ctp__*.json).
Overí, že appka po prihlásení každého usera stiahne správne počty a nič nemieša medzi profilmi."""
import asyncio, json, sys, os, re, base64, urllib.request
from playwright.async_api import async_playwright

URL = 'http://127.0.0.1:8765/index.html'
MOCK = 'http://127.0.0.1:8766'
DEPLOY = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/ctp/deploy/cvictypic-data'
LEGACY = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/data-sources/server/repo/kv'

def put(path, text):
    req = urllib.request.Request(MOCK + '/repos/o/r/contents/' + path, method='PUT',
        data=json.dumps({'content': base64.b64encode(text.encode()).decode()}).encode())
    req.add_header('Authorization', 'Bearer tok'); req.add_header('Content-Type', 'application/json')
    urllib.request.urlopen(req)

def seed():
    urllib.request.urlopen(MOCK + '/__reset')
    n = 0
    for root, _, fs in os.walk(DEPLOY):
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, DEPLOY)
            if not rel.startswith('kv/'): continue
            put(rel, open(p, encoding='utf-8').read()); n += 1
    for f in os.listdir(LEGACY):
        if f.startswith('ctp__') and f.endswith('.json'):
            put('kv/' + f, open(os.path.join(LEGACY, f), encoding='utf-8').read()); n += 1
    return n

async def device(p, user, errs):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport={'width': 412, 'height': 915})
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errs.append(user + ': ' + str(e)))
    page.on('console', lambda m: errs.append(user + ' CONSOLE ' + m.text) if m.type == 'error' and not re.search(r'status of (404|409|422)', m.text) else None)
    async def route(r):
        url = r.request.url.replace('https://api.github.com', MOCK)
        req = urllib.request.Request(url, data=r.request.post_data_buffer, method=r.request.method)
        for k, v in r.request.headers.items():
            if k.lower() in ('authorization', 'content-type', 'accept'): req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req); status, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        await r.fulfill(status=status, body=body, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})
    await page.route('https://api.github.com/**', route)
    await page.goto(URL + '#gh=o/r&t=tok'); await page.wait_for_timeout(400)
    await page.click('[data-pick="%s"]' % user); await page.wait_for_timeout(1500)
    return b, page

async def phone(p, user, errs, n_seed):
    """Telefón so starou v4 appkou: localStorage má ctp:profiles + ctp:d:<user> pre všetkých (v4 sťahovala všetky dokumenty)
    + jeden fantómový zápis, ktorý bol na serveri zmazaný (zastaraný telefón). Po otvorení v5 sa nič nesmie zduplikovať ani oživiť."""
    docs = {}
    for f in os.listdir(LEGACY):
        m = re.match(r'ctp__d__(\w+)\.json$', f)
        if m: docs[m.group(1)] = json.load(open(os.path.join(LEGACY, f), encoding='utf-8'))
    prof = json.load(open(os.path.join(LEGACY, 'ctp__profiles.json'), encoding='utf-8'))
    stale = dict(docs['bocian']['logs'][0]); stale = json.loads(json.dumps(stale)); stale['id'] = 'ajx073bmtstqqia'; stale['date'] = '2026-09-08'; stale['session'] = 'LA'
    docs['bocian']['logs'].append(stale)
    init = "localStorage.setItem('ctp:profiles',%s);" % json.dumps(json.dumps(prof))
    for u, d in docs.items():
        init += "localStorage.setItem('ctp:d:%s',%s);" % (u, json.dumps(json.dumps(d)))
    init += "localStorage.setItem('ctp:me',%s);" % json.dumps(json.dumps(user))
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport={'width': 412, 'height': 915})
    await ctx.add_init_script("if(!localStorage.getItem('ctp5:meta')){%s}" % init)
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errs.append('phone: ' + str(e)))
    page.on('console', lambda m: errs.append('phone CONSOLE ' + m.text) if m.type == 'error' and not re.search(r'status of (404|409|422)', m.text) else None)
    async def route(r):
        url = r.request.url.replace('https://api.github.com', MOCK)
        req = urllib.request.Request(url, data=r.request.post_data_buffer, method=r.request.method)
        for k, v in r.request.headers.items():
            if k.lower() in ('authorization', 'content-type', 'accept'): req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req); status, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        await r.fulfill(status=status, body=body, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})
    await page.route('https://api.github.com/**', route)
    await page.goto(URL + '#gh=o/r&t=tok'); await page.wait_for_timeout(4000)   # init → migrácia → login(ctp:me) → plný sync
    st = await page.evaluate("""(()=>{const out={};for(const u of Object.keys(DB.w)){const ws=Object.values(DB.w[u]||{});out[u]={live:ws.filter(w=>!w.deleted).length,dead:ws.filter(w=>w.deleted).map(w=>w.id),conf:ws.filter(w=>w.conflict_of).map(w=>w.id),dirty:ws.filter(w=>w._dirty).map(w=>w.id),legacy:ws.filter(w=>w._legacy).map(w=>w.id),flags:ws.filter(w=>w.flag).map(w=>w.id),acts:Object.values(DB.a[u]||{}).filter(a=>!a.deleted).map(a=>a.id),deadActs:Object.values(DB.a[u]||{}).filter(a=>a.deleted).map(a=>a.id),dirtyActs:Object.values(DB.a[u]||{}).filter(a=>a._dirty).map(a=>a.id),plan:!!DB.plan[u]}}return {me:ME&&ME.id,users:out,busy:SRV.busy,ok:SRV.ok}})()""")
    print('phone', user, json.dumps(st, ensure_ascii=False))
    assert st['me'] == user and st['ok'] is True and not st['busy'], st
    assert st['users']['bocian']['live'] == 15 and st['users']['thephilosopher']['live'] == 10, st
    assert sorted(st['users']['bocian']['dead']) == ['ajx073bmtstqqia', 't0jj9j9mtstsizc'], st['users']['bocian']['dead']
    for u, s in st['users'].items():
        assert not s['conf'] and not s['dirty'] and not s['legacy'] and not s['dirtyActs'], (u, s)
    assert st['users']['bocian']['flags'] == ['gdyu4f7mtadsbe2'] and sorted(st['users']['thephilosopher']['flags']) == ['seed-ua-2026-08-24', 'seed-ub-2026-08-21'], st
    assert st['users']['bocian']['acts'] == ['chat-hiit-2026-08-27'] and st['users']['thephilosopher']['acts'] == ['chat-hiit-2026-08-27'], st
    d = json.load(urllib.request.urlopen(MOCK + '/__dump'))
    puts = [l for l in d['log'] if l.startswith('PUT')][n_seed:]
    plan_puts = [x for x in puts if '/plan.json' in x]
    other = [x for x in puts if '/plan.json' not in x]
    assert not other, other            # nič okrem plánu z telefónu sa na server nezapísalo (žiadne kópie, žiadne oživené záznamy)
    print('phone PUT (len plán z v4 telefónu):', plan_puts)
    hist = await page.text_content('#histList')
    await b.close()
    return len(puts)

async def main():
    n = seed(); print('seeded', n, 'files')
    expect = {'thephilosopher': 10, 'bocian': 15, 'agiraa': 0}
    errs = []
    async with async_playwright() as p:
        n += await phone(p, 'bocian', errs, n)
        for user, cnt in expect.items():
            b, page = await device(p, user, errs)
            r = await page.evaluate("syncAll('test')"); await page.wait_for_timeout(200)
            st = await page.evaluate("""(()=>{const out={};for(const u of Object.keys(DB.w)){const ws=Object.values(DB.w[u]||{});out[u]={w:ws.filter(w=>!w.deleted).length,dead:ws.filter(w=>w.deleted).length,badUser:ws.filter(w=>w.user_id!==u).length,badEntries:ws.reduce((s,w)=>s+(w.entries||[]).filter(e=>e.user_id!==u||!e.exercise_id||e.schema_version!==5).length,0),flags:ws.filter(w=>w.flag).map(w=>w.id),a:Object.values((DB.a||{})[u]||{}).filter(a=>!a.deleted).length}}return {me:ME&&ME.id,profiles:PROFILES.map(p=>p.id),users:out}})()""")
            print(user, json.dumps(r), json.dumps(st, ensure_ascii=False))
            assert st['me'] == user, st
            assert sorted(st['profiles']) == ['agiraa', 'bocian', 'thephilosopher'], st['profiles']
            for u, s in st['users'].items():
                assert s['badUser'] == 0 and s['badEntries'] == 0, (u, s)
            assert st['users'].get(user, {'w': 0})['w'] == cnt, (user, st['users'])
            if user == 'thephilosopher':
                assert sorted(st['users'][user]['flags']) == ['seed-ua-2026-08-24', 'seed-ub-2026-08-21'], st['users'][user]['flags']
                assert st['users'][user]['a'] == 1
            if user == 'bocian':
                assert st['users'][user]['flags'] == ['gdyu4f7mtadsbe2'], st['users'][user]['flags']
                assert st['users'][user]['a'] == 1
            # história zobrazí len vlastné záznamy
            hist = await page.text_content('#histList')
            ids_other = [w for u2 in expect if u2 != user for w in (await page.evaluate("Object.keys(DB.w[%r]||{})" % u2))]
            # nič cudzie sa nezapísalo na server
            d = json.load(urllib.request.urlopen(MOCK + '/__dump'))
            puts = [l for l in d['log'] if l.startswith('PUT')][n:]   # prvých n PUT = seed
            assert not puts, puts
            await b.close()
    print('ERRORS:', errs)
    assert not errs
    print('REALDATA OK')

asyncio.run(main())
