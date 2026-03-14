"""
visualisering.py — deterministisk fremregning og depot-visualisering.

Viser to produkter til sammenligning:
  1. Livrente:     alder 40, depot 100.000 kr, præmie = maks. rateloft × 1,2.
                   Opsparingsperiode til 67 år, livrente-udbetaling til 100 år.
  2. Ratepension:  alder 40, depot 100.000 kr, præmie = maks. rateloft (PBL § 16).
                   Opsparingsperiode til 67 år, rateudbetaling over 15 år (67–82 år).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions
from pension.policy import Policy, ProductType, RATEPENSION_INDBETALINGSLOFT
from pension.projection import projicér
from pension.output import trin_til_dataframe

# --- Modelparametre --------------------------------------------------------

# Gompertz-Makeham parametre (approksimative danske værdier)
biometri = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)

# Marked: 4 % rente, deterministisk (ε=0)
marked = MarketAssumptions(rf=0.04, volatilitet=0.15)

# Præmier: ratepension = maks. loft, livrente = 20 % højere
praemie_rate = RATEPENSION_INDBETALINGSLOFT / 12          # 5.725 kr/md
praemie_livrente = praemie_rate * 1.20                    # 6.870 kr/md

# Policy 1: Livrente, alder 40, opsparingsstart
police_livrente = Policy(
    alder=40.0,
    depot=100_000.0,
    doedsfaldssum=500_000.0,
    praemie=praemie_livrente,
    omkostningspct=0.005 / 12.0,   # 0,5 % p.a. månedligt fratrukket
    produkt=ProductType.LIVRENTE,
    udbetalingsstart_alder=67.0,
)

# Policy 2: Ratepension, alder 40, opsparingsstart, 15 års udbetaling
police_rate = Policy(
    alder=40.0,
    depot=100_000.0,
    doedsfaldssum=500_000.0,
    praemie=praemie_rate,
    omkostningspct=0.005 / 12.0,
    produkt=ProductType.RATEPENSION,
    udbetalingsstart_alder=67.0,
    udbetalingsperiode_aar=15,
)

# Fremregn livrente: 60 år = 720 måneder (alder 40 → 100)
resultater_livrente = projicér(police_livrente, marked, biometri, 60 * 12)
df_livrente = trin_til_dataframe(resultater_livrente)

# Fremregn ratepension: 42 år = 504 måneder (alder 40 → 82)
resultater_rate = projicér(police_rate, marked, biometri, 42 * 12)
df_rate = trin_til_dataframe(resultater_rate)

udbet_start = police_livrente.udbetalingsstart_alder

# --- Graf ------------------------------------------------------------------

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle(
    f"Deterministisk fremregning — livrente ({praemie_livrente:,.0f} kr/md) vs. ratepension ({praemie_rate:,.0f} kr/md)  |  rf=4 %, α=0,5 % p.a.",
    fontsize=12,
)

aldre_l = df_livrente["alder"].values
aldre_r = df_rate["alder"].values

# Subplot 1: Depot
ax1.plot(aldre_l, df_livrente["depot"] / 1_000, color="steelblue", linewidth=1.5, label="Depot — livrente")
ax1.plot(aldre_r, df_rate["depot"] / 1_000, color="darkorange", linewidth=1.5, linestyle="--", label="Depot — ratepension (15 år)")
ax1.axvline(udbet_start, color="gray", linestyle="--", linewidth=1, label=f"Udbetalingsstart ({int(udbet_start)} år)")
ax1.set_ylabel("Depot (1.000 kr)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)
ax1.set_title("Depotudvikling")

# Subplot 2: Ydelse og risikopræmie
ax2.plot(aldre_l, df_livrente["ydelse"], color="seagreen", linewidth=1.5, label="Ydelse — livrente $U_t$")
ax2.plot(aldre_r, df_rate["ydelse"], color="darkorange", linewidth=1.5, linestyle="--", label="Ydelse — ratepension $U_t$")

opsparing_l = df_livrente["risikopraemie"] != 0.0
ax2.plot(
    aldre_l[opsparing_l],
    df_livrente.loc[opsparing_l, "risikopraemie"],
    color="firebrick",
    linewidth=1.2,
    linestyle=":",
    label="Risikopræmie $\\delta_{\\mathrm{liv},t}$",
)
ax2.axvline(udbet_start, color="gray", linestyle="--", linewidth=1)
ax2.set_xlabel("Alder (år)")
ax2.set_ylabel("Kr. per måned")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax2.legend(loc="upper right")
ax2.grid(True, alpha=0.3)
ax2.set_title("Månedlig ydelse og risikopræmie")

plt.tight_layout()
plt.savefig("depot_graf.png", dpi=150, bbox_inches="tight")
print("Graf gemt som depot_graf.png")

# Udskriv nøgletal
depot_ved_67_l = df_livrente.loc[df_livrente["alder"].sub(67.0).abs().idxmin(), "depot"]
depot_ved_67_r = df_rate.loc[df_rate["alder"].sub(67.0).abs().idxmin(), "depot"]
print(f"\nNøgletal (deterministisk, ε=0):")
print(f"  Livrente — depot ved alder 67:     {depot_ved_67_l:>12,.0f} kr")
print(f"  Ratepension — depot ved alder 67:  {depot_ved_67_r:>12,.0f} kr")
print(f"  Livrente — maks. månedlig ydelse:  {df_livrente['ydelse'].max():>12,.0f} kr")
print(f"  Ratepension — første månedlige ydelse: {df_rate.loc[df_rate['ydelse'] > 0, 'ydelse'].iloc[0]:>12,.0f} kr")
