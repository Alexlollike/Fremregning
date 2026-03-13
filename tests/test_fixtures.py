"""
test_fixtures.py — verificerer at fixtures kan importeres og instansieres korrekt.

Sikrer at testfixtures i tests/fixtures/ er gyldige og kan bruges i
kommende analytiske kontrolcases.
"""

from tests.fixtures.models import (
    NUL_BIOMETRI,
    NUL_MARKED,
    STANDARD_BIOMETRI,
    STANDARD_MARKED,
)
from tests.fixtures.policies import (
    LIVRENTE_UDBETALING,
    NULRISIKO_POLICY,
    STANDARD_RATEPENSION,
)


def test_standard_ratepension_is_policy():
    from pension.policy import Policy

    assert isinstance(STANDARD_RATEPENSION, Policy)


def test_nulrisiko_policy_har_ens_depot_og_sum():
    assert NULRISIKO_POLICY.depot == NULRISIKO_POLICY.doedsfaldssum


def test_livrente_udbetaling_alder_lig_start():
    assert LIVRENTE_UDBETALING.alder == LIVRENTE_UDBETALING.udbetalingsstart_alder


def test_nul_marked_instans():
    from pension.market import MarketAssumptions

    assert isinstance(NUL_MARKED, MarketAssumptions)
    assert NUL_MARKED.rf == 0.0
    assert NUL_MARKED.volatilitet == 0.0


def test_standard_marked_instans():
    from pension.market import MarketAssumptions

    assert isinstance(STANDARD_MARKED, MarketAssumptions)


def test_nul_biometri_instans():
    from pension.biometrics import BiometricModel

    assert isinstance(NUL_BIOMETRI, BiometricModel)


def test_standard_biometri_instans():
    from pension.biometrics import BiometricModel

    assert isinstance(STANDARD_BIOMETRI, BiometricModel)
