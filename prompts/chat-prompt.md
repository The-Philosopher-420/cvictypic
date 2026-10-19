# Prompt pre môj chat s Claude (vyhodnotenie exportu)

Použitie: nový chat → vlož tento prompt → pod neho vlož celý export-MD z appky (Nastavenia → Export). Odpoveď = (1) import-MD, (2) 3–6 bodov. Import-MD skopíruj do appky (Nastavenia → Import odpovede).

---

Nižšie je export z appky „Cvič ty pič“ (schéma ctp-export/1). Na konci exportu je sekcia `## prompt` – riaď sa ňou presne (ako čítať dáta, čo analyzovať, formát odpovede ctp-import/1).

Vráť presne dve časti, nič iné:

1. Blok ```md s import-MD podľa schémy ctp-import/1 (začína riadkom `# CVIČ TY PIČ · import`, obsahuje `## user:` pre každého používateľa z exportu, sekcie stav / ciele / hodnotenie / podpora). Nikdy nemiešaj dáta ani text medzi používateľmi; `cvik_id` a `user id` len také, aké sú v exporte.
2. Nadpis „Čo je nové / čo zmeniť“ a 3–6 veľmi krátkych bodov (max 15 slov každý), spolu za všetkých používateľov, s menom používateľa na začiatku bodu.

Bez úvodu, bez záveru, bez otázok, bez odporúčaní na stravu či kardio.
