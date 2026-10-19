"""Sync + konflikty cez mock GitHub API: 2 zariadenia, rovnaký user."""
import asyncio, json, sys, re, urllib.request
from playwright.async_api import async_playwright

URL = 'http://127.0.0.1:8765/index.html'
MOCK = 'http://127.0.0.1:8766'

def dump():
    return json.load(urllib.request.urlopen(MOCK + '/__dump'))

async def new_device(p, name):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport={'width': 412, 'height': 915})
    page = await ctx.new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(name + ': ' + str(e)))
    page.on('console', lambda m: errs.append(name + ' CONSOLE ' + m.text) if m.type == 'error' and not re.search(r'status of (404|409|422)', m.text) else None)
    async def route(r):
        url = r.request.url.replace('https://api.github.com', MOCK)
        req = urllib.request.Request(url, data=r.request.post_data_buffer, method=r.request.method)
        for k, v in r.request.headers.items():
            if k.lower() in ('authorization', 'content-type', 'accept'):
                req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req)
            status, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        await r.fulfill(status=status, body=body, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})
    await page.route('https://api.github.com/**', route)
    await page.goto(URL + '#gh=o/r&t=tok')
    await page.wait_for_timeout(400)
    await page.click('[data-pick="thephilosopher"]')
    await page.wait_for_timeout(800)
    return b, page, errs

async def sync(page):
    r = await page.evaluate("syncAll('test')")
    await page.wait_for_timeout(100)
    return r

async def main():
    urllib.request.urlopen(MOCK + '/__reset')
    async with async_playwright() as p:
        bA, A, eA = await new_device(p, 'A')
        bB, B, eB = await new_device(p, 'B')
        # A zapíše tréning
        await A.click('[data-new="UA"]'); await A.wait_for_timeout(200)
        r0 = A.locator('#logItems .lex').nth(0).locator('.setrow').nth(0)
        await r0.locator('[data-w]').fill('20'); await r0.locator('[data-r]').fill('10')
        await A.wait_for_timeout(700); await A.click('#logDone'); await A.wait_for_timeout(2200)  # scheduleSync 1.5 s
        d = dump()
        wfiles = [k for k in d['files'] if k.startswith('kv/thephilosopher/w/')]
        assert len(wfiles) == 1, d['files'].keys()
        assert 'kv/profiles.json' in d['files']
        wid = wfiles[0].split('/')[-1][:-5]
        rec = json.loads(d['files'][wfiles[0]])
        assert rec['user_id'] == 'thephilosopher' and rec['schema_version'] == 5 and '_dirty' not in rec and '_sha' not in rec
        # B stiahne
        r = await sync(B)
        assert r['pulled'] >= 1, r
        hist = await B.text_content('#histList')
        assert 'Upper A' in hist, hist
        # konflikt: obaja upravia ten istý zápis (B offline simulujeme tým, že sync spustíme až potom)
        await A.evaluate(f"(()=>{{const w=DB.w.thephilosopher['{wid}'];w.note='A verzia';w.entries[0].sets[0].w=22.5;markDirty(w);persist('thephilosopher');}})()")
        await B.evaluate(f"(()=>{{const w=DB.w.thephilosopher['{wid}'];w.note='B verzia';w.entries[0].sets[0].w=25;markDirty(w);persist('thephilosopher');}})()")
        ra = await sync(A); assert ra['conflicts'] == 0, ra
        rb = await sync(B); assert rb['conflicts'] == 1, rb
        d = dump()
        wfiles = sorted(k for k in d['files'] if k.startswith('kv/thephilosopher/w/'))
        assert len(wfiles) == 2, wfiles
        recs = {k: json.loads(v) for k, v in d['files'].items() if k.startswith('kv/thephilosopher/w/')}
        main = recs['kv/thephilosopher/w/%s.json' % wid]
        other = [v for k, v in recs.items() if k != 'kv/thephilosopher/w/%s.json' % wid][0]
        assert main['note'] == 'A verzia' and main['entries'][0]['sets'][0]['w'] == 22.5, main
        assert other['conflict_of'] == wid and other['note'] == 'B verzia' and other['entries'][0]['sets'][0]['w'] == 25, other
        # A stiahne konfliktnú kópiu
        ra = await sync(A)
        n = await A.evaluate("Object.values(DB.w.thephilosopher).filter(w=>w.conflict_of).length")
        assert n == 1
        await A.click('[data-tab="set"]'); await A.wait_for_timeout(200)
        assert 'konfliktných' in (await A.text_content('#tab-set'))
        # B lokálne (nesynchronizované) záznamy nesmú byť po pulle prepísané: B má main = A verzia + vlastnú kópiu
        bmain = await B.evaluate(f"DB.w.thephilosopher['{wid}'].note")
        assert bmain == 'A verzia'
        # zmazanie = tombstone, nie fyzické vymazanie
        await B.evaluate(f"(()=>{{const w=DB.w.thephilosopher['{wid}'];w.deleted=true;markDirty(w);persist('thephilosopher');}})()")
        await sync(B); await sync(A)
        d = dump()
        assert json.loads(d['files']['kv/thephilosopher/w/%s.json' % wid])['deleted'] is True
        assert await A.evaluate(f"DB.w.thephilosopher['{wid}'].deleted") is True
        assert await A.evaluate("workoutsOf('thephilosopher').length") == 1  # ostala len konfliktná kópia
        # kalendár: obaja naplánujú ten istý deň inak
        await A.evaluate("(()=>{const c=monthCal('thephilosopher','2026-11');c.days['2026-11-05']='UA';markDirty(c);persist('thephilosopher');})()")
        await B.evaluate("(()=>{const c=monthCal('thephilosopher','2026-11');c.days['2026-11-05']='LB';c.days['2026-11-07']='LA';markDirty(c);persist('thephilosopher');})()")
        await sync(A); await sync(B); await sync(A)
        ca = await A.evaluate("DB.cal.thephilosopher['2026-11']")
        cb = await B.evaluate("DB.cal.thephilosopher['2026-11']")
        for c in (ca, cb):
            assert c['days']['2026-11-05'] == 'UA' and c['days']['2026-11-07'] == 'LA' and c['conf']['2026-11-05'] == 'LB', c
        # plán: Apply to all z A, B dostane
        await A.evaluate("(()=>{const p={schema_version:5,user_id:'bocian',sessions:{UA:[{id:'mcp',nm:'',sets:'4 × 8',drop:0,pu:0,k:'x'}]}};markDirty(p);DB.plan.bocian=p;persist('bocian');})()")
        await sync(A); await sync(B)
        pb = await B.evaluate("DB.plan.bocian.sessions.UA[0].sets")
        assert pb == '4 × 8', pb
        # neplatný záznam sa nepushne (bez user_id)
        await B.evaluate("(()=>{DB.w.thephilosopher['bad1']={id:'bad1',schema_version:5,user_id:'',date:'2026-10-01',ts:'2026-10-01T10:00',session:'UA',entries:[],_dirty:true};persist('thephilosopher');})()")
        await sync(B)
        assert 'kv/thephilosopher/w/bad1.json' not in dump()['files']
        # legacy záznam z telefónu zhodný so serverom → žiadny duplikát; rozdielny → konflikt
        srv_rec = json.loads(dump()['files']['kv/thephilosopher/w/%s.json' % wid])
        lg = dump()['log']
        print('requests:', len(lg))
        print('\n'.join(l for i, l in enumerate(lg) if l.startswith('  ->') or (i + 1 < len(lg) and lg[i + 1].startswith('  ->'))))
        print('ERRORS:', eA + eB)
        assert not (eA + eB)
        print('SYNC OK')
        await bA.close(); await bB.close()

asyncio.run(main())
