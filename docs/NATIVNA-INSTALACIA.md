# Natívna inštalácia – návrh ciest (rozhodnutie pred buildom)

Cieľ: ikona na ploche, celá obrazovka bez prehliadača, Pixel 8 Pro + iPhone 13, sync cez server, offline zápis.

Prečo „web záložka“ doteraz nefungovala: stará verzia bežala v claude.ai (artefakt v iframe – nedá sa nainštalovať) a layout nemal safe-area/standalone úpravy. Verzia 5 má manifest, service worker (offline), `viewport-fit=cover` a layout pre úzky displej – to je základ pre všetky tri cesty nižšie.

| Cesta | Pixel 8 Pro | iPhone 13 | Náklady | Čas | Aktualizácie |
|---|---|---|---|---|---|
| **A. PWA (inštalácia z prehliadača)** | Chrome → menu → „Inštalovať aplikáciu“ → vznikne WebAPK: vlastná ikona, splash, bez lišty prehliadača, v zozname appiek | Safari → Zdieľať → „Pridať na plochu“ (aj Chrome iOS) → standalone okno | 0 € | ~1 h (tlačidlo „Inštalovať“ v appke + návod pre iOS) | okamžité (pri otvorení) |
| **B. Capacitor obal (natívny APK + iOS)** | APK zo skriptu, sideload (povoliť „neznáme zdroje“) alebo Play (25 $ jednorazovo) | potrebný Mac + Xcode; bez Apple Developer (99 $/rok) sa appka podpísaná zadarmo vymaže po 7 dňoch; s programom TestFlight (build platí 90 dní) | 0 € Android / 99 $ + Mac iOS | 1–2 dni + každá aktualizácia = nový build (alebo obal len načítava web → aktualizácie okamžité, ale App Store také obaly odmieta; TestFlight ich toleruje) | ručné buildy |
| **C. PWABuilder → TWA (Android) + PWA (iOS)** | Z manifestu vygeneruje podpísaný APK/AAB (Trusted Web Activity = Chrome bez lišty); sideload alebo Play | to isté ako A (PWABuilder vie vyrobiť aj Xcode projekt, platia obmedzenia z B) | 0 € (+25 $ Play voliteľne) | ~2 h | web okamžité; APK len pri zmene ikony/manifestu |

Mimo hry: Expo / React Native = prepis celej appky (iný kód), žiadny prínos pre jednosúborovú appku.

## Odporúčanie: **A**, so záložnou **C** pre Pixel
- Jediná cesta s 0 € a bez Macu pre oba telefóny; aktualizácie bez buildov; offline funguje (service worker + localStorage, sync pri návrate online).
- iPhone: „Pridať na plochu“ zo Safari je jediný bezplatný spôsob natívnej ikony na iOS bez Apple Developer programu. Dáta appky na ploche iOS nemaže (na rozdiel od záložky v Safari po 7 dňoch nečinnosti).
- Ak by Pixel po A stále neponúkol inštaláciu (Chrome ju podmieňuje HTTPS + manifest + ikony 192/512 + SW – všetko je splnené), vyrobím cez C podpísaný APK (~2 h), ktorý sa nainštaluje ako bežná appka.

Čo spravím po tvojej voľbe A: tlačidlo „Inštalovať na plochu“ v Nastaveniach (Android `beforeinstallprompt`), krátky návod pre iOS priamo v appke, overenie na oboch telefónoch (Lighthouse PWA check + ručne). Nič z toho nespúšťam bez tvojej voľby.
