"""
test_policy.py — analytiske tests for Policy-dataklassen.

Dækker:
- alder_ved_trin(): korrekt aldersberegning ved t=0, t=1, t=12, t=360
- er_i_udbetalingsperiode(): korrekt overgang ved præcis grænse og
  måneden før/efter
- grænsetilfælde: alder == udbetalingsstart_alder ved t=0
- alle tre produkttyper bruger samme logik
"""

import pytest

from pension.policy import Policy, ProductType


@pytest.fixture
def ratepension():
    return Policy(
        alder=40.0,
        depot=100_000.0,
        doedsfaldssum=200_000.0,
        praemie=2_000.0,
        omkostningspct=0.005 / 12,
        produkt=ProductType.RATEPENSION,
        udbetalingsstart_alder=67.0,
    )


@pytest.fixture
def livrente_ved_start():
    """Police hvor alder == udbetalingsstart ved t=0."""
    return Policy(
        alder=67.0,
        depot=500_000.0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=ProductType.LIVRENTE,
        udbetalingsstart_alder=67.0,
    )


# ---------------------------------------------------------------------------
# alder_ved_trin
# ---------------------------------------------------------------------------

def test_alder_ved_trin_t0(ratepension):
    assert ratepension.alder_ved_trin(0) == 40.0


def test_alder_ved_trin_t1(ratepension):
    assert ratepension.alder_ved_trin(1) == pytest.approx(40.0 + 1 / 12)


def test_alder_ved_trin_t12(ratepension):
    assert ratepension.alder_ved_trin(12) == pytest.approx(41.0)


def test_alder_ved_trin_t360(ratepension):
    """30 år frem → alder 70."""
    assert ratepension.alder_ved_trin(360) == pytest.approx(70.0)


def test_alder_ved_trin_stor_t(ratepension):
    """Generel formel: alder + t/12."""
    t = 324  # 27 år → alder 67
    assert ratepension.alder_ved_trin(t) == pytest.approx(67.0)


# ---------------------------------------------------------------------------
# er_i_udbetalingsperiode
# ---------------------------------------------------------------------------

def test_ikke_udbetaling_ved_t0(ratepension):
    """Alder 40, start 67 → opsparingsperiode ved t=0."""
    assert ratepension.er_i_udbetalingsperiode(0) is False


def test_ikke_udbetaling_maaned_foer_grænse(ratepension):
    """En måned før alder 67: t = 27*12 - 1 = 323."""
    assert ratepension.er_i_udbetalingsperiode(323) is False


def test_udbetaling_præcis_ved_grænse(ratepension):
    """Præcis ved alder 67: t = 27*12 = 324."""
    assert ratepension.er_i_udbetalingsperiode(324) is True


def test_udbetaling_efter_grænse(ratepension):
    """En måned efter alder 67: t = 325."""
    assert ratepension.er_i_udbetalingsperiode(325) is True


def test_livrente_udbetaling_fra_t0(livrente_ved_start):
    """Alder == udbetalingsstart → udbetalingsperiode fra t=0."""
    assert livrente_ved_start.er_i_udbetalingsperiode(0) is True


def test_livrente_udbetaling_fremtidige_trin(livrente_ved_start):
    assert livrente_ved_start.er_i_udbetalingsperiode(120) is True


# ---------------------------------------------------------------------------
# Alle tre produkttyper — samme logik
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("produkt", list(ProductType))
def test_alle_produkttyper_alder_logik(produkt):
    p = Policy(
        alder=50.0,
        depot=0.0,
        doedsfaldssum=0.0,
        praemie=0.0,
        omkostningspct=0.0,
        produkt=produkt,
        udbetalingsstart_alder=65.0,
    )
    assert p.alder_ved_trin(0) == 50.0
    assert p.er_i_udbetalingsperiode(0) is False
    assert p.er_i_udbetalingsperiode(180) is True  # t=180 → alder 65.0
