"""
market.py — markedsantagelser til brug i projektionsmodellen.

Ansvar:
- Definere `MarketAssumptions` dataklasse med risikofri rente og volatilitet.
- Generere månedligt investeringsafkast r_t ved risikoneutral (certainty equivalent)
  lognormal model: r_t = exp((r_f - ½σ²)·(1/12) + σ·√(1/12)·ε_t) - 1.
- Stille deterministiske afkastscenarier til rådighed (ε=0) til tests.
- Ingen policer eller biometri — kun finansielle markedsparametre og afkastgenerering.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MarketAssumptions:
    """
    Markedsantagelser for den finansielle model.

    Parametre
    ---------
    rf : float
        Risikofri rente p.a. (f.eks. 0.03 for 3 %).
    volatilitet : float
        Annualiseret volatilitet σ (f.eks. 0.15 for 15 %).
    """

    rf: float
    volatilitet: float

    def afkast(self, epsilon: float) -> float:
        """
        Beregner månedligt investeringsafkast r_t for en given normalfordelt innovation.

        Formel (CLAUDE.md Trin 2):
            r_t = exp((r_f - ½σ²)·(1/12) + σ·√(1/12)·ε_t) - 1

        Parametre
        ---------
        epsilon : float
            Standard-normalfordelt innovation ε_t ~ N(0,1).
            Brug epsilon=0 for det deterministiske certainty-equivalent afkast.

        Returnerer
        ----------
        float
            Månedligt afkast r_t (dimensionsløst, f.eks. 0.002 for 0,2 %).
        """
        return math.exp(
            (self.rf - 0.5 * self.volatilitet ** 2) / 12.0
            + self.volatilitet * math.sqrt(1.0 / 12.0) * epsilon
        ) - 1.0

    def deterministisk_afkast(self) -> float:
        """
        Returnerer det deterministiske certainty-equivalent månedlige afkast (ε=0).

        Svarer til afkast(epsilon=0).

        Returnerer
        ----------
        float
            Månedligt certainty-equivalent afkast.
        """
        return self.afkast(0.0)
