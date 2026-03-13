"""
policy.py — aftale- og produktdataklasser.

Ansvar:
- Definere `ProductType` enum med de støttede produkttyper
  (livrente, ratepension, aldersopsparing).
- Definere `Policy` dataklasse med alle parametre for én forsikringsaftale:
  alder, depot, dødsfaldsum, præmie, omkostningsprocent og produkt.
- Ingen beregningslogik — kun datarepræsentation og validering.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProductType(Enum):
    """Understøttede pensionsprodukter."""

    LIVRENTE = "livrente"
    RATEPENSION = "ratepension"
    ALDERSOPSPARING = "aldersopsparing"


@dataclass
class Policy:
    """
    Dataklasse der repræsenterer én forsikringsaftale.

    Parametre
    ---------
    alder : float
        Forsikringstagerens alder i år ved t=0.
    depot : float
        Depotværdi ved t=0 (D_0). Enhed: kr.
    doedsfaldssum : float
        Fast dødsfaldsum S. Enhed: kr.
    praemie : float
        Fast månedlig præmie π. Enhed: kr.
    omkostningspct : float
        Løbende depotomkostning α (f.eks. 0.005 for 0,5 % p.a./12).
    produkt : ProductType
        Produkttype — afgør fremregningsregel i udbetalingsperioden.
    udbetalingsstart_alder : float
        Alder (i år) hvor opsparingsperioden ophører og udbetalingsperioden begynder.
    maanedlig_ydelse : float, optional
        Fast månedlig ydelse U_t for ratepension/aldersopsparing i udbetalingsperioden.
        Beregnes ved konvertering; sættes til 0.0 indtil da.
    """

    alder: float
    depot: float
    doedsfaldssum: float
    praemie: float
    omkostningspct: float
    produkt: ProductType
    udbetalingsstart_alder: float
    maanedlig_ydelse: float = 0.0

    def er_i_udbetalingsperiode(self, t: int) -> bool:
        """
        Returnerer True hvis tidstrin t befinder sig i udbetalingsperioden.

        Parametre
        ---------
        t : int
            Månedsnummer fra 0.
        """
        return self.alder_ved_trin(t) >= self.udbetalingsstart_alder

    def alder_ved_trin(self, t: int) -> float:
        """
        Returnerer forsikringstagerens alder ved tidstrin t.

        Parametre
        ---------
        t : int
            Månedsnummer fra 0.
        """
        return self.alder + t / 12
