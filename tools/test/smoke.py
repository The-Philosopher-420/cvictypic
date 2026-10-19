"""Smoke test v lokálnom režime (bez servera): výber usera → zápis → kalendár → export/import."""
import asyncio, json, sys, re
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765/index.html'

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 412, 'height': 915}, device_scale_factor=2, is_mobile=True, has_touch=True)
        await ctx.add_init_script("localStorage.setItem('ctp5:noseed','1')")
        page = await ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append('CONSOLE ' + m.text) if m.type == 'error' else None)
        await page.goto(URL)
        await page.wait_for_timeout(500)
        # výber používateľa
        assert await page.is_visible('#shPick'), 'má sa zobraziť výber používateľa'
        await page.click('[data-pick="bocian"]')
        await page.wait_for_timeout(200)
        assert (await page.text_content('#hName')).strip() == 'BociaN'
        # nový zápis LA
        await page.click('[data-new="LA"]')
        await page.wait_for_timeout(200)
        assert await page.is_visible('#shLog')
        names = await page.eval_on_selector_all('#logItems .lex input.nm', 'els=>els.map(e=>e.value)')
        assert names[0].startswith('Hack squat'), names
        assert any('Cable crunch' in n for n in names), 'Matej má mať brucho (std core)'
        # zapíš 2 série hack squat
        rows = page.locator('#logItems .lex').nth(0).locator('.setrow')
        await rows.nth(0).locator('[data-w]').fill('20')
        await rows.nth(0).locator('[data-r]').fill('10')
        await rows.nth(1).locator('[data-w]').fill('20')
        await rows.nth(1).locator('[data-r]').fill('8')
        await rows.nth(1).locator('[data-drop]').click()
        await page.click('#startNow')
        await page.wait_for_timeout(700)
        st = await page.text_content('#logState')
        assert 'uložené' in st, st
        await page.click('#endNow')
        await page.wait_for_timeout(700)
        await page.click('#logDone')
        await page.wait_for_timeout(300)
        recs = await page.evaluate("Object.values(JSON.parse(localStorage.getItem('ctp5:w:bocian')))")
        assert len(recs) == 1, recs
        w = recs[0]
        assert w['user_id'] == 'bocian' and w['schema_version'] == 5 and w['session'] == 'LA'
        hack = [e for e in w['entries'] if e['exercise_id'] == 'hack'][0]
        assert hack['sets'] == [{'w': 20, 'r': 10, 'd': 0}, {'w': 20, 'r': 8, 'd': 1}], hack['sets']
        skipped = [e for e in w['entries'] if e['exercise_id'] == 'lp'][0]
        assert skipped['sets'] == [], 'nevyplnený cvik = nevykonaný (prázdne sets)'
        assert w['start'] and w['end'] and w['_dirty'] is True
        # história
        hist = await page.text_content('#histList')
        assert 'Lower A' in hist and '1 cvikov' in hist, hist
        # znovu otvoriť LA dnes → placeholder = posledné hodnoty? (iný deň) – dnes otvorí ten istý zápis
        await page.click('[data-new="LA"]')
        await page.wait_for_timeout(200)
        v = await page.locator('#logItems .lex').nth(0).locator('.setrow').nth(0).locator('[data-w]').input_value()
        assert v == '20', 'dnešný zápis sa má otvoriť s hodnotami'
        await page.click('#logClose')
        await page.wait_for_timeout(300)
        # kalendár
        await page.click('[data-tab="cal"]')
        await page.wait_for_timeout(200)
        assert await page.locator('.day.today .m.done.LA').count() == 1, 'dnes má byť plná značka LA'
        stats = await page.text_content('#tab-cal .stats')
        assert '1/16' in stats and 'lower' in stats, stats
        # plán na zajtra
        tomorrow = await page.evaluate("addDays(today(),1)")
        if tomorrow[:7] == (await page.evaluate("today()"))[:7]:
            await page.click(f'[data-day="{tomorrow}"]')
            await page.wait_for_timeout(200)
            await page.click('#dayPlan [data-v="UB"]')
            await page.wait_for_timeout(200)
            await page.click('[data-close="shDay"]')
            await page.wait_for_timeout(200)
            assert await page.locator(f'[data-day="{tomorrow}"] .m.UB').count() == 1
        # nastavenia → export všetci
        await page.click('[data-tab="set"]')
        await page.wait_for_timeout(200)
        await page.click('#expAll')
        await page.wait_for_timeout(300)
        md = await page.input_value('#exTa')
        assert md.startswith('# CVIČ TY PIČ · export') and 'schema: ctp-export/1' in md and '## user: bocian' in md and '## user: thephilosopher' in md
        assert '- hack · Hack squat · 20×10, 20×8↓' in md, md[:2000]
        assert '- lp · Leg press 45° · —' in md
        assert '## prompt' in md
        await page.click('[data-close="shText"]')
        # import MD – platný
        good = "# CVIČ TY PIČ · import\nschema: ctp-import/1\ndate: 2026-10-18\n\n## user: bocian\n### stav\n- Hack squat 20 kg × 10 → drž techniku\n### ciele\n- hack: 22.5×10 · plný rozsah\n- hyp0: 15\n### hodnotenie\nDobrý štart.\n### podpora\nPokračuj.\n"
        await page.click('#impMd')
        await page.wait_for_timeout(200)
        await page.fill('#imTa', good)
        await page.click('#imGo')
        await page.wait_for_timeout(300)
        st = await page.text_content('#imStatus')
        assert 'Importované pre: BociaN' in st, st
        ai = await page.evaluate("JSON.parse(localStorage.getItem('ctp5:ai:bocian'))")
        assert ai['goals']['hack'] == {'w': 22.5, 'r': '10', 'note': 'plný rozsah'}, ai
        assert ai['goals']['hyp0']['w'] == 0 and ai['goals']['hyp0']['r'] == '15'
        assert await page.evaluate("localStorage.getItem('ctp5:ai:thephilosopher')") is None, 'druhý user sa nesmie zmeniť'
        # import MD – neplatné prípady
        for bad, msg in [
            ("# CVIČ TY PIČ · import\nschema: ctp-import/2\n## user: bocian\n### stav\n- x\n", 'schema'),
            ("# CVIČ TY PIČ · import\nschema: ctp-import/1\n## user: matej\n### stav\n- x\n", 'neznámy používateľ'),
            ("# CVIČ TY PIČ · import\nschema: ctp-import/1\n## user: bocian\n### jedlo\n- x\n", 'nepovolená sekcia'),
            ("# CVIČ TY PIČ · import\nschema: ctp-import/1\n## user: bocian\n### ciele\n- bench: 20×10\n", 'neznámy cvik'),
            ("nejaký text", 'JSON ani MD'),
        ]:
            await page.fill('#imTa', bad)
            await page.click('#imGo')
            await page.wait_for_timeout(200)
            st = await page.text_content('#imStatus')
            assert msg in st, (bad, st)
        await page.click('[data-close="shText"]')
        # ciele sa zobrazia v zápise
        await page.click('[data-tab="train"]')
        await page.wait_for_timeout(200)
        assert 'Claude' in (await page.text_content('#tab-train'))
        await page.click('[data-new="LA"]')
        await page.wait_for_timeout(200)
        sub = await page.locator('#logItems .lex').nth(0).locator('.sub').text_content()
        assert '✦ cieľ 22.5 kg × 10' in sub, sub
        await page.click('#logClose')
        await page.wait_for_timeout(200)
        # plán: uprav a Apply to all
        await page.click('[data-tab="set"]')
        await page.wait_for_timeout(200)
        await page.click('details.acc:has([data-editplan="LA"]) summary')
        await page.wait_for_timeout(100)
        await page.click('[data-editplan="LA"]')
        await page.wait_for_timeout(200)
        await page.click('#planItems .pex:nth-child(1) [data-prm]')  # odstráň hack squat
        await page.wait_for_timeout(100)
        await page.click('#planAll')
        await page.wait_for_timeout(200)
        await page.click('#askYes')
        await page.wait_for_timeout(300)
        pb = await page.evaluate("JSON.parse(localStorage.getItem('ctp5:plan:bocian')).sessions.LA.map(x=>x.id)")
        pt = await page.evaluate("JSON.parse(localStorage.getItem('ctp5:plan:thephilosopher')).sessions.LA.map(x=>x.id)")
        assert 'hack' not in pb and 'hack' not in pt
        assert 'cabc' in pb and 'dead' in pt and 'cabc' not in pt, (pb, pt)  # osobné koncovky ostali
        # záloha JSON obsahuje všetkých
        bk = await page.evaluate("backupPayload()")
        assert set(bk['users'].keys()) >= {'bocian', 'thephilosopher', 'agiraa'} and len(bk['users']['bocian']['workouts']) == 1
        # validátor: záznam bez user_id sa neuloží
        r = await page.evaluate("validateWorkout(Object.assign({}, Object.values(DB.w.bocian)[0], {user_id:''}))")
        assert any('user_id' in e for e in r), r
        # legacy migrácia z localStorage (telefón s v4 dátami)
        await page.evaluate("""localStorage.setItem('ctp:d:thephilosopher', JSON.stringify({v:3,u:1,checks:{'2026-08-24':{UB:{s:'done',d:'2026-08-26',t:'sila',ses:'UB'},H1:{s:'done',d:'2026-08-27',t:'kardio',ses:'HIIT',min:30}}},logs:[{id:'old1',date:'2026-08-25',session:'LA',ex:{hack:[[25,7],[25,10]]},note:''},{id:'old2',date:'2026-09-02',session:'LA',items:[{id:'hack',nm:'',k:'kk',sets:[{w:25,r:10},{w:5,r:10,d:1}]}]}],acts:[{id:'a1',d:'2026-09-05',kind:'LISS',min:30}]}))""")
        await page.reload()
        await page.wait_for_timeout(600)
        tp = await page.evaluate("JSON.parse(localStorage.getItem('ctp5:w:thephilosopher'))")
        assert set(tp.keys()) == {'old1', 'old2', 'chk-2026-08-24-UB'}, tp.keys()
        assert tp['old1']['entries'][0]['sets'] == [{'w': 25, 'r': 7, 'd': 0}, {'w': 25, 'r': 10, 'd': 0}]
        assert tp['old1']['src'] == 'phone:v1' and tp['old2']['src'] == 'phone:v3' and tp['chk-2026-08-24-UB']['src'] == 'check'
        ta = await page.evaluate("JSON.parse(localStorage.getItem('ctp5:a:thephilosopher'))")
        assert set(ta.keys()) == {'a1', 'chk-2026-08-24-H1'}, ta.keys()
        await page.reload(); await page.wait_for_timeout(500)
        tp2 = await page.evaluate("Object.keys(JSON.parse(localStorage.getItem('ctp5:w:thephilosopher')))")
        assert sorted(tp2) == sorted(tp.keys()), 'druhý štart nesmie duplikovať'
        await page.screenshot(path='/tmp/shot-train.png')
        print('ERRORS:', errors)
        assert not errors, errors
        print('SMOKE OK')
        await b.close()

asyncio.run(main())
