"""
generer_markov_figurer.py — grafer for Markov-fremregning (4-tilstandsmodel).

Modellerer en opsparingspolice med tilstandene:
  aktiv   — rask, betaler præmie, har dødsfaldsdækning
  invalid — præmiefritagelse, forhøjet dødelighed
  genkøbt — absorberende; hele depotet udbetales ved overgang fra aktiv
  doed    — absorberende; nettorisiko (S − D) udbetales

Konvention: betalinger ved overgange fratrækkes afgivende tilstands depot.

Figurer:
  7_markov_depoter.png         — betingede depoter + sandsynligheder
  8_markov_betalingsstroemme.png — forventede betalingsstrømme per overgang
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions
from pension.markov import MarkovModel, Tilstand
from pension.markov_produkt import MarkovProdukt, OvgangsCashflow, TilstandsCashflow
from pension.markov_projection import markov_projicér

# ---------------------------------------------------------------------------
# Modelparametre
# ---------------------------------------------------------------------------

FIGURER_DIR = "figurer"
os.makedirs(FIGURER_DIR, exist_ok=True)

biometri = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)
marked = MarketAssumptions(rf=0.04, volatilitet=0.0)   # deterministisk

DOEDSFALDSSUM = 500_000.0
DEPOT0        = 200_000.0
PRAEMIE       = 3_000.0          # kr/md (aktiv); præmiefritagelse i invalid
OMKOSTNINGSPCT = 0.005 / 12.0   # 0,5 % p.a.

START_ALDER = 40.0
SLUT_ALDER  = 67.0
ANTAL_TRIN  = round((SLUT_ALDER - START_ALDER) * 12)

# ---------------------------------------------------------------------------
# Markov-model og produkt
# ---------------------------------------------------------------------------

MODEL = MarkovModel(
    tilstande=[
        Tilstand("aktiv"),
        Tilstand("invalid"),
        Tilstand("genkøbt", absorberende=True),
        Tilstand("doed",    absorberende=True),
    ],
    intensiteter={
        ("aktiv",   "invalid"):  lambda a: 0.005,
        ("aktiv",   "genkøbt"):  lambda a: 0.03,
        ("aktiv",   "doed"):     biometri.intensitet,
        ("invalid", "aktiv"):    lambda a: 0.01,
        ("invalid", "doed"):     lambda a: biometri.intensitet(a) * 1.5,
    },
)

PRODUKT = MarkovProdukt(
    navn="standardprodukt_4tilstand",
    tilstands_cashflows=[
        TilstandsCashflow("aktiv",   lambda a, d: PRAEMIE, tidspunkt="pre"),
        TilstandsCashflow("invalid", lambda a, d: 0.0,     tidspunkt="pre"),
    ],
    overgangscashflows=[
        OvgangsCashflow("aktiv",   "doed",    lambda a, d, S=DOEDSFALDSSUM: S - d),
        OvgangsCashflow("invalid", "doed",    lambda a, d, S=DOEDSFALDSSUM: S - d),
        OvgangsCashflow("aktiv",   "genkøbt", lambda a, d: d),
    ],
    omkostningspct=OMKOSTNINGSPCT,
    initial_depot={"aktiv": DEPOT0},
)

resultater = markov_projicér(MODEL, PRODUKT, marked, START_ALDER, ANTAL_TRIN)

# ---------------------------------------------------------------------------
# Udtræk tidsserier
# ---------------------------------------------------------------------------

navne  = [t.navn for t in MODEL.tilstande]
indeks = {navn: i for i, navn in enumerate(navne)}

aldre = [r.alder for r in resultater]

pi = {
    navn: [r.pi[indeks[navn]] for r in resultater]
    for navn in navne
}

# Betingede depoter D_s(t)
depot_betinget = {
    navn: [r.depot_per_tilstand[navn] for r in resultater]
    for navn in navne
}

# Sandsynlighedsvægtede depotbidrag: π_s(t) · D_s(t)
depot_vaegtet = {
    navn: [r.pi[indeks[navn]] * r.depot_per_tilstand[navn] for r in resultater]
    for navn in navne
}

forventet_depot = [r.forventet_depot for r in resultater]

# Forventede betalingsstrømme per overgangstype
# Konvention: betaling beregnes fra afgivende tilstands depot og intensitet
p_matrices = [MODEL.p_matrix(r.alder) for r in resultater]

def _overgangsflow(fra: str, til: str, beloeb_fn):
    """π_fra(t) · P_{fra,til}(t) · beloeb(alder, D_fra(t))."""
    i, j = indeks[fra], indeks[til]
    return [
        r.pi[i] * p[i][j] * beloeb_fn(r.alder, r.depot_per_tilstand[fra])
        for r, p in zip(resultater, p_matrices)
    ]

cf_aktiv_genkøbt = _overgangsflow(
    "aktiv", "genkøbt", lambda a, d: d
)
cf_aktiv_doed = _overgangsflow(
    "aktiv", "doed", lambda a, d, S=DOEDSFALDSSUM: S - d
)
cf_invalid_doed = _overgangsflow(
    "invalid", "doed", lambda a, d, S=DOEDSFALDSSUM: S - d
)

forventet_ydelse = [r.forventet_ydelse for r in resultater]
forventet_pal    = [r.forventet_pal_skat for r in resultater]


def _fmt_kr(x, _):
    return f"{x:,.0f}"


# ===========================================================================
# Figur 7 — Forventede depoter og tilstandssandsynligheder
# ===========================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
fig.suptitle(
    "Markov 4-tilstandsmodel — forventede depoter og tilstandssandsynligheder\n"
    f"aktiv/invalid/genkøbt/doed  |  D₀={DEPOT0:,.0f} kr  |  præmie {PRAEMIE:,.0f} kr/md  "
    f"|  S={DOEDSFALDSSUM:,.0f} kr  |  rf=4 %, α=0,5 % p.a.",
    fontsize=9,
)

# --- Panel 1: depoter ---

# Stacked area: sandsynlighedsvægtet bidrag fra aktiv og invalid
ax1.stackplot(
    aldre,
    [v / 1_000 for v in depot_vaegtet["aktiv"]],
    [v / 1_000 for v in depot_vaegtet["invalid"]],
    labels=["π_aktiv · D_aktiv", "π_invalid · D_invalid"],
    colors=["steelblue", "darkorange"],
    alpha=0.55,
)
# Betingede depoter som stiplede kurver
ax1.plot(
    aldre, [d / 1_000 for d in depot_betinget["aktiv"]],
    color="steelblue", linewidth=1.2, linestyle="--",
    label="D_aktiv (betinget)",
)
ax1.plot(
    aldre, [d / 1_000 for d in depot_betinget["invalid"]],
    color="darkorange", linewidth=1.2, linestyle="--",
    label="D_invalid (betinget)",
)
# Forventet depot som tyk sort kurve
ax1.plot(
    aldre, [d / 1_000 for d in forventet_depot],
    color="black", linewidth=2.0,
    label="E[D(t)] = Σ π_s · D_s",
)

ax1.set_ylabel("Depot (1.000 kr)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_kr))
ax1.legend(loc="upper left", fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_title("Betingede og forventede depoter")

# --- Panel 2: sandsynligheder ---

farver_pi = {
    "aktiv":   "steelblue",
    "invalid": "darkorange",
    "genkøbt": "seagreen",
    "doed":    "firebrick",
}
for navn in navne:
    ax2.plot(
        aldre, pi[navn],
        color=farver_pi[navn], linewidth=1.5,
        label=f"π_{navn}",
    )

ax2.set_xlabel("Alder (år)")
ax2.set_ylabel("Sandsynlighed")
ax2.set_ylim(0, 1.05)
ax2.legend(loc="center right", fontsize=8)
ax2.grid(True, alpha=0.3)
ax2.set_title("Tilstandssandsynligheder π(t)")

plt.tight_layout()
sti = os.path.join(FIGURER_DIR, "7_markov_depoter.png")
plt.savefig(sti, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Gemt: {sti}")


# ===========================================================================
# Figur 8 — Forventede betalingsstrømme per afgivende tilstand
# ===========================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
fig.suptitle(
    "Markov 4-tilstandsmodel — forventede betalingsstrømme per afgivende tilstand\n"
    "Betalinger ved overgange fratrækkes afgivende tilstands depot  "
    f"|  D₀={DEPOT0:,.0f} kr  |  S={DOEDSFALDSSUM:,.0f} kr  |  rf=4 %, α=0,5 % p.a.",
    fontsize=9,
)

# --- Panel 1: betalingsstrømme per overgangstype ---
# Tegnes som linjer så negative værdier (S − D < 0: dødelighedsgevinst) vises korrekt.

ax1.fill_between(aldre, forventet_ydelse, alpha=0.12, color="black")
ax1.plot(
    aldre, forventet_ydelse,
    color="black", linewidth=2.0,
    label="E[U(t)] total",
)
ax1.plot(
    aldre, cf_aktiv_genkøbt,
    color="seagreen", linewidth=1.5,
    label="Genkøb:  aktiv → genkøbt  (= π_aktiv · P_ag · D_aktiv)",
)
ax1.plot(
    aldre, cf_aktiv_doed,
    color="steelblue", linewidth=1.5, linestyle="--",
    label="Dødsfald: aktiv → doed    (= π_aktiv · P_ad · (S − D_aktiv))",
)
ax1.plot(
    aldre, cf_invalid_doed,
    color="darkorange", linewidth=1.5, linestyle="--",
    label="Dødsfald: invalid → doed  (= π_invalid · P_id · (S − D_invalid))",
)
ax1.axhline(0, color="gray", linewidth=0.8, linestyle=":")

ax1.set_ylabel("Kr. per måned")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_kr))
ax1.legend(loc="upper left", fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_title(
    "Forventet betalingsstrøm per overgang (afgivende tilstand)  "
    "— negativt = dødelighedsgevinst (D > S)"
)

# --- Panel 2: PAL-skat ---

ax2.fill_between(aldre, forventet_pal, alpha=0.60, color="slategray")
ax2.plot(aldre, forventet_pal, color="slategray", linewidth=1.2, label="E[PAL(t)]")

ax2.set_xlabel("Alder (år)")
ax2.set_ylabel("Kr. per måned")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_kr))
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)
ax2.set_title("Forventet PAL-skat")

plt.tight_layout()
sti = os.path.join(FIGURER_DIR, "8_markov_betalingsstroemme.png")
plt.savefig(sti, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Gemt: {sti}")

print(f"\nAlle Markov-figurer gemt i '{FIGURER_DIR}/'.")
