# Aktualizácia appky bez straty dát: stará verzia zapíše dáta → otvorí sa nová verzia na tej istej adrese → každý záznam musí ostať.
# Stará verzia: git show <commit>:index.html > _old_index.html (v koreni, kvôli seed.json; je v .gitignore) (predvolene posledná nasadená). Spustenie: python3 -m http.server 8765 v cvictypic/
import asyncio, json
from playwright.async_api import async_playwright
OLD = 'http://127.0.0.1:8765/_old_index.html'; NEW = 'http://127.0.0.1:8765/index.html'
SNAP = """(()=>{const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(/^ctp5:(w|a|plan|cal):/.test(k))o[k]=JSON.parse(localStorage.getItem(k));}return o;})()"""
def strip(r): return {k: v for k, v in r.items() if not k.startswith('_')} if isinstance(r, dict) else r
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width': 412, 'height': 915}); pg = await ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(OLD); await pg.wait_for_timeout(800)
        old_ver = await pg.evaluate("APP_VERSION")
        await pg.click('[data-pick="thephilosopher"]'); await pg.wait_for_timeout(300)
        # nový tréning, HIIT, úprava starého záznamu, zmazanie starého záznamu, kalendár
        await pg.click('[data-new="LA"]'); await pg.wait_for_timeout(300)
        rows = pg.locator('#logItems .lex').nth(0).locator('.setrow')
        await rows.nth(0).locator('[data-w]').fill('42'); await rows.nth(0).locator('[data-r]').fill('8'); await pg.wait_for_timeout(300)
        await pg.click('#logDone'); await pg.wait_for_timeout(300)
        await pg.click('[data-newact="LIIT"]'); await pg.wait_for_timeout(200); await pg.click('#actDone'); await pg.wait_for_timeout(300)
        await pg.evaluate("(()=>{const r=DB.w.thephilosopher['seed-ua-2026-08-24'];r.entries[0].sets[0].w=55;markDirty(r);persist('thephilosopher');})()")
        await pg.evaluate("(()=>{const c=monthCal('thephilosopher','2026-10');c.days['2026-10-22']='UB';markDirty(c);persist('thephilosopher');})()")
        before = await pg.evaluate(SNAP)
        nrec = sum(len(v) for k, v in before.items() if k.startswith(('ctp5:w:', 'ctp5:a:')))
        # update: nová verzia na tej istej adrese (rovnaké úložisko)
        await pg.goto(NEW); await pg.wait_for_timeout(1000)
        new_ver = await pg.evaluate("APP_VERSION")
        after = await pg.evaluate(SNAP)
        lost, changed = [], []
        for k, recs in before.items():
            if k.startswith(('ctp5:w:', 'ctp5:a:')):
                for rid, r in recs.items():
                    a = after.get(k, {}).get(rid)
                    if a is None: lost.append((k, rid))
                    elif strip(a) != strip(r): changed.append((k, rid))
            elif strip(after.get(k)) != strip(before[k]) and k.startswith(('ctp5:plan:', 'ctp5:cal:')):
                if json.dumps(before[k], sort_keys=True) != json.dumps(after.get(k), sort_keys=True): changed.append((k, '*'))
        print(f'{old_ver} → {new_ver}: {nrec} záznamov, stratené {lost}, zmenené {changed}')
        assert not lost and not changed
        h = await pg.text_content('#tab-train'); assert '42' in json.dumps(after) and 'LIIT' in h
        assert await pg.evaluate("DB.w.thephilosopher['seed-ua-2026-08-24'].entries[0].sets[0].w") == 55
        print('ERRORS:', errs); assert not errs
        print('UPGRADE OK'); await b.close()
asyncio.run(main())
