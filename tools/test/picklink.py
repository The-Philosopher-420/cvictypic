# Nová inštalácia bez servera (iPhone ikona na ploche = vlastné úložisko): vo výbere mena sa dá vložiť odkaz → pripojí server,
# stiahne profily (aj tie, čo appka v kóde nemá, napr. N3flex_g0d) → vyberie meno. Spustenie: http.server 8765 + node tools/test/mockgas.js
import asyncio, json, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'; GAS = 'http://127.0.0.1:8767/exec'
LINK = APP + '#srv=' + urllib.request.quote(GAS, safe='')
def gas(op, **kw):
    body = json.dumps(dict(key='ctp-2026', op=op, **kw)).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(GAS, data=body, headers={'Content-Type': 'text/plain'}), timeout=20).read())
PROFS = [{'id': 'thephilosopher', 'name': 'ThePhilosopher', 'dia': True, 'goalMonth': 16}, {'id': 'bocian', 'name': 'maťuvka', 'dia': False, 'goalMonth': 16, 'updated': 1},
         {'id': 'agiraa', 'name': 'Agiraa', 'dia': False, 'goalMonth': 16}, {'id': 'jakub_d10', 'name': 'jakub_d10', 'dia': False, 'goalMonth': 16},
         {'id': 'finak', 'name': 'Fiňak', 'dia': False, 'goalMonth': 16}, {'id': 'n3flex_g0d', 'name': 'N3flex_g0d', 'dia': False, 'goalMonth': 16}]
async def main():
    urllib.request.urlopen('http://127.0.0.1:8767/_reset').read()
    assert 'sha' in gas('put', path='kv/profiles.json', text=json.dumps({'schema_version': 5, 'profiles': PROFS}))
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await (await b.new_context(viewport={'width': 390, 'height': 844})).new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(APP); await pg.wait_for_timeout(800)
        names = await pg.eval_on_selector_all('#pickGrid [data-pick]', 'els=>els.map(e=>e.textContent)')
        assert 'N3flex_g0d' not in names and await pg.is_visible('#pickUrl'), names
        await pg.fill('#pickUrl', 'blabla'); await pg.click('#pickGo'); await pg.wait_for_timeout(300)
        assert 'nie je odkaz' in await pg.text_content('#pickSt'); assert not await pg.evaluate("srvOn()")
        await pg.fill('#pickUrl', LINK); await pg.click('#pickGo')
        for _ in range(120):
            await pg.wait_for_timeout(250)
            if not await pg.is_visible('#pickUrl'): break
        await pg.wait_for_timeout(300)
        names = await pg.eval_on_selector_all('#pickGrid [data-pick]', 'els=>els.map(e=>e.textContent)')
        print('mená po vložení odkazu:', names)
        assert names == ['ThePhilosopher', 'maťuvka', 'Agiraa', 'jakub_d10', 'Fiňak', 'N3flex_g0d'], names
        assert (await pg.evaluate("JSON.parse(localStorage.getItem('ctp:server')).gas.url")) == GAS
        await pg.click('[data-pick="n3flex_g0d"]'); await pg.wait_for_timeout(500)
        assert (await pg.text_content('#hName')) == 'N3flex_g0d' and '0 tréningov' in await pg.text_content('#tab-train')
        # ďalší štart: server ostáva, pole na odkaz sa už neukazuje
        await pg.reload(); await pg.wait_for_timeout(600)
        assert (await pg.text_content('#hName')) == 'N3flex_g0d'
        print('ERRORS:', errs); assert not errs
        print('PICKLINK OK'); await b.close()
asyncio.run(main())
