"""
generer_figurer.py — genererer grafer for forskellige policesammensætninger.

Gemmer alle figurer i mappen 'figurer/'.

Scenarier:
  1. Varierende startdepot        — 0 / 100k / 500k / 1M kr.
  2. Varierende startalder        — 30 / 40 / 50 år.
  3. Varierende pensionsalder     — 62 / 65 / 67 år.
  4. Varierende præmie            — lav / middel / høj (livrente).
  5. Produktsammenligning         — livrente / ratepension / aldersopsparing.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions
from pension.policy import Policy, ProductType, RATEPENSION_INDBETALINGSLOFT
from pension.projection import projicér
from pension.output import trin_til_dataframe

# ---------------------------------------------------------------------------
# Fælles modelparametre
# ---------------------------------------------------------------------------

biometri = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)
marked = MarketAssumptions(rf=0.04, volatilitet=0.15)

OMKOSTNINGSPCT = 0.005 / 12.0   # 0,5 % p.a. månedligt
DOEDSFALDSSUM = 500_000.0

FIGURER_DIR = "figurer"
os.makedirs(FIGURER_DIR, exist_ok=True)


def _fmt_kr(x, _):
    """Talformater til kr-akser."""
    return f"{x:,.0f}"


def _alder_serie(df):
    return df["alder"].values


def _maaneder(start_alder, slut_alder):
    return round((slut_alder - start_alder) * 12)


def _fremregn(police, slut_alder):
    n = _maaneder(police.alder, slut_alder)
    res = projicér(police, marked, biometri, n)
    return trin_til_dataframe(res)


# ---------------------------------------------------------------------------
# Hjælpefunktion: to-panel grafskabelon
# ---------------------------------------------------------------------------

def _to_panel_graf(titel, filnavn, serier_depot, serier_ydelse,
                   udbet_alder=None, x_label="Alder (år)"):
    """
    Tegner standard to-panel graf (depot øverst, ydelse nederst).

    serier_depot / serier_ydelse : liste af dict med nøgler
        x, y, label, color, linestyle (valgfri)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(titel, fontsize=11)

    for s in serier_depot:
        ax1.plot(s["x"], s["y"] / 1_000,
                 color=s["color"], linewidth=1.5,
                 linestyle=s.get("linestyle", "-"),
                 label=s["label"])

    if udbet_alder is not None:
        ax1.axvline(udbet_alder, color="gray", linestyle="--",
                    linewidth=1, label=f"Udbetalingsstart ({int(udbet_alder)} år)")

    ax1.set_ylabel("Depot (1.000 kr)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_kr))
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("Depotudvikling")

    for s in serier_ydelse:
        ax2.plot(s["x"], s["y"],
                 color=s["color"], linewidth=1.5,
                 linestyle=s.get("linestyle", "-"),
                 label=s["label"])

    if udbet_alder is not None:
        ax2.axvline(udbet_alder, color="gray", linestyle="--", linewidth=1)

    ax2.set_xlabel(x_label)
    ax2.set_ylabel("Kr. per måned")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_kr))
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("Månedlig ydelse")

    plt.tight_layout()
    sti = os.path.join(FIGURER_DIR, filnavn)
    plt.savefig(sti, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Gemt: {sti}")


# ===========================================================================
# Scenarie 1 — Varierende startdepot (livrente, alder 40, pension 67)
# ===========================================================================

print("\n=== Scenarie 1: Varierende startdepot ===")

depots = [0, 100_000, 500_000, 1_000_000]
farver_depot = ["steelblue", "darkorange", "seagreen", "purple"]
praemie_lv = RATEPENSION_INDBETALINGSLOFT / 12 * 1.2   # 6.870 kr/md

serier_d, serier_y = [], []
for depot_val, farve in zip(depots, farver_depot):
    police = Policy(
        alder=40.0, depot=depot_val, doedsfaldssum=DOEDSFALDSSUM,
        praemie=praemie_lv, omkostningspct=OMKOSTNINGSPCT,
        produkt=ProductType.LIVRENTE, udbetalingsstart_alder=67.0,
    )
    df = _fremregn(police, slut_alder=100.0)
    lbl = f"Depot D₀ = {depot_val:,.0f} kr"
    serier_d.append(dict(x=_alder_serie(df), y=df["depot"].values,
                         label=lbl, color=farve))
    serier_y.append(dict(x=_alder_serie(df), y=df["ydelse"].values,
                         label=lbl, color=farve))

_to_panel_graf(
    titel=(f"Livrente — varierende startdepot  |  alder 40 → pension 67 → 100  "
           f"|  præmie {praemie_lv:,.0f} kr/md  |  rf=4 %, α=0,5 % p.a."),
    filnavn="1_varierende_startdepot.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
    udbet_alder=67.0,
)

# ===========================================================================
# Scenarie 2 — Varierende startalder (livrente, depot 100k, pension 67)
# ===========================================================================

print("\n=== Scenarie 2: Varierende startalder ===")

aldre = [30, 40, 50]
farver_alder = ["steelblue", "darkorange", "seagreen"]

serier_d, serier_y = [], []
for start_alder, farve in zip(aldre, farver_alder):
    police = Policy(
        alder=float(start_alder), depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
        praemie=praemie_lv, omkostningspct=OMKOSTNINGSPCT,
        produkt=ProductType.LIVRENTE, udbetalingsstart_alder=67.0,
    )
    df = _fremregn(police, slut_alder=100.0)
    lbl = f"Startalder {start_alder} år"
    serier_d.append(dict(x=_alder_serie(df), y=df["depot"].values,
                         label=lbl, color=farve))
    serier_y.append(dict(x=_alder_serie(df), y=df["ydelse"].values,
                         label=lbl, color=farve))

_to_panel_graf(
    titel=(f"Livrente — varierende startalder  |  depot 100.000 kr  "
           f"|  pension ved 67  |  præmie {praemie_lv:,.0f} kr/md  |  rf=4 %, α=0,5 % p.a."),
    filnavn="2_varierende_startalder.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
    udbet_alder=67.0,
)

# ===========================================================================
# Scenarie 3 — Varierende pensionsalder (livrente, alder 40, depot 100k)
# ===========================================================================

print("\n=== Scenarie 3: Varierende pensionsalder ===")

pensionsaldre = [62, 65, 67]
farver_pension = ["steelblue", "darkorange", "seagreen"]

serier_d, serier_y = [], []
for pens_alder, farve in zip(pensionsaldre, farver_pension):
    police = Policy(
        alder=40.0, depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
        praemie=praemie_lv, omkostningspct=OMKOSTNINGSPCT,
        produkt=ProductType.LIVRENTE, udbetalingsstart_alder=float(pens_alder),
    )
    df = _fremregn(police, slut_alder=100.0)
    lbl = f"Pension ved {pens_alder} år"
    serier_d.append(dict(x=_alder_serie(df), y=df["depot"].values,
                         label=lbl, color=farve))
    serier_y.append(dict(x=_alder_serie(df), y=df["ydelse"].values,
                         label=lbl, color=farve))

_to_panel_graf(
    titel=(f"Livrente — varierende pensionsalder  |  alder 40, depot 100.000 kr  "
           f"|  præmie {praemie_lv:,.0f} kr/md  |  rf=4 %, α=0,5 % p.a."),
    filnavn="3_varierende_pensionsalder.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
)

# ===========================================================================
# Scenarie 4 — Varierende præmie (livrente, alder 40, depot 100k, pension 67)
# ===========================================================================

print("\n=== Scenarie 4: Varierende præmie ===")

# Livrente har intet lovbestemt loft — vi vælger tre niveauer
praemier = [
    (2_000.0, "Lav — 2.000 kr/md"),
    (praemie_lv, f"Middel — {praemie_lv:,.0f} kr/md"),
    (15_000.0, "Høj — 15.000 kr/md"),
]
farver_praemie = ["steelblue", "darkorange", "seagreen"]

serier_d, serier_y = [], []
for (praemie_val, lbl), farve in zip(praemier, farver_praemie):
    police = Policy(
        alder=40.0, depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
        praemie=praemie_val, omkostningspct=OMKOSTNINGSPCT,
        produkt=ProductType.LIVRENTE, udbetalingsstart_alder=67.0,
    )
    df = _fremregn(police, slut_alder=100.0)
    serier_d.append(dict(x=_alder_serie(df), y=df["depot"].values,
                         label=lbl, color=farve))
    serier_y.append(dict(x=_alder_serie(df), y=df["ydelse"].values,
                         label=lbl, color=farve))

_to_panel_graf(
    titel="Livrente — varierende præmie  |  alder 40, depot 100.000 kr, pension 67  |  rf=4 %, α=0,5 % p.a.",
    filnavn="4_varierende_praemie.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
    udbet_alder=67.0,
)

# ===========================================================================
# Scenarie 5 — Produktsammenligning (alder 40, depot 100k, pension 67)
# ===========================================================================

print("\n=== Scenarie 5: Produktsammenligning ===")

praemie_rate = RATEPENSION_INDBETALINGSLOFT / 12      # 5.725 kr/md (loft)
praemie_lv_5 = praemie_rate * 1.2                    # 6.870 kr/md

# Livrente
police_lv = Policy(
    alder=40.0, depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
    praemie=praemie_lv_5, omkostningspct=OMKOSTNINGSPCT,
    produkt=ProductType.LIVRENTE, udbetalingsstart_alder=67.0,
)
df_lv = _fremregn(police_lv, slut_alder=100.0)

# Ratepension (15 år udbetaling — slut alder 82)
police_rp = Policy(
    alder=40.0, depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
    praemie=praemie_rate, omkostningspct=OMKOSTNINGSPCT,
    produkt=ProductType.RATEPENSION, udbetalingsstart_alder=67.0,
    udbetalingsperiode_aar=15,
)
df_rp = _fremregn(police_rp, slut_alder=82.0)

# Aldersopsparing (præmie = ratepensionsloft, ingen dødsfaldsdækning)
# Udbetales som éngangsbeløb ved pensionering — depot falder til 0 ved alder 67.
police_ao = Policy(
    alder=40.0, depot=100_000.0, doedsfaldssum=0.0,
    praemie=praemie_rate, omkostningspct=OMKOSTNINGSPCT,
    produkt=ProductType.ALDERSOPSPARING, udbetalingsstart_alder=67.0,
)
df_ao = _fremregn(police_ao, slut_alder=68.0)

serier_d = [
    dict(x=_alder_serie(df_lv), y=df_lv["depot"].values,
         label=f"Livrente ({praemie_lv_5:,.0f} kr/md)", color="steelblue"),
    dict(x=_alder_serie(df_rp), y=df_rp["depot"].values,
         label=f"Ratepension 15 år ({praemie_rate:,.0f} kr/md)", color="darkorange",
         linestyle="--"),
    dict(x=_alder_serie(df_ao), y=df_ao["depot"].values,
         label=f"Aldersopsparing 15 år ({praemie_rate:,.0f} kr/md)", color="seagreen",
         linestyle="-."),
]
serier_y = [
    dict(x=_alder_serie(df_lv), y=df_lv["ydelse"].values,
         label="Ydelse — livrente", color="steelblue"),
    dict(x=_alder_serie(df_rp), y=df_rp["ydelse"].values,
         label="Ydelse — ratepension", color="darkorange", linestyle="--"),
    dict(x=_alder_serie(df_ao), y=df_ao["ydelse"].values,
         label="Ydelse — aldersopsparing", color="seagreen", linestyle="-."),
]

_to_panel_graf(
    titel="Produktsammenligning  |  alder 40, depot 100.000 kr, pension 67  |  rf=4 %, α=0,5 % p.a.",
    filnavn="5_produktsammenligning.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
    udbet_alder=67.0,
)

# ===========================================================================
# Scenarie 6 — Ratepension: varierende udbetalingsperiode (10 / 15 / 20 år)
# ===========================================================================

print("\n=== Scenarie 6: Ratepension — varierende udbetalingsperiode ===")

udbet_perioder = [10, 15, 20]
farver_udbet = ["steelblue", "darkorange", "seagreen"]

serier_d, serier_y = [], []
for periode, farve in zip(udbet_perioder, farver_udbet):
    slut = 67 + periode
    police = Policy(
        alder=40.0, depot=100_000.0, doedsfaldssum=DOEDSFALDSSUM,
        praemie=praemie_rate, omkostningspct=OMKOSTNINGSPCT,
        produkt=ProductType.RATEPENSION, udbetalingsstart_alder=67.0,
        udbetalingsperiode_aar=periode,
    )
    df = _fremregn(police, slut_alder=float(slut))
    lbl = f"{periode} års udbetaling (→ {slut} år)"
    serier_d.append(dict(x=_alder_serie(df), y=df["depot"].values,
                         label=lbl, color=farve))
    serier_y.append(dict(x=_alder_serie(df), y=df["ydelse"].values,
                         label=lbl, color=farve))

_to_panel_graf(
    titel=(f"Ratepension — varierende udbetalingsperiode  |  alder 40, depot 100.000 kr  "
           f"|  præmie {praemie_rate:,.0f} kr/md  |  rf=4 %, α=0,5 % p.a."),
    filnavn="6_ratepension_udbetalingsperiode.png",
    serier_depot=serier_d,
    serier_ydelse=serier_y,
    udbet_alder=67.0,
)

print(f"\nAlle figurer er gemt i mappen '{FIGURER_DIR}/'.")
