# Cvič ty pič

Minimalistická appka na zápis a tracking tréningov (1 súbor `index.html`, PWA). História je vstavaná (`seed.json`); zdieľanie cez Google server (`tools/server/Code.gs`, bez tokenov) alebo voliteľne súkromný repozitár `cvictypic-data`.

- `index.html` – celá appka · `seed.json` – vstavaná história · `manifest.json`, `sw.js`, ikony, `sticker.png` (minihra) – PWA
- `tools/server/Code.gs` – Google Apps Script server (KV úložisko v Script Properties, API v `docs/SCHEMA.md`)
- `tools/legacy.js` – prevod dát v1–v4 → v5 (používa appka aj migrácia) · `tools/migrate.js` – serverová migrácia + report · `tools/backup.yml` – denná záloha (patrí do cvictypic-data)
- `prompts/` – prompt v exporte a prompt pre chat · `docs/SCHEMA.md` – schéma záznamov a MD formátov · `docs/NATIVNA-INSTALACIA.md` – cesty k natívnej inštalácii
- `tools/test/` – Playwright testy (mock GitHub + mock Google server)
- `NAVOD.md` – návod pre používateľov
