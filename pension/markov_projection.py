"""
markov_projection.py — Markov-fremregning med N tilstande.

Ansvar:
- Implementere `markov_projicér()` der fremregner et MarkovProdukt over tid.
- Returnere en liste af `MarkovTrinResultat` med tilstandsbetingede og forventede
  størrelser per månedstrin.
- Beregne D_s(t) som det sande betingede depot E[D(t) | X(t)=s] via Thiele-blanding.
- Beregne forventede størrelser E[D(t)], E[U(t)], E[PAL(t)] til regnskabsbrug.

Thiele-blanding (depotmixing):
    D_s(t) er det forventede depot givet tilstand s på tid t, over alle mulige stier
    der ender i s. Fordi depotudviklingen er lineær, kan D_s(t+1) beregnes som:

        π_s(t+1) · D_s(t+1) = Σ_i π_i(t) · P_{is}(t) · D̂_{is}

    hvor D̂_{is} er depotet for en sti der starter i tilstand i og ender i s:
        1. Pre-cashflows for tilstand i.
        2. Overgangscashflow K_{is} (0 for i=s).
        3. Investeringsafkast r_t og depotomkostning α.
        4. Post-cashflow for tilstand s (evalueret ved D_i).

Fremregningsrækkefølge per trin:
    1. Beregn D̂_{is} for alle overgangspar (i → s).
    2. Bland: D_s(t+1) = Σ_i w_{is} · D̂_{is}  (vægtet med π_i · P_{is} / π_s(t+1)).
    3. Opdater π(t+1) = π(t) · P(t).
    4. Beregn forventede størrelser E[D], E[U], E[PAL].

Ikke modificeret: pension/projection.py (2-tilstandsmodel bevares uændret).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Sequence

from pension.market import MarketAssumptions
from pension.markov import MarkovModel
from pension.markov_produkt import MarkovProdukt
from pension.projection import SIMULATION_START_DATO, _dato_ved_trin


@dataclass
class MarkovTrinResultat:
    """
    Mellemresultater for ét månedstrin i Markov-fremregningen.

    Attributter
    -----------
    t : int
        Månedsnummer (0-baseret).
    alder : float
        Forsikredes alder ved trinstart: x + t/12.
    dato : date
        Kalenderdato (1. i måneden) for trinstart.
    pi : list[float]
        Tilstandssandsynlighedsvektor π(t) ved trinstart (summerer til 1).
    depot_per_tilstand : dict[str, float]
        Betinget depotværdi D_s(t) = E[D(t) | X(t)=s] ved trinstart.
        Korrekt blandet over alle stier der ender i tilstand s.
    cashflow_per_tilstand : dict[str, float]
        Forventet udgående cashflow givet afsendertilstand i:
        Σ_s P_{is} · (K_{is} + post_s). Bruges til E[U(t)].
    pal_per_tilstand : dict[str, float]
        Forventet PAL-skat givet afsendertilstand i:
        Σ_s P_{is} · PAL_{is}(t).
    forventet_depot : float
        E[D(t)] = Σ_s π_s(t) · D_s(t) ved trinstart.
    forventet_ydelse : float
        E[U(t)] = Σ_s π_s(t) · cashflow_s(t) (udgående cashflows).
    forventet_pal_skat : float
        E[PAL(t)] = Σ_s π_s(t) · PAL_s(t).
    afkast : float
        Månedligt investeringsafkast r_t (fælles for alle tilstande).
    """

    t: int
    alder: float
    dato: date
    pi: list[float]
    depot_per_tilstand: dict[str, float]
    cashflow_per_tilstand: dict[str, float]
    pal_per_tilstand: dict[str, float]
    forventet_depot: float
    forventet_ydelse: float
    forventet_pal_skat: float
    afkast: float


def markov_projicér(
    model: MarkovModel,
    produkt: MarkovProdukt,
    marked: MarketAssumptions,
    start_alder: float,
    antal_trin: int,
    epsilons: Sequence[float] | None = None,
    start_dato: date = SIMULATION_START_DATO,
    start_pi: list[float] | None = None,
) -> list[MarkovTrinResultat]:
    """
    Fremregner et MarkovProdukt over `antal_trin` måneder.

    Benytter Thiele-blanding: D_s(t+1) beregnes som det sande betingede depot
    E[D(t+1) | X(t+1)=s], dvs. en forventning over alle stier i → s vægtet med
    π_i(t) · P_{is}(t).

    Parametre
    ---------
    model : MarkovModel
        Markov-kæden med tilstande og overgangsintensiteter.
    produkt : MarkovProdukt
        Produktets cashflow-regler og startdepoter.
    marked : MarketAssumptions
        Finansielle markedsantagelser (r_f, σ).
    start_alder : float
        Forsikredes alder i år ved t=0.
    antal_trin : int
        Antal måneder der fremregnes.
    epsilons : sequence of float, optional
        N(0,1)-innovationer, én per trin. Hvis None: ε=0 (deterministisk).
    start_dato : date, optional
        Kalenderdato for t=0. Standard: 1. januar 2027.
    start_pi : list[float], optional
        Startvektor π(0). Hvis None: sandsynlighed 1 i første ikke-absorberende tilstand.

    Returnerer
    ----------
    list[MarkovTrinResultat]
        Ét resultat per trin (længde = antal_trin).
    """
    navne = [t.navn for t in model.tilstande]
    n = model.n
    indeks = {navn: i for i, navn in enumerate(navne)}

    # Startdepot pr. tilstand
    depot_s: dict[str, float] = {navn: produkt.depot_start(navn) for navn in navne}

    # Startsandsynligheder
    if start_pi is not None:
        pi: list[float] = list(start_pi)
    else:
        første_transient = next(
            (t.navn for t in model.tilstande if not t.absorberende), None
        )
        if første_transient is None:
            raise ValueError("MarkovModel har ingen transiente tilstande.")
        pi = model.initial_pi(første_transient)

    resultater: list[MarkovTrinResultat] = []

    for t in range(antal_trin):
        alder = start_alder + t / 12.0
        dato = _dato_ved_trin(start_dato, t)
        epsilon = epsilons[t] if epsilons is not None else 0.0
        r_t = marked.afkast(epsilon)

        # Gem åbningsstørrelser
        pi_t = list(pi)
        depot_start_t = {navn: depot_s[navn] for navn in navne}

        p = model.p_matrix(alder)

        # ------------------------------------------------------------------
        # Thiele-blanding:
        # For hvert overgangspar (i → s) beregn D̂_{is}: depotet for en sti
        # der starter i tilstand i med depot D_i og ender i tilstand s.
        #
        # Evaluering: alle cashflow-funktioner evalueres ved D_i (afsenderdepot),
        # da depotudviklingen er lineær i D og D_i er det kendte startdepot.
        # ------------------------------------------------------------------

        # D_hat[(i_navn, s_navn)] og pal_hat[(i_navn, s_navn)]
        D_hat: dict[tuple[str, str], float] = {}
        pal_hat: dict[tuple[str, str], float] = {}

        for fra_t in model.tilstande:
            i_navn = fra_t.navn
            D_i = depot_start_t[i_navn]
            i_idx = indeks[i_navn]

            # Pre-cashflows for afsendertilstand i (præmie, indgående)
            pre_i = sum(
                cf.beloeb(alder, D_i)
                for cf in produkt.tilstands_cashflows_for(i_navn)
                if cf.tidspunkt == "pre"
            )

            for til_t in model.tilstande:
                s_navn = til_t.navn

                # Overgangscashflow K_{is}: 0 for selvovergang (i=s)
                if i_navn == s_navn:
                    K_is = 0.0
                else:
                    K_is = sum(
                        ocf.beloeb(alder, D_i)
                        for ocf in produkt.overgangscashflows_for(i_navn, s_navn)
                    )

                D_after_pre = D_i + pre_i - K_is

                # PAL-skat (påvirker ikke depotet)
                pal_is = (0.153 / 12.0) * max(D_after_pre * r_t, 0.0)

                # Trin 2+3: afkast og depotomkostning
                D_after_inv = D_after_pre * (1.0 + r_t) * (1.0 - produkt.omkostningspct)

                # Post-cashflows for ankomsttilstand s (ydelse, udgående)
                # Evalueres ved D_i (afsenderdepot) jf. linearitetsantagelse
                post_s = sum(
                    cf.beloeb(alder, D_i)
                    for cf in produkt.tilstands_cashflows_for(s_navn)
                    if cf.tidspunkt == "post"
                )

                D_hat[(i_navn, s_navn)] = max(D_after_inv - post_s, 0.0)
                pal_hat[(i_navn, s_navn)] = pal_is

        # Opdater π(t+1) = π(t) · P(t)
        pi_naeste = model.opdater_pi(pi, alder)

        # ------------------------------------------------------------------
        # D_s(t+1) = Σ_i π_i(t) · P_{is}(t) · D̂_{is}  /  π_s(t+1)
        # ------------------------------------------------------------------
        depot_efter_s: dict[str, float] = {}
        for til_t in model.tilstande:
            s_navn = til_t.navn
            s_idx = indeks[s_navn]
            pi_s_next = pi_naeste[s_idx]

            if pi_s_next <= 0.0:
                depot_efter_s[s_navn] = 0.0
                continue

            numerator = sum(
                pi_t[indeks[i_navn]] * p[indeks[i_navn]][s_idx] * D_hat[(i_navn, s_navn)]
                for i_navn in navne
            )
            depot_efter_s[s_navn] = numerator / pi_s_next

        # ------------------------------------------------------------------
        # Cashflow og PAL pr. afsendertilstand i (til E[U] og E[PAL])
        # cashflow_i = Σ_s P_{is} · (K_{is} + post_s)
        # pal_i      = Σ_s P_{is} · PAL_{is}
        # ------------------------------------------------------------------
        cashflow_s: dict[str, float] = {}
        pal_s: dict[str, float] = {}

        for fra_t in model.tilstande:
            i_navn = fra_t.navn
            i_idx = indeks[i_navn]
            D_i = depot_start_t[i_navn]

            cf_i = 0.0
            pal_i = 0.0
            for til_t in model.tilstande:
                s_navn = til_t.navn
                s_idx = indeks[s_navn]
                p_is = p[i_idx][s_idx]

                K_is = (
                    0.0 if i_navn == s_navn
                    else sum(
                        ocf.beloeb(alder, D_i)
                        for ocf in produkt.overgangscashflows_for(i_navn, s_navn)
                    )
                )
                post_s_val = sum(
                    cf.beloeb(alder, D_i)
                    for cf in produkt.tilstands_cashflows_for(s_navn)
                    if cf.tidspunkt == "post"
                )
                cf_i += p_is * (K_is + post_s_val)
                pal_i += p_is * pal_hat[(i_navn, s_navn)]

            cashflow_s[i_navn] = cf_i
            pal_s[i_navn] = pal_i

        # Forventede størrelser
        forventet_depot = sum(pi_t[indeks[s]] * depot_start_t[s] for s in navne)
        forventet_ydelse = sum(pi_t[indeks[s]] * cashflow_s[s] for s in navne)
        forventet_pal = sum(pi_t[indeks[s]] * pal_s[s] for s in navne)

        resultater.append(MarkovTrinResultat(
            t=t,
            alder=alder,
            dato=dato,
            pi=pi_t,
            depot_per_tilstand=dict(depot_start_t),
            cashflow_per_tilstand=dict(cashflow_s),
            pal_per_tilstand=dict(pal_s),
            forventet_depot=forventet_depot,
            forventet_ydelse=forventet_ydelse,
            forventet_pal_skat=forventet_pal,
            afkast=r_t,
        ))

        # Fremfør tilstand til næste trin
        depot_s = depot_efter_s
        pi = pi_naeste

    return resultater
