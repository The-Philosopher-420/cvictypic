# CVIČ TY PIČ – návod (verzia 5.2)

**Appka:** https://the-philosopher-420.github.io/cvictypic/ · **Dáta:** github.com/The-Philosopher-420/cvictypic-data (súkromné, priečinok `kv/`)

Celá história (všetky tréningy od augusta 2026, zo všetkých starých verzií) je **vstavaná v appke** (`seed.json`) – ukáže sa hneď, aj bez servera a bez internetu. Vyber, kto cvičí (telefón si to pamätá; každý zápis sa ukladá pod zvoleným používateľom). Zdieľanie medzi telefónmi zapne server (nižšie, 1 minúta, bez tokenov).

## Tréning
- Ťuk na typ (Upper A / Lower A / Upper B / Lower B) = dnešný zápis. Sivé čísla sú tvoje posledné hodnoty – len napovedajú. Cvik bez čísel = nevykonaný, to je v poriadku.
- Začiatok / Koniec: „teraz“ alebo ručne. Trvanie a čas dňa idú do exportu.
- Ukladá sa priebežne (stav vpravo hore). ✕ zatvorí, Hotovo zatvorí a potvrdí.
- Zápis sa dá presunúť inému používateľovi (ak bol zapísaný pod zlým menom).
- **HIIT / LIIT** (tlačidlá pod typmi tréningu): HIIT = minúty (±1) + krátky popis, LIIT = kilometre (±0,5) + minúty (±5) + popis; začiatok/koniec „teraz“ dopočíta minúty. Ťuk na aktivitu v histórii ju otvorí na úpravu alebo zmazanie.
- **Minihra** (Matej beží): 3× rýchlo ťukni na Matejovo logo vľavo hore. Rekord sa ukladá do profilu, rebríček je v hre.

## Kalendár
- Obrys = plán (ťuk na deň → vyber typ), plné = odcvičené. H = HIIT, L = LIIT. Ťuk na deň: zápis tréningu aj aktivity v ten deň.
- Štatistiky: % mesačného cieľa (Nastavenia → Upraviť), % upper / % lower z odcvičených.

## Plán (Nastavenia → Plán tréningov → ✏️)
- Poradie ☰, názvy, série, DROP, pridať/odobrať cvik. „Uložiť pre mňa“ alebo „Apply to all users“.
- OSOB. = osobná položka (koncovka leg day: diastáza vs. brucho) – ostatným sa nekopíruje.
- Staré zápisy sa nemenia; nový plán platí od ďalšieho zápisu.

## Claude (bez API)
1. Nastavenia → **Export – ja / všetci** → Kopírovať (alebo .md). Export obsahuje dáta + hotový prompt.
2. Nový chat: vlož `prompts/chat-prompt.md` + export. Claude vráti import-MD a 3–6 bodov.
3. Nastavenia → **Import odpovede (MD)** → vlož → Importovať. Neplatný súbor appka odmietne s dôvodom. Aktualizuje sa len používateľ zo súboru.

## Server (zdieľanie medzi telefónmi)
- **Google server – bez tokenov.** Kód je v `tools/server/Code.gs` a je už vložený v projekte na script.google.com (účet Xaviera). Zapnutie raz: script.google.com → projekt so skriptom → **Deploy → New deployment** → ⚙️ typ **Web app** → Execute as **Me**, Who has access **Anyone** → **Deploy** → skopíruj **Web app URL** (končí `/exec`) → v appke Nastavenia → Server → vlož → **Uložiť a otestovať**. Appka nahrá vstavanú históriu na server a odvtedy sa všetko zdieľa.
- Ostatné telefóny: Nastavenia → **🔗 Odkaz** (obsahuje adresu servera) → otvoriť na druhom telefóne (alebo adresu vložiť do Nastavenia → Server). Pozor: iPhone ikona na ploche má vlastné úložisko oddelené od Safari – odkaz treba otvoriť priamo v nej.
- Zmena kódu servera: v editore skriptu uprav kód → Deploy → **Manage deployments** → ✏️ → Version: New version → Deploy (adresa ostáva). Dáta sú v Script Properties (gzip), limit ~500 kB ≈ niekoľko rokov tréningov; appka má zálohu JSON.
- GitHub repozitár s tokenom ostáva ako voliteľná alternatíva (Nastavenia → Server → GitHub).
- Nastavenia → Diagnostika ukáže verziu, server, počty záznamov a či sú v tomto prehliadači staré v4 dáta.

## Sync a zálohy
- Bodka pri mene: zelená = synchronizované, oranžová = prebieha, sivá = bez servera alebo server práve neodpovedá (zapisuje sa do telefónu, pošle sa neskôr; detail v Nastaveniach). Nič nebliká na červeno.
- Konflikt (dve zariadenia zmenili ten istý zápis) sa nikdy neprepíše: obe verzie ostanú, označené „konflikt“ v Nastaveniach – otvor a zmaž tú zlú.
- Zmazané zápisy ostávajú na serveri ako zmazané. Ručne: Nastavenia → Záloha JSON; Obnoviť = zlúčenie. (Pri GitHub serveri navyše denná záloha Action do `backups/`.)

## Pre vývoj
- `index.html` je celá appka; `seed.json` = vstavaná história (doplní sa raz podľa `SEED_VER`, len chýbajúce záznamy); `tools/legacy.js` = prevod v1–v4 dát; `tools/server/Code.gs` = Google server; `docs/SCHEMA.md` = schéma záznamov, MD formátov a API servera.
- Po zmene: `node --check`, test v prehliadači, commit do `main` → GitHub Pages. Pri zmene `sw.js` zvýš názov cache.
