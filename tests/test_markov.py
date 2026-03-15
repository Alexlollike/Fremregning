"""
tests/test_markov.py — analytiske kontrolcases for Markov-modellen.

Teststrategien følger samme filosofi som test_projection.py:
lukket-form validering med nul-intensiteter, nulrente og kendte betingelser.

Testgrupper:
    1. MarkovModel: Q-matrix, P-matrix, validering, π-opdatering
    2. Reduktionscase: 2-tilstand → sammenligning med projicér()
    3. Nul-intensiteter: π(t) = π(0) for alle t
    4. Absorption: høj intensitet → π_doed → 1
    5. Depot: nul-cashflow → depot vokser kun ved afkast
    6. Cashflow: præmie og ydelse præcist bogført
    7. Overgangsydelse: livsforsikring (S - D) korrekt vægtet
    8. Genkøbt: absorberende tilstand med hel-depot-udbetaling
"""

import math

import pytest

from pension.market import MarketAssumptions
from pension.markov import MarkovModel, Tilstand
from pension.markov_produkt import MarkovProdukt, OvgangsCashflow, TilstandsCashflow
from pension.markov_projection import markov_projicér
from tests.fixtures.markov_fixtures import (
    NUL_BIOMETRI,
    NUL_MARKOV_2,
    NUL_MARKOV_3,
    NUL_MARKOV_4,
    STANDARD_BIOMETRI,
    STANDARD_MARKOV_2,
    STANDARD_MARKOV_3,
    STANDARD_MARKOV_4,
    nul_produkt,
    simpelt_opsparingsprodukt,
    simpelt_opsparingsprodukt_med_genkøb,
)
from tests.fixtures.models import NUL_MARKED, STANDARD_MARKED

# ---------------------------------------------------------------------------
# 1. MarkovModel: Q- og P-matrix
# ---------------------------------------------------------------------------


class TestMarkovModel:
    def test_q_matrix_nul_intensiteter(self):
        """Ingen intensiteter → Q er nulmatrix."""
        q = NUL_MARKOV_2.q_matrix(50.0)
        for række in q:
            for v in række:
                assert math.isclose(v, 0.0)

    def test_q_matrix_diagonal_er_negativ_rækkesum(self):
        """Diagonal = −Σ off-diagonale elementer."""
        q = STANDARD_MARKOV_2.q_matrix(50.0)
        n = len(q)
        for i in range(n):
            off_sum = sum(q[i][j] for j in range(n) if j != i)
            assert math.isclose(q[i][i], -off_sum, rel_tol=1e-12)

    def test_p_matrix_rækker_summer_til_1(self):
        """Alle rækker i P summer til 1."""
        for alder in [30.0, 50.0, 70.0]:
            p = STANDARD_MARKOV_3.p_matrix(alder)
            for i, række in enumerate(p):
                assert math.isclose(sum(række), 1.0, rel_tol=1e-12), (
                    f"Alder {alder}, række {i}: sum={sum(række)}"
                )

    def test_p_matrix_off_diagonale_ikke_negative(self):
        """Off-diagonale elementer i P er ≥ 0."""
        p = STANDARD_MARKOV_3.p_matrix(50.0)
        n = len(p)
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert p[i][j] >= -1e-12, f"P[{i}][{j}] = {p[i][j]:.6f} < 0"

    def test_validér_kaster_ikke_for_gyldige_modeller(self):
        """validér() kaster ingen fejl for gyldige modeller."""
        NUL_MARKOV_2.validér()
        STANDARD_MARKOV_2.validér()
        NUL_MARKOV_3.validér()
        STANDARD_MARKOV_3.validér()

    def test_opdater_pi_summer_til_1(self):
        """π(t+1) summerer til 1 efter opdatering."""
        pi = STANDARD_MARKOV_3.initial_pi("aktiv")
        for _ in range(120):
            pi = STANDARD_MARKOV_3.opdater_pi(pi, 50.0)
        assert math.isclose(sum(pi), 1.0, rel_tol=1e-10)

    def test_opdater_pi_nul_intensiteter_uforandret(self):
        """Med nul-intensiteter forbliver π uforandret."""
        pi0 = [0.6, 0.4]
        pi1 = NUL_MARKOV_2.opdater_pi(pi0, 50.0)
        assert math.isclose(pi1[0], 0.6, rel_tol=1e-12)
        assert math.isclose(pi1[1], 0.4, rel_tol=1e-12)

    def test_absorberende_tilstand_vokser_monotont(self):
        """π_doed øges eller forbliver uændret for alle t."""
        pi = STANDARD_MARKOV_2.initial_pi("aktiv")
        forrige_doed = pi[1]
        for _ in range(60):
            pi = STANDARD_MARKOV_2.opdater_pi(pi, 50.0)
            assert pi[1] >= forrige_doed - 1e-12
            forrige_doed = pi[1]

    def test_initial_pi_kun_én_tilstand(self):
        """initial_pi returnerer vektor med 1 i starttilstand."""
        pi = STANDARD_MARKOV_3.initial_pi("aktiv")
        assert math.isclose(pi[0], 1.0)
        assert math.isclose(pi[1], 0.0)
        assert math.isclose(pi[2], 0.0)

    def test_ukendt_tilstand_kaster_fejl(self):
        """Ukendt tilstandsnavn kaster ValueError."""
        with pytest.raises(ValueError):
            NUL_MARKOV_2.initial_pi("blah")


# ---------------------------------------------------------------------------
# 2. Nul-intensiteter: π(t) = π(0), depot vokser som forventet
# ---------------------------------------------------------------------------


class TestNulIntensiteter:
    def test_pi_uforandret_ved_nul_intensiteter(self):
        """Ingen overgange → π(t) = π(0) for alle t."""
        produkt = nul_produkt(100_000.0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 12)
        for r in resultater:
            assert math.isclose(r.pi[0], 1.0, rel_tol=1e-12), f"Trin {r.t}: π_aktiv={r.pi[0]}"
            assert math.isclose(r.pi[1], 0.0, abs_tol=1e-12), f"Trin {r.t}: π_doed={r.pi[1]}"

    def test_depot_uforandret_ved_nulrente_og_nul_cashflows(self):
        """r=0, α=0, ingen cashflows → D(t) = D(0) for alle t."""
        depot0 = 100_000.0
        produkt = nul_produkt(depot0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 12)
        for r in resultater:
            assert math.isclose(r.depot_per_tilstand["aktiv"], depot0, rel_tol=1e-12)
            assert math.isclose(r.forventet_depot, depot0, rel_tol=1e-12)

    def test_forventet_depot_lig_betinget_ved_pi_lik_1(self):
        """Når π_aktiv = 1 og π_doed = 0: E[D] = D_aktiv."""
        depot0 = 200_000.0
        produkt = nul_produkt(depot0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 6)
        for r in resultater:
            assert math.isclose(r.forventet_depot, r.depot_per_tilstand["aktiv"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# 3. Præmie: depot vokser korrekt
# ---------------------------------------------------------------------------


class TestPraemie:
    def test_depot_vokser_med_praemie_ved_nulrente(self):
        """r=0, α=0, ingen livsforsikring, præmie=π → D(t) = D(0) + t·π."""
        depot0 = 100_000.0
        praemie = 2_000.0
        produkt = MarkovProdukt(
            navn="praemie_test",
            tilstands_cashflows=[
                TilstandsCashflow("aktiv", lambda a, d: praemie, tidspunkt="pre"),
            ],
            overgangscashflows=[],
            omkostningspct=0.0,
            initial_depot={"aktiv": depot0},
        )
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 40.0, 12)
        for i, r in enumerate(resultater):
            forventet = depot0 + i * praemie
            assert math.isclose(r.depot_per_tilstand["aktiv"], forventet, rel_tol=1e-9), (
                f"Trin {i}: forventet {forventet}, fik {r.depot_per_tilstand['aktiv']}"
            )

    def test_forventet_ydelse_er_nul_uden_ydelse(self):
        """Ingen ydelse-cashflows → forventet_ydelse ≈ 0 (kun overgangsydelse mulig)."""
        produkt = MarkovProdukt(
            navn="kun_praemie",
            tilstands_cashflows=[
                TilstandsCashflow("aktiv", lambda a, d: 1_000.0, tidspunkt="pre"),
            ],
            overgangscashflows=[],
            omkostningspct=0.0,
            initial_depot={"aktiv": 100_000.0},
        )
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 40.0, 6)
        for r in resultater:
            assert math.isclose(r.forventet_ydelse, 0.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# 4. Overgangsydelse: livsforsikring (nettorisiko)
# ---------------------------------------------------------------------------


class TestOvergangsydelse:
    def test_ingen_overgangsydelse_ved_nul_intensitet(self):
        """Ingen overgangsintensitet → overgangsydelse = 0."""
        doedsfaldssum = 500_000.0
        depot0 = 100_000.0
        produkt = simpelt_opsparingsprodukt(
            depot0, 0.0, doedsfaldssum, 0.0, NUL_MARKOV_2
        )
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 1)
        r = resultater[0]
        # Ingen overgangsintensitet → ingen P[aktiv→doed] → ingen overgangsydelse
        assert math.isclose(r.forventet_ydelse, 0.0, abs_tol=1e-9)

    def test_overgangsydelse_proportinoal_med_intensitet(self):
        """Overgangsydelse ved aktiv→doed = P_{aktiv,doed} · (S - D_aktiv)."""
        doedsfaldssum = 300_000.0
        depot0 = 100_000.0
        alder = 50.0

        mu = STANDARD_BIOMETRI.intensitet(alder)
        p_doed = mu / 12.0  # Euler: P[aktiv→doed] ≈ μ/12

        forventet_overgangsydelse = p_doed * (doedsfaldssum - depot0)

        produkt = simpelt_opsparingsprodukt(
            depot0, 0.0, doedsfaldssum, 0.0, STANDARD_MARKOV_2
        )
        resultater = markov_projicér(STANDARD_MARKOV_2, produkt, NUL_MARKED, alder, 1)
        r = resultater[0]

        # forventet_ydelse = π_aktiv(0) · cashflow_aktiv(0)
        # cashflow_aktiv = overgangs_netto = p_doed · (S - D)
        assert math.isclose(r.forventet_ydelse, forventet_overgangsydelse, rel_tol=1e-9), (
            f"Forventet overgangsydelse {forventet_overgangsydelse:.2f}, fik {r.forventet_ydelse:.2f}"
        )

    def test_livsforsikring_fra_begge_levende_tilstande(self):
        """S udbetales ved overgang til doed fra både aktiv og invalid."""
        doedsfaldssum = 400_000.0
        depot_aktiv = 100_000.0
        depot_invalid = 80_000.0
        alder = 50.0

        produkt = MarkovProdukt(
            navn="livsforsikring_3tilstand",
            tilstands_cashflows=[],
            overgangscashflows=[
                OvgangsCashflow("aktiv",   "doed", lambda a, d, S=doedsfaldssum: S - d),
                OvgangsCashflow("invalid", "doed", lambda a, d, S=doedsfaldssum: S - d),
            ],
            omkostningspct=0.0,
            initial_depot={"aktiv": depot_aktiv, "invalid": depot_invalid},
        )

        # Start med 50/50 fordeling aktiv/invalid
        start_pi = [0.5, 0.5, 0.0]
        resultater = markov_projicér(
            STANDARD_MARKOV_3, produkt, NUL_MARKED, alder, 1, start_pi=start_pi
        )
        r = resultater[0]

        p = STANDARD_MARKOV_3.p_matrix(alder)
        p_aktiv_doed   = p[0][2]
        p_invalid_doed = p[1][2]

        forventet = (
            0.5 * p_aktiv_doed   * (doedsfaldssum - depot_aktiv)
            + 0.5 * p_invalid_doed * (doedsfaldssum - depot_invalid)
        )
        assert math.isclose(r.forventet_ydelse, forventet, rel_tol=1e-9), (
            f"Forventet {forventet:.2f}, fik {r.forventet_ydelse:.2f}"
        )


# ---------------------------------------------------------------------------
# 5. PAL-skat
# ---------------------------------------------------------------------------


class TestPalSkat:
    def test_pal_nul_ved_nulrente(self):
        """PAL = 0 når r_t = 0."""
        produkt = nul_produkt(100_000.0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 6)
        for r in resultater:
            assert math.isclose(r.forventet_pal_skat, 0.0, abs_tol=1e-12)

    def test_pal_positiv_ved_positivt_afkast(self):
        """PAL > 0 når afkast > 0."""
        marked = MarketAssumptions(rf=0.05, volatilitet=0.0)
        produkt = nul_produkt(100_000.0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, marked, 50.0, 1)
        assert resultater[0].forventet_pal_skat > 0.0

    def test_pal_formel(self):
        """PAL_s = (0.153/12) · D_star_s · r_t for deterministisk r."""
        depot0 = 100_000.0
        marked = MarketAssumptions(rf=0.06, volatilitet=0.0)
        r_t = marked.afkast(0.0)

        produkt = nul_produkt(depot0, NUL_MARKOV_2)
        resultater = markov_projicér(NUL_MARKOV_2, produkt, marked, 50.0, 1)
        r = resultater[0]

        forventet_pal = (0.153 / 12.0) * depot0 * r_t
        assert math.isclose(r.forventet_pal_skat, forventet_pal, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# 6. 3-tilstandsmodel: restitution og absorption
# ---------------------------------------------------------------------------


class TestTreTilstande:
    def test_pi_sum_er_1_alle_trin(self):
        """π(t) summerer til 1 for alle t i 3-tilstandsmodel."""
        produkt = nul_produkt(100_000.0, STANDARD_MARKOV_3)
        resultater = markov_projicér(STANDARD_MARKOV_3, produkt, NUL_MARKED, 50.0, 120)
        for r in resultater:
            assert math.isclose(sum(r.pi), 1.0, rel_tol=1e-10), (
                f"Trin {r.t}: sum(π) = {sum(r.pi)}"
            )

    def test_doed_pi_vokser_monotont(self):
        """π_doed vokser monotont over tid."""
        produkt = nul_produkt(100_000.0, STANDARD_MARKOV_3)
        resultater = markov_projicér(STANDARD_MARKOV_3, produkt, NUL_MARKED, 50.0, 60)
        forrige = 0.0
        for r in resultater:
            assert r.pi[2] >= forrige - 1e-12
            forrige = r.pi[2]

    def test_invalid_andel_stiger_ved_høj_invalidiseringsrate(self):
        """Med høj μ_ai og lav μ_ia stiger π_invalid over tid."""
        høj_ai_model = MarkovModel(
            tilstande=[
                Tilstand("aktiv"),
                Tilstand("invalid"),
                Tilstand("doed", absorberende=True),
            ],
            intensiteter={
                ("aktiv",   "invalid"): lambda a: 0.5,   # meget høj invalidiseringsrate
                ("aktiv",   "doed"):    lambda a: 0.001,
                ("invalid", "aktiv"):   lambda a: 0.0,   # ingen restitution
                ("invalid", "doed"):    lambda a: 0.001,
            },
        )
        produkt = nul_produkt(100_000.0, høj_ai_model)
        resultater = markov_projicér(høj_ai_model, produkt, NUL_MARKED, 40.0, 12)
        assert resultater[-1].pi[1] > resultater[0].pi[1], (
            "π_invalid burde stige ved høj invalidiseringsrate"
        )


# ---------------------------------------------------------------------------
# 7. Depotomkostning
# ---------------------------------------------------------------------------


class TestDepotomkostning:
    def test_depot_reduceres_med_omkostningspct(self):
        """Med r=0, ingen cashflows: D(t+1) = D(t) · (1 - α)."""
        depot0 = 200_000.0
        alpha = 0.001  # 0.1 % månedlig

        produkt = MarkovProdukt(
            navn="kun_omkostning",
            tilstands_cashflows=[],
            overgangscashflows=[],
            omkostningspct=alpha,
            initial_depot={"aktiv": depot0},
        )
        resultater = markov_projicér(NUL_MARKOV_2, produkt, NUL_MARKED, 50.0, 12)
        for i, r in enumerate(resultater):
            forventet = depot0 * ((1.0 - alpha) ** i)
            assert math.isclose(r.depot_per_tilstand["aktiv"], forventet, rel_tol=1e-9), (
                f"Trin {i}: forventet {forventet:.2f}, fik {r.depot_per_tilstand['aktiv']:.2f}"
            )


# ---------------------------------------------------------------------------
# 8. Genkøbt: absorberende tilstand med hel-depot-udbetaling
# ---------------------------------------------------------------------------


class TestGenkøbt:
    def test_genkøbt_er_absorberende_i_4tilstandsmodel(self):
        """π_genkøbt vokser monotont — tilstanden er absorberende."""
        produkt = nul_produkt(100_000.0, STANDARD_MARKOV_4)
        resultater = markov_projicér(STANDARD_MARKOV_4, produkt, NUL_MARKED, 40.0, 60)
        idx_g = 2  # indeks for "genkøbt" i STANDARD_MARKOV_4
        forrige = 0.0
        for r in resultater:
            assert r.pi[idx_g] >= forrige - 1e-12, (
                f"Trin {r.t}: π_genkøbt={r.pi[idx_g]:.6f} < forrige {forrige:.6f}"
            )
            forrige = r.pi[idx_g]

    def test_pi_sum_er_1_med_genkøbt(self):
        """π(t) summerer til 1 for alle t i 4-tilstandsmodel."""
        produkt = nul_produkt(100_000.0, STANDARD_MARKOV_4)
        resultater = markov_projicér(STANDARD_MARKOV_4, produkt, NUL_MARKED, 40.0, 60)
        for r in resultater:
            assert math.isclose(sum(r.pi), 1.0, rel_tol=1e-10), (
                f"Trin {r.t}: sum(π) = {sum(r.pi)}"
            )

    def test_overgangsydelse_ved_genkøb_er_hele_depotet(self):
        """Overgangsydelse aktiv→genkøbt = P_{aktiv,genkøbt} · D_aktiv."""
        depot0 = 150_000.0
        alder = 45.0

        genkøbsrate = 0.03  # p.a. — svarer til STANDARD_MARKOV_4
        p_genkøbt = genkøbsrate / 12.0  # Euler: P[aktiv→genkøbt] ≈ μ_ag/12

        forventet_ydelse = p_genkøbt * depot0  # λ/12 · D (hele depotet)

        produkt = simpelt_opsparingsprodukt_med_genkøb(
            depot=depot0,
            praemie=0.0,
            doedsfaldssum=0.0,
            genkøbsrate=genkøbsrate,
            omkostningspct=0.0,
            markov_model=STANDARD_MARKOV_4,
        )
        resultater = markov_projicér(STANDARD_MARKOV_4, produkt, NUL_MARKED, alder, 1)
        r = resultater[0]

        # Isolér genkøbsydelsen: da doedsfaldssum=0 og S−D=−D<0 giver negativ
        # overgangsydelse til doed, bruger vi direkte forventet_ydelse som sum.
        # For korrekt isolering: byg produkt kun med genkøbs-cashflow.
        produkt_kun_genkøb = MarkovProdukt(
            navn="kun_genkøb",
            tilstands_cashflows=[],
            overgangscashflows=[
                OvgangsCashflow("aktiv", "genkøbt", lambda a, d: d),
            ],
            omkostningspct=0.0,
            initial_depot={"aktiv": depot0},
        )
        resultater2 = markov_projicér(STANDARD_MARKOV_4, produkt_kun_genkøb, NUL_MARKED, alder, 1)
        r2 = resultater2[0]

        assert math.isclose(r2.forventet_ydelse, forventet_ydelse, rel_tol=1e-9), (
            f"Forventet genkøbsydelse {forventet_ydelse:.2f}, fik {r2.forventet_ydelse:.2f}"
        )

    def test_nul_intensitet_giver_nul_genkøbsydelse(self):
        """Ingen genkøbsintensitet → genkøbsydelse = 0."""
        produkt = MarkovProdukt(
            navn="genkøb_nul",
            tilstands_cashflows=[],
            overgangscashflows=[
                OvgangsCashflow("aktiv", "genkøbt", lambda a, d: d),
            ],
            omkostningspct=0.0,
            initial_depot={"aktiv": 200_000.0},
        )
        resultater = markov_projicér(NUL_MARKOV_4, produkt, NUL_MARKED, 40.0, 1)
        assert math.isclose(resultater[0].forventet_ydelse, 0.0, abs_tol=1e-9)

    def test_validér_kaster_ikke_for_4tilstandsmodeller(self):
        """validér() kaster ingen fejl for NUL_MARKOV_4 og STANDARD_MARKOV_4."""
        NUL_MARKOV_4.validér()
        STANDARD_MARKOV_4.validér()
