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

from dataclasses import dataclass, field
from enum import Enum

# Årligt indbetalingsloft for ratepension jf. PBL § 16, stk. 2 (2026-niveau).
RATEPENSION_INDBETALINGSLOFT: float = 68_700.0


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
    udbetalingsperiode_aar : int, optional
        Antal år ratepensionen udbetales over (10–20 år).
        Kun relevant for RATEPENSION; ignoreres for øvrige produkttyper.
    """

    alder: float
    depot: float
    doedsfaldssum: float
    praemie: float
    omkostningspct: float
    produkt: ProductType
    udbetalingsstart_alder: float
    udbetalingsperiode_aar: int = 15

    def __post_init__(self) -> None:
        if self.produkt == ProductType.RATEPENSION:
            if self.praemie * 12 > RATEPENSION_INDBETALINGSLOFT:
                raise ValueError(
                    f"Månedlig præmie {self.praemie:.2f} kr. svarer til "
                    f"{self.praemie * 12:.2f} kr./år og overskrider "
                    f"indbetalingsloftet for ratepension på "
                    f"{RATEPENSION_INDBETALINGSLOFT:.0f} kr. (2026)."
                )
            if not (10 <= self.udbetalingsperiode_aar <= 20):
                raise ValueError(
                    f"udbetalingsperiode_aar={self.udbetalingsperiode_aar} er "
                    f"ugyldig: ratepension skal udbetales over 10–20 år."
                )

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
