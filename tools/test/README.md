# Testy (Playwright + mock GitHub API)
```
cd cvictypic && python3 -m http.server 8765 --bind 127.0.0.1 &      # appka
node tools/test/mockgh.js &                                          # mock GitHub Contents API (port 8766)
node tools/test/mockgas.js &                                         # mock Google servera – spúšťa skutočný tools/server/Code.gs (port 8767)
python3 tools/test/smoke.py      # výber usera → zápis → kalendár → export/import MD (validátor) → plán → legacy migrácia z localStorage
python3 tools/test/extra.py      # v4 záloha import, deň → zápis, presun inému userovi, profil, konflikt v nastaveniach
python3 tools/test/sync.py       # 2 zariadenia: push/pull, konflikt = obe verzie, tombstone, kalendár merge, plán, neplatný záznam
python3 tools/test/acts.py       # HIIT/LIIT aktivity (zápis, úprava, zmazanie, kalendár, export), banner bez servera, odkaz pre kamošov v poli token, minihra
python3 tools/test/gas.py        # Google server + vstavaná história: seed → nahratie na server, 2. telefón cez odkaz #srv=, nový zápis, tombstone
python3 tools/test/seedsync.py   # 2 telefóny menili históriu offline → server: úpravy platia, zmazané ostanú zmazané, 0 falošných konfliktov
python3 tools/test/upgrade.py    # aktualizácia: stará verzia (_old_index.html = git show <posledný commit>:index.html) zapíše dáta → nová verzia → nič sa nestratí ani nezmení
python3 tools/test/newprof.py    # nové profily (jakub_d10, Fiňak): starý telefón ich doplní a pošle na server, nový telefón cez odkaz ich vidí, dáta sa nemiešajú
python3 tools/test/realdata.py   # reálne nasadené dáta (kv/ z deploy priečinka + v4 ctp__*.json): počty per user, žiadne miešanie; starý v4 telefón s fantómovým zápisom → nič sa nezduplikuje ani neoživí
```
Testy smoke/extra/sync/acts vypínajú vstavanú históriu (`localStorage ctp5:noseed=1`); realdata a gas ju používajú. Potrebuje `pip install playwright` + chromium. Po každej zmene `index.html` navyše `node --check` na obsahu `<script>`.
