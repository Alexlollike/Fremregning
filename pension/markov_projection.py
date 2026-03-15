"""
markov_projection.py — Markov-fremregning med N tilstande.

Ansvar:
- Implementere `markov_projicér()` der fremregner et MarkovProdukt over tid.
- Returnere en liste af `MarkovTrinResultat` med tilstandsbetingede og forventede
  størrelser per månedstrin.
- Følge CLAUDE.md's Trin 1–5 per transient tilstand med tilstandsspecifikke cashflows.
- Beregne forventede størrelser E[D(t)], E[U(t)], E[PAL(t)] til regnskabsbrug.

Fremregningsrækkefølge per trin (jf. CLAUDE.md's Markov-afsnit):

    For hver transient tilstand s:
        1. Pre-investment cashflows (TilstandsCashflow tidspunkt="pre"): tillægges depotet.
           OvgangsCashflows: forventet nettorisikopræmie fratrækkes depotet (som i 2-tilstandsmodel).
        2. Investeringsafkast r_t (fælles for alle tilstande).
        3. Depotomkostning α.
        4. PAL-skat (akkumuleres separat).
        5. Post-investment cashflows (TilstandsCashflow tidspunkt="post"): fratrækkes depotet.

    Herefter:
        Opdater π(t+1) = π(t) · P(t).
        Beregn forventede størrelser E[D], E[U], E[PAL].

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
        Betinget depotværdi D_s(t) ved trinstart, pr. tilstandsnavn.
        Inkluderer alle tilstande (også doed hvis doed_depot > 0).
    depot_efter_per_tilstand : dict[str, float]
        Betinget depotværdi D_s(t+1) efter fremregning, pr. tilstandsnavn.
    cashflow_per_tilstand : dict[str, float]
        Nettoudgående cashflow U_s(t) per tilstand (sum af post-ydelser
        og forventede overgangsydelser fra tilstand s).
    pal_per_tilstand : dict[str, float]
        PAL-skat pr. tilstand PAL_s(t).
    forventet_depot : float
        E[D(t)] = Σ_s π_s(t) · D_s(t) ved trinstart.
    forventet_depot_efter : float
        E[D(t+1)] = Σ_s π_s(t+1) · D_s(t+1) efter fremregning.
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
    depot_efter_per_tilstand: dict[str, float]
    cashflow_per_tilstand: dict[str, float]
    pal_per_tilstand: dict[str, float]
    forventet_depot: float
    forventet_depot_efter: float
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

    Fremregningsrækkefølgen følger CLAUDE.md Trin 1–5 per transient tilstand,
    efterfulgt af sandsynlighedsopdatering og beregning af forventede størrelser.

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

    # Startdepot pr. tilstand
    depot_s: dict[str, float] = {navn: produkt.depot_start(navn) for navn in navne}

    # Startsandsynligheder
    if start_pi is not None:
        pi: list[float] = list(start_pi)
    else:
        # Standard: sandsynlighed 1 i første transiente tilstand
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

        # Gem tilstandssandsynligheder og depoter ved trinstart
        pi_t = list(pi)
        depot_start_t = {navn: depot_s[navn] for navn in navne}

        # Hent overgangsmatrix P(t) til brug i overgangsydelsesberegninger
        p = model.p_matrix(alder)
        indeks = {navn: i for i, navn in enumerate(navne)}

        # --- Trin 1–5 per transient tilstand ---
        depot_efter_s: dict[str, float] = {}
        cashflow_s: dict[str, float] = {}
        pal_s: dict[str, float] = {}

        for tilstand in model.tilstande:
            s = tilstand.navn
            D = depot_s[s]
            i_s = indeks[s]

            if tilstand.absorberende and D <= 0.0:
                # Absorberende tilstand uden depot: ingen beregning nødvendig
                depot_efter_s[s] = 0.0
                cashflow_s[s] = 0.0
                pal_s[s] = 0.0
                continue

            # Trin 1 — pre-investment cashflows (præmier tillægges, overgangsrisici fratrækkes)
            pre_ind = sum(
                cf.beloeb(alder, D)
                for cf in produkt.tilstands_cashflows_for(s)
                if cf.tidspunkt == "pre"
            )

            # Forventet nettoomkostning ved overgange fra s (analogt med risikopræmie):
            # Σ_{j≠s} μ_{sj}/12 · K_{sj}(alder, D_s)
            # K_{sj} er OvgangsCashflow.beloeb (direkte sum ved overgang)
            overgangs_netto = 0.0
            for j_navn in navne:
                if j_navn == s:
                    continue
                j = indeks[j_navn]
                p_sj = p[i_s][j]
                for ocf in produkt.overgangscashflows_for(s, j_navn):
                    overgangs_netto += p_sj * ocf.beloeb(alder, D)

            depot_star = D + pre_ind - overgangs_netto

            # Trin 4 — PAL-skat (påvirker ikke depotet)
            pal = (0.153 / 12.0) * max(depot_star * r_t, 0.0)

            # Trin 2+3 — afkast og depotomkostning
            depot_after_inv = depot_star * (1.0 + r_t) * (1.0 - produkt.omkostningspct)

            # Trin 5 — post-investment cashflows (ydelser fratrækkes)
            post_ud = sum(
                cf.beloeb(alder, D)
                for cf in produkt.tilstands_cashflows_for(s)
                if cf.tidspunkt == "post"
            )

            D_naeste = max(depot_after_inv - post_ud, 0.0)

            depot_efter_s[s] = D_naeste
            # Udgående cashflow pr. tilstand: overgangsydelser + post-ydelser
            cashflow_s[s] = overgangs_netto + post_ud
            pal_s[s] = pal

        # Opdater depot for absorberende tilstande med positiv indstrømning
        # (doed_depot: arvingernes resterende ydelse akkumulerer via overgangscashflows)
        # Depotoverførslen til absorberende tilstande sker allerede via overgangs_netto
        # på afsendersiden — modtagersiden (doed) fremregnes separat ovenfor.

        # --- Opdater π(t+1) ---
        pi_naeste = model.opdater_pi(pi, alder)

        # --- Forventede størrelser ---
        forventet_depot = sum(pi_t[indeks[s]] * depot_start_t[s] for s in navne)
        forventet_depot_efter = sum(pi_naeste[indeks[s]] * depot_efter_s[s] for s in navne)
        forventet_ydelse = sum(pi_t[indeks[s]] * cashflow_s[s] for s in navne)
        forventet_pal = sum(pi_t[indeks[s]] * pal_s[s] for s in navne)

        resultater.append(MarkovTrinResultat(
            t=t,
            alder=alder,
            dato=dato,
            pi=pi_t,
            depot_per_tilstand=dict(depot_start_t),
            depot_efter_per_tilstand=dict(depot_efter_s),
            cashflow_per_tilstand=dict(cashflow_s),
            pal_per_tilstand=dict(pal_s),
            forventet_depot=forventet_depot,
            forventet_depot_efter=forventet_depot_efter,
            forventet_ydelse=forventet_ydelse,
            forventet_pal_skat=forventet_pal,
            afkast=r_t,
        ))

        # Fremfør tilstand til næste trin
        depot_s = depot_efter_s
        pi = pi_naeste

    return resultater
