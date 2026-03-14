"""
markov_produkt.py — produktdefinition via cashflow-regler for Markov-model.

Ansvar:
- Definere `TilstandsCashflow`: løbende cashflow i en given tilstand.
- Definere `OvgangsCashflow`: éngangscashflow ved overgang mellem tilstande.
- Definere `MarkovProdukt`: et forsikrings-/pensionsprodukt som en samling regler.

Designprincip: Tilstand ≠ cashflow.
  En tilstand beskriver kun et element i tilstandsrummet (markov.py).
  Et MarkovProdukt definerer hvornår og hvad der udbetales — enten mens
  den forsikrede er i en tilstand, eller når tilstanden skifter.

Eksempler på produktsammensætning:
  Livsforsikring (sum S):
    OvgangsCashflow("aktiv",   "doed", lambda a, d: S - d)   # nettorisiko R = S - D
    OvgangsCashflow("invalid", "doed", lambda a, d: S - d)

  Invalidesum (sum I ved invalidisering):
    OvgangsCashflow("aktiv", "invalid", lambda a, d: I)

  Ratepension (ydelse i udbetalingsperiode):
    TilstandsCashflow("aktiv", lambda a, d: d / (annuity_pv(a) * 12))

  Arvingernes resterende ydelse:
    OvgangsCashflow("aktiv",   "doed", lambda a, d: d)  # depot overføres til doed
    OvgangsCashflow("invalid", "doed", lambda a, d: d)
    TilstandsCashflow("doed",  lambda a, d: d / (resterende_perioder * 12))

  Præmie (pre-investment, indgående):
    TilstandsCashflow("aktiv", lambda a, d: praemie, tidspunkt="pre")
    # pre-cashflow med positiv beloeb = indgående (tillægges depotet)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TilstandsCashflow:
    """
    Løbende cashflow betalt mens den forsikrede er i en given tilstand.

    Beløbskonvention og tidspunkt:
        tidspunkt="pre"  → beløbet TILLÆGGES depotet FØR investeringsafkast (indgående, som præmie).
        tidspunkt="post" → beløbet FRATRÆKKES depotet EFTER afkast og omkostninger (udgående, som ydelse).
        Beløbet er altid positivt og fortolkes ud fra `tidspunkt`.

    Attributter
    -----------
    tilstand : str
        Navn på den tilstand hvori cashflowet opstår.
    beloeb : Callable[[float, float], float]
        Funktion (alder, depot_s) → cashflow-beløb per måned (positivt tal).
        `alder` er den forsikredes alder i år; `depot_s` er det betingede
        depot D_s(t) i den pågældende tilstand.
    tidspunkt : str
        "pre"  — indgående cashflow (tillægges depot FØR afkast).
        "post" — udgående cashflow (fratrækkes depot EFTER afkast og omkostninger).
        Standard: "post".
    """

    tilstand: str
    beloeb: Callable[[float, float], float]
    tidspunkt: str = "post"  # "pre" eller "post"


@dataclass
class OvgangsCashflow:
    """
    Éngangscashflow ved overgang fra én tilstand til en anden.

    Cashflowet opstår i det trin, overgangen sker, og vægtes med
    overgangsintensiteten π_s(t) · P_{ss'}(t) i de forventede størrelser.

    Attributter
    -----------
    fra : str
        Navn på afgangstilstanden.
    til : str
        Navn på ankomsttilstanden.
    beloeb : Callable[[float, float], float]
        Funktion (alder, depot_fra) → cashflow-beløb (éngangs).
        `depot_fra` er det betingede depot D_{fra}(t) ved overgangsøjeblikket.
    """

    fra: str
    til: str
    beloeb: Callable[[float, float], float]


@dataclass
class MarkovProdukt:
    """
    Et forsikrings-/pensionsprodukt defineret ved sine cashflow-regler.

    Alle cashflows udtrykkes via `TilstandsCashflow` og `OvgangsCashflow`.
    Produktet har ingen indlejret viden om tilstandsrummet — det afhænger af
    at den tilknyttede `MarkovModel` indeholder de refererede tilstandsnavne.

    Attributter
    -----------
    navn : str
        Beskrivende produktnavn (til rapportering).
    tilstands_cashflows : list[TilstandsCashflow]
        Løbende cashflows pr. tilstand.
    overgangscashflows : list[OvgangsCashflow]
        Éngangscashflows ved tilstandsskift.
    omkostningspct : float
        Månedlig depotomkostning α. Fratrækkes som procentsats af
        den investerede formue efter afkast (Trin 3, CLAUDE.md).
    initial_depot : dict[str, float]
        Startdepotværdi D_s(0) pr. tilstandsnavn.
        Tilstande uden angivet startværdi antages at starte med 0.
    """

    navn: str
    tilstands_cashflows: list[TilstandsCashflow] = field(default_factory=list)
    overgangscashflows: list[OvgangsCashflow] = field(default_factory=list)
    omkostningspct: float = 0.0
    initial_depot: dict[str, float] = field(default_factory=dict)

    def tilstands_cashflows_for(self, tilstand: str) -> list[TilstandsCashflow]:
        """Returnerer alle TilstandsCashflow for den givne tilstand."""
        return [cf for cf in self.tilstands_cashflows if cf.tilstand == tilstand]

    def overgangscashflows_fra(self, fra: str) -> list[OvgangsCashflow]:
        """Returnerer alle OvgangsCashflow med `fra` som afgangstilstand."""
        return [cf for cf in self.overgangscashflows if cf.fra == fra]

    def overgangscashflows_for(self, fra: str, til: str) -> list[OvgangsCashflow]:
        """Returnerer alle OvgangsCashflow for den specifikke overgang fra → til."""
        return [cf for cf in self.overgangscashflows if cf.fra == fra and cf.til == til]

    def depot_start(self, tilstand: str) -> float:
        """Returnerer startdepot for tilstanden; 0 hvis ikke angivet."""
        return self.initial_depot.get(tilstand, 0.0)
