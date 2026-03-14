"""
visualisering.py — deterministisk fremregning og depot-visualisering.

Eksempelpolicy: livrente, alder 40, depot 100.000 kr, præmie 2.000 kr/md.
Opsparingsperiode til 67 år, derefter livrente-udbetaling til 100 år.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions
from pension.policy import Policy, ProductType
from pension.projection import projicér
from pension.output import trin_til_dataframe

# --- Modelparametre --------------------------------------------------------

# Gompertz-Makeham parametre (approksimative danske værdier)
biometri = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)

# Marked: 4 % rente, deterministisk (ε=0)
marked = MarketAssumptions(rf=0.04, volatilitet=0.15)

# Policy: livrente, alder 40, opsparingsstart
police = Policy(
    alder=40.0,
    depot=100_000.0,
    doedsfaldssum=500_000.0,
    praemie=2_000.0,
    omkostningspct=0.005 / 12.0,   # 0,5 % p.a. månedligt fratrukket
    produkt=ProductType.LIVRENTE,
    udbetalingsstart_alder=67.0,
)

# Fremregn 60 år = 720 måneder (alder 40 → 100)
antal_trin = 60 * 12
resultater = projicér(police, marked, biometri, antal_trin)
df = trin_til_dataframe(resultater)

# --- Graf ------------------------------------------------------------------

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle(
    "Deterministisk fremregning — livrente (40 → 100 år, rf=4 %, α=0,5 % p.a.)",
    fontsize=13,
)

aldre = df["alder"].values
udbet_start = police.udbetalingsstart_alder

# Subplot 1: Depot
ax1.plot(aldre, df["depot"] / 1_000, color="steelblue", linewidth=1.5, label="Depot $D_t$")
ax1.axvline(udbet_start, color="gray", linestyle="--", linewidth=1, label=f"Udbetalingsstart ({int(udbet_start)} år)")
ax1.set_ylabel("Depot (1.000 kr)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)
ax1.set_title("Depotudvikling")

# Subplot 2: Ydelse og risikopræmie
ax2.plot(aldre, df["ydelse"], color="seagreen", linewidth=1.5, label="Månedlig ydelse $U_t$")
opsparing = df["risikopraemie"] != 0.0
ax2.plot(
    aldre[opsparing],
    df.loc[opsparing, "risikopraemie"],
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
depot_ved_67 = df.loc[df["alder"].sub(67.0).abs().idxmin(), "depot"]
max_ydelse = df["ydelse"].max()
print(f"\nNøgletal (deterministisk, ε=0):")
print(f"  Depot ved alder 67:      {depot_ved_67:>12,.0f} kr")
print(f"  Maks. månedlig ydelse:   {max_ydelse:>12,.0f} kr")
print(f"  Første ydelse (md. 325): {df.loc[df['ydelse'] > 0, 'ydelse'].iloc[0]:>12,.0f} kr")
