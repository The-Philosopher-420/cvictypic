"""Aktivity HIIT / LIIT + minihra + hlásenie „bez servera“ (lokálny režim, bez mock servera)."""
import asyncio, json, re
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:8765/index.html'

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True)
        await ctx.add_init_script("localStorage.setItem('ctp5:noseed','1')")
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE ' + m.text + ' ' + str(m.location.get('url', ''))) if m.type == 'error' and not re.search(r'status of (401|403|404|409|422)', m.text) and 'script.google.com' not in (m.text + str(m.location.get('url', ''))) else None)
        res404 = []
        pg.on('response', lambda r: res404.append(r.url) if r.status == 404 and '127.0.0.1' in r.url else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('[data-pick="thephilosopher"]'); await pg.wait_for_timeout(300)
        # bez servera → v Tréningu žiadny banner ani chyba (ticho), stav je len v Nastaveniach
        assert 'Server' not in (await pg.text_content('#tab-train')) and (await pg.get_attribute('#syncDot','class')) == 'dot off'
        # HIIT: 20 min predvolené, + stepper, popis
        await pg.click('[data-newact="HIIT"]'); await pg.wait_for_timeout(200)
        assert await pg.is_visible('#shAct') and (await pg.text_content('#actTitle')).strip() == 'HIIT'
        assert await pg.input_value('#actMin') == '20'
        await pg.click('[data-inc="actMin"]'); await pg.click('[data-inc="actMin"]')
        assert await pg.input_value('#actMin') == '22'
        await pg.fill('#actNote', '8× 30 s šprint'); await pg.click('#actStartNow'); await pg.wait_for_timeout(100)
        await pg.click('#actDone'); await pg.wait_for_timeout(300)
        acts = await pg.evaluate("Object.values(DB.a.thephilosopher)")
        assert len(acts) == 1 and acts[0]['kind'] == 'HIIT' and acts[0]['min'] == 22 and acts[0]['note'] == '8× 30 s šprint' and acts[0]['user_id'] == 'thephilosopher' and acts[0]['schema_version'] == 5 and acts[0]['start'], acts
        assert 'km' not in acts[0]
        hist = await pg.text_content('#histList'); assert 'HIIT' in hist and '22 min' in hist and '8× 30 s šprint' in hist, hist
        # LIIT: km + min + tempo
        await pg.click('[data-newact="LIIT"]'); await pg.wait_for_timeout(200)
        assert await pg.input_value('#actKm') == '3' and await pg.input_value('#actMin') == '30'
        await pg.fill('#actKm', '5.5'); await pg.fill('#actMin', '55'); await pg.fill('#actNote', 'les, svižne')
        await pg.click('#actDone'); await pg.wait_for_timeout(300)
        acts = await pg.evaluate("Object.values(DB.a.thephilosopher).sort((a,b)=>a.kind<b.kind?-1:1)")
        li = [a for a in acts if a['kind'] == 'LIIT'][0]
        assert li['km'] == 5.5 and li['min'] == 55, li
        hist = await pg.text_content('#histList'); assert 'LIIT' in hist and '5,5 km' in hist and '10,0 min/km' in hist, hist
        assert '2 aktivít' in (await pg.text_content('#tab-train'))
        # úprava existujúcej aktivity z histórie + prepnutie na HIIT zruší km
        await pg.click(f'[data-act="{li["id"]}"]'); await pg.wait_for_timeout(200)
        assert await pg.input_value('#actKm') == '5.5'
        await pg.fill('#actMin', '50'); await pg.click('#actDone'); await pg.wait_for_timeout(200)
        assert await pg.evaluate(f"DB.a.thephilosopher['{li['id']}'].min") == 50
        # validácia: 0 min a 0 km sa neuloží
        await pg.click('[data-newact="HIIT"]'); await pg.wait_for_timeout(200)
        await pg.fill('#actMin', '0'); await pg.click('#actDone'); await pg.wait_for_timeout(200)
        assert await pg.is_visible('#shAct'), 'prázdna aktivita sa nesmie uložiť'
        await pg.click('#actClose'); await pg.wait_for_timeout(200)
        assert await pg.evaluate("Object.keys(DB.a.thephilosopher).length") == 2
        # kalendár: značky H a L dnes, deň → aktivity + nové
        await pg.click('[data-tab="cal"]'); await pg.wait_for_timeout(200)
        assert await pg.locator('.day.today .m.done.H').count() == 1 and await pg.locator('.day.today .m.done.L').count() == 1
        t = await pg.evaluate("today()")
        await pg.click(f'[data-day="{t}"]'); await pg.wait_for_timeout(200)
        assert await pg.locator('#dayBody [data-dact]').count() == 2
        await pg.click('#dayNewAct'); await pg.wait_for_timeout(200)
        assert await pg.is_visible('#shAct') and await pg.input_value('#actDate') == t
        await pg.click('#actClose'); await pg.wait_for_timeout(100)
        # export obsahuje aktivity s km
        await pg.click('[data-tab="set"]'); await pg.wait_for_timeout(200)
        await pg.click('#expMe'); await pg.wait_for_timeout(300)
        md = await pg.input_value('#exTa')
        assert '### activities' in md and '· LIIT · 5.5 km · 50 min' in md and '· HIIT · 22 min' in md, md[-1500:]
        assert 'HIIT (minúty) a LIIT (km, minúty)' in md
        await pg.click('[data-close="shText"]'); await pg.wait_for_timeout(100)
        # zmazanie aktivity (bez _sha = fyzicky lokálne)
        await pg.click('[data-tab="train"]'); await pg.wait_for_timeout(200)
        await pg.click(f'[data-act="{li["id"]}"]'); await pg.wait_for_timeout(200)
        await pg.click('#actDel'); await pg.wait_for_timeout(200); await pg.click('#askYes'); await pg.wait_for_timeout(300)
        assert await pg.evaluate("Object.keys(DB.a.thephilosopher).length") == 1
        # diagnostika v nastaveniach
        await pg.click('[data-tab="set"]'); await pg.wait_for_timeout(200)
        s = await pg.text_content('#tab-set'); assert 'Diagnostika' in s and 'staré v4 dáta v tomto prehliadači: žiadne' in s and 'bez servera' in s and 'script.google.com' in s, s
        # Google server: zlá adresa → hláška, odkaz pre kamošov #srv= → uloží sa adresa
        await pg.fill('#gasUrl', 'https://example.com/nie'); await pg.click('#gasSave'); await pg.wait_for_timeout(200)
        assert 'exec' in (await pg.text_content('#srvStatus')) and not (await pg.evaluate("localStorage.getItem('ctp:server')"))
        await pg.fill('#gasUrl', 'https://app.x/#srv=https%3A%2F%2Fscript.google.com%2Fmacros%2Fs%2FABC%2Fexec'); await pg.click('#gasSave'); await pg.wait_for_timeout(1500)
        cfg = await pg.evaluate("JSON.parse(localStorage.getItem('ctp:server'))"); assert cfg['gas']['url'] == 'https://script.google.com/macros/s/ABC/exec', cfg
        await pg.click('summary:has-text("Nastavenie servera")'); await pg.wait_for_timeout(200)
        await pg.fill('#gasUrl', ''); await pg.click('#gasSave'); await pg.wait_for_timeout(300)
        assert not (await pg.evaluate("localStorage.getItem('ctp:server')"))
        # vloženie celého odkazu pre kamošov do poľa token → repo + token sa rozparsujú (server mock nebeží → „neodpovedá“, ale konfigurácia sa uloží)
        await pg.click('summary:has-text("GitHub repozitár s tokenom")'); await pg.wait_for_timeout(200)
        await pg.fill('#ghRepo', ''); await pg.fill('#ghTok', 'https://x.y/app/#gh=o%2Fr&t=tok123')
        await pg.click('#srvSave'); await pg.wait_for_timeout(1500)
        cfg = await pg.evaluate("JSON.parse(localStorage.getItem('ctp:server'))")
        assert cfg['gh']['owner'] == 'o' and cfg['gh']['repo'] == 'r' and cfg['gh']['token'] == 'tok123', cfg
        # minihra: 3 ťuky na logo
        await pg.click('[data-tab="train"]'); await pg.wait_for_timeout(100)
        for _ in range(3): await pg.click('#logo')
        await pg.wait_for_timeout(600)
        assert await pg.is_visible('#game'), 'minihra sa má otvoriť'
        await pg.evaluate("(()=>{const c=$('gc');c.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));})()")
        await pg.wait_for_timeout(400)
        await pg.click('#gclose'); await pg.wait_for_timeout(200)
        assert not await pg.is_visible('#game')
        print('ERRORS:', errs, '404:', res404); assert not errs and not res404
        print('ACTS OK'); await b.close()
asyncio.run(main())
