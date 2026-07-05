import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master = pd.read_csv(os.path.join(PROJECT_DIR, "master_candidates.csv"))

COLORS = {"HIGH": "green", "MEDIUM": "orange", "LOW": "grey"}

# --- Scatter: band_gap vs mie_qscat_800nm, colored by priority ---
fig, ax = plt.subplots(figsize=(9, 7))
for priority, color in COLORS.items():
    sub = master[master["priority"] == priority]
    ax.scatter(sub["band_gap"], sub["mie_qscat_800nm"], c=color, label=priority, alpha=0.75, edgecolors="k", linewidths=0.3)

top10 = master.sort_values("mie_qscat_800nm", ascending=False).head(10)
for _, row in top10.iterrows():
    ax.annotate(
        row["formula"], (row["band_gap"], row["mie_qscat_800nm"]),
        textcoords="offset points", xytext=(5, 5), fontsize=8,
    )

ax.axvline(3.5, linestyle="--", color="black", linewidth=1)
ax.axhline(2.0, linestyle="--", color="black", linewidth=1)
ax.set_xlabel("Band gap (eV)")
ax.set_ylabel("Mie scattering efficiency Q_scat (400nm particle, 800nm, n_matrix=1.59)")
ax.set_title("Oxide candidate screening: band gap vs. Mie scattering efficiency")
ax.legend(title="Priority")
fig.tight_layout()
fig.savefig(os.path.join(PROJECT_DIR, "candidate_screening.png"), dpi=150)
plt.close(fig)
print("Saved candidate_screening.png")

# --- Bar chart: top 15 by mie_qscat_800nm ---
top15 = master.sort_values("mie_qscat_800nm", ascending=False).head(15)
fig2, ax2 = plt.subplots(figsize=(10, 6))
bar_colors = [COLORS.get(p, "grey") for p in top15["priority"]]
ax2.bar(top15["formula"], top15["mie_qscat_800nm"], color=bar_colors, edgecolor="k", linewidth=0.3)
ax2.set_xlabel("Formula")
ax2.set_ylabel("Mie scattering efficiency Q_scat")
ax2.set_title("Top 15 candidates by Mie scattering efficiency")
plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
fig2.tight_layout()
fig2.savefig(os.path.join(PROJECT_DIR, "top_candidates.png"), dpi=150)
plt.close(fig2)
print("Saved top_candidates.png")
