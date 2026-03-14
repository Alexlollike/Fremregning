"""
tests/test_biometrics.py — analytiske tests for BiometricModel.
"""

import math

import pytest

from pension.biometrics import BiometricModel
from tests.fixtures.models import NUL_BIOMETRI, STANDARD_BIOMETRI


# ---------------------------------------------------------------------------
# intensitet
# ---------------------------------------------------------------------------

def test_intensitet_nul_naar_ab_nul():
    assert NUL_BIOMETRI.intensitet(40.0) == 0.0
    assert NUL_BIOMETRI.intensitet(0.0) == 0.0
    assert NUL_BIOMETRI.intensitet(80.0) == 0.0


def test_intensitet_gompertz_led_alene():
    m = BiometricModel(A=0.0, B=0.0001, c=1.1)
    assert math.isclose(m.intensitet(0.0), 0.0001, rel_tol=1e-12)
    assert math.isclose(m.intensitet(10.0), 0.0001 * 1.1 ** 10, rel_tol=1e-12)


def test_intensitet_makeham_og_gompertz():
    m = BiometricModel(A=0.001, B=0.0001, c=1.1)
    forventet = 0.001 + 0.0001 * 1.1 ** 40
    assert math.isclose(m.intensitet(40.0), forventet, rel_tol=1e-12)


def test_intensitet_standard_positiv():
    assert STANDARD_BIOMETRI.intensitet(30.0) > 0.0
    assert STANDARD_BIOMETRI.intensitet(80.0) > STANDARD_BIOMETRI.intensitet(30.0)


# ---------------------------------------------------------------------------
# maanedlig_intensitet
# ---------------------------------------------------------------------------

def test_maanedlig_intensitet_er_intensitet_divideret_med_12():
    m = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)
    alder = 55.0
    assert math.isclose(m.maanedlig_intensitet(alder), m.intensitet(alder) / 12.0, rel_tol=1e-12)


def test_maanedlig_intensitet_nul():
    assert NUL_BIOMETRI.maanedlig_intensitet(60.0) == 0.0


# ---------------------------------------------------------------------------
# annuity_pv
# ---------------------------------------------------------------------------

def test_annuity_pv_nul_doedelighed_nul_rente():
    """Med nuldødelighed og rente=0 er ä_x = 120 - alder (resterende år til terminalsbetingelse)."""
    m = BiometricModel(A=0.0, B=0.0, c=1.0)
    alder = 67.0
    forventet = 120.0 - alder  # dä/dt = -1, ä(120)=0 → ä(alder) = 120-alder
    resultat = m.annuity_pv(alder, rente=0.0)
    assert math.isclose(resultat, forventet, rel_tol=1e-6)


def test_annuity_pv_nul_doedelighed_positiv_rente():
    """Med nuldødelighed er ä_x = Δt · Σ_{k=0}^{K-1} e^{-δ·k·Δt} (geometrisk sum, eksakt)."""
    m = BiometricModel(A=0.0, B=0.0, c=1.0)
    alder = 67.0
    rente = 0.04
    delta = math.log(1.0 + rente)
    dt = 1.0 / 12.0
    K = int((120.0 - alder) * 12)
    # Eksakt geometrisk sum for frem-summation med kontinuert diskont
    q = math.exp(-delta * dt)
    forventet = dt * (1.0 - q ** K) / (1.0 - q)
    resultat = m.annuity_pv(alder, rente)
    assert math.isclose(resultat, forventet, rel_tol=1e-12)


def test_annuity_pv_falder_med_alder():
    """Ældre individer har lavere livrente-nutidsværdi."""
    m = STANDARD_BIOMETRI
    assert m.annuity_pv(60.0, 0.03) > m.annuity_pv(70.0, 0.03)


def test_annuity_pv_falder_med_rente():
    """Højere rente giver lavere nutidsværdi."""
    m = STANDARD_BIOMETRI
    assert m.annuity_pv(67.0, 0.01) > m.annuity_pv(67.0, 0.05)


def test_annuity_pv_positiv():
    assert STANDARD_BIOMETRI.annuity_pv(67.0, 0.03) > 0.0
