"""
test_imports.py — verificerer at alle moduler kan importeres og at de
forventede klasser og funktioner eksisterer med korrekte navne.

Dette er trin-1-tests: strukturtests der ikke kræver implementering.
"""

import inspect


def test_policy_module_importable():
    import pension.policy  # noqa: F401


def test_policy_exports_product_type():
    from pension.policy import ProductType

    assert hasattr(ProductType, "LIVRENTE")
    assert hasattr(ProductType, "RATEPENSION")
    assert hasattr(ProductType, "ALDERSOPSPARING")


def test_policy_exports_policy_class():
    from pension.policy import Policy

    assert inspect.isclass(Policy)


def test_policy_has_required_fields():
    from pension.policy import Policy

    fields = {f.name for f in Policy.__dataclass_fields__.values()}
    required = {
        "alder",
        "depot",
        "doedsfaldssum",
        "praemie",
        "omkostningspct",
        "produkt",
        "udbetalingsstart_alder",
    }
    assert required <= fields


def test_policy_has_er_i_udbetalingsperiode():
    from pension.policy import Policy

    assert callable(getattr(Policy, "er_i_udbetalingsperiode", None))


def test_policy_has_alder_ved_trin():
    from pension.policy import Policy

    assert callable(getattr(Policy, "alder_ved_trin", None))


def test_biometrics_module_importable():
    import pension.biometrics  # noqa: F401


def test_biometric_model_class_exists():
    from pension.biometrics import BiometricModel

    assert inspect.isclass(BiometricModel)


def test_biometric_model_has_required_methods():
    from pension.biometrics import BiometricModel

    assert callable(getattr(BiometricModel, "intensitet", None))
    assert callable(getattr(BiometricModel, "maanedlig_intensitet", None))
    assert callable(getattr(BiometricModel, "annuity_pv", None))


def test_market_module_importable():
    import pension.market  # noqa: F401


def test_market_assumptions_class_exists():
    from pension.market import MarketAssumptions

    assert inspect.isclass(MarketAssumptions)


def test_market_assumptions_has_required_fields():
    from pension.market import MarketAssumptions

    fields = {f.name for f in MarketAssumptions.__dataclass_fields__.values()}
    assert {"rf", "volatilitet"} <= fields


def test_market_assumptions_has_afkast():
    from pension.market import MarketAssumptions

    assert callable(getattr(MarketAssumptions, "afkast", None))


def test_market_assumptions_has_deterministisk_afkast():
    from pension.market import MarketAssumptions

    assert callable(getattr(MarketAssumptions, "deterministisk_afkast", None))


def test_projection_module_importable():
    import pension.projection  # noqa: F401


def test_projection_exports_trin_resultat():
    from pension.projection import TrinResultat

    assert inspect.isclass(TrinResultat)


def test_trin_resultat_has_required_fields():
    from pension.projection import TrinResultat

    fields = {f.name for f in TrinResultat.__dataclass_fields__.values()}
    required = {
        "t",
        "alder",
        "depot",
        "depot_efter",
        "doedsintensitet",
        "nettorisiko",
        "risikopraemie",
        "afkast",
        "ydelse",
        "pal_skat",
        "aldersopsparing_depot",
        "aldersopsparing_depot_efter",
    }
    assert required <= fields


def test_projection_exports_projicér():
    from pension.projection import projicér

    assert callable(projicér)


def test_projection_exports_projicér_portefølje():
    from pension.projection import projicér_portefølje

    assert callable(projicér_portefølje)


def test_output_module_importable():
    import pension.output  # noqa: F401


def test_output_exports_trin_til_dataframe():
    from pension.output import trin_til_dataframe

    assert callable(trin_til_dataframe)


def test_output_exports_portefølje_til_dataframe():
    from pension.output import portefølje_til_dataframe

    assert callable(portefølje_til_dataframe)


def test_output_exports_gem_csv():
    from pension.output import gem_csv

    assert callable(gem_csv)
