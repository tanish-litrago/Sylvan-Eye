# Phase 7: regional test report

Run on 2026-10-25. 7 site(s): 6 matched your expectations, 1 did not, 0 failed to run.

Your expectations were written before the run (see the commit history of phase7_sites.json). A mismatch is a finding to review: either the system or the expectation is wrong.

## Summary

| Site | Region | Gate: you / system | Rain mm | Temp C | pH | Texture | Elev m | Outlines (share, count) | Strong / Likely / Caution | Ruled out | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kuderu | Dry Deccan village | none / none | 689 | 27.6 | 7.09 | medium | 419.3 | 10.7% (857) | 5 / 7 / 11 | 9 | 39.6 | MATCH |
| bellare | Western Ghats foothill village | none / none | 3525 | 26.1 | 5.62 | medium | 109.6 | 6.8% (366) | 2 / 3 / 19 | 8 | 30.7 | MATCH |
| kakdwip | Hooghly delta village | none / none | 1919 | 26.3 | 6.56 | medium | 6.6 | 16.5% (1013) | 6 / 11 / 11 | 4 | 32.8 | MATCH |
| mohali-sohana | Punjab plains peri-urban edge | warning / warning | 906 | 23.0 | 7.13 | medium | 310.1 | 23.3% (815) | 3 / 10 / 14 | 5 | 25.8 | MATCH |
| pirangut | Western Ghats peri-urban edge | warning / warning | 1145 | 24.0 | 6.54 | heavy | 594.4 | 20.5% (683) | 3 / 6 / 20 | 3 | 32.0 | MATCH |
| sandila | Gangetic plain small town | warning / warning | 1041 | 24.6 | 7.34 | medium | 135.9 | 45.8% (3977) | 4 / 11 / 12 | 5 | 30.6 | MATCH |
| kalimpong | Eastern Himalaya hill town | warning / warning | 3487 | 17.3 | 5.67 | medium | 1151.6 | 29.6% (2119) | 0 / 2 / 21 | 9 | 34.3 | MISMATCH |

## Mismatches to review

### kalimpong (Kalimpong)
- a warning mentions 'built-up': you expected **yes**, the system gave **no**

## Data coverage

Every measured value was present at every site.

## Site details

### kuderu: Kuderu large village (Anantapur) (Dry Deccan village)
- Point 14.73051282285115, 77.4302253808614, radius 400 m. You saw: Compact cluster of flat-roofed village houses surrounded by dry red-brown fallow fields and low scrub. Trap seen: bare ground and dry fallow plots between the village lanes..
- Terrain summary (radius 400 m): water/wet 0%, bare/built 20%, sparse vegetation or crops 65%, dense vegetation 15%; NDVI dry 0.233 to peak 0.454, big seasonal swing 31% (by year: 2023 32%, 2024 36%, 2025 31%)
- Building outlines (extra, not used for matching): 10.7% (857)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: none
- Strong fit (5): Amla, Babul, Mango, Moringa, Sissoo / Shisham
- Likely, not fully verified (7): Amaltas, Bael, Ber, Karanj / Pongamia, Peepal, Siris, Tamarind
- Caution (11): Banyan, Casuarina, Chir pine, Khair / Catechu, Khejri, Mahua, Neem, Palash, Salai / Indian frankincense, Semal, Teak
- Ruled out (9): Sal: rainfall: 689 mm is below the stated minimum 1000; Arjun: rainfall: 689 mm is below the stated minimum 750; Jamun: rainfall: 689 mm is below the stated minimum 800; Bamboo (male bamboo): rainfall: 689 mm is below the stated minimum 1200; Gamhar: rainfall: 689 mm is below the stated minimum 750; Baheda: rainfall: 689 mm is below the stated minimum 900; Bijasal: rainfall: 689 mm is below the stated minimum 750; Deodar: elevation: 419.3 m is below its altitude range (1200 to 3500 m); Indian rosewood: rainfall: 689 mm is below the stated minimum 750
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Bamboo (male bamboo) is ruled out (expected yes, got yes)

### bellare: Bellare large village (Sullia, Dakshin Kannada) (Western Ghats foothill village)
- Point 12.6625, 75.367, radius 400 m. You saw: Hill-valley village with tiled-roof houses and homesteads under dense arecanut, coconut and forest canopy. Trap seen: heavy tree cover directly over the roofs..
- Terrain summary (radius 400 m): water/wet 0%, bare/built 6%, sparse vegetation or crops 34%, dense vegetation 60%; NDVI dry 0.442 to peak 0.694, big seasonal swing 39% (by year: 2023 34%, 2024 34%, 2025 39%)
- Building outlines (extra, not used for matching): 6.8% (366)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: none
- Strong fit (2): Jamun, Moringa
- Likely, not fully verified (3): Gamhar, Indian rosewood, Peepal
- Caution (19): Amaltas, Amla, Arjun, Bael, Baheda, Bamboo (male bamboo), Banyan, Ber, Casuarina, Khair / Catechu, Mahua, Neem, Palash, Sal, Semal, Siris, Sissoo / Shisham, Tamarind, Teak
- Ruled out (8): Babul: rainfall: 3525 mm is above the stated maximum 2300; Khejri: rainfall: 3525 mm is above the stated maximum 900; Karanj / Pongamia: rainfall: 3525 mm is above the stated maximum 2500; Mango: rainfall: 3525 mm is above the stated maximum 3500; Bijasal: rainfall: 3525 mm is above the stated maximum 2000; Deodar: elevation: 109.6 m is below its altitude range (1200 to 3500 m); Chir pine: rainfall: 3525 mm is above the stated maximum 2900; Salai / Indian frankincense: rainfall: 3525 mm is above the stated maximum 2000
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Jamun is an option (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Babul is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### kakdwip: Kakdwip large settlement (South 24 Parganas) (Hooghly delta village)
- Point 21.8765, 88.1885, radius 400 m. You saw: Delta settlement where house compounds are interleaved with rectangular backyard ponds (pukurs) and palm and bamboo groves. Trap seen: many domestic ponds and tree rings inside the settlement. Kakdwip is a municipal town, so the type label 'village' is approximate..
- Terrain summary (radius 400 m): water/wet 2%, bare/built 3%, sparse vegetation or crops 54%, dense vegetation 41%; NDVI dry 0.304 to peak 0.597, big seasonal swing 68% (by year: 2023 63%, 2024 55%, 2025 68%)
- Building outlines (extra, not used for matching): 16.5% (1013)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: none
- Strong fit (6): Amla, Banyan, Jamun, Moringa, Palash, Sissoo / Shisham
- Likely, not fully verified (11): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Siris, Tamarind, Teak
- Caution (11): Arjun, Babul, Bamboo (male bamboo), Bijasal, Casuarina, Khair / Catechu, Mahua, Mango, Neem, Salai / Indian frankincense, Semal
- Ruled out (4): Sal: elevation: 6.6 m is below its altitude range (100 to 1500 m); Khejri: rainfall: 1919 mm is above the stated maximum 900; Deodar: elevation: 6.6 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 6.6 m is below its altitude range (400 to 2300 m)
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Casuarina is an option (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### mohali-sohana: Sohana / Sectors 78-79 fringe, Mohali (Punjab plains peri-urban edge)
- Point 30.6785, 76.7215, radius 400 m. You saw: Peri-urban residential blocks and urban-village houses directly bordering irrigated plains cropland. Trap seen: graded bare-ground plots and active cropland inside the same circle..
- Terrain summary (radius 400 m): water/wet 1%, bare/built 42%, sparse vegetation or crops 43%, dense vegetation 14%; NDVI dry 0.201 to peak 0.343, big seasonal swing 9% (by year: 2023 28%, 2024 34%, 2025 9%)
- Building outlines (extra, not used for matching): 23.3% (815)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: WARNING: 42% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted.
- Strong fit (3): Amla, Babul, Moringa
- Likely, not fully verified (10): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Siris, Tamarind
- Caution (14): Arjun, Banyan, Bijasal, Casuarina, Jamun, Khair / Catechu, Mahua, Mango, Neem, Palash, Salai / Indian frankincense, Semal, Sissoo / Shisham, Teak
- Ruled out (5): Sal: rainfall: 906 mm is below the stated minimum 1000; Khejri: rainfall: 906 mm is above the stated maximum 900; Bamboo (male bamboo): rainfall: 906 mm is below the stated minimum 1200; Deodar: elevation: 310.1 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 310.1 m is below its altitude range (400 to 2300 m)
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'built-up' (expected yes, got yes)
  - [x] Sissoo / Shisham is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)

### pirangut: Pirangut (Mulshi, west Pune fringe) (Western Ghats peri-urban edge)
- Point 18.511, 73.6815, radius 400 m. You saw: Hillside peri-urban housing and residential layouts between steep Western Ghats scrub and grassland slopes and valley fields. Trap seen: bare basalt slopes and dry grass next to dense roofs..
- Terrain summary (radius 400 m): water/wet 1%, bare/built 53%, sparse vegetation or crops 45%, dense vegetation 2%; NDVI dry 0.127 to peak 0.332, big seasonal swing 33% (by year: 2023 40%, 2024 36%, 2025 33%)
- Building outlines (extra, not used for matching): 20.5% (683)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: WARNING: 53% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted.
- Strong fit (3): Babul, Moringa, Palash
- Likely, not fully verified (6): Amaltas, Bael, Indian rosewood, Karanj / Pongamia, Sal, Tamarind
- Caution (20): Amla, Arjun, Baheda, Banyan, Ber, Bijasal, Casuarina, Chir pine, Gamhar, Jamun, Khair / Catechu, Mahua, Mango, Neem, Peepal, Salai / Indian frankincense, Semal, Siris, Sissoo / Shisham, Teak
- Ruled out (3): Khejri: rainfall: 1145 mm is above the stated maximum 900; Bamboo (male bamboo): rainfall: 1145 mm is below the stated minimum 1200; Deodar: elevation: 594.4 m is below its altitude range (1200 to 3500 m)
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'built-up' (expected yes, got yes)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### sandila: Sandila (Hardoi, Uttar Pradesh) (Gangetic plain small town)
- Point 27.0725, 80.518, radius 400 m. You saw: Dense low-rise brick residential neighbourhood in a small Gangetic town, bordered by mango orchards and fields. Trap seen: town ponds (talabs) and orchard canopy next to tightly packed brick roofs..
- Terrain summary (radius 400 m): water/wet 0%, bare/built 78%, sparse vegetation or crops 16%, dense vegetation 5%; NDVI dry 0.099 to peak 0.221, big seasonal swing 10% (by year: 2023 10%, 2024 8%, 2025 10%)
- Building outlines (extra, not used for matching): 45.8% (3977)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: WARNING: 78% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted.
- Strong fit (4): Amla, Babul, Mango, Moringa
- Likely, not fully verified (11): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Sal, Siris, Tamarind
- Caution (12): Arjun, Banyan, Bijasal, Casuarina, Jamun, Mahua, Neem, Palash, Salai / Indian frankincense, Semal, Sissoo / Shisham, Teak
- Ruled out (5): Khejri: rainfall: 1041 mm is above the stated maximum 900; Bamboo (male bamboo): rainfall: 1041 mm is below the stated minimum 1200; Deodar: elevation: 135.9 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 135.9 m is below its altitude range (400 to 2300 m); Khair / Catechu: pH: 7.34 is above the stated maximum 7
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'built-up' (expected yes, got yes)
  - [x] Sissoo / Shisham is an option (expected yes, got yes)
  - [x] Mango is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)
  - [x] Bamboo (male bamboo) is ruled out (expected yes, got yes)

### kalimpong: Kalimpong (Eastern Himalaya hill town)
- Point 27.068, 88.472, radius 400 m. You saw: Steep wet-hill town with terraced houses along ridges, surrounded by dense mountain trees and shaded slopes. Traps seen: topographic shadows and bright tin or sheet roofs (the Darjeeling false-water and shadow case) next to dense tree cover..
- Terrain summary (radius 400 m): water/wet 0%, bare/built 34%, sparse vegetation or crops 32%, dense vegetation 34%; NDVI dry 0.204 to peak 0.459, big seasonal swing 46% (by year: 2023 40%, 2024 41%, 2025 46%)
- Building outlines (extra, not used for matching): 29.6% (2119)
- Cache: store sqlite:sylvan_cache.db, terrain miss, soil miss, climate miss, footprints miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (0): none
- Likely, not fully verified (2): Indian rosewood, Peepal
- Caution (21): Amaltas, Amla, Arjun, Bael, Bamboo (male bamboo), Banyan, Ber, Casuarina, Gamhar, Jamun, Khair / Catechu, Mahua, Mango, Neem, Palash, Sal, Semal, Siris, Sissoo / Shisham, Tamarind, Teak
- Ruled out (9): Babul: rainfall: 3487 mm is above the stated maximum 2300; Khejri: rainfall: 3487 mm is above the stated maximum 900; Karanj / Pongamia: rainfall: 3487 mm is above the stated maximum 2500; Moringa: elevation: 1151.6 m is above its altitude limit (1000 m); Baheda: elevation: 1151.6 m is above its altitude limit (1000 m); Bijasal: rainfall: 3487 mm is above the stated maximum 2000; Deodar: elevation: 1151.6 m is below its altitude range (1200 to 3500 m); Chir pine: rainfall: 3487 mm is above the stated maximum 2900; Salai / Indian frankincense: rainfall: 3487 mm is above the stated maximum 2000
- Your checks:
  - [x] gate (expected warning, got warning)
  - [ ] a warning mentions 'built-up' (expected yes, got no)
  - [x] Khejri is ruled out (expected yes, got yes)

