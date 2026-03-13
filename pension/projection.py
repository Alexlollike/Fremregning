"""
projection.py — hovedprojektionsalgoritme.

Ansvar:
- Implementere `projicér()` der fremregner én police trin for trin
  via formlerne i CLAUDE.md (Trin 1–5).
- Returnere en liste af `TrinResultat` med alle mellemresultater per månedstrin.
- Understøtte opsparingsperiode og udbetalingsperiode for alle tre produkttyper.
- Implementere `projicér_portefølje()` der aggregerer resultater over en liste af policer.
- Ingen I/O — kun beregning.

Fremregningsrækkefølge per trin (CLAUDE.md):
    1. Nettorisiko og risikopræmie (kun opsparingsperiode)
    2. Investeringsafkast
    3. Depotomkostning
    4. PAL-skat (akkumuleres, påvirker ikke depotet)
    5. Udbetaling U_t
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions
from pension.policy import Policy


@dataclass
class TrinResultat:
    """
    Mellemresultater for ét månedstrin t.

    Attributter
    -----------
    t : int
        Månedsnummer.
    alder : float
        Forsikringstagerens alder ved trin t.
    depot : float
        Depotværdi D_t ved trinstart (før fremregning).
    depot_efter : float
        Depotværdi D_{t+1} efter fremregning.
    doedsintensitet : float
        Månedlig dødelighedsintensitet μ_t = μ(alder)/12.
    nettorisiko : float
        R_t = S - D_t (kun opsparingsperiode; ellers 0).
    risikopraemie : float
        δ_{liv,t} = μ_t · R_t (kun opsparingsperiode; ellers 0).
    afkast : float
        Månedligt investeringsafkast r_t.
    ydelse : float
        Udbetaling U_t.
    pal_skat : float
        PAL-skat for dette trin (akkumuleres separat).
    """

    t: int
    alder: float
    depot: float
    depot_efter: float
    doedsintensitet: float
    nettorisiko: float
    risikopraemie: float
    afkast: float
    ydelse: float
    pal_skat: float


def projicér(
    police: Policy,
    marked: MarketAssumptions,
    biometri: BiometricModel,
    antal_trin: int,
    epsilons: Sequence[float] | None = None,
) -> list[TrinResultat]:
    """
    Fremregner én police over `antal_trin` måneder.

    Fremregningsrækkefølgen følger CLAUDE.md Trin 1–5 strengt.
    Deterministisk scenarie bruges hvis `epsilons` er None (alle ε=0).

    Parametre
    ---------
    police : Policy
        Forsikringsaftalen der skal fremregnes.
    marked : MarketAssumptions
        Finansielle markedsantagelser (r_f, σ).
    biometri : BiometricModel
        Biometrisk model (Gompertz-Makeham parametre).
    antal_trin : int
        Antal måneder der fremregnes.
    epsilons : sequence of float, optional
        Liste af N(0,1)-innovationer, én per trin.
        Hvis None anvendes ε=0 for alle trin (deterministisk).

    Returnerer
    ----------
    list[TrinResultat]
        Liste med ét `TrinResultat` per trin (længde = antal_trin).
    """
    pass


def projicér_portefølje(
    portefølje: Sequence[Policy],
    marked: MarketAssumptions,
    biometri: BiometricModel,
    antal_trin: int,
) -> list[list[TrinResultat]]:
    """
    Fremregner en portefølje af policer deterministisk.

    Parametre
    ---------
    portefølje : sequence of Policy
        Liste af forsikringsaftaler.
    marked : MarketAssumptions
        Finansielle markedsantagelser.
    biometri : BiometricModel
        Biometrisk model.
    antal_trin : int
        Antal måneder der fremregnes.

    Returnerer
    ----------
    list[list[TrinResultat]]
        Ét indre liste-element per police, hvert indeholdende `antal_trin` trin.
    """
    pass
