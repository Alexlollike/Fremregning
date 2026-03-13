"""
biometrics.py — biometrisk model med dødelighedsintensiteter.

Ansvar:
- Implementere `BiometricModel` med Gompertz-Makeham dødelighedsintensitet.
- Beregne kontinuert dødelighedsintensitet μ(x) = A + B·c^x (Makeham-led + Gompertz-led).
- Beregne månedlig dødelighedsintensitet μ_t = μ(x + t/12) / 12.
- Beregne nutidsværdi af livrente ä_{x+t} via annuityPV til brug i livrente-ydelsesformel.
- Ingen produktlogik — kun demografiske og aktuarielle beregninger.
"""

from __future__ import annotations


class BiometricModel:
    """
    Gompertz-Makeham dødelighedsmodel.

    Dødelighedsintensiteten er:
        μ(x) = A + B · c^x

    hvor A er Makeham-konstanten (ulykker m.v.) og B, c er Gompertz-parametrene.

    Parametre
    ---------
    A : float
        Makeham-led (konstant baggrundsrisiko).
    B : float
        Gompertz-skalafaktor.
    c : float
        Gompertz-vækstrate (> 1).
    """

    def __init__(self, A: float, B: float, c: float) -> None:
        pass

    def intensitet(self, alder: float) -> float:
        """
        Kontinuert dødelighedsintensitet μ(alder) = A + B · c^alder.

        Parametre
        ---------
        alder : float
            Alder i år.

        Returnerer
        ----------
        float
            Kontinuert dødelighedsintensitet (per år).
        """
        pass

    def maanedlig_intensitet(self, alder: float) -> float:
        """
        Månedlig dødelighedsintensitet μ_t = μ(alder) / 12.

        Svarer til μ(x + t/12) / 12 i CLAUDE.md's notation.

        Parametre
        ---------
        alder : float
            Alder i år ved tidstrin t, dvs. x + t/12.

        Returnerer
        ----------
        float
            Månedlig dødelighedsintensitet (dimensionsløs).
        """
        pass

    def annuity_pv(self, alder: float, rente: float) -> float:
        """
        Nutidsværdi af livsvarig livrente ä_{alder} ved diskret månedlig beregning.

        Beregnes som:
            ä_{x} = sum_{k=0}^{omega} k_p_x · v^k
        hvor v = 1/(1 + r/12) og k_p_x er sandsynlighed for at overleve k måneder.

        Parametre
        ---------
        alder : float
            Aktuel alder i år.
        rente : float
            Årlig rente (f.eks. 0.03 for 3 %).

        Returnerer
        ----------
        float
            Nutidsværdi af livsvarig livrente (ä_{x+t} i enheder af 1 kr./måned).
        """
        pass
