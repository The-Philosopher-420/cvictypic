# Cvič ty pič

Minimalistická appka na zápis a tracking tréningov (1 súbor `index.html`, PWA, dáta v súkromnom repozitári `cvictypic-data`).

- `index.html` – celá appka · `manifest.json`, `sw.js`, ikony – PWA
- `tools/legacy.js` – prevod dát v1–v4 → v5 (používa appka aj migrácia) · `tools/migrate.js` – serverová migrácia + report · `tools/backup.yml` – denná záloha (patrí do cvictypic-data)
- `prompts/` – prompt v exporte a prompt pre chat · `docs/SCHEMA.md` – schéma záznamov a MD formátov · `docs/NATIVNA-INSTALACIA.md` – cesty k natívnej inštalácii
- `NAVOD.md` – návod pre používateľov
