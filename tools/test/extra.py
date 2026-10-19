"""Doplnkové scenáre: v4 záloha import, deň v kalendári → nový zápis, presun zápisu inému userovi, profil, konflikt v nastaveniach."""
import asyncio, json
from playwright.async_api import async_playwright
URL='http://127.0.0.1:8765/index.html'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':412,'height':915});pg=await ctx.new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL);await pg.wait_for_timeout(400);await pg.click('[data-pick="thephilosopher"]');await pg.wait_for_timeout(300)
        # v4 záloha {profile,data} pre bociana → ide k bocianovi, nie ku mne
        v4=json.dumps({"profile":{"id":"bocian","name":"BociaN"},"data":{"v":3,"logs":[{"id":"b1","date":"2026-09-03","session":"UB","items":[{"id":"lpd","nm":"","k":"q","sets":[{"w":30,"r":10},{"w":15,"r":8,"d":1}]}]}],"checks":{},"acts":[]}})
        r=await pg.evaluate("(t)=>importAny(t)",v4)
        assert 'BociaN' in r and '1 nových' in r, r
        assert await pg.evaluate("Object.keys(DB.w.bocian)")==['b1']
        assert await pg.evaluate("Object.keys(DB.w.thephilosopher)")==[]
        # opakovaný import = nič nové, žiadny konflikt
        r=await pg.evaluate("(t)=>importAny(t)",v4); assert '0 nových' in r and 'konflikt' not in r, r
        # zmenená verzia toho istého id = konflikt (obe)
        v4b=v4.replace('"w": 30','"w": 35'); r=await pg.evaluate("(t)=>importAny(t)",v4b); assert '1 rozdielnych' in r, r
        assert await pg.evaluate("Object.values(DB.w.bocian).filter(w=>w.conflict_of==='b1').length")==1
        # kalendár: deň → nový zápis v minulosti
        await pg.click('[data-tab="cal"]');await pg.wait_for_timeout(200)
        d=await pg.evaluate("addDays(today(),-1)")
        if d[:7]==(await pg.evaluate("today()"))[:7]:
            await pg.click(f'[data-day="{d}"]');await pg.wait_for_timeout(200);await pg.click('#dayNew');await pg.wait_for_timeout(200)
            assert (await pg.input_value('#logDate'))==d
            r0=pg.locator('#logItems .lex').nth(0).locator('.setrow').nth(0)
            await r0.locator('[data-w]').fill('30');await r0.locator('[data-r]').fill('10');await pg.wait_for_timeout(700)
            await pg.click('#logDone');await pg.wait_for_timeout(300)
            assert await pg.evaluate(f"workoutsOf('thephilosopher').filter(w=>w.date==='{d}').length")==1
            assert await pg.locator(f'[data-day="{d}"] .m.done').count()==1
        # presun zápisu inému userovi
        wid=await pg.evaluate("workoutsOf('thephilosopher')[0].id")
        await pg.click('[data-tab="train"]');await pg.wait_for_timeout(200);await pg.click(f'[data-log="{wid}"]');await pg.wait_for_timeout(200)
        await pg.select_option('#logMove','bocian');await pg.wait_for_timeout(200);await pg.click('#askYes');await pg.wait_for_timeout(400)
        assert await pg.evaluate("workoutsOf('thephilosopher').length")==0
        mv=await pg.evaluate("Object.values(DB.w.bocian).find(w=>w.moved_from)")
        assert mv and mv['user_id']=='bocian' and all(e['user_id']=='bocian' for e in mv['entries']) and mv['moved_from'].startswith('thephilosopher:'), mv
        assert await pg.evaluate("validateWorkout(Object.values(DB.w.bocian).find(w=>w.moved_from)).length")==0
        # profil: cieľ + diastáza
        await pg.click('[data-tab="set"]');await pg.wait_for_timeout(200);await pg.click('#setProf');await pg.wait_for_timeout(200)
        await pg.fill('#pfGoal','12');await pg.click('#pfDia [data-v="0"]');await pg.click('#pfSave');await pg.wait_for_timeout(300)
        prof=await pg.evaluate("profile('thephilosopher')"); assert prof['goalMonth']==12 and prof['dia'] is False, prof
        assert 'cabc' in (await pg.evaluate("planFor('thephilosopher').LA.map(x=>x.id)")), 'po vypnutí diastázy základný plán = brucho'
        # konflikt v nastaveniach – odkaz prepne usera a otvorí zápis
        assert 'konfliktných' in (await pg.text_content('#tab-set'))
        await pg.click('#tab-set [data-conf]');await pg.wait_for_timeout(300)
        assert (await pg.text_content('#hName')).strip()=='BociaN' and await pg.is_visible('#shLog')
        assert 'konfliktná kópia' in (await pg.text_content('#logBody'))
        print('ERRORS:',errs);assert not errs;print('EXTRA OK');await b.close()
asyncio.run(main())
