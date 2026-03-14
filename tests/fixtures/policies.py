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
    udbetalingsperiode_aar=15,
)

# Policy med dødsfaldsum = 0 → nettorisiko = 0
# For RATEPENSION går depotet til efterladte ved død, så S=0 giver nul nettorisiko.
NULRISIKO_POLICY = Policy(
    alder=50.0,
    depot=100_000.0,
    doedsfaldssum=0.0,
    praemie=0.0,
    omkostningspct=0.0,
    produkt=ProductType.RATEPENSION,
    udbetalingsstart_alder=67.0,
    udbetalingsperiode_aar=15,
)

# Ratepension i udbetalingsperiode (alder >= udbetalingsstart), 15-årig udbetaling
RATEPENSION_UDBETALING = Policy(
    alder=67.0,
    depot=500_000.0,
    doedsfaldssum=0.0,
    praemie=0.0,
    omkostningspct=0.0,
    produkt=ProductType.RATEPENSION,
    udbetalingsstart_alder=67.0,
    udbetalingsperiode_aar=15,
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
)

# Aldersopsparing ved pensionering (alder >= udbetalingsstart) — udbetales som éngangsbeløb
ALDERSOPSPARING_UDBETALING = Policy(
    alder=67.0,
    depot=500_000.0,
    doedsfaldssum=0.0,
    praemie=0.0,
    omkostningspct=0.0,
    produkt=ProductType.ALDERSOPSPARING,
    udbetalingsstart_alder=67.0,
)
