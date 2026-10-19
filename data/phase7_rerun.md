# Phase 7: regional test report

Run on 2026-10-15. 1 site(s): 1 matched your expectations, 0 did not, 0 failed to run.

Your expectations were written before the run (see the commit history of phase7_sites.json). A mismatch is a finding to review: either the system or the expectation is wrong.

## Summary

| Site | Region | Gate: you / system | Rain mm | Temp C | pH | Texture | Elev m | Strong / Likely / Caution | Ruled out | Seconds | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bhopal-lake | Open water | blocked / blocked | 1360 | 25.1 | missing | missing | 506 | 0 / 0 / 0 | 2 | 16.5 | MATCH |

## Mismatches to review

None. Every expectation matched.
## Data coverage

- bhopal-lake: no value for pH, Texture

## Site details

### bhopal-lake: Bhopal Upper Lake (Open water)
- Point 23.249545700690536, 77.34386981384519, radius 400 m. You saw: Open water, middle of the lake.
- Terrain summary (radius 400 m): water/wet 100%, bare/built 0%, sparse vegetation or crops 0%, dense vegetation 0%; NDVI dry -0.233 to peak 0.249, big seasonal swing 98% (by year: 2023 96%, 2024 62%, 2025 98%)
- Cache: store postgres:localhost/sylvan, terrain hit, soil skipped (blocked site), climate miss
- Warnings: BLOCKED: 100% of the area reads as water or wet surface, so plants cannot be recommended here. WARNING: vegetation swings strongly between bare and green in 3 of 3 years (2023, 2024, 2025), which looks like active cropland (unvalidated rule). Check whether the land is in use.
- Strong fit (0): none
- Likely, not fully verified (0): none
- Caution (0): none
- Ruled out (2): Khejri: rainfall: 1360 mm is above the stated maximum 900; Deodar: elevation: 506 m is below its altitude range (1200 to 3500 m)
- No data to assess: Banyan, Bamboo (male bamboo), Amla, Semal, Bijasal, Chir pine
- Your checks:
  - [x] gate (expected blocked, got blocked)

