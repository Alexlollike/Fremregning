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

import math


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
        self.A = A
        self.B = B
        self.c = c

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
        return self.A + self.B * self.c ** alder

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
        return self.intensitet(alder) / 12

    def annuity_pv(self, alder: float, rente: float) -> float:
        """
        Nutidsværdi af livsvarig livrente ä_{alder} via Thieles differentialligning.

        ODE-formuleringen er:

            dä/dt = (δ − μ(x+t)) · ä(t) − 1,    ä(120) = 0

        med δ = ln(1+r) (kontinuert rentekraft).

        Implementeres via Duhamels formel — det analytiske integral for ODE-løsningen:

            ä(t) = ∫_t^{120}  _{s−t}p_{x+t} · e^{−δ(s−t)} ds

        approksimeret som månedlig frem-summation (numerisk stabil modsat
        eksplicit baglæns integration, der er ustabil ved høj μ):

            ä(t) ≈ Δt · Σ_{k=0}^{K−1}  k_p_{x+t} · e^{−δ·k·Δt}

        Returnerer ä i enheder af år (PV af 1 kr./år annuitet).
        Brug ä · 12 som nævner i ydelsesformlen U_t = D_t / (ä · 12).

        Parametre
        ---------
        alder : float
            Aktuel alder i år.
        rente : float
            Årlig rente (f.eks. 0.05 for 5 %).

        Returnerer
        ----------
        float
            Nutidsværdi af livsvarig livrente ä_{x+t} i år.
        """
        delta = math.log(1.0 + rente)   # kontinuert rentekraft δ = ln(1+r)
        dt = 1.0 / 12.0                  # månedstrin i år
        max_months = int((120.0 - alder) * 12)

        pv = 0.0
        kpx = 1.0   # k_p_x: overlevelsessandsynlighed k måneder fra alder
        for k in range(max_months):
            pv += kpx * math.exp(-delta * k * dt)
            kpx *= math.exp(-self.intensitet(alder + k * dt) * dt)
            if kpx < 1e-10:
                break
        return pv * dt   # Riemann-sum × Δt → år-enheder


def ophørende_annuitet_pv(n_years: float, rente: float) -> float:
    """
    Nutidsværdi af ophørende (ikke-livsbetinget) annuitet over n_years år,
    betalt månedligt.

    Formlen er:

        ä_N^(12) ≈ Δt · Σ_{k=0}^{12·N − 1} e^{−δ·k·Δt}

    med δ = ln(1+r) og Δt = 1/12.

    Returnerer ä i enheder af år (PV af 1 kr./år annuitet).
    Brug ä · 12 som nævner i ydelsesformlen U_t = D_t / (ä · 12).

    Analytisk kontrol (rente=0): ä_N = N (summen af N·12 led à 1/12).

    Parametre
    ---------
    n_years : float
        Resterende udbetalingsperiode i år. Returnerer 0.0 hvis n_years <= 0.
    rente : float
        Årlig rente (f.eks. 0.03 for 3 %).

    Returnerer
    ----------
    float
        Nutidsværdi af ophørende annuitet i år-enheder.
    """
    if n_years <= 0.0:
        return 0.0
    delta = math.log(1.0 + rente)
    dt = 1.0 / 12.0
    total_months = int(round(n_years * 12))
    pv = sum(math.exp(-delta * k * dt) for k in range(total_months))
    return pv * dt
