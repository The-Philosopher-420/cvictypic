# Nové profily (jakub_d10, Fiňak): starý telefón s 3 profilmi ich dostane a pošle na server; nový telefón cez odkaz ich vidí hneď vo výbere;
# zápis nového kamoša ide len pod neho (kv/finak/…), ostatní nič nestratia. Spustenie: http.server 8765 + node tools/test/mockgas.js
import asyncio, json, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'; GAS = 'http://127.0.0.1:8767/exec'
LINK = APP + '#srv=' + urllib.request.quote(GAS, safe='')
def gas(op, **kw):
    body = json.dumps(dict(key='ctp-2026', op=op, **kw)).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(GAS, data=body, headers={'Content-Type': 'text/plain'}), timeout=20).read())
async def idle(pg):
    for _ in range(160):
        await pg.wait_for_timeout(250)
        if await pg.evaluate("!SRV.busy&&!syncQueued"): break
    await pg.wait_for_timeout(300)
OLD3 = """if(!localStorage.getItem('ctp5:profiles'))localStorage.setItem('ctp5:profiles',JSON.stringify([{id:'thephilosopher',name:'ThePhilosopher',dia:true,goalMonth:16,created:'2026-08-20'},{id:'bocian',name:'BociaN',dia:false,goalMonth:16,created:'2026-08-20'},{id:'agiraa',name:'Agiraa',dia:false,goalMonth:16,created:'2026-08-20'}]))"""
async def main():
    urllib.request.urlopen('http://127.0.0.1:8767/_reset').read()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # A: starý telefón (3 profily, prihlásený Xavier) zapne server
        ca = await b.new_context(viewport={'width': 412, 'height': 915}); await ca.add_init_script(OLD3 + ";localStorage.setItem('ctp:me',JSON.stringify('thephilosopher'))")
        A = await ca.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto(LINK); await A.wait_for_timeout(600); await idle(A)
        ids = await A.evaluate("PROFILES.map(p=>p.id)")
        assert ids == ['thephilosopher', 'bocian', 'agiraa', 'jakub_d10', 'finak'], ids
        srv = json.loads(gas('get', path='kv/profiles.json')['text'])
        assert [x['id'] for x in srv['profiles']] == ids and [x['name'] for x in srv['profiles']][-2:] == ['jakub_d10', 'Fiňak'], srv
        # B: úplne nový telefón kamoša cez odkaz → výber ukáže 5 mien, vyberie Fiňak, zapíše tréning
        cb = await b.new_context(viewport={'width': 412, 'height': 915}); B = await cb.new_page(); B.on('pageerror', lambda e: errs.append(str(e)))
        await B.goto(LINK); await B.wait_for_timeout(600); await idle(B)
        names = await B.eval_on_selector_all('#pickGrid [data-pick]', 'els=>els.map(e=>e.textContent)')
        assert names == ['ThePhilosopher', 'BociaN', 'Agiraa', 'jakub_d10', 'Fiňak'], names
        await B.click('[data-pick="finak"]'); await B.wait_for_timeout(300)
        h = await B.text_content('#tab-train'); assert '0 tréningov' in h, h
        assert (await B.text_content('#hName')) == 'Fiňak'
        await B.click('[data-new="UA"]'); await B.wait_for_timeout(300)
        rows = B.locator('#logItems .lex').nth(0).locator('.setrow')
        await rows.nth(0).locator('[data-w]').fill('20'); await rows.nth(0).locator('[data-r]').fill('12'); await B.wait_for_timeout(300)
        await B.click('#logDone'); await B.wait_for_timeout(1500); await idle(B)
        fw = gas('list', dir='kv/finak/w')['files']; assert len(fw) == 1, fw
        rec = json.loads(gas('get', path='kv/finak/w/' + fw[0]['name'])['text'])
        assert rec['user_id'] == 'finak' and all(e['user_id'] == 'finak' for e in rec['entries']), rec
        assert gas('list', dir='kv/jakub_d10/w')['files'] == []
        assert len(gas('list', dir='kv/thephilosopher/w')['files']) == 10 and len(gas('list', dir='kv/bocian/w')['files']) == 17
        # A stiahne Fiňakov tréning pod Fiňaka, Xavierova história nezmenená
        await A.evaluate("syncAll('manual')"); await idle(A)
        st = await A.evaluate("[Object.keys(DB.w.finak||{}).length, Object.values(DB.w.thephilosopher).filter(w=>!w.deleted).length, dirtyCount()]")
        assert st == [1, 10, 0], st
        print('ERRORS:', errs); assert not errs
        print('NEWPROF OK'); await b.close()
asyncio.run(main())
