# Alexov iPhone (22. 11.): „píše zlý github token“ – odkaz na Google server sa dostal do poľa GitHub token.
# A: telefón s pokazeným uloženým nastavením (GitHub token = odkaz) → appka sa sama opraví, pripojí Google server, Alex vidí svoje meno
# B: GitHub token aj Google server uložené naraz → používa sa Google server (bez chyby)
# C: nový telefón: vybrať meno → Nastavenia → vložiť odkaz do (jediného) poľa → funguje; GitHub sekcia sa neukazuje
# GitHub API je v teste podvrhnuté na 401 (zlý token). Spustenie: http.server 8765 + node tools/test/mockgas.js
import asyncio, json, sys, urllib.request
from playwright.async_api import async_playwright
APP = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765/index.html'
GAS = 'http://127.0.0.1:8767/exec'; LINK = 'http://127.0.0.1:8765/index.html#srv=' + urllib.request.quote(GAS, safe='')
def gas(op, **kw):
    body = json.dumps(dict(key='ctp-2026', op=op, **kw)).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(GAS, data=body, headers={'Content-Type': 'text/plain'}), timeout=20).read())
PROFS = [{'id': 'thephilosopher', 'name': 'ThePhilosopher', 'dia': True, 'goalMonth': 16}, {'id': 'bocian', 'name': 'maťuvka', 'dia': False, 'goalMonth': 16},
         {'id': 'agiraa', 'name': 'Agiraa', 'dia': False, 'goalMonth': 16}, {'id': 'jakub_d10', 'name': 'jakub_d10', 'dia': False, 'goalMonth': 16},
         {'id': 'finak', 'name': 'Fiňak', 'dia': False, 'goalMonth': 16}, {'id': 'n3flex_g0d', 'name': 'N3flex_g0d', 'dia': False, 'goalMonth': 16}]
async def idle(pg):
    for _ in range(160):
        await pg.wait_for_timeout(250)
        if await pg.evaluate("!SRV.busy&&(typeof syncQueued==='undefined'||!syncQueued)"): break
    await pg.wait_for_timeout(300)
async def device(b, init=None):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844})
    await ctx.route('https://api.github.com/**', lambda r: r.fulfill(status=401, body='{"message":"Bad credentials"}', headers={'Access-Control-Allow-Origin': '*'}))
    if init: await ctx.add_init_script(init)
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(APP); await pg.wait_for_timeout(800); await idle(pg)
    return pg, errs
async def state(pg):
    return await pg.evaluate("({ok:SRV.ok,err:SRV.lastErr,gh:!!SRV.gh,gas:SRV.gas&&SRV.gas.url,names:PROFILES.map(p=>p.name),dot:document.getElementById('syncDot').className,me:ME&&ME.id})")
async def main():
    urllib.request.urlopen('http://127.0.0.1:8767/_reset').read()
    assert 'sha' in gas('put', path='kv/profiles.json', text=json.dumps({'schema_version': 5, 'profiles': PROFS}))
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        # A: pokazené uložené nastavenie z Alexovho telefónu
        bad = json.dumps({'gh': {'owner': 'The-Philosopher-420', 'repo': 'cvictypic-data', 'token': LINK}})
        A, e = await device(b, "if(!localStorage.getItem('ctp5:meta')){localStorage.setItem('ctp:server',%s);localStorage.setItem('ctp:me',JSON.stringify('agiraa'));}" % json.dumps(bad)); allerr += e
        st = await state(A); print('A', st)
        assert st['ok'] is True and not st['gh'] and st['gas'] == GAS and 'N3flex_g0d' in st['names'] and 'zlý' not in (st['err'] or ''), st
        assert st['dot'] == 'dot ok', st
        await A.click('[data-tab="set"]'); await A.wait_for_timeout(300)
        s = await A.text_content('#tab-set'); assert 'zlý' not in s and 'Google server' in s and 'GitHub repozitár' not in s, s
        await A.click('#setSwitch'); await A.wait_for_timeout(300); await A.click('[data-pick="n3flex_g0d"]'); await A.wait_for_timeout(500)
        assert (await A.text_content('#hName')) == 'N3flex_g0d'
        # B: GitHub (zlý token v tvare tokenu) + Google naraz → Google
        both = json.dumps({'gh': {'owner': 'The-Philosopher-420', 'repo': 'cvictypic-data', 'token': 'ghp_' + 'x' * 36}, 'gas': {'url': GAS, 'key': 'ctp-2026'}})
        B, e = await device(b, "if(!localStorage.getItem('ctp5:meta')){localStorage.setItem('ctp:server',%s);localStorage.setItem('ctp:me',JSON.stringify('n3flex_g0d'));}" % json.dumps(both)); allerr += e
        st = await state(B); print('B', st); assert st['ok'] is True and st['dot'] == 'dot ok' and 'N3flex_g0d' in st['names'], st
        # C: nový telefón, meno → Nastavenia → odkaz do poľa (aj omylom holý text) → funguje
        C, e = await device(b); allerr += e
        await C.click('[data-pick="agiraa"]'); await C.wait_for_timeout(300); await C.click('[data-tab="set"]'); await C.wait_for_timeout(300)
        assert not await C.query_selector('#ghTok'), 'GitHub pole sa nemá ukazovať'
        await C.fill('#gasUrl', 'nejaky zly text'); await C.click('#gasSave'); await C.wait_for_timeout(300)
        assert 'nie je odkaz' in await C.text_content('#srvStatus') and not await C.evaluate("localStorage.getItem('ctp:server')")
        await C.fill('#gasUrl', LINK); await C.click('#gasSave'); await C.wait_for_timeout(500); await idle(C)
        st = await state(C); print('C', st); assert st['ok'] is True and st['gas'] == GAS and 'N3flex_g0d' in st['names'], st
        print('ERRORS:', allerr); assert not allerr
        print('ALEXBUG OK'); await b.close()
asyncio.run(main())
