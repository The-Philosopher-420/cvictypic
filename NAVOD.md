# CVIČ TY PIČ – návod (verzia 4)

**Appka:** https://the-philosopher-420.github.io/cvictypic/ · **Dáta:** github.com/The-Philosopher-420/cvictypic-data (súkromné)
Prvé otvorenie cez „odkaz pre kamošov“ (avatar → Pokročilé → Server → 🔗) nastaví zdieľaný server sám.

## Vyhodnotenie cez Claude (bez API, bez kľúčov)
1. Avatar → **📤 Export pre Claude** → Skopírovať (alebo Zdieľať / stiahnuť .md).
2. Vlož do samostatného chatu s Claude („Cvič ty pič – vyhodnotenie“). Export obsahuje všetky tvoje dáta + hotový prompt.
3. Claude odpovie krátkym bodovým zhodnotením a JSON blokom.
4. Avatar → **📥 Import od Claude** → vlož celú odpoveď → Importovať. Appka prestaví: kredo, zhodnotenie, ciele stravy, odporúčané váhy pri každom cviku (✦), odporúčania, program (ak ho Claude zmenil), makrá jedál bez odhadu, mikroživiny, recepty.
Odporúčam raz týždenne, ideálne po víkende.

## Tréning
- Karty potiahni doľava (hotovo) / doprava (vynechané). ＋ Aktivita = HIIT, LISS, mobilita, čokoľvek (minúty, intenzita) – počíta sa do kardia a leaderboardu.
- Meranie: ľubovoľné série, DROP, ☰ poradie, prepis názvu, vlastný cvik, ukladá sa samo. Napovedá **tvoje** posledné váhy a ✦ odporúčanie od Claude. „Presunúť do profilu“ ak si zapísal do zlého profilu.
- Program: v tréningu ✏️ Upraviť = poradie, názvy, série, DROP, pridať/odobrať cvik, „Pôvodný“, „Prevziať od kamoša“. Platí len pre tvoj profil.

## Jedlo
- ＋ Jedlo → napíš, čo si jedol („150 g kura, 200 g ryža, brokolica“) → **⚡ Odhadnúť z popisu** (offline databáza ~110 potravín na 100 g). Fotka je voliteľná – Claude ju pri exporte doplní (jedlá bez makier majú needs_estimate).
- Prepínač Deň / 2 dni / Týždeň / 30 dní: makrá vs. ciele a krytie 18 živín (koľko zdrojov denne – EFSA). Ciele počítajú sedavý režim (PC) – nastavíš v profile.

## Zálohy
Avatar → Pokročilé → Záloha (JSON). Obnoviť = zlúčenie (nič sa neprepíše). Staré dáta z Claude verzie: tam Záloha → tu Obnoviť.
