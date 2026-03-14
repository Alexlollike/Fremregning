"""
tests/test_projection.py — analytiske kontrolcases for projicér().
"""

import math

import pytest

from datetime import date

from pension.policy import Policy, ProductType, RATEPENSION_INDBETALINGSLOFT
from pension.projection import projicér, projicér_portefølje, SIMULATION_START_DATO, _dato_ved_trin
from tests.fixtures.models import NUL_MARKED, NUL_BIOMETRI, STANDARD_BIOMETRI, STANDARD_MARKED
from tests.fixtures.policies import (
    STANDARD_RATEPENSION,
    NULRISIKO_POLICY,
    LIVRENTE_UDBETALING,
    RATEPENSION_UDBETALING,
    ALDERSOPSPARING_UDBETALING,
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
# Ratepension: rp_depot ekskluderes fra nettorisiko (ingen dødelighedsarv)
# ---------------------------------------------------------------------------

def test_ratepension_nettorisiko_ekskluderer_rp_depot():
    """For ratepension tæller rp_depot ikke som depotoffset i nettorisiko.

    nettorisiko = doedsfaldssum - (depot - rp_depot) = doedsfaldssum for standalone RATEPENSION.
    """
    police = Policy(
        alder=40.0,
        depot=100_000.0,
        doedsfaldssum=200_000.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=15,
    )
    resultater = projicér(police, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=1)
    trin = resultater[0]
    # rp_depot = depot, så nettorisiko = doedsfaldssum (ikke doedsfaldssum - depot)
    assert math.isclose(trin.nettorisiko, 200_000.0, rel_tol=1e-9), (
        f"Forventet nettorisiko=200000, fik {trin.nettorisiko}"
    )
    mu = STANDARD_BIOMETRI.maanedlig_intensitet(40.0)
    assert math.isclose(trin.risikopraemie, mu * 200_000.0, rel_tol=1e-9), (
        f"Forventet risikopraemie={mu * 200_000.0:.6f}, fik {trin.risikopraemie:.6f}"
    )


def test_livrente_nettorisiko_upaavirktet_af_rp_depot_aendring():
    """For livrente er rp_depot=0, så nettorisiko = doedsfaldssum - depot (uændret)."""
    police = Policy(
        alder=40.0,
        depot=100_000.0,
        doedsfaldssum=200_000.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.LIVRENTE,
        udbetalingsstart_alder=67.0,
    )
    resultater = projicér(police, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=1)
    trin = resultater[0]
    # rp_depot = 0 for LIVRENTE, nettorisiko = doedsfaldssum - depot = 100k
    assert math.isclose(trin.nettorisiko, 100_000.0, rel_tol=1e-9), (
        f"Forventet nettorisiko=100000, fik {trin.nettorisiko}"
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


# ---------------------------------------------------------------------------
# Kalendertid og _dato_ved_trin
# ---------------------------------------------------------------------------

def test_dato_ved_trin_nul():
    """t=0 returnerer start_dato uændret."""
    start = date(2027, 1, 1)
    assert _dato_ved_trin(start, 0) == date(2027, 1, 1)


def test_dato_ved_trin_midt_paa_aar():
    """t=6 fra januar 2027 → juli 2027."""
    assert _dato_ved_trin(date(2027, 1, 1), 6) == date(2027, 7, 1)


def test_dato_ved_trin_aarsskifte():
    """t=12 fra januar 2027 → januar 2028."""
    assert _dato_ved_trin(date(2027, 1, 1), 12) == date(2028, 1, 1)


def test_dato_ved_trin_flere_aar():
    """t=24 fra januar 2027 → januar 2029."""
    assert _dato_ved_trin(date(2027, 1, 1), 24) == date(2029, 1, 1)


def test_simulation_start_dato_er_2027():
    """Standardstart er 1. januar 2027."""
    assert SIMULATION_START_DATO == date(2027, 1, 1)


# ---------------------------------------------------------------------------
# aarlig_indbetaling og dato i TrinResultat
# ---------------------------------------------------------------------------

def test_dato_i_trin_resultat():
    """TrinResultat indeholder korrekt kalenderdato."""
    resultater = projicér(STANDARD_RATEPENSION, NUL_MARKED, NUL_BIOMETRI, antal_trin=3)
    assert resultater[0].dato == date(2027, 1, 1)
    assert resultater[1].dato == date(2027, 2, 1)
    assert resultater[2].dato == date(2027, 3, 1)


def test_dato_med_brugerdefineret_start():
    """start_dato-parameteren propageres korrekt."""
    start = date(2030, 6, 1)
    resultater = projicér(STANDARD_RATEPENSION, NUL_MARKED, NUL_BIOMETRI,
                          antal_trin=3, start_dato=start)
    assert resultater[0].dato == date(2030, 6, 1)
    assert resultater[1].dato == date(2030, 7, 1)
    assert resultater[2].dato == date(2030, 8, 1)


def test_aarlig_indbetaling_akkumulerer_inden_for_aar():
    """aarlig_indbetaling vokser med praemie hvert trin i opsparingsperioden."""
    praemie = 2_000.0
    police = Policy(
        alder=40.0,
        depot=0.0,
        doedsfaldssum=0.0,
        praemie=praemie,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=15,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for i, r in enumerate(resultater):
        assert math.isclose(r.aarlig_indbetaling, praemie * (i + 1), rel_tol=1e-12), (
            f"Trin {i}: forventet {praemie * (i + 1):.2f}, fik {r.aarlig_indbetaling:.2f}"
        )


def test_aarlig_indbetaling_nulstilles_ved_nyt_aar():
    """aarlig_indbetaling nulstilles ved kalenderårsskifte (t=12)."""
    praemie = 2_000.0
    police = Policy(
        alder=40.0,
        depot=0.0,
        doedsfaldssum=0.0,
        praemie=praemie,
        omkostningspct=0.0,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=15,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=14)
    # t=11 (december 2027): 12 × praemie
    assert math.isclose(resultater[11].aarlig_indbetaling, 12 * praemie, rel_tol=1e-12)
    # t=12 (januar 2028): nulstillet → 1 × praemie
    assert math.isclose(resultater[12].aarlig_indbetaling, praemie, rel_tol=1e-12)
    # t=13 (februar 2028): 2 × praemie
    assert math.isclose(resultater[13].aarlig_indbetaling, 2 * praemie, rel_tol=1e-12)


def test_aarlig_indbetaling_nul_i_udbetalingsperiode():
    """aarlig_indbetaling er 0 i udbetalingsperioden (ingen præmier)."""
    resultater = projicér(RATEPENSION_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.aarlig_indbetaling == 0.0


# ---------------------------------------------------------------------------
# Aldersopsparing: éngangsydelse ved pensionering
# ---------------------------------------------------------------------------

def test_aldersopsparing_ydelse_ved_forste_udbetalingstrin():
    """Hele ao_depot udbetales som éngangsydelse i første udbetalingstrin."""
    d0 = ALDERSOPSPARING_UDBETALING.depot
    resultater = projicér(ALDERSOPSPARING_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    assert math.isclose(resultater[0].ydelse, d0, rel_tol=1e-9), (
        f"Forventet ydelse={d0}, fik {resultater[0].ydelse}"
    )


def test_aldersopsparing_depot_nul_efter_udbetaling():
    """Depot er 0 fra og med trin 1 (efter éngangsydelsen)."""
    resultater = projicér(ALDERSOPSPARING_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater[1:]:
        assert r.depot == 0.0, f"Trin {r.t}: forventet depot=0, fik {r.depot}"


def test_aldersopsparing_ydelse_nul_efter_forste_trin():
    """Ydelse er 0 i alle trin efter det første (allerede udbetalt)."""
    resultater = projicér(ALDERSOPSPARING_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater[1:]:
        assert r.ydelse == 0.0, f"Trin {r.t}: forventet ydelse=0, fik {r.ydelse}"


def test_aldersopsparing_ingen_risikopraemie_i_udbetalingsperiode():
    """Ingen risikopræmie i udbetalingsperioden (dækning ophørt)."""
    resultater = projicér(ALDERSOPSPARING_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.risikopraemie == 0.0
        assert r.nettorisiko == 0.0


def test_aldersopsparing_ao_depot_sporet_i_opsparingsperiode():
    """aldersopsparing_depot følger depot i opsparingsperioden."""
    police = Policy(
        alder=40.0,
        depot=100_000.0,
        doedsfaldssum=0.0,
        praemie=2_000.0,
        omkostningspct=0.0,
        produkt=ProductType.ALDERSOPSPARING,
        udbetalingsstart_alder=67.0,
    )
    resultater = projicér(police, NUL_MARKED, NUL_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert math.isclose(r.aldersopsparing_depot, r.depot, rel_tol=1e-12), (
            f"Trin {r.t}: ao_depot={r.aldersopsparing_depot} != depot={r.depot}"
        )


def test_aldersopsparing_ao_depot_nul_efter_udbetaling():
    """aldersopsparing_depot_efter er 0 fra og med udbetalingstrinnet."""
    resultater = projicér(ALDERSOPSPARING_UDBETALING, NUL_MARKED, NUL_BIOMETRI, antal_trin=3)
    # Trin 0: ao_depot_efter = 0 (udbetalt)
    assert resultater[0].aldersopsparing_depot_efter == 0.0
    # Trin 1+: ao_depot = 0 og ao_depot_efter = 0
    for r in resultater[1:]:
        assert r.aldersopsparing_depot == 0.0
        assert r.aldersopsparing_depot_efter == 0.0


def test_livrente_ao_depot_nul():
    """aldersopsparing_depot er 0 for livrente-policer."""
    resultater = projicér(LIVRENTE_UDBETALING, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=12)
    for r in resultater:
        assert r.aldersopsparing_depot == 0.0
        assert r.aldersopsparing_depot_efter == 0.0


def test_aldersopsparing_nettorisiko_nul_med_nul_doedsfaldssum():
    """Med dødsfaldsum=0 og ao_depot==depot er nettorisiko=0 i opsparingsperioden."""
    police = Policy(
        alder=40.0,
        depot=200_000.0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.ALDERSOPSPARING,
        udbetalingsstart_alder=67.0,
    )
    resultater = projicér(police, NUL_MARKED, STANDARD_BIOMETRI, antal_trin=1)
    assert math.isclose(resultater[0].nettorisiko, 0.0, abs_tol=1e-9), (
        f"Forventet nettorisiko=0, fik {resultater[0].nettorisiko}"
    )
