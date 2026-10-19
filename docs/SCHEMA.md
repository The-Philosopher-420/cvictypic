# Cvič ty pič · dátová schéma v5

Zdroj pravdy pre záznamy, sync a MD import/export. Verzia schémy: `schema_version: 5`.

## 1. Záznamy

### Tréning (workout) – `kv/<user_id>/w/<id>.json`
```json
{
 "id": "k3f9a2bmxv1c0d2",            // povinné, stabilné
 "schema_version": 5,                // povinné
 "user_id": "thephilosopher",        // povinné – bez user_id sa záznam neuloží (validateWorkout)
 "date": "2026-10-18",               // povinné
 "ts": "2026-10-18T17:05",           // povinné – timestamp (začiatok, inak dátum T00:00)
 "session": "UA",                    // UA | LA | UB | LB | K | X
 "start": "2026-10-18T17:05",        // voliteľné (tlačidlo „teraz“)
 "end": "2026-10-18T18:20",          // voliteľné → trvanie, čas dňa
 "note": "",
 "entries": [                        // záznamy cvikov – každý má exercise_id, user_id, ts, schema_version
  {"id":"e1","exercise_id":"mcp","nm":"","order":0,"sets":[{"w":20,"r":10,"d":0},{"w":10,"r":12,"d":1}],
   "user_id":"thephilosopher","schema_version":5,"ts":"2026-10-18T17:05","scheme":"3 × 6–10","drop":1}
 ],
 "src": "app",                       // app | check | phone:v1 | phone:v3 | artifact:v1 | server:v3 | import …
 "created": 1760800000000, "updated": 1760800000000, "dev": "ab12cd",
 "deleted": false,                   // zmazanie = tombstone, súbor ostáva
 "conflict_of": null,                // id záznamu, ktorého je toto konfliktná verzia
 "moved_from": null, "moved_to": null,
 "flag": null                        // {type,note,proposal} – nejasný záznam na rozhodnutie
}
```
- `sets[].w` kg (0 = bez závažia), `sets[].r` opakovania (alebo sekundy/metre pri cvikoch s `u`), `d` = 1 dropset.
- Cvik s prázdnym `sets` = bol v pláne, nevykonal sa. Tréning bez jediného vyplneného cviku sa neukladá (okrem `src: "check"` = odcvičené bez čísel z v4 check-inov).
- `exercise_id` je kľúč z `EX` v appke alebo `c:<id>` (vlastný cvik, názov v `nm`). Staré id ostávajú čitateľné.

### Aktivita (HIIT / LIIT mimo silového plánu) – `kv/<user_id>/a/<id>.json`
`{id, schema_version:5, user_id, date, ts, kind:"HIIT"|"LIIT", min, km?, start?, end?, note, src:"app", created, updated, dev, deleted?}` – HIIT = minúty + krátky popis, LIIT = kilometre + minúty + popis (`km` chýba, keď je 0). Staré druhy z v4 (`LISS`, `MOB`, `OTHER`, `name`, `int`) ostávajú čitateľné. Sync a náhrobky rovnako ako pri tréningu.

### Plán – `kv/<user_id>/plan.json`
`{schema_version:5, user_id, sessions:{UA:[{id,nm,sets,drop,pu,k}],…}, updated, prev?}` – `pu:1` = osobná položka (Apply to all ju nekopíruje). Ak chýba, platí základný plán (`DEF_PLAN` + `CORE.dia`/`CORE.std` podľa `profile.dia`).

### Kalendár – `kv/<user_id>/cal/<YYYY-MM>.json`
`{schema_version:5, user_id, month, days:{"2026-10-20":"UA"}, conf:{}, updated}` – `conf` = druhá verzia dňa pri konflikte.

### Claude import – `kv/<user_id>/ai.json`
`{schema_version:5, user_id, date, state:[…], goals:{mcp:{w,r,note}}, eval, support, imported}`

### Profily – `kv/profiles.json`
`{schema_version:5, profiles:[{id, name, dia, goalMonth, created, updated, best?}]}` – `id` sa nikdy nemení; `best` = rekord v minihre.

## 2. Sync (KV server: Google Apps Script alebo GitHub Contents API)
Appka pracuje nad jednotným KV API (`ghGet/ghList/ghPut/ghGetMany`), cesta = `kv/...` ako v repozitári. Dva servery:
- **Google server** (`tools/server/Code.gs`, web app „Anyone“, bez tokenov; adresa v `localStorage ctp:server.gas.url`, odkaz pre kamošov `#srv=<url>`): `POST <url>` s telom `text/plain` JSON `{key:'ctp-2026', op, ...}` → JSON. Operácie: `ping` → `{ok}`; `list{dir}` → `{files:[{name,sha}]}`; `get{path}` → `{sha,text}` | `{missing:true}`; `getmany{paths[]}` → `{items:{path:{sha,text}}}`; `put{path,text,sha?}` → `{sha}` | `{conflict:true}` (rovnaká CAS logika ako GitHub: iná sha / existujúci súbor bez sha = konflikt); `bulk{files:[{path,text}],force?}`; `count`. Úložisko: Script Properties, JSON mapy `{path:{s:sha1,t:text,u:ms}}` gzip+base64 po 8000 znakoch (limit ~500 kB).
- **GitHub** (`ctp:server.gh = {owner,repo,token}`, odkaz `#gh=owner/repo&t=token`): Contents API, sha z gitu. Ak sú nastavené oba, používa sa GitHub.
- **Vstavaná história** `seed.json` (`{ver, profiles, users:{<id>:{w:{id:rec}, a:{id:rec}}}}`): pri prvom spustení (podľa `SEED_VER`) sa doplnia chýbajúce záznamy ako `_legacy` → so serverom sa zladia rovnako ako migrácia starého telefónu (nižšie); bez servera sú história hneď.
- Jeden záznam = jeden súbor. PUT vždy s `sha` poslednej známej verzie → server odmietne prepis cudzej zmeny (409/422).
- Pri odmietnutí: ak je obsah rovnaký (série, dátum, poznámka – líšia sa len metadáta `updated/created/dev/src/srcs/flag`) → prevezme sa serverová verzia a sha; inak serverová verzia ostáva pod pôvodným id a lokálna sa uloží ako `<id>~k####.json` s `conflict_of` – **obe verzie ostávajú, označené**.
- Pull: zoznam adresára → stiahnu sa len súbory s inou sha. Lokálne `_sha`, `_dirty`, `_legacy` sa na server nikdy nezapisujú.
- Offline: zápis do localStorage, `_dirty`; sync pri návrate online / otvorení / každých 5 min / ručne.
- Zmazanie = `deleted:true` (tombstone). Nič sa fyzicky nemaže. Staré v4 súbory `kv/ctp__*.json` ostávajú nedotknuté.
- Starý telefón (v4 dáta v localStorage `ctp:d:<user>`): pri prvom otvorení sa prevedú na v5 záznamy označené `_legacy` a pushujú sa až po stiahnutí servera: čo server už má (rovnaký obsah alebo náhrobok), prevezme sa zo servera; check-in, ktorý server zatieňuje meraním v tom istom týždni, sa zahodí; len skutočne nové záznamy idú na server. Záznamy z migrácie majú `srcs` (zoznam zdrojov) a prípadne `flag`.
- Denná záloha: GitHub Action v `cvictypic-data` (`.github/workflows/backup.yml`) ukladá `backups/<dátum>.json`; každý zápis je aj commit v git histórii.

## 3. Export MD – `ctp-export/1`
```
# CVIČ TY PIČ · export
schema: ctp-export/1
app: 5.0.0
exported: RRRR-MM-DDThh:mm
period: RRRR-MM-DD – RRRR-MM-DD
users: id1, id2

## user: <id>
name: …
diastaza: ano|nie
goal_month: 16

### plan
#### UA · Upper A
1. <cvik_id> · <názov> · <série> [· drop] [· osobné]
### workouts
#### RRRR-MM-DD · UA · Upper A [· hh:mm–hh:mm] [· NN min] [· bez čísel]
- <cvik_id> · <názov> · 20×10, 22.5×8↓ | —      (— = nevykonané)
note: …
### activities
- RRRR-MM-DD · HIIT · NN min [· hh:mm] [· popis]
- RRRR-MM-DD · LIIT · N.N km · NN min [· hh:mm] [· popis]
### calendar (plán)
RRRR-MM: DD UA · DD LA
### stats
RRRR-MM: done/goal (pct %) · upper N % · lower N %
### last_import

## prompt
<EXPORT_PROMPT>
```

## 4. Import MD – `ctp-import/1` (validátor odmietne všetko ostatné)
```
# CVIČ TY PIČ · import
schema: ctp-import/1
date: RRRR-MM-DD              (voliteľné)

## user: <id>                  (id musí existovať; každý user max raz)
### stav                       (0–6 riadkov „- …“, max 160 znakov)
- …
### ciele                      (max 25 riadkov „- <cvik_id>: [<kg>×]<opak> [· poznámka]“, cvik_id z EX alebo c:…)
- mcp: 22.5×10 · plný rozsah
- hyp0: 15
### hodnotenie                 (text, max 600 znakov)
### podpora                    (text, max 400 znakov)
```
Pravidlá: povolené sekcie len tieto štyri; neznámy user, neznámy cvik, text mimo sekcie, iná schéma → chyba s popisom, nič sa neuloží. Aktualizujú sa len používatelia uvedení v súbore.
