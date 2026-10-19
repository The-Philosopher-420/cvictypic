# CVIČ TY PIČ – návod (verzia 5)

**Appka:** https://the-philosopher-420.github.io/cvictypic/ · **Dáta:** github.com/The-Philosopher-420/cvictypic-data (súkromné, priečinok `kv/`)

Prvé otvorenie na novom telefóne: cez „odkaz pre kamošov“ (Nastavenia → 🔗 Odkaz) – nastaví server. Potom vyber, kto cvičí (telefón si to pamätá; každý zápis sa ukladá pod zvoleným používateľom).

## Tréning
- Ťuk na typ (Upper A / Lower A / Upper B / Lower B) = dnešný zápis. Sivé čísla sú tvoje posledné hodnoty – len napovedajú. Cvik bez čísel = nevykonaný, to je v poriadku.
- Začiatok / Koniec: „teraz“ alebo ručne. Trvanie a čas dňa idú do exportu.
- Ukladá sa priebežne (stav vpravo hore). ✕ zatvorí, Hotovo zatvorí a potvrdí.
- Zápis sa dá presunúť inému používateľovi (ak bol zapísaný pod zlým menom).

## Kalendár
- Obrys = plán (ťuk na deň → vyber typ), plné = odcvičené. K = stará kardio história.
- Štatistiky: % mesačného cieľa (Nastavenia → Upraviť), % upper / % lower z odcvičených.

## Plán (Nastavenia → Plán tréningov → ✏️)
- Poradie ☰, názvy, série, DROP, pridať/odobrať cvik. „Uložiť pre mňa“ alebo „Apply to all users“.
- OSOB. = osobná položka (koncovka leg day: diastáza vs. brucho) – ostatným sa nekopíruje.
- Staré zápisy sa nemenia; nový plán platí od ďalšieho zápisu.

## Claude (bez API)
1. Nastavenia → **Export – ja / všetci** → Kopírovať (alebo .md). Export obsahuje dáta + hotový prompt.
2. Nový chat: vlož `prompts/chat-prompt.md` + export. Claude vráti import-MD a 3–6 bodov.
3. Nastavenia → **Import odpovede (MD)** → vlož → Importovať. Neplatný súbor appka odmietne s dôvodom. Aktualizuje sa len používateľ zo súboru.

## Sync a zálohy
- Bodka pri mene: zelená = synchronizované, oranžová = prebieha, červená = server neodpovedá (zapisuje sa do telefónu, pošle sa neskôr), sivá = bez servera.
- Konflikt (dve zariadenia zmenili ten istý zápis) sa nikdy neprepíše: obe verzie ostanú, označené „konflikt“ v Nastaveniach – otvor a zmaž tú zlú.
- Zmazané zápisy ostávajú na serveri ako zmazané. Denná záloha: GitHub Action v cvictypic-data (`backups/`). Ručne: Nastavenia → Záloha JSON; Obnoviť = zlúčenie.

## Pre vývoj
- `index.html` je celá appka; `tools/legacy.js` = prevod v1–v4 dát (zdieľa ho appka aj `tools/migrate.js`); `docs/SCHEMA.md` = schéma záznamov a MD formátov.
- Po zmene: `node --check`, test v prehliadači, commit do `main` → GitHub Pages. Pri zmene `sw.js` zvýš názov cache.
