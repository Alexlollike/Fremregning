# PLANNING.md

## Nuværende fokus

Cashflow-projektionsmodul til forretningscase, driftsplan og produktdesign.

## Næste trin

1. Opret repo-struktur med tomme Python-moduler og docstrings (jf. README.md)
2. Implementer `Policy` og `Product` dataklasser i `policy.py`
3. Implementer `BiometricModel` i `biometrics.py` (Gompertz-Makeham)
4. Implementer `MarketAssumptions` i `market.py` (rentekurve, certainty equivalent)
5. Implementer `projicér()` i `projection.py` for ét produkt, én police
6. Udvid `projicér()` til portefølje af 5-10 repræsentative policer
7. Implementer CSV-output i `output.py` alignet med Solvens II QRT
8. Skriv tests i `tests/` med analytiske kontrolcases

## Teststrategi

Alle projektionsfunktioner skal have analytiske kontrolcases. Ingen ny funktionalitet
merges uden tilhørende test.

Prioriterede analytiske kontrolcases:
- Rente = 0, konstant dødelighed: depot og cashflows har lukket løsning
- Rente = 0, ingen dødelighed: ren opsparingscase
- Dødelighed = 0, konstant rente: ren investeringscase
- Dødsfaldsum = depot ($S = D_t$): nettorisiko er nul, ingen risikopræmie
- Livrente i udbetalingsperiode: depot udtyndes præcis til nul i forventning

Tests ligger i `tests/` og bruger pytest. Fixtures med deterministiske inputparametre
ligger i `tests/fixtures/`.

## Beslutninger

- To tilstande: levende og død
- Ét fælles depot per police investeret i unit-link portefølje
- Fast dødsfaldsum $S$ — max-funktion udelades foreløbigt
- Negative nettorisiko tilladt (dødelighedsgevinst)
- Én finansiel model og én biometrisk model — stress-scenarier er out of scope indtil videre
- PAL-skat opgøres separat og påvirker ikke depotet

## Out of scope indtil videre

- Solvens II stress-scenarier
- Invalidedækning
- Genkøb/lapsation
- Max-funktion for dødsfaldsum
