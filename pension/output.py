"""
output.py — konvertering af projektionsresultater til QRT-alignet CSV-output.

Ansvar:
- Konvertere en liste af `TrinResultat` til et pandas DataFrame.
- Formatere kolonnenavne og enheder alignet med Solvens II QRT-konventioner.
- Skrive DataFrame til CSV-fil.
- Aggregere cashflows på tværs af en portefølje til samlet rapporteringsformat.
- Ingen beregningslogik — kun formatering og I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pension.projection import TrinResultat


def trin_til_dataframe(resultater: Sequence[TrinResultat]):
    """
    Konverterer en liste af TrinResultat til et pandas DataFrame.

    Kolonner svarer til felterne i TrinResultat plus en sti-kolonne (police-id).
    Enheder og kolonnenavne er alignet med Solvens II QRT S.14.01-format.

    Parametre
    ---------
    resultater : sequence of TrinResultat
        Projektionsresultater for én police.

    Returnerer
    ----------
    pandas.DataFrame
        DataFrame med én række per tidstrin.
    """
    pass


def portefølje_til_dataframe(alle_resultater: Sequence[Sequence[TrinResultat]]):
    """
    Aggregerer projektionsresultater for en hel portefølje til ét DataFrame.

    Parametre
    ---------
    alle_resultater : sequence of sequence of TrinResultat
        Ydre sekvens er policer; indre sekvens er tidstrin per police.

    Returnerer
    ----------
    pandas.DataFrame
        Aggregeret DataFrame med police-id som indeks.
    """
    pass


def gem_csv(df, sti: Path | str) -> None:
    """
    Skriver et DataFrame til CSV-fil på den angivne sti.

    Parametre
    ---------
    df : pandas.DataFrame
        DataFrame der skal gemmes.
    sti : Path or str
        Destinationssti for CSV-filen.
    """
    pass
