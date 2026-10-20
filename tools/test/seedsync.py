# Vstavaná história + Google server, 2 telefóny, ktoré pred zapnutím servera menili históriu offline.
# Spustenie: python3 -m http.server 8765 (v cvictypic/) + node tools/test/mockgas.js (8767)
# A (Xavier): upraví svoj starý tréning X, zmaže Matejov duplikát Y (v5.2.0 štýlom = fyzicky), zapíše nový tréning → zapne server prvý.
# B (Matej, ešte z v5.2.0 bez _seedh): upraví svoj starý tréning Z, rovnaký záznam W upravia obaja inak → zapne server.
# Očakávanie: 0 falošných konfliktov, A-úprava X a B-úprava Z platia všade, Y zmazaný všade, W = presne 1 konflikt (obe verzie), nič nestratené.
import asyncio, json, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'; GAS = 'http://127.0.0.1:8767/exec'
LINK = APP + '#srv=' + urllib.request.quote(GAS, safe='')
X, Y, Z = 'seed-ua-2026-08-24', 'gdyu4f7mtadsbe2', None
def gas(op, **kw):
    body = json.dumps(dict(key='ctp-2026', op=op, **kw)).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(GAS, data=body, headers={'Content-Type': 'text/plain'}), timeout=20).read())
async def idle(pg):
    for _ in range(160):
        await pg.wait_for_timeout(250)
        if await pg.evaluate("!SRV.busy&&!syncQueued"): break
    await pg.wait_for_timeout(400)
async def device(b, user):
    ctx = await b.new_context(viewport={'width': 412, 'height': 915}); pg = await ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    await pg.goto(APP); await pg.wait_for_timeout(700)
    await pg.click(f'[data-pick="{user}"]'); await pg.wait_for_timeout(300)
    return pg, errs
EDIT = "(([u,id,w])=>{const r=DB.w[u][id];r.entries[0].sets[0].w=w;markDirty(r);persist(u);})"
async def main():
    urllib.request.urlopen('http://127.0.0.1:8767/_reset').read()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        A, eA = await device(b, 'thephilosopher')
        B, eB = await device(b, 'bocian')
        z = await B.evaluate("Object.values(DB.w.bocian).filter(w=>!w.deleted&&w.date==='2026-09-11')[0].id")
        w = await B.evaluate("Object.values(DB.w.bocian).filter(w=>!w.deleted&&w.date==='2026-09-14')[0].id")
        # B simuluje telefón z v5.2.0: kópie bez _seedh, seedTag chýba → po reloade sa označia
        await B.evaluate("(()=>{PROFILES.forEach(p=>{['w','a'].forEach(k=>Object.values(DB[k][p.id]).forEach(r=>delete r._seedh));persist(p.id);});const m=LS.get(K.meta);delete m.seedTag;LS.set(K.meta,m);})()")
        await B.reload(); await B.wait_for_timeout(800)
        assert await B.evaluate("Object.values(DB.w.bocian).every(r=>r._seedh!=null)"), 'tagovanie'
        # A: úprava X (svoj), fyzické zmazanie Y (ako v5.2.0) + reload → má vzniknúť náhrobok, úprava W, nový tréning
        await A.evaluate(EDIT + "(['thephilosopher','%s',99])" % X)
        await A.evaluate(EDIT + "(['bocian','%s',77])" % w)
        await A.evaluate("(()=>{delete DB.w.bocian['%s'];persist('bocian');const m=LS.get(K.meta);delete m.seedTag;LS.set(K.meta,m);})()" % Y)
        await A.reload(); await A.wait_for_timeout(800)
        assert await A.evaluate("!!(DB.w.bocian['%s']&&DB.w.bocian['%s'].deleted)" % (Y, Y)), 'náhrobok pre fyzicky zmazanú históriu'
        await A.click('[data-new="UB"]'); await A.wait_for_timeout(300)
        rows = A.locator('#logItems .lex').nth(0).locator('.setrow')
        await rows.nth(0).locator('[data-w]').fill('61'); await rows.nth(0).locator('[data-r]').fill('9'); await A.wait_for_timeout(300)
        await A.click('#logDone'); await A.wait_for_timeout(300)
        # B: úprava Z, iná úprava W; zmazanie cez UI (seed záznam bez _sha → náhrobok, nie fyzické zmazanie)
        await B.evaluate(EDIT + "(['bocian','%s',88])" % z)
        await B.evaluate(EDIT + "(['bocian','%s',66])" % w)
        # A zapína server prvý
        await A.goto(LINK); await A.wait_for_timeout(500); await idle(A)
        assert await A.evaluate("dirtyCount()") == 0
        assert gas('count')['total'] == 33, gas('count')   # 27 + 4 + profiles + nový tréning
        # B zapína server
        await B.goto(LINK); await B.wait_for_timeout(500); await idle(B)
        await B.evaluate("syncAll('manual')"); await idle(B)
        await A.evaluate("syncAll('manual')"); await idle(A)
        for pg, name in [(A, 'A'), (B, 'B')]:
            st = await pg.evaluate("""(([x,y,z,w])=>({x:DB.w.thephilosopher[x].entries[0].sets[0].w, y:!!DB.w.bocian[y].deleted, z:DB.w.bocian[z].entries[0].sets[0].w,
              w:DB.w.bocian[w].entries[0].sets[0].w, conf:PROFILES.flatMap(p=>Object.values(DB.w[p.id]).filter(r=>r.conflict_of)).map(r=>[r.conflict_of,r.entries[0].sets[0].w]),
              dirty:dirtyCount(), t:Object.values(DB.w.thephilosopher).filter(r=>!r.deleted&&!r.conflict_of).length, b:Object.values(DB.w.bocian).filter(r=>!r.deleted&&!r.conflict_of).length}))""" + "(['%s','%s','%s','%s'])" % (X, Y, z, w))
            print(name, st)
            assert st['x'] == 99 and st['y'] and st['z'] == 88 and st['dirty'] == 0, (name, st)
            assert len(st['conf']) == 1 and st['conf'][0][0] == w and {st['w'], st['conf'][0][1]} == {66, 77}, (name, st)
            assert st['t'] == 11 and st['b'] == 14, (name, st)   # A: 10 + nový; B: 15 − Y
        srv = gas('get', path='kv/bocian/w/%s.json' % Y); assert json.loads(srv['text'])['deleted'] is True
        print('ERRORS:', eA, eB); assert not eA and not eB
        print('SEEDSYNC OK'); await b.close()
asyncio.run(main())
