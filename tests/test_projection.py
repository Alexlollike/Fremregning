"""
tests/test_projection.py — analytiske kontrolcases for projicér().
"""

import math

import pytest

from pension.policy import Policy, ProductType, RATEPENSION_INDBETALINGSLOFT
from pension.projection import projicér, projicér_portefølje
from tests.fixtures.models import NUL_MARKED, NUL_BIOMETRI, STANDARD_BIOMETRI, STANDARD_MARKED
from tests.fixtures.policies import (
    STANDARD_RATEPENSION,
    NULRISIKO_POLICY,
    LIVRENTE_UDBETALING,
    RATEPENSION_UDBETALING,
)


# ---------------------------------------------------------------------------
# Rente=0, ingen dødelighed → depot vokser med præmie·t
# ---------------------------------------------------------------------------

def test_depot_vokser_lineaert_med_praemie():
    """Med r=0, μ=0, α=0 og S=0 vokser depotet med præmie per trin."""
    police = Policy(
        alder=40.0,
        depot=100_000.0,
        doedsfaldssum=0.0,
        praemie=2_000.0,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for i, r in enumerate(resultater):
        forventet_depot = 100_000.0 + i * 2_000.0
        assert math.isclose(r.depot, forventet_depot, rel_tol=1e-9), (
            f"Trin {i}: forventet {forventet_depot}, fik {r.depot}"
        )


# ---------------------------------------------------------------------------
# Nettorisiko=0 → risikopræmie=0 (μ=0)
# ---------------------------------------------------------------------------

def test_risikopraemie_nul_naar_mu_nul():
    """Med nuldødelighed er risikopræmien altid nul."""
    resultater = projicér(NULRISIKO_POLICY, NUL_MARKED, NUL_BIOMETRI, antal_trin=24)
    for r in resultater:
        assert r.risikopraemie == 0.0
        assert r.nettorisiko == 0.0


# ---------------------------------------------------------------------------
# Ingen præmie, ingen dødelighed, r=0, α=0 → depot konstant
# ---------------------------------------------------------------------------

def test_depot_konstant_uden_praemie_rente_omkostning():
    police = Policy(
        alder=40.0,
        depot=200_000.0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=24)
    for r in resultater:
        assert math.isclose(r.depot, 200_000.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Livrente i udbetalingsperiode: depot er positivt og aftager
# ---------------------------------------------------------------------------

def test_livrente_depot_aftager():
    """Depot bør være positivt og faldende i udbetalingsperioden."""
    resultater = projicér(LIVRENTE_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=120)
    # Depot starter positivt
    assert resultater[0].depot > 0.0
    # Depot aftager over tid (deterministisk, ingen afkast, ingen omkostninger fraregnet)
    depoter = [r.depot for r in resultater]
    assert depoter[-1] < depoter[0]


def test_livrente_ydelse_positiv_i_udbetalingsperiode():
    resultater = projicér(LIVRENTE_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=60)
    for r in resultater:
        assert r.ydelse > 0.0


def test_livrente_ingen_risikopraemie_i_udbetalingsperiode():
    resultater = projicér(LIVRENTE_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.risikopraemie == 0.0
        assert r.nettorisiko == 0.0


# ---------------------------------------------------------------------------
# Opsparingsperiode: ydelse=0
# ---------------------------------------------------------------------------

def test_ingen_ydelse_i_opsparingsperiode():
    resultater = projicér(STANDARD_RATEPENSION, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.ydelse == 0.0


# ---------------------------------------------------------------------------
# PAL-skat: nul ved nul afkast
# ---------------------------------------------------------------------------

def test_pal_nul_ved_nul_afkast():
    resultater = projicér(STANDARD_RATEPENSION, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.pal_skat == 0.0


# ---------------------------------------------------------------------------
# projicér_portefølje
# ---------------------------------------------------------------------------

def test_projektaer_portefolje_returnerer_ét_resultat_per_police():
    portefølje = [STANDARD_RATEPENSION, NULRISIKO_POLICY]
    alle = projicér_portefølje(portefølje, NUL_MARKED, NUL_BIOMETRI, antal_trin=6)
    assert len(alle) == 2
    assert all(len(res) == 6 for res in alle)


def test_projektaer_portefolje_tom_liste():
    alle = projicér_portefølje([], NUL_MARKED, NUL_BIOMETRI, antal_trin=6)
    assert alle == []


# ---------------------------------------------------------------------------
# Ratepension i udbetalingsperiode
# ---------------------------------------------------------------------------

def test_ratepension_ydelse_positiv_i_udbetalingsperiode():
    """Ydelse er positiv i udbetalingsperioden (RATEPENSION)."""
    resultater = projicér(RATEPENSION_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=60)
    for r in resultater:
        assert r.ydelse > 0.0


def test_ratepension_depot_aftager_i_udbetalingsperiode():
    """Depot er positivt og aftager i udbetalingsperioden med nul afkast."""
    resultater = projicér(RATEPENSION_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=60)
    depoter = [r.depot for r in resultater]
    assert depoter[0] > 0.0
    assert depoter[-1] < depoter[0]


def test_ratepension_depot_nul_ved_udbetalingsperiodens_slutning():
    """Med nul rente og nul omkostninger er depot ~0 efter N·12 måneder."""
    n = 15
    police = Policy(
        alder=67.0,
        depot=600_000.0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=n,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=n * 12)
    assert math.isclose(resultater[-1].depot_efter, 0.0, abs_tol=1e-6), (
        f"Depotet er ikke nul ved slutning: {resultater[-1].depot_efter}"
    )


def test_ratepension_konstant_ydelse_nul_rente():
    """Med nul rente er ydelse konstant (D_0 / (N·12)) i hele udbetalingsperioden."""
    n = 10
    d0 = 480_000.0
    police = Policy(
        alder=67.0,
        depot=d0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=n,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=n * 12)
    forventet_ydelse = d0 / (n * 12)
    for r in resultater:
        assert math.isclose(r.ydelse, forventet_ydelse, rel_tol=1e-9), (
            f"Trin {r.t}: forventet {forventet_ydelse:.4f}, fik {r.ydelse:.4f}"
        )


def test_ratepension_ingen_risikopraemie_i_udbetalingsperiode():
    """Ingen risikopræmie i udbetalingsperioden (dækning ophørt)."""
    resultater = projicér(RATEPENSION_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.risikopraemie == 0.0
        assert r.nettorisiko == 0.0


def test_ratepension_depot_sporet_i_trin_resultat():
    """ratepension_depot følger depot for standalone RATEPENSION-police."""
    resultater = projicér(RATEPENSION_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert math.isclose(r.ratepension_depot, r.depot, rel_tol=1e-12)
        assert math.isclose(r.ratepension_depot_efter, r.depot_efter, rel_tol=1e-12)


def test_livrente_ratepension_depot_nul():
    """ratepension_depot er 0 for livrente-policer."""
    resultater = projicér(LIVRENTE_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.ratepension_depot == 0.0
        assert r.ratepension_depot_efter == 0.0


# ---------------------------------------------------------------------------
# Indbetalingsloft
# ---------------------------------------------------------------------------

def test_indbetalingsloft_raise_ved_overskridelse():
    """ValueError kastes hvis månedlig præmie * 12 > indbetalingsloft."""
    with pytest.raises(ValueError, match="indbetalingsloftet"):
        Policy(
            alder=40.0,
            depot=0.0,
            doedsfaldssum=0.0,
            praemie=RATEPENSION_INDBETALINGSLOFT / 12 + 1.0,
            omkostningspct=0.0,
            produkt=ProductType.RATEPENSION,
            udbetalingsstart_alder=67.0,
            udbetalingsperiode_aar=15,
        )


def test_indbetalingsloft_præcis_grænse_tilladt():
    """Præmie præcis på loftet er tilladt."""
    p = Policy(
        alder=40.0,
        depot=0.0,
        doedsfaldssum=0.0,
        praemie=RATEPENSION_INDBETALINGSLOFT / 12,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=15,
    )
    assert math.isclose(p.praemie * 12, RATEPENSION_INDBETALINGSLOFT, rel_tol=1e-12)


def test_udbetalingsperiode_aar_ugyldig():
    """ValueError kastes ved udbetalingsperiode_aar uden for [10, 20]."""
    for aar in [9, 21]:
        with pytest.raises(ValueError, match="10.20 år"):
            Policy(
                alder=40.0,
                depot=0.0,
                doedsfaldssum=0.0,
                praemie=0.0,
                omkostningspct=0.0,
                produkt=ProductType.RATEPENSION,
                udbetalingsstart_alder=67.0,
                udbetalingsperiode_aar=aar,
            )
