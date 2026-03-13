"""
tests/test_market.py — analytiske tests for MarketAssumptions.
"""

import math

from pension.market import MarketAssumptions
from tests.fixtures.models import NUL_MARKED, STANDARD_MARKED


# ---------------------------------------------------------------------------
# afkast
# ---------------------------------------------------------------------------

def test_afkast_nul_volatilitet():
    """Med σ=0 er afkast(0) = exp(rf/12) - 1."""
    m = MarketAssumptions(rf=0.03, volatilitet=0.0)
    forventet = math.exp(0.03 / 12.0) - 1.0
    assert math.isclose(m.afkast(0.0), forventet, rel_tol=1e-12)


def test_afkast_nul_rente_nul_volatilitet():
    """Med rf=0 og σ=0 er afkast(0) = 0."""
    assert math.isclose(NUL_MARKED.afkast(0.0), 0.0, abs_tol=1e-15)


def test_afkast_positiv_epsilon_giver_hoejere_afkast():
    """Positiv stød giver højere afkast end deterministisk (ε=0)."""
    assert STANDARD_MARKED.afkast(1.0) > STANDARD_MARKED.afkast(0.0)
    assert STANDARD_MARKED.afkast(0.0) > STANDARD_MARKED.afkast(-1.0)


def test_afkast_symmetri():
    """Afkast er monotont i epsilon."""
    m = STANDARD_MARKED
    assert m.afkast(2.0) > m.afkast(1.0) > m.afkast(0.0) > m.afkast(-1.0) > m.afkast(-2.0)


# ---------------------------------------------------------------------------
# deterministisk_afkast
# ---------------------------------------------------------------------------

def test_deterministisk_afkast_lig_afkast_nul():
    assert math.isclose(
        STANDARD_MARKED.deterministisk_afkast(),
        STANDARD_MARKED.afkast(0.0),
        rel_tol=1e-15,
    )


def test_deterministisk_afkast_nul_marked():
    assert math.isclose(NUL_MARKED.deterministisk_afkast(), 0.0, abs_tol=1e-15)
