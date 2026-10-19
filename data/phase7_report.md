# Phase 7: regional test report

Run on 2026-10-14. 10 site(s): 3 matched your expectations, 6 did not, 1 failed to run.

Your expectations were written before the run (see the commit history of phase7_sites.json). A mismatch is a finding to review: either the system or the expectation is wrong.

## Summary

| Site | Region | Gate: you / system | Rain mm | Temp C | pH | Texture | Elev m | Strong / Likely / Caution | Ruled out | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| jaisalmer | Hot arid | none / warning | 224 | 27.2 | 8.0 | medium | 192.6 | 0 / 1 / 15 | 10 | 53.1 | MISMATCH |
| ratnagiri | Wet coast | none / none | 3364 | 26.5 | 6.3 | medium | 56.3 | 3 / 3 / 14 | 6 | 27.8 | MISMATCH |
| shimla | Hills | warning / none | 1313 | 10.9 | 5.82 | medium | 2261.9 | 0 / 0 / 12 | 14 | 30.4 | MISMATCH |
| varanasi | Gangetic plain | warning / warning | 1203 | 25.7 | 7.24 | medium | 82.5 | 2 / 12 / 10 | 2 | 27.9 | MATCH |
| solapur | Deccan plateau | warning / none | 928 | 27.6 | 7.45 | heavy | 443.2 | 2 / 5 / 16 | 3 | 25.3 | MISMATCH |
| jagdalpur | Forest belt | none / none | 1705 | 24.7 | 5.88 | medium | 558.8 | 2 / 10 / 12 | 2 | 28.6 | MATCH |
| puri | Coast | none / none | 1762 | 26.8 | 6.55 | medium | 13.0 | 5 / 12 / 7 | 2 | 29.3 | MATCH |
| morena-ravines | Degraded land | none / none | 786 | 25.4 | 7.79 | medium | 161.0 | 2 / 9 / 11 | 4 | 34.0 | MISMATCH |
| bhopal-lake | Open water | blocked / - | - | - | - | - | - | - | - | - | ERROR |
| leh | Extreme cold | none / warning | 836 | 4.5 | 8.08 | light | 3304.2 | 0 / 1 / 5 | 20 | 29.2 | MISMATCH |

## Mismatches to review

### jaisalmer (Jaisalmer open scrub)
- gate: you expected **none**, the system gave **warning**
- Sal is ruled out: you expected **yes**, the system gave **no**
- Bamboo is ruled out: you expected **yes**, the system gave **no**

### ratnagiri (Ratnagiri open laterite)
- Mango is an option: you expected **yes**, the system gave **no**

### shimla (Shimla slope)
- gate: you expected **warning**, the system gave **none**
- a warning mentions 'built-up': you expected **yes**, the system gave **no**

### solapur (Solapur open land)
- gate: you expected **warning**, the system gave **none**
- a warning mentions 'cropland': you expected **yes**, the system gave **no**
- Sal is ruled out: you expected **yes**, the system gave **no**

### morena-ravines (Chambal ravines)
- Teak is ruled out: you expected **yes**, the system gave **no**

### leh (Leh open ground)
- gate: you expected **none**, the system gave **warning**

### bhopal-lake: ERROR
- RuntimeError: No soil source returned values. SoilGrids 2.0 (Earth Engine): all values empty | OpenLandMap (Earth Engine): all values empty

## Data coverage

Every measured value was present at every site.

## Site details

### jaisalmer: Jaisalmer open scrub (Hot arid)
- Point 26.908896940521768, 70.65072955088517, radius 400 m. You saw: Open arid desert, sandy soil, sparse dry scrub.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 100%, sparse vegetation or crops 0%, dense vegetation 0%; NDVI dry 0.048 to peak 0.096, big seasonal swing 0% (by year: 2023 0%, 2024 5%, 2025 0%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: WARNING: 100% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted. WARNING: the land never greens up. It could be barren, built-up, or non-natural ground (ash, mined or filled land), where soil data does not apply.
- Strong fit (0): none
- Likely, not fully verified (1): Ber
- Caution (15): Amaltas, Arjun, Babul, Bael, Baheda, Casuarina, Gamhar, Indian rosewood, Khejri, Mahua, Palash, Peepal, Sal, Siris, Tamarind
- Ruled out (10): Neem: rainfall: 224 mm is below the stated minimum 250; Teak: rainfall: 224 mm is below the stated minimum 600; Sissoo / Shisham: rainfall: 224 mm is below the stated minimum 300; Jamun: rainfall: 224 mm is below the stated minimum 800; Karanj / Pongamia: rainfall: 224 mm is below the stated minimum 400; Moringa: rainfall: 224 mm is below the stated minimum 500; Mango: rainfall: 224 mm is below the stated minimum 300; Deodar: elevation: 192.6 m is below its altitude range (1200 to 3500 m); Salai / Indian frankincense: rainfall: 224 mm is below the stated minimum 500; Khair / Catechu: rainfall: 224 mm is below the stated minimum 500
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [ ] gate (expected none, got warning)
  - [x] Khejri is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [ ] Sal is ruled out (expected yes, got no)
  - [ ] Bamboo is ruled out (expected yes, got no)
  - [x] Deodar is ruled out (expected yes, got yes)

### ratnagiri: Ratnagiri open laterite (Wet coast)
- Point 17.025, 73.33, radius 400 m. You saw: Exposed rocky laterite plateau, low patchy scrub, no large trees.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 10%, sparse vegetation or crops 27%, dense vegetation 63%; NDVI dry 0.445 to peak 0.637, big seasonal swing 23% (by year: 2023 35%, 2024 37%, 2025 23%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (3): Jamun, Moringa, Palash
- Likely, not fully verified (3): Gamhar, Indian rosewood, Peepal
- Caution (14): Amaltas, Arjun, Bael, Baheda, Ber, Casuarina, Khair / Catechu, Mahua, Neem, Sal, Siris, Sissoo / Shisham, Tamarind, Teak
- Ruled out (6): Babul: rainfall: 3364 mm is above the stated maximum 2300; Khejri: rainfall: 3364 mm is above the stated maximum 900; Karanj / Pongamia: rainfall: 3364 mm is above the stated maximum 2500; Mango: rainfall: 3364 mm is above the stated maximum 2600; Deodar: elevation: 56.3 m is below its altitude range (1200 to 3500 m); Salai / Indian frankincense: rainfall: 3364 mm is above the stated maximum 2000
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected none, got none)
  - [ ] Mango is an option (expected yes, got no)
  - [x] Jamun is an option (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Babul is ruled out (expected yes, got yes)

### shimla: Shimla slope (Hills)
- Point 31.135, 77.225, radius 400 m. You saw: Forested slope with some houses, small-town edge.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 7%, sparse vegetation or crops 27%, dense vegetation 66%; NDVI dry 0.321 to peak 0.664, big seasonal swing 76% (by year: 2023 52%, 2024 53%, 2025 76%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (0): none
- Likely, not fully verified (0): none
- Caution (12): Amaltas, Arjun, Babul, Deodar, Karanj / Pongamia, Khair / Catechu, Mahua, Mango, Sal, Salai / Indian frankincense, Sissoo / Shisham, Tamarind
- Ruled out (14): Neem: elevation: 2261.9 m is above its altitude limit (1500 m); Teak: elevation: 2261.9 m is above its altitude limit (1200 m); Khejri: rainfall: 1313 mm is above the stated maximum 900; Jamun: temperature: 10.9 C is below the stated minimum 12; Peepal: elevation: 2261.9 m is above its altitude limit (1520 m); Gamhar: elevation: 2261.9 m is above its altitude limit (1200 m); Bael: elevation: 2261.9 m is above its altitude limit (1200 m); Palash: elevation: 2261.9 m is above its altitude limit (1500 m); Moringa: elevation: 2261.9 m is above its altitude limit (1000 m); Casuarina: elevation: 2261.9 m is above its altitude limit (1400 m); Ber: elevation: 2261.9 m is above its altitude limit (1500 m); Siris: elevation: 2261.9 m is above its altitude limit (1800 m); Baheda: elevation: 2261.9 m is above its altitude limit (1000 m); Indian rosewood: elevation: 2261.9 m is above its altitude limit (1500 m)
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [ ] gate (expected warning, got none)
  - [ ] a warning mentions 'built-up' (expected yes, got no)
  - [x] Deodar is an option (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Moringa is ruled out (expected yes, got yes)

### varanasi: Varanasi farmland (Gangetic plain)
- Point 25.32, 82.85, radius 400 m. You saw: Flat, actively cultivated crop fields with visible plot boundaries.
- Terrain summary (radius 400 m): water/wet 1%, bare/built 6%, sparse vegetation or crops 76%, dense vegetation 16%; NDVI dry 0.193 to peak 0.681, big seasonal swing 87% (by year: 2023 91%, 2024 83%, 2025 87%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (2): Mango, Moringa
- Likely, not fully verified (12): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Sal, Siris, Tamarind, Teak
- Caution (10): Arjun, Babul, Casuarina, Jamun, Khair / Catechu, Mahua, Neem, Palash, Salai / Indian frankincense, Sissoo / Shisham
- Ruled out (2): Khejri: rainfall: 1203 mm is above the stated maximum 900; Deodar: elevation: 82.5 m is below its altitude range (1200 to 3500 m)
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected warning, got warning)
  - [x] a warning mentions 'cropland' (expected yes, got yes)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Sissoo is an option (expected yes, got yes)
  - [x] Mango is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### solapur: Solapur open land (Deccan plateau)
- Point 17.55, 75.9, radius 400 m. You saw: Flat farmland, dark soil, little vertical cover.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 21%, sparse vegetation or crops 72%, dense vegetation 7%; NDVI dry 0.204 to peak 0.552, big seasonal swing 73% (by year: 2023 92%, 2024 89%, 2025 73%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (2): Babul, Moringa
- Likely, not fully verified (5): Amaltas, Bael, Indian rosewood, Karanj / Pongamia, Tamarind
- Caution (16): Arjun, Baheda, Ber, Casuarina, Gamhar, Jamun, Mahua, Mango, Neem, Palash, Peepal, Sal, Salai / Indian frankincense, Siris, Sissoo / Shisham, Teak
- Ruled out (3): Khejri: rainfall: 928 mm is above the stated maximum 900; Deodar: elevation: 443.2 m is below its altitude range (1200 to 3500 m); Khair / Catechu: pH: 7.45 is above the stated maximum 7
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [ ] gate (expected warning, got none)
  - [ ] a warning mentions 'cropland' (expected yes, got no)
  - [x] Neem is an option (expected yes, got yes)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Ber is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)
  - [ ] Sal is ruled out (expected yes, got no)

### jagdalpur: Jagdalpur forest (Forest belt)
- Point 18.877690070696538, 81.9662936057062, radius 400 m. You saw: Dense unbroken forest canopy, dead centre of the forest.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 0%, sparse vegetation or crops 0%, dense vegetation 100%; NDVI dry 0.595 to peak 0.816, big seasonal swing 13% (by year: 2023 82%, 2024 85%, 2025 13%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (2): Jamun, Moringa
- Likely, not fully verified (10): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Peepal, Sal, Siris, Tamarind
- Caution (12): Arjun, Babul, Casuarina, Karanj / Pongamia, Khair / Catechu, Mahua, Mango, Neem, Palash, Salai / Indian frankincense, Sissoo / Shisham, Teak
- Ruled out (2): Khejri: rainfall: 1705 mm is above the stated maximum 900; Deodar: elevation: 558.8 m is below its altitude range (1200 to 3500 m)
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Sal is an option (expected yes, got yes)
  - [x] Teak is an option (expected yes, got yes)
  - [x] Khejri is ruled out (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### puri: Puri sandy ground (Coast)
- Point 19.815, 85.875, radius 400 m. You saw: Open sandy coastal dunes with low coastal vegetation.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 2%, sparse vegetation or crops 34%, dense vegetation 64%; NDVI dry 0.388 to peak 0.679, big seasonal swing 64% (by year: 2023 73%, 2024 69%, 2025 64%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (5): Arjun, Jamun, Moringa, Palash, Sissoo / Shisham
- Likely, not fully verified (12): Amaltas, Bael, Baheda, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Sal, Siris, Tamarind, Teak
- Caution (7): Babul, Casuarina, Khair / Catechu, Mahua, Mango, Neem, Salai / Indian frankincense
- Ruled out (2): Khejri: rainfall: 1762 mm is above the stated maximum 900; Deodar: elevation: 13 m is below its altitude range (1200 to 3500 m)
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Casuarina is an option (expected yes, got yes)
  - [x] Deodar is ruled out (expected yes, got yes)

### morena-ravines: Chambal ravines (Degraded land)
- Point 26.685, 77.935, radius 400 m. You saw: Eroded barren badlands with deep branching gullies (ravines).
- Terrain summary (radius 400 m): water/wet 0%, bare/built 3%, sparse vegetation or crops 59%, dense vegetation 38%; NDVI dry 0.275 to peak 0.641, big seasonal swing 91% (by year: 2023 89%, 2024 90%, 2025 91%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: none
- Strong fit (2): Babul, Moringa
- Likely, not fully verified (9): Amaltas, Bael, Ber, Gamhar, Indian rosewood, Karanj / Pongamia, Peepal, Siris, Tamarind
- Caution (11): Arjun, Baheda, Casuarina, Khejri, Mahua, Mango, Neem, Palash, Sal, Sissoo / Shisham, Teak
- Ruled out (4): Jamun: rainfall: 786 mm is below the stated minimum 800; Deodar: elevation: 161 m is below its altitude range (1200 to 3500 m); Salai / Indian frankincense: pH: 7.79 is above the stated maximum 7.4; Khair / Catechu: pH: 7.79 is above the stated maximum 7
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected none, got none)
  - [x] Babul is an option (expected yes, got yes)
  - [x] Khejri is an option (expected yes, got yes)
  - [x] Ber is an option (expected yes, got yes)
  - [ ] Teak is ruled out (expected yes, got no)
  - [x] Deodar is ruled out (expected yes, got yes)

### leh: Leh open ground (Extreme cold)
- Point 34.08, 77.65, radius 400 m. You saw: Barren high valley floor, rock and gravel, no trees, about 3500 m.
- Terrain summary (radius 400 m): water/wet 0%, bare/built 100%, sparse vegetation or crops 0%, dense vegetation 0%; NDVI dry 0.029 to peak 0.055, big seasonal swing 0% (by year: 2023 0%, 2024 0%, 2025 0%)
- Cache: store postgres:localhost/sylvan, terrain miss, soil miss, climate miss
- Warnings: WARNING: 100% is bare or built-up and the satellite signal cannot tell these apart. If it is built-up, nothing can be planted. WARNING: the land never greens up. It could be barren, built-up, or non-natural ground (ash, mined or filled land), where soil data does not apply.
- Strong fit (0): none
- Likely, not fully verified (1): Mahua
- Caution (5): Amaltas, Arjun, Deodar, Sal, Tamarind
- Ruled out (20): Neem: elevation: 3304.2 m is above its altitude limit (1500 m); Teak: elevation: 3304.2 m is above its altitude limit (1200 m); Sissoo / Shisham: temperature: 4.5 C is below the stated minimum 5; Babul: temperature: 4.5 C is below the stated minimum 10; Khejri: temperature: 4.5 C is below the stated minimum 6; Jamun: temperature: 4.5 C is below the stated minimum 12; Karanj / Pongamia: temperature: 4.5 C is below the stated minimum 10; Peepal: elevation: 3304.2 m is above its altitude limit (1520 m); Gamhar: elevation: 3304.2 m is above its altitude limit (1200 m); Bael: elevation: 3304.2 m is above its altitude limit (1200 m); Palash: elevation: 3304.2 m is above its altitude limit (1500 m); Moringa: elevation: 3304.2 m is above its altitude limit (1000 m); Casuarina: elevation: 3304.2 m is above its altitude limit (1400 m); Mango: temperature: 4.5 C is below the stated minimum 8; Ber: temperature: 4.5 C is below the stated minimum 7; Siris: elevation: 3304.2 m is above its altitude limit (1800 m); Baheda: elevation: 3304.2 m is above its altitude limit (1000 m); Indian rosewood: elevation: 3304.2 m is above its altitude limit (1500 m); Salai / Indian frankincense: temperature: 4.5 C is below the stated minimum 7; Khair / Catechu: temperature: 4.5 C is below the stated minimum 7
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [ ] gate (expected none, got warning)
  - [x] Neem is ruled out (expected yes, got yes)
  - [x] Teak is ruled out (expected yes, got yes)
  - [x] Mango is ruled out (expected yes, got yes)

