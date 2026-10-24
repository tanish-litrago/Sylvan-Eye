# Phase 7: regional test report

Run on 2026-10-24. 11 site(s): 3 matched your expectations, 8 did not, 0 failed to run.

Your expectations were written before the run (see the commit history of phase7_sites.json). A mismatch is a finding to review: either the system or the expectation is wrong.

## Summary

| Site | Region | Gate: you / system | Rain mm | Temp C | pH | Texture | Elev m | Outlines (share, count) | Strong / Likely / Caution | Ruled out | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anantapur | Rayalaseema plateau | warning / none | 699 | 27.8 | 7.29 | medium | 373.3 | 1.8% (30) | 5 / 7 / 10 | 10 | 7.7 | MISMATCH |
| hisar | Haryana semi-arid plain | warning / warning | 464 | 24.9 | 7.69 | medium | 210.9 | 0.4% (36) | 1 / 2 / 7 | 22 | 5.4 | MATCH |
| malihabad | Gangetic plain (orchard belt) | warning / none | 1054 | 24.9 | 6.43 | medium | 129.7 | 0.0% (0) | 6 / 10 / 12 | 4 | 5.6 | MISMATCH |
| dibrugarh | Upper Assam valley | warning / none | 3485 | 23.2 | 5.22 | medium | 115.0 | 0.1% (14) | 2 / 3 / 20 | 7 | 6.0 | MISMATCH |
| dive-ghat | Western Ghats rain-shadow | none / warning | 893 | 24.5 | 6.81 | heavy | 730.3 | 0.0% (0) | 3 / 5 / 19 | 5 | 7.8 | MISMATCH |
| cherrapunji | Khasi Hills | none / warning | 4978 | 17.0 | 5.47 | medium | 1333.0 | 0.0% (2) | 0 / 2 / 10 | 20 | 6.4 | MISMATCH |
| pampore | Kashmir valley | warning / warning | 1388 | 12.4 | 7.04 | medium | 1603.7 | 0.1% (7) | 0 / 1 / 3 | 28 | 9.2 | MATCH |
| kolkata-core | Lower Gangetic delta (city) | warning / warning | 1882 | 26.1 | 6.39 | heavy | 13.3 | 46.6% (3090) | 2 / 4 / 22 | 4 | 12.6 | MATCH |
| darjeeling | Eastern Himalaya | warning / blocked | 3550 | 12.2 | 5.66 | medium | 2079.0 | 41.8% (2387) | 0 / 0 / 0 | 31 | 6.5 | MISMATCH |
| kochi | Malabar coast | warning / none | 2960 | 26.7 | 5.61 | heavy | 9.0 | 43.8% (2328) | 1 / 1 / 22 | 8 | 7.3 | MISMATCH |
| sundarbans | Sundarbans delta | warning / none | 2085 | 26.2 | 6.21 | heavy | 6.5 | 0.0% (0) | 2 / 3 / 21 | 6 | 6.4 | MISMATCH |

## Mismatches to review

### anantapur (Anantapur rainfed fields)
- gate: you expected **warning**, the system gave **none**
- a warning mentions 'cropland': you expected **yes**, the system gave **no**

### malihabad (Malihabad mango orchard)
- gate: you expected **warning**, the system gave **none**

### dibrugarh (Dibrugarh tea plantation)
- gate: you expected **warning**, the system gave **none**

### dive-ghat (Dive Ghat leeward scrub)
- gate: you expected **none**, the system gave **warning**

### cherrapunji (Cherrapunji plateau grassland)
- gate: you expected **none**, the system gave **warning**

### darjeeling (Darjeeling Chauk Bazaar)
- gate: you expected **warning**, the system gave **blocked**
- a warning mentions 'built-up': you expected **yes**, the system gave **no**
- Deodar is an option: you expected **yes**, the system gave **no**

### kochi (Kochi Mattancherry)
- gate: you expected **warning**, the system gave **none**
- a warning mentions 'built-up': you expected **yes**, the system gave **no**

### sundarbans (Sundarbans mangrove forest)
- gate: you expected **warning**, the system gave **none**
- a warning mentions 'water': you expected **yes**, the system gave **no**

## Data coverage

Every measured value was present at every site.

## Site details

### anantapur: Anantapur rainfed fields (Rayalaseema plateau)
- Point 14.6218, 77.5294, radius 400 m. You saw: dryland farmland.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 10%, sparse vegetation or crops 82%, dense vegetation 8%; NDVI dry 0.244 to peak 0.528, big seasonal swing 54% (by year: 2023 29%, 2024 57%, 2025 54%)
- Building outlines (extra, not used for matching): 1.8% (30)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate hit, footprints miss
- Warnings: none
- Strong fit (5): Amla, Babul, Mango, Moringa, Sissoo / Shisham
- Likely, not fully verified (7): Amaltas, Bael, Ber, Karanj / Pongamia, Peepal, Siris, Tamarind
- Caution (10): Banyan, Casuarina, Khair / Catechu, Khejri, Mahua, Neem, Palash, Salai / Indian frankincense, Semal, Teak
- Ruled out (10): Sal: rainfall: 699 mm is below the stated minimum 1000; Arjun: rainfall: 699 mm is below the stated minimum 750; Jamun: rainfall: 699 mm is below the stated minimum 800; Bamboo (male bamboo): rainfall: 699 mm is below the stated minimum 1200; Gamhar: rainfall: 699 mm is below the stated minimum 750; Baheda: rainfall: 699 mm is below the stated minimum 900; Bijasal: rainfall: 699 mm is below the stated minimum 750; Deodar: elevation: 373.3 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 373.3 m is below its altitude range (400 to 2300 m); Indian rosewood: rainfall: 699 mm is below the stated minimum 750
- Your checks:
  - [ ] gate (expected warning, got none)
  - [ ] a warning mentions 'cropland' (expected yes, got no)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Ber is an option (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Arjun is ruled out (expected yes, got yes)

### hisar: Hisar rainfed fields (Haryana semi-arid plain)
- Point 29.0814, 75.6188, radius 400 m. You saw: barani farmland.
- Terrain summary (radius 400 m): water/wet 3%, bare/built 1%, sparse vegetation or crops 74%, dense vegetation 22%; NDVI dry 0.115 to peak 0.789, big seasonal swing 98% (by year: 2023 99%, 2024 98%, 2025 98%)
- Building outlines (extra, not used for matching): 0.4% (36)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (1): Babul
- Likely, not fully verified (2): Ber, Tamarind
- Caution (7): Casuarina, Karanj / Pongamia, Khejri, Mango, Neem, Palash, Sissoo / Shisham
- Ruled out (22): Teak: rainfall: 464 mm is below the stated minimum 600; Sal: rainfall: 464 mm is below the stated minimum 1000; Arjun: rainfall: 464 mm is below the stated minimum 750; Mahua: rainfall: 464 mm is below the stated minimum 550; Jamun: rainfall: 464 mm is below the stated minimum 800; Peepal: rainfall: 464 mm is below the stated minimum 500; Banyan: rainfall: 464 mm is below the stated minimum 500; Bamboo (male bamboo): rainfall: 464 mm is below the stated minimum 1200; Gamhar: rainfall: 464 mm is below the stated minimum 750; Amla: rainfall: 464 mm is below the stated minimum 630; Bael: rainfall: 464 mm is below the stated minimum 570; Moringa: rainfall: 464 mm is below the stated minimum 500; Semal: rainfall: 464 mm is below the stated minimum 500; Siris: rainfall: 464 mm is below the stated minimum 500; Amaltas: rainfall: 464 mm is below the stated minimum 480; Baheda: rainfall: 464 mm is below the stated minimum 900; Bijasal: rainfall: 464 mm is below the stated minimum 750; Deodar: elevation: 210.9 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 210.9 m is below its altitude range (400 to 2300 m); Indian rosewood: rainfall: 464 mm is below the stated minimum 750; Salai / Indian frankincense: rainfall: 464 mm is below the stated minimum 500; Khair / Catechu: rainfall: 464 mm is below the stated minimum 500
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'cropland' (expected yes, got yes)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Ber is an option (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Jamun is ruled out (expected yes, got yes)

### malihabad: Malihabad mango orchard (Gangetic plain (orchard belt))
- Point 26.886117, 80.728061, radius 400 m. You saw: dense mango orchard.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 0%, sparse vegetation or crops 2%, dense vegetation 98%; NDVI dry 0.534 to peak 0.797, big seasonal swing 47% (by year: 2023 40%, 2024 53%, 2025 47%)
- Building outlines (extra, not used for matching): 0.0% (0)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: none
- Strong fit (6): Amla, Bijasal, Mango, Moringa, Neem, Palash
- Likely, not fully verified (10): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Peepal, Sal, Siris, Tamarind
- Caution (12): Arjun, Babul, Banyan, Casuarina, Jamun, Karanj / Pongamia, Khair / Catechu, Mahua, Salai / Indian frankincense, Semal, Sissoo / Shisham, Teak
- Ruled out (4): Khejri: rainfall: 1054 mm is above the stated maximum 900; Bamboo (male bamboo): rainfall: 1054 mm is below the stated minimum 1200; Deodar: elevation: 129.7 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 129.7 m is below its altitude range (400 to 2300 m)
- Your checks:
  - [ ] gate (expected warning, got none)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Mango is an option (expected yes, got yes)
  - [x] Sissoo is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)

### dibrugarh: Dibrugarh tea plantation (Upper Assam valley)
- Point 27.474586, 95.095129, radius 400 m. You saw: tea garden with shade trees.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 0%, sparse vegetation or crops 4%, dense vegetation 95%; NDVI dry 0.498 to peak 0.853, big seasonal swing 97% (by year: 2023 94%, 2024 67%, 2025 97%)
- Building outlines (extra, not used for matching): 0.1% (14)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: none
- Strong fit (2): Bamboo (male bamboo), Moringa
- Likely, not fully verified (3): Gamhar, Indian rosewood, Peepal
- Caution (20): Amaltas, Amla, Arjun, Bael, Baheda, Banyan, Ber, Casuarina, Jamun, Khair / Catechu, Mahua, Mango, Neem, Palash, Sal, Semal, Siris, Sissoo / Shisham, Tamarind, Teak
- Ruled out (7): Babul: rainfall: 3485 mm is above the stated maximum 2300; Khejri: rainfall: 3485 mm is above the stated maximum 900; Karanj / Pongamia: rainfall: 3485 mm is above the stated maximum 2500; Bijasal: rainfall: 3485 mm is above the stated maximum 2000; Deodar: elevation: 115 m is below its altitude range (1200 to 3500 m); Chir pine: rainfall: 3485 mm is above the stated maximum 2900; Salai / Indian frankincense: rainfall: 3485 mm is above the stated maximum 2000
- Your checks:
  - [ ] gate (expected warning, got none)
  - [x] Teak is an option (expected yes, got yes)
  - [x] Mango is an option (expected yes, got yes)
  - [x] Arjun is an option (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)

### dive-ghat: Dive Ghat leeward scrub (Western Ghats rain-shadow)
- Point 18.420939, 73.941969, radius 400 m. You saw: dry scrub just adjacent to hills.
- Terrain summary (radius 400 m): water/wet 1%, bare/built 25%, sparse vegetation or crops 74%, dense vegetation 0%; NDVI dry 0.149 to peak 0.487, big seasonal swing 93% (by year: 2023 26%, 2024 94%, 2025 93%)
- Building outlines (extra, not used for matching): 0.0% (0)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 2 of 3 years (2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (3): Babul, Moringa, Palash
- Likely, not fully verified (5): Amaltas, Bael, Indian rosewood, Karanj / Pongamia, Tamarind
- Caution (19): Amla, Arjun, Banyan, Ber, Bijasal, Casuarina, Chir pine, Gamhar, Jamun, Khair / Catechu, Mahua, Mango, Neem, Peepal, Salai / Indian frankincense, Semal, Siris, Sissoo / Shisham, Teak
- Ruled out (5): Sal: rainfall: 893 mm is below the stated minimum 1000; Khejri: elevation: 730.3 m is above its altitude limit (600 m); Bamboo (male bamboo): rainfall: 893 mm is below the stated minimum 1200; Baheda: rainfall: 893 mm is below the stated minimum 900; Deodar: elevation: 730.3 m is below its altitude range (1200 to 3500 m)
- Your checks:
  - [ ] gate (expected none, got warning)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Ber is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Bamboo is ruled out (expected yes, got yes)

### cherrapunji: Cherrapunji plateau grassland (Khasi Hills)
- Point 25.271366, 91.706878, radius 400 m. You saw: plateau grassland (moved here because the previous point had many water ponds and this one has very few).
- Terrain summary (radius 400 m): water/wet 0%, bare/built 0%, sparse vegetation or crops 53%, dense vegetation 46%; NDVI dry 0.116 to peak 0.612, big seasonal swing 98% (by year: 2023 96%, 2024 85%, 2025 98%)
- Building outlines (extra, not used for matching): 0.0% (2)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (0): none
- Likely, not fully verified (2): Indian rosewood, Peepal
- Caution (10): Ber, Casuarina, Deodar, Jamun, Neem, Palash, Sal, Semal, Siris, Tamarind
- Ruled out (20): Teak: rainfall: 4978 mm is above the stated maximum 4000; Sissoo / Shisham: rainfall: 4978 mm is above the stated maximum 4500; Babul: rainfall: 4978 mm is above the stated maximum 2300; Khejri: rainfall: 4978 mm is above the stated maximum 900; Arjun: elevation: 1333 m is above its altitude limit (1200 m); Mahua: elevation: 1333 m is above its altitude limit (1200 m); Karanj / Pongamia: rainfall: 4978 mm is above the stated maximum 2500; Banyan: rainfall: 4978 mm is above the stated maximum 4000; Bamboo (male bamboo): rainfall: 4978 mm is above the stated maximum 4200; Gamhar: elevation: 1333 m is above its altitude limit (1200 m); Amla: rainfall: 4978 mm is above the stated maximum 4200; Bael: elevation: 1333 m is above its altitude limit (1200 m); Moringa: elevation: 1333 m is above its altitude limit (1000 m); Mango: rainfall: 4978 mm is above the stated maximum 3500; Amaltas: elevation: 1333 m is above its altitude limit (1220 m); Baheda: elevation: 1333 m is above its altitude limit (1000 m); Bijasal: rainfall: 4978 mm is above the stated maximum 2000; Chir pine: rainfall: 4978 mm is above the stated maximum 2900; Salai / Indian frankincense: rainfall: 4978 mm is above the stated maximum 2000; Khair / Catechu: rainfall: 4978 mm is above the stated maximum 3800
- Your checks:
  - [ ] gate (expected none, got warning)
  - [x] Deodar is an option (expected yes, got yes)
  - [x] Siris is an option (expected yes, got yes)
  - [x] Palash is an option (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [x] Mango is ruled out (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)

### pampore: Pampore karewa farmland (Kashmir valley)
- Point 34.004022, 74.939165, radius 400 m. You saw: karewa terrace farmland.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 1%, sparse vegetation or crops 98%, dense vegetation 0%; NDVI dry 0.122 to peak 0.503, big seasonal swing 95% (by year: 2023 97%, 2024 98%, 2025 95%)
- Building outlines (extra, not used for matching): 0.1% (7)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (0): none
- Likely, not fully verified (1): Deodar
- Caution (3): Chir pine, Jamun, Siris
- Ruled out (28): Neem: elevation: 1603.7 m is above its altitude limit (1500 m); Teak: elevation: 1603.7 m is above its altitude limit (1200 m); Sal: elevation: 1603.7 m is above its altitude limit (1500 m); Sissoo / Shisham: elevation: 1603.7 m is above its altitude limit (1500 m); Babul: elevation: 1603.7 m is above its altitude limit (1340 m); Khejri: rainfall: 1388 mm is above the stated maximum 900; Arjun: elevation: 1603.7 m is above its altitude limit (1200 m); Mahua: elevation: 1603.7 m is above its altitude limit (1200 m); Karanj / Pongamia: elevation: 1603.7 m is above its altitude limit (1200 m); Peepal: elevation: 1603.7 m is above its altitude limit (1520 m); Banyan: elevation: 1603.7 m is above its altitude limit (1200 m); Tamarind: elevation: 1603.7 m is above its altitude limit (1500 m); Bamboo (male bamboo): temperature: 12.4 C is below the stated minimum 16; Gamhar: elevation: 1603.7 m is above its altitude limit (1200 m); Amla: temperature: 12.4 C is below the stated minimum 14; Bael: elevation: 1603.7 m is above its altitude limit (1200 m); Palash: elevation: 1603.7 m is above its altitude limit (1500 m); Moringa: elevation: 1603.7 m is above its altitude limit (1000 m); Casuarina: elevation: 1603.7 m is above its altitude limit (1400 m); Mango: elevation: 1603.7 m is above its altitude limit (1200 m); Semal: elevation: 1603.7 m is above its altitude limit (1500 m); Ber: elevation: 1603.7 m is above its altitude limit (1500 m); Amaltas: elevation: 1603.7 m is above its altitude limit (1220 m); Baheda: elevation: 1603.7 m is above its altitude limit (1000 m); Bijasal: elevation: 1603.7 m is above its altitude limit (1200 m); Indian rosewood: elevation: 1603.7 m is above its altitude limit (1500 m); Salai / Indian frankincense: elevation: 1603.7 m is above its altitude limit (1150 m); Khair / Catechu: elevation: 1603.7 m is above its altitude limit (1500 m)
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'cropland' (expected yes, got yes)
  - [x] Deodar is an option (expected yes, got yes)
  - [x] Siris is an option (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [x] Mango is ruled out (expected yes, got yes)
  - [x] Banyan is ruled out (expected yes, got yes)

### kolkata-core: Kolkata Bara Bazar core (Lower Gangetic delta (city))
- Point 22.578, 88.358, radius 400 m. You saw: dense built-up urban core.
- Terrain summary (radius 400 m): water/wet 1%, bare/built 82%, sparse vegetation or crops 17%, dense vegetation 0%; NDVI dry 0.07 to peak 0.245, big seasonal swing 11% (by year: 2023 8%, 2024 6%, 2025 11%)
- Building outlines (extra, not used for matching): 46.6% (3090)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: WARNING: 82% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted.
- Strong fit (2): Moringa, Palash
- Likely, not fully verified (4): Amaltas, Bael, Indian rosewood, Tamarind
- Caution (22): Amla, Arjun, Babul, Baheda, Bamboo (male bamboo), Banyan, Ber, Bijasal, Casuarina, Gamhar, Jamun, Karanj / Pongamia, Khair / Catechu, Mahua, Mango, Neem, Peepal, Salai / Indian frankincense, Semal, Siris, Sissoo / Shisham, Teak
- Ruled out (4): Sal: elevation: 13.3 m is below its altitude range (100 to 1500 m); Khejri: rainfall: 1882 mm is above the stated maximum 900; Deodar: elevation: 13.3 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 13.3 m is below its altitude range (400 to 2300 m)
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'built-up' (expected yes, got yes)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Peepal is an option (expected yes, got yes)
  - [x] Banyan is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)

### darjeeling: Darjeeling Chauk Bazaar (Eastern Himalaya)
- Point 27.0422, 88.2654, radius 400 m. You saw: dense hill town built-up.
- Terrain summary (radius 400 m): water/wet 61%, bare/built 13%, sparse vegetation or crops 14%, dense vegetation 12%; NDVI dry 0.015 to peak 0.328, big seasonal swing 45% (by year: 2023 42%, 2024 44%, 2025 45%)
- Building outlines (extra, not used for matching): 41.8% (2387)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: BLOCKED: 61% of the area reads as water or wet surface, so plants cannot be recommended here. WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (0): none
- Likely, not fully verified (0): none
- Caution (0): none
- Ruled out (31): Neem: elevation: 2079 m is above its altitude limit (1500 m); Teak: elevation: 2079 m is above its altitude limit (1200 m); Sal: elevation: 2079 m is above its altitude limit (1500 m); Sissoo / Shisham: elevation: 2079 m is above its altitude limit (1500 m); Babul: rainfall: 3550 mm is above the stated maximum 2300; Khejri: rainfall: 3550 mm is above the stated maximum 900; Arjun: elevation: 2079 m is above its altitude limit (1200 m); Mahua: elevation: 2079 m is above its altitude limit (1200 m); Jamun: elevation: 2079 m is above its altitude limit (1800 m); Karanj / Pongamia: rainfall: 3550 mm is above the stated maximum 2500; Peepal: elevation: 2079 m is above its altitude limit (1520 m); Banyan: elevation: 2079 m is above its altitude limit (1200 m); Tamarind: elevation: 2079 m is above its altitude limit (1500 m); Bamboo (male bamboo): temperature: 12.2 C is below the stated minimum 16; Gamhar: elevation: 2079 m is above its altitude limit (1200 m); Amla: temperature: 12.2 C is below the stated minimum 14; Bael: elevation: 2079 m is above its altitude limit (1200 m); Palash: elevation: 2079 m is above its altitude limit (1500 m); Moringa: elevation: 2079 m is above its altitude limit (1000 m); Casuarina: elevation: 2079 m is above its altitude limit (1400 m); Mango: rainfall: 3550 mm is above the stated maximum 3500; Semal: elevation: 2079 m is above its altitude limit (1500 m); Ber: elevation: 2079 m is above its altitude limit (1500 m); Siris: elevation: 2079 m is above its altitude limit (1800 m); Amaltas: elevation: 2079 m is above its altitude limit (1220 m); Baheda: elevation: 2079 m is above its altitude limit (1000 m); Bijasal: rainfall: 3550 mm is above the stated maximum 2000; Chir pine: rainfall: 3550 mm is above the stated maximum 2900; Indian rosewood: elevation: 2079 m is above its altitude limit (1500 m); Salai / Indian frankincense: rainfall: 3550 mm is above the stated maximum 2000; Khair / Catechu: elevation: 2079 m is above its altitude limit (1500 m)
- Your checks:
  - [ ] gate (expected warning, got blocked)
  - [ ] a warning mentions 'built-up' (expected yes, got no)
  - [ ] Deodar is an option (expected yes, got no)
  - [x] Mango is ruled out (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [x] Neem is ruled out (expected yes, got yes)

### kochi: Kochi Mattancherry (Malabar coast)
- Point 9.9575, 76.2545, radius 400 m. You saw: dense coastal town built-up.
- Terrain summary (radius 400 m): water/wet 1%, bare/built 37%, sparse vegetation or crops 51%, dense vegetation 11%; NDVI dry 0.194 to peak 0.354, big seasonal swing 11% (by year: 2023 20%, 2024 6%, 2025 11%)
- Building outlines (extra, not used for matching): 43.8% (2328)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: none
- Strong fit (1): Moringa
- Likely, not fully verified (1): Indian rosewood
- Caution (22): Amaltas, Amla, Arjun, Bael, Baheda, Bamboo (male bamboo), Banyan, Ber, Casuarina, Gamhar, Jamun, Khair / Catechu, Mahua, Mango, Neem, Palash, Peepal, Semal, Siris, Sissoo / Shisham, Tamarind, Teak
- Ruled out (8): Sal: elevation: 9 m is below its altitude range (100 to 1500 m); Babul: rainfall: 2960 mm is above the stated maximum 2300; Khejri: rainfall: 2960 mm is above the stated maximum 900; Karanj / Pongamia: rainfall: 2960 mm is above the stated maximum 2500; Bijasal: rainfall: 2960 mm is above the stated maximum 2000; Deodar: elevation: 9 m is below its altitude range (1200 to 3500 m); Chir pine: rainfall: 2960 mm is above the stated maximum 2900; Salai / Indian frankincense: rainfall: 2960 mm is above the stated maximum 2000
- Your checks:
  - [ ] gate (expected warning, got none)
  - [ ] a warning mentions 'built-up' (expected yes, got no)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Mango is an option (expected yes, got yes)
  - [x] Banyan is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)

### sundarbans: Sundarbans mangrove forest (Sundarbans delta)
- Point 22.105, 88.825, radius 400 m. You saw: closed-canopy mangrove forest.
- Terrain summary (radius 400 m): water/wet 1%, bare/built 0%, sparse vegetation or crops 10%, dense vegetation 89%; NDVI dry 0.42 to peak 0.798, big seasonal swing 93% (by year: 2023 94%, 2024 19%, 2025 93%)
- Building outlines (extra, not used for matching): 0.0% (0)
- Cache: store sqlite:sylvan_cache.db, terrain hit, soil hit, climate miss, footprints miss
- Warnings: none
- Strong fit (2): Moringa, Palash
- Likely, not fully verified (3): Amaltas, Indian rosewood, Tamarind
- Caution (21): Amla, Arjun, Babul, Bael, Baheda, Bamboo (male bamboo), Banyan, Ber, Casuarina, Gamhar, Jamun, Karanj / Pongamia, Khair / Catechu, Mahua, Mango, Neem, Peepal, Semal, Siris, Sissoo / Shisham, Teak
- Ruled out (6): Sal: elevation: 6.5 m is below its altitude range (100 to 1500 m); Khejri: rainfall: 2085 mm is above the stated maximum 900; Bijasal: rainfall: 2085 mm is above the stated maximum 2000; Deodar: elevation: 6.5 m is below its altitude range (1200 to 3500 m); Chir pine: elevation: 6.5 m is below its altitude range (400 to 2300 m); Salai / Indian frankincense: rainfall: 2085 mm is above the stated maximum 2000
- Your checks:
  - [ ] gate (expected warning, got none)
  - [ ] a warning mentions 'water' (expected yes, got no)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [x] Chir pine is ruled out (expected yes, got yes)
  - [x] Sal is ruled out (expected yes, got yes)

