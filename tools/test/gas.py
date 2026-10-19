# Google server (Apps Script) + vstavaná história: node tools/test/mockgas.js (8767) + python3 -m http.server 8765
# A: nový telefón bez servera → vidí vstavanú históriu (seed) · zapne server cez odkaz #srv= → seed sa nahrá (0 konfliktov)
# B: ďalší nový telefón s odkazom → stiahne to isté, nič sa nezduplikuje · B zapíše tréning → A ho stiahne · tombstone zo seedu sa drží
import asyncio, json, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'; GAS = 'http://127.0.0.1:8767/exec'
def gas(op, **kw):
    body = json.dumps(dict(key='ctp-2026', op=op, **kw)).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(GAS, data=body, headers={'Content-Type': 'text/plain'}), timeout=20).read())
async def wait_sync(pg):
    for _ in range(120):
        await pg.wait_for_timeout(250)
        if not await pg.evaluate("SRV.busy||!!syncT&&false"): 
            if await pg.evaluate("!SRV.busy"): break
    await pg.wait_for_timeout(300)
async def device(b, link):
    ctx = await b.new_context(viewport={'width': 412, 'height': 915}); pg = await ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'favicon' not in m.text else None)
    await pg.goto(link); await pg.wait_for_timeout(600)
    return pg, errs
async def main():
    urllib.request.urlopen('http://127.0.0.1:8767/_reset').read()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # A: bez servera – vstavaná história
        A, errA = await device(b, APP)
        await A.click('[data-pick="bocian"]'); await A.wait_for_timeout(300)
        cnt = await A.evaluate("[Object.values(DB.w.bocian).filter(w=>!w.deleted).length, Object.values(DB.w.bocian).filter(w=>w.deleted).length, Object.values(DB.w.thephilosopher).filter(w=>!w.deleted).length, Object.values(DB.a.bocian).filter(a=>!a.deleted).length]")
        assert cnt == [15, 2, 10, 1], cnt
        h = await A.text_content('#tab-train'); assert '15 tréningov' in h and 'Server' not in h, h
        assert (await A.get_attribute('#syncDot', 'class')) == 'dot off'
        assert gas('count')['total'] == 0
        # zapnutie servera cez odkaz pre kamošov
        await A.goto(APP + '#srv=' + urllib.request.quote(GAS, safe='')); await A.wait_for_timeout(2500)
        assert (await A.evaluate("JSON.parse(localStorage.getItem('ctp:server')).gas.url")) == GAS
        assert (await A.evaluate("location.hash")) == ''
        await A.click('[data-tab="set"]'); await A.wait_for_timeout(200)
        await A.click('#syncNow'); await A.wait_for_timeout(500); await wait_sync(A)
        st = await A.text_content('#tab-set'); assert 'Google server' in st and 'neodpovedá' not in st, st
        tot = gas('count')['total']; assert tot == 32, tot   # 27 w + 4 a + profiles.json
        files = gas('list', dir='kv/bocian/w')['files']; assert len(files) == 17, len(files)
        dirty = await A.evaluate("PROFILES.map(p=>userDirty(p.id)).reduce((a,b)=>a+b,0)"); assert dirty == 0, dirty
        legacy = await A.evaluate("Object.values(DB.w.bocian).filter(w=>w._legacy).length"); assert legacy == 0, legacy
        assert (await A.get_attribute('#syncDot', 'class')) == 'dot ok'
        # B: ďalší telefón s odkazom – stiahne, nič nezduplikuje
        B, errB = await device(b, APP + '#srv=' + urllib.request.quote(GAS, safe=''))
        await B.click('[data-pick="thephilosopher"]'); await B.wait_for_timeout(500); await wait_sync(B)
        cntB = await B.evaluate("[Object.keys(DB.w.bocian).length, Object.keys(DB.w.thephilosopher).length, Object.values(DB.w.bocian).filter(w=>w.conflict_of).length, Object.values(DB.w.bocian).filter(w=>w._dirty).length]")
        assert cntB == [17, 10, 0, 0], cntB
        assert gas('count')['total'] == 32
        # B zapíše tréning → A stiahne
        await B.click('[data-tab="train"]'); await B.wait_for_timeout(200)
        await B.click('[data-new="UA"]'); await B.wait_for_timeout(300)
        rows = B.locator('#logItems .lex').nth(0).locator('.setrow')
        await rows.nth(0).locator('[data-w]').fill('30'); await rows.nth(0).locator('[data-r]').fill('10'); await B.wait_for_timeout(300)
        await B.click('#logDone'); await B.wait_for_timeout(2000); await wait_sync(B)
        assert gas('list', dir='kv/thephilosopher/w')['files'].__len__() == 11
        await A.click('[data-tab="set"]'); await A.click('#syncNow'); await A.wait_for_timeout(500); await wait_sync(A)
        assert (await A.evaluate("Object.values(DB.w.thephilosopher).filter(w=>!w.deleted).length")) == 11
        # tombstone zo seedu ostáva mŕtvy na oboch
        dead = await A.evaluate("['ajx073bmtstqqia','t0jj9j9mtstsizc'].map(i=>!!(DB.w.bocian[i]&&DB.w.bocian[i].deleted))"); assert dead == [True, True], dead
        print('ERRORS:', errA, errB); assert not errA and not errB
        print('GAS OK'); await b.close()
asyncio.run(main())
