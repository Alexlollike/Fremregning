"""
tests/fixtures/markov_fixtures.py — standardfixtures til Markov-tests.

Indeholder MarkovModel og MarkovProdukt instanser med kendte parametre
til brug i analytiske kontrolcases.

Tilstandsrum:
    - 2-tilstand: aktiv, doed (reduktionscase til eksisterende model)
    - 3-tilstand: aktiv, invalid, doed (fuld model med restitution)
    - 4-tilstand: aktiv, invalid, genkøbt, doed (inkl. genkøbsabsorption)
"""

from pension.biometrics import BiometricModel
from pension.markov import MarkovModel, Tilstand
from pension.markov_produkt import MarkovProdukt, OvgangsCashflow, TilstandsCashflow

# ---------------------------------------------------------------------------
# Biometriske hjælpemodeller
# ---------------------------------------------------------------------------

NUL_BIOMETRI = BiometricModel(A=0.0, B=0.0, c=1.0)
STANDARD_BIOMETRI = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)

# ---------------------------------------------------------------------------
# 2-tilstandsmodeller (aktiv / doed)
# ---------------------------------------------------------------------------

NUL_MARKOV_2 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={},  # ingen overgange → π uforandret
)

STANDARD_MARKOV_2 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={
        ("aktiv", "doed"): STANDARD_BIOMETRI.intensitet,
    },
)

# ---------------------------------------------------------------------------
# 3-tilstandsmodeller (aktiv / invalid / doed)
# ---------------------------------------------------------------------------

# Nul-intensiteter: ingen overgange
NUL_MARKOV_3 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("invalid"),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={},
)

# Standard 3-tilstandsmodel med restitution
# μ_ai = 0.005 p.a. (invalidiseringsrate), μ_ia = 0.01 p.a. (restitutionsrate)
# μ_id = 1.5 × standarddødelighed (forhøjet for invalide)
STANDARD_MARKOV_3 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("invalid"),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={
        ("aktiv",   "invalid"): lambda a: 0.005,
        ("aktiv",   "doed"):    STANDARD_BIOMETRI.intensitet,
        ("invalid", "aktiv"):   lambda a: 0.01,
        ("invalid", "doed"):    lambda a: STANDARD_BIOMETRI.intensitet(a) * 1.5,
    },
)

# ---------------------------------------------------------------------------
# 4-tilstandsmodeller (aktiv / invalid / genkøbt / doed)
# ---------------------------------------------------------------------------

# Nul-intensiteter: ingen overgange
NUL_MARKOV_4 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("invalid"),
        Tilstand("genkøbt", absorberende=True),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={},
)

# Standard 4-tilstandsmodel: aktiv, invalid, genkøbt (lapsus), doed
# μ_ag = 0.03 p.a. (genkøbsrate fra aktiv — kun opsparingsperioden)
# Øvrige intensiteter som i STANDARD_MARKOV_3.
STANDARD_MARKOV_4 = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("invalid"),
        Tilstand("genkøbt", absorberende=True),
        Tilstand("doed", absorberende=True),
    ],
    intensiteter={
        ("aktiv",   "invalid"):  lambda a: 0.005,
        ("aktiv",   "genkøbt"):  lambda a: 0.03,
        ("aktiv",   "doed"):     STANDARD_BIOMETRI.intensitet,
        ("invalid", "aktiv"):    lambda a: 0.01,
        ("invalid", "doed"):     lambda a: STANDARD_BIOMETRI.intensitet(a) * 1.5,
    },
)

# ---------------------------------------------------------------------------
# Produktfixtures
# ---------------------------------------------------------------------------

def simpelt_opsparingsprodukt(
    depot: float,
    praemie: float,
    doedsfaldssum: float,
    omkostningspct: float,
    markov_model: MarkovModel,
) -> MarkovProdukt:
    """
    Opsparingsprodukt med livsforsikring — ingen ydelse i opsparingsperioden.

    Livsforsikringen (S) udbetales ved overgang til doed fra alle levende tilstande.
    Nettorisiko = S − D_s(t); tilbagebetales til poolen ved negativ nettorisiko.

    Parametre
    ---------
    depot : float
        Startdepot D_0.
    praemie : float
        Månedlig præmie π.
    doedsfaldssum : float
        Dødsfaldsum S.
    omkostningspct : float
        Månedlig depotomkostning α.
    markov_model : MarkovModel
        Bruges til at finde levende (ikke-absorberende) tilstandsnavne.
    """
    levende = [t.navn for t in markov_model.tilstande if not t.absorberende]

    tilstands_cf = [
        TilstandsCashflow(s, lambda a, d, pi=praemie: pi, tidspunkt="pre")
        for s in levende
    ]

    overgangs_cf = [
        OvgangsCashflow(s, "doed", lambda a, d, S=doedsfaldssum: S - d)
        for s in levende
    ]

    return MarkovProdukt(
        navn="simpelt_opsparing",
        tilstands_cashflows=tilstands_cf,
        overgangscashflows=overgangs_cf,
        omkostningspct=omkostningspct,
        initial_depot={"aktiv": depot},
    )


def simpelt_opsparingsprodukt_med_genkøb(
    depot: float,
    praemie: float,
    doedsfaldssum: float,
    genkøbsrate: float,
    omkostningspct: float,
    markov_model: MarkovModel,
) -> MarkovProdukt:
    """
    Opsparingsprodukt med livsforsikring og genkøbsmulighed.

    Bygger videre på `simpelt_opsparingsprodukt`:
    - Præmie indbetales månedligt fra alle levende tilstande.
    - Livsforsikringen (S − D) udbetales ved overgang til doed.
    - Ved overgang aktiv → genkøbt udbetales hele depotet D_aktiv.

    Parametre
    ---------
    depot : float
        Startdepot D_0.
    praemie : float
        Månedlig præmie π.
    doedsfaldssum : float
        Dødsfaldsum S.
    genkøbsrate : float
        Ubrugt her — intensiteten styres af markov_model. Parameteren er med
        for at gøre kaldsstedet selvdokumenterende.
    omkostningspct : float
        Månedlig depotomkostning α.
    markov_model : MarkovModel
        Skal indeholde tilstanden "genkøbt" som absorberende.
    """
    levende = [t.navn for t in markov_model.tilstande if not t.absorberende]

    tilstands_cf = [
        TilstandsCashflow(s, lambda a, d, pi=praemie: pi, tidspunkt="pre")
        for s in levende
    ]

    overgangs_cf = [
        OvgangsCashflow(s, "doed", lambda a, d, S=doedsfaldssum: S - d)
        for s in levende
    ]
    # Genkøb: hele depotet udbetales ved overgang aktiv → genkøbt
    overgangs_cf.append(
        OvgangsCashflow("aktiv", "genkøbt", lambda a, d: d)
    )

    return MarkovProdukt(
        navn="simpelt_opsparing_med_genkøb",
        tilstands_cashflows=tilstands_cf,
        overgangscashflows=overgangs_cf,
        omkostningspct=omkostningspct,
        initial_depot={"aktiv": depot},
    )


def nul_produkt(depot: float, markov_model: MarkovModel) -> MarkovProdukt:
    """
    Minimalt produkt: ingen præmie, ingen ydelse, ingen livsforsikring.
    Depot vokser kun ved investeringsafkast.
    """
    return MarkovProdukt(
        navn="nul_produkt",
        tilstands_cashflows=[],
        overgangscashflows=[],
        omkostningspct=0.0,
        initial_depot={"aktiv": depot},
    )
