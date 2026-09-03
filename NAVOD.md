# CVIČ TY PIČ – návod (verzia 3)

## 0. Čo je v balíku
- `index.html` – celá appka (jeden súbor). Funguje troma spôsobmi:
  1. **ako publikovaný Claude artefakt** (tak ako doteraz) – zdieľané dáta a AI idú cez Claude,
  2. **ako normálna webstránka** (GitHub Pages) + **Google tabuľka** ako zdieľaný server – ikonka na ploche, fullscreen, žiadny Claude okolo,
  3. offline v telefóne – všetko funguje, len bez zdieľania a AI.
- `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png` – aby sa dala nainštalovať ako appka (ikona = Matej so sticker-om, dá sa zmeniť v nastaveniach).
- `Code.gs` – 80 riadkov pre Google Apps Script (server). Kopíruješ raz.

## 1. Ako zachovať dáta, čo ste už zapísali (ty aj Matej)
Dáta žijú v úložisku publikovaného artefaktu. Nová verzia používa **rovnaké kľúče** a staré záznamy si sama prevedie (merania dostanú nový formát so sériami/dropsetmi).

**Najjednoduchšie:** v Claude otvor rovnaký artefakt („cvic-ty-pic“), skontroluj, že je zobrazená najnovšia verzia, a klikni **Publish/Update**. Dáta zostanú, Matej nič nerobí. **Neklikaj Unpublish** – to dáta natrvalo zmaže.

**Poistka (odporúčam spraviť pred update):** v starej verzii avatar → **Záloha (JSON)** – ty aj Matej, každý svoj profil. V novej verzii: avatar → **Obnoviť zo zálohy**. Zálohu si pošlite na mail/Drive.

**Presun na vlastný hosting (bod 2 a 3):** urobte zálohu JSON v Claude verzii, potom v novej appke (na GitHub Pages) po prihlásení avatar → Obnoviť zo zálohy. Odvtedy sa dáta ukladajú do vašej Google tabuľky.

Merania z chatu (21. 8. a 24. 8.) appka ponúkne pri prvom otvorení na Domove – ťukneš, komu patria. Matejove 27. 8. (kríže, abduktor, aduktor, HIIT 30 min) sa mu pridajú samy pri jeho prvom prihlásení.

## 2. Vlastná webstránka zadarmo (GitHub Pages) – 10 minút, raz
1. Otvor **github.com** → Sign up (zadarmo) → over mail.
2. Vpravo hore **+** → **New repository** → Repository name: `cvictypic` → Public → **Create repository**.
3. Klikni **uploading an existing file** (alebo Add file → Upload files) → nahraj **všetkých 5 súborov** naraz: `index.html`, `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png` → dole **Commit changes**.
4. **Settings** (záložka hore) → vľavo **Pages** → Build and deployment → Source: **Deploy from a branch** → Branch: **main**, priečinok **/ (root)** → **Save**.
5. Počkaj ~1 minútu, obnov stránku – hore uvidíš adresu typu `https://TVOJEMENO.github.io/cvictypic/`. To je appka.
6. Aktualizácia neskôr: otvor `index.html` v repozitári → ikona ceruzky / Upload files → nahraj nový `index.html` → Commit. Telefóny si novú verziu stiahnu pri ďalšom otvorení.

Alternatíva bez GitHubu: **Netlify Drop** (app.netlify.com/drop) – potiahneš priečinok so súbormi, dostaneš adresu. Vyžaduje bezplatný účet.

## 3. Zdieľaný server = Google tabuľka (aby ste videli leaderboard navzájom)
1. Otvor **sheets.new** (nová Google tabuľka), pomenuj ju napr. „cvictypic“.
2. Menu **Rozšírenia → Apps Script**. Zmaž, čo tam je, a vlož celý obsah `Code.gs`.
3. Na 1. riadku zmeň `SECRET = 'zmen-toto-heslo'` na svoje heslo (bez diakritiky). Ulož (Ctrl+S).
4. Vpravo hore **Nasadiť → Nové nasadenie** → ozubené koliesko → **Webová aplikácia**:
   - Spustiť ako: **Ja**
   - Kto má prístup: **Ktokoľvek**
   → **Nasadiť** → Google sa spýta na povolenia → Autorizovať → (varovanie „aplikácia nie je overená“ → Rozšírené → Prejsť na projekt) → Povoliť.
5. Skopíruj **URL webovej aplikácie** (končí na `/exec`).
6. V appke: avatar → **Server** → vlož URL + heslo → **Uložiť a otestovať** → má svietiť zelené ✔.
7. Ťukni **🔗 Odkaz pre kamošov** → pošli Matejovi a Agi. Keď odkaz otvoria, appka sa im nastaví sama (server aj heslo sú v odkaze).
8. Ak niečo upravíš v `Code.gs`: Nasadiť → **Spravovať nasadenia** → ceruzka → Verzia: **Nová** → Nasadiť (URL zostane).

Tabuľka je zároveň tvoja záloha – vidíš v nej všetky dáta. Ak mi ju budeš chcieť ukázať v chate, daj Súbor → Zdieľať → Publikovať na web → CSV a pošli odkaz – viem si ju prečítať.

## 4. AI (Claude) mimo Claude rozhrania
Prihlásenie cez Claude účet v cudzej appke neexistuje – Anthropic to nepovoľuje. Preto:
- **Bez kľúča:** chat ✦ napíše otázku, pribalí celý kontext (profil, plán, štatistiky) a otvorí tvoju Claude appku – zadarmo, ale AI sync, kredo a fotky jedla nepôjdu (kredo beží zo zabudovanej banky hlášok).
- **S kľúčom (odporúčam):** console.anthropic.com → Sign up → **API Keys → Create Key** → nabi kredit (platí sa za spotrebu; text = centy, fotky jedla o niečo viac; nastav si tam mesačný limit).
  - **Pre všetkých naraz:** kľúč vlož do `Code.gs` (`ANTHROPIC_KEY`) a nasadiť novú verziu → chat, AI sync aj fotky fungujú Matejovi aj Agi cez server, nikto kľúč nevidí.
  - **Len pre seba:** avatar → AI → vlož kľúč (ostáva len v tvojom telefóne).
- **Denný sync automaticky:** v Apps Scripte vľavo **Spúšťače (⏰) → + Pridať spúšťač** → funkcia `dailySync`, zdroj udalosti: časovač, denne, 6–7 h. Každé ráno pripraví kredo a hodnotenie pre každého. Tlačidlo **AI sync** v každej karte je poistka; **Full AI sync** je v nastaveniach (avatar).

Ak otvoríš appku ako Claude artefakt, AI ide automaticky cez Claude (viewer musí byť prihlásený), kľúč netreba.

## 5. Ikona na plochu
- **Android (Chrome):** otvor adresu → ⋮ → **Pridať na plochu** / **Inštalovať aplikáciu** → Pridať. Otvára sa fullscreen bez lišty.
- **iPhone (Safari!):** otvor adresu v Safari → **Zdieľať** (štvorček so šípkou) → **Pridať na plochu** → Pridať. Otvára sa fullscreen bez lišty.
- Ikonu/názov appky zmeníš: avatar → Vzhľad appky (zmena sa prejaví po opätovnom pridaní na plochu).

## 6. Novinky v tejto verzii
Merania: ľubovoľný počet sérií (základ 2), DROP pri každej sérii, každý cvik samostatne (abdukcia/addukcia, wrist/reverse wrist), prepísanie názvu, vlastný cvik, ☰ presun poradia (aj v pláne), 0/prázdne = nerobili sme, ukladá sa samo, žiadne duplikáty (jedno meranie na deň a tréning), mazanie funguje.
Jedlo: denník s fotkami (jedna alebo hromadne), AI doplní gramáže/makrá, denné ciele podľa profilu, recepty s filtrami/variantmi + recepty z denníka pri mesačnom synce, príručka.
Nákup: ~175 potravín, počet osôb, množstvá, makrá na týždeň vs. potreba, 18 mikroživín s ❗/⚠️/✅ a návrhmi, vlastné položky, „najčastejšie jete“ z denníka.
Domov: kredo dňa (AI/banka), AI hodnotenie, odhad chudnutia na cieľové % tuku, minihra cez sticker v rohu leaderboardu.
