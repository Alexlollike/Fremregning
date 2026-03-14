"""
tests/fixtures/policies.py — deterministiske policefixtures til tests.

Indeholder færdigkonfigurerede Policy-instanser til de analytiske kontrolcases
beskrevet i PLANNING.md:
- Rente=0, konstant dødelighed
- Rente=0, ingen dødelighed
- Dødelighed=0, konstant rente
- Dødsfaldsum = depot (nettorisiko er nul)
- Livrente i udbetalingsperiode
"""

from pension.policy import Policy, ProductType

# Standardpolicy til brug i tests: ratepension, midt i opsparingsperioden
STANDARD_RATEPENSION = Policy(
    alder=40.0,
    depot=100_000.0,
    doedsfaldssum=200_000.0,
    praemie=2_000.0,
    omkostningspct=0.005 / 12,
    produkt=ProductType.RATEPENSION,
    udbetalingsstart_alder=67.0,
    maanedlig_ydelse=0.0,
)

# Policy med dødsfaldsum lig depot → nettorisiko = 0
NULRISIKO_POLICY = Policy(
    alder=50.0,
    depot=100_000.0,
    doedsfaldssum=100_000.0,
    praemie=0.0,
    omkostningspct=0.0,
    produkt=ProductType.RATEPENSION,
    udbetalingsstart_alder=67.0,
    maanedlig_ydelse=0.0,
)

# Livrente i udbetalingsperiode (alder >= udbetalingsstart)
LIVRENTE_UDBETALING = Policy(
    alder=67.0,
    depot=500_000.0,
    doedsfaldssum=0.0,
    praemie=0.0,
    omkostningspct=0.005 / 12,
    produkt=ProductType.LIVRENTE,
    udbetalingsstart_alder=67.0,
    maanedlig_ydelse=0.0,
)
