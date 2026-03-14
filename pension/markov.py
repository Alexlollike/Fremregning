"""
markov.py — transient Markov-model med N tilstande.

Ansvar:
- Definere `Tilstand`-dataklassen (tilstandsnavn + absorberingsmarkering).
- Implementere `MarkovModel` med intensitetsmatrix Q(t) og overgangsmatrix P(t).
- Validere at P(t) er en gyldig stokastisk matrix (rækker summer til 1, elementer ≥ 0).
- Ingen cashflow-logik — kun tilstandsstruktur og overgangssandsynligheder.

Diskretiseringsmetode: Euler-approksimation P(t) ≈ I + Q(t)/12 (passende for månedsstep).
Ingen ekstern matrixbibliotekafhængighed kræves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Tilstand:
    """
    Ét element i tilstandsrummet.

    Attributter
    -----------
    navn : str
        Entydigt tilstandsnavn (f.eks. "aktiv", "invalid", "doed").
    absorberende : bool
        True hvis tilstanden er absorberende (ingen udgående overgange).
        Eksempel: "doed" er absorberende.
    """

    navn: str
    absorberende: bool = False


@dataclass
class MarkovModel:
    """
    Transient Markov-kæde med diskret månedlig tid.

    Tilstande og overgange defineres ved oprettelse. Intensiteterne er
    aldersafhængige funktioner der paralleller `BiometricModel.intensitet(alder)`.

    Parametre
    ---------
    tilstande : list[Tilstand]
        Ordnet liste af tilstande. Indeksrækkefølgen bestemmer position i Q og P.
    intensiteter : dict[tuple[str, str], Callable[[float], float]]
        Mapping (fra_navn, til_navn) → funktion alder (år) → overgangsintensitet p.a.
        Diagonalen beregnes automatisk som negativ rækkesum.
        Kun ikke-nul off-diagonale intensiteter skal angives.

    Eksempel (3 tilstande):
        MarkovModel(
            tilstande=[Tilstand("aktiv"), Tilstand("invalid"), Tilstand("doed", absorberende=True)],
            intensiteter={
                ("aktiv",   "invalid"): lambda a: 0.005,      # invalidiseringsrate p.a.
                ("aktiv",   "doed"):    biometri.intensitet,   # dødelighedsintensitet p.a.
                ("invalid", "aktiv"):   lambda a: 0.01,        # restitutionsrate p.a.
                ("invalid", "doed"):    lambda a: biometri.intensitet(a) * 1.5,
            },
        )
    """

    tilstande: list[Tilstand]
    intensiteter: dict[tuple[str, str], Callable[[float], float]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self._indeks: dict[str, int] = {t.navn: i for i, t in enumerate(self.tilstande)}
        self._navne: list[str] = [t.navn for t in self.tilstande]

    @property
    def n(self) -> int:
        """Antal tilstande."""
        return len(self.tilstande)

    def _indeks_for(self, navn: str) -> int:
        try:
            return self._indeks[navn]
        except KeyError:
            raise ValueError(f"Ukendt tilstand: '{navn}'. Kendte: {self._navne}") from None

    def q_matrix(self, alder: float) -> list[list[float]]:
        """
        Beregn intensitetsmatrix Q ved given alder.

        Parametre
        ---------
        alder : float
            Alder i år ved aktuelt tidstrin (x + t/12).

        Returnerer
        ----------
        list[list[float]]
            N×N matrix; Q[i][j] = μ_{ij}(alder) for i≠j, Q[i][i] = −Σ_{j≠i} Q[i][j].
        """
        n = self.n
        q = [[0.0] * n for _ in range(n)]

        for (fra, til), intensitet_fn in self.intensiteter.items():
            i = self._indeks_for(fra)
            j = self._indeks_for(til)
            if i == j:
                raise ValueError(
                    f"Intensitet ({fra!r}, {til!r}): fra- og til-tilstand må ikke være ens."
                )
            q[i][j] = intensitet_fn(alder)

        # Diagonal: negativ rækkesum
        for i in range(n):
            q[i][i] = -sum(q[i][j] for j in range(n) if j != i)

        return q

    def p_matrix(self, alder: float) -> list[list[float]]:
        """
        Beregn månedlig overgangsmatrix P ≈ I + Q/12 (Euler-approksimation).

        Parametre
        ---------
        alder : float
            Alder i år ved aktuelt tidstrin.

        Returnerer
        ----------
        list[list[float]]
            N×N stokastisk matrix; P[i][j] = sandsynlighed for overgang i→j i én måned.
        """
        n = self.n
        q = self.q_matrix(alder)
        dt = 1.0 / 12.0
        p = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                p[i][j] = (1.0 if i == j else 0.0) + q[i][j] * dt
        return p

    def validér(self, alder: float = 50.0) -> None:
        """
        Kontrollér at P(t) er en gyldig stokastisk matrix ved given alder.

        Kontrollerer:
        - Alle off-diagonale elementer i P er ≥ 0 (ingen negative sandsynligheder).
        - Alle rækker i P summer til 1 (inden for numerisk tolerance).

        Kaster ValueError ved overtrædelse.

        Parametre
        ---------
        alder : float
            Alder til validering. Standard: 50 år (middelvalg).
        """
        p = self.p_matrix(alder)
        n = self.n
        for i in range(n):
            rækkesum = sum(p[i])
            if abs(rækkesum - 1.0) > 1e-10:
                raise ValueError(
                    f"P-matrix række {i} ({self._navne[i]!r}) summer til {rækkesum:.6f}, ikke 1."
                )
            for j in range(n):
                if i != j and p[i][j] < -1e-12:
                    raise ValueError(
                        f"P[{self._navne[i]!r}][{self._navne[j]!r}] = {p[i][j]:.6f} < 0. "
                        "Intensiteten er for høj til Euler-approksimationen."
                    )

    def opdater_pi(self, pi: list[float], alder: float) -> list[float]:
        """
        Beregn π(t+1) = π(t) · P(t).

        Parametre
        ---------
        pi : list[float]
            Sandsynlighedsvektor π(t) af længde N.
        alder : float
            Alder ved trin t.

        Returnerer
        ----------
        list[float]
            Opdateret sandsynlighedsvektor π(t+1).
        """
        p = self.p_matrix(alder)
        n = self.n
        ny_pi = [0.0] * n
        for j in range(n):
            ny_pi[j] = sum(pi[i] * p[i][j] for i in range(n))
        return ny_pi

    def initial_pi(self, start_tilstand: str) -> list[float]:
        """
        Returnerer startvektor π(0) med sandsynlighed 1 i `start_tilstand`.

        Parametre
        ---------
        start_tilstand : str
            Navn på starttilstanden.

        Returnerer
        ----------
        list[float]
            π(0) med π[start_tilstand] = 1, øvrige = 0.
        """
        pi = [0.0] * self.n
        pi[self._indeks_for(start_tilstand)] = 1.0
        return pi
