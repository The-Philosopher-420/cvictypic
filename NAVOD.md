# CVIČ TY PIČ – návod (verzia 3, GitHub)

**Appka:** https://the-philosopher-420.github.io/cvictypic/
**Dáta (súkromné):** https://github.com/The-Philosopher-420/cvictypic-data (priečinok `kv/`)
**Kód appky:** https://github.com/The-Philosopher-420/cvictypic

## Ako to funguje
- Appka je webstránka na GitHub Pages (zadarmo, HTTPS, dá sa pridať na plochu ako appka, fullscreen).
- Zdieľané dáta (profily, tréningy, jedlo, leaderboard) sú JSON súbory v súkromnom repozitári `cvictypic-data`. Appka do nich zapisuje cez GitHub token, ktorý dostaneš raz v odkaze – uloží sa do telefónu.
- Každý telefón má aj lokálnu kópiu → appka funguje offline, po pripojení sa dopíše.
- AI (kredo, hodnotenie, chat, fotky jedla): cez Anthropic API kľúč (v odkaze pre kamošov / nastavenia → AI). Bez kľúča chat otvorí Claude appku s kontextom, kredo ide z banky hlášok.
- Denný AI sync: appka ho spustí sama pri prvom otvorení v deň (ak je kľúč). Navyše je pripravený `sync.js` v data repozitári – ak sa pridá secret `ANTHROPIC_API_KEY` a workflow, píše kredo každé ráno aj bez otvorenia appky.

## Prvé spustenie (každý)
1. Otvor **odkaz pre kamošov** (dostaneš od ThePhilosophera – obsahuje prístup k dátam, neposielaj ďalej).
2. Vyber profil → avatar → **Upraviť profil** (váha, výška, vek, cieľ vlastnými slovami).
3. Na plochu: Chrome ⋮ → **Pridať na plochu / Inštalovať**; Safari **Zdieľať → Pridať na plochu**.

## Prenos starých dát z Claude verzie
Stará verzia (Claude artefakt): avatar → **Záloha (JSON)**. Nová appka: avatar → **Obnoviť zo zálohy**. Každý svoj profil.

## Odkaz pre kamošov
Avatar → Server → **🔗 Odkaz pre kamošov**. Skopíruje sa odkaz s nastavením servera (a AI kľúčom, ak je zadaný).

## Aktualizácie appky
Nový `index.html` nahrať do repozitára `cvictypic` (Add file → Upload files → Commit). Telefóny si novú verziu stiahnu pri ďalšom otvorení. Alebo daj Claudovi krátkodobý token a nahrá to on.

## Bezpečnosť
- Token v odkaze má prístup **len** k repozitáru `cvictypic-data`. Ak by unikol: GitHub → Settings → Developer settings → Fine-grained tokens → Delete, a vygenerovať nový.
- Klasický token s prístupom ku všetkým repozitárom (použitý na nasadenie) **zmaž hneď po nasadení**.
