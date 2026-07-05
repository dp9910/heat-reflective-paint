import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import miepython
import numpy as np
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(PROJECT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

N_MATRIX = 1.59
DIAMETERS_NM = [100, 200, 300, 400, 500, 600, 800, 1000]
CANDIDATES = ["TiO2", "ZrO2", "YZr5O11", "ZrTiO4", "CaTiO3", "ZrSiO4", "SiO2", "BaSO4", "YZr4O9", "MgWO4"]

spectrum = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
WAVELENGTHS_NM = spectrum["wavelength_nm"].values.astype(float)
IRRADIANCE = spectrum["irradiance_w_m2_nm"].values.astype(float)

VIS_MASK = WAVELENGTHS_NM <= 700
NIR1_MASK = (WAVELENGTHS_NM > 700) & (WAVELENGTHS_NM <= 1400)
NIR2_MASK = WAVELENGTHS_NM > 1400

master = pd.read_csv(os.path.join(PROJECT_DIR, "master_candidates_clean.csv"))


def solar_weighted_mean(qsca, mask):
    wl, irr = WAVELENGTHS_NM[mask], IRRADIANCE[mask]
    denom = np.trapezoid(irr, wl)
    if denom <= 0:
        return None
    return float(np.trapezoid(qsca[mask] * irr, wl) / denom)


results = []
combined_curves = {}

for formula in CANDIDATES:
    rows = master[master["formula"] == formula]
    if rows.empty:
        print(f"WARNING: {formula} not found in master_candidates_clean.csv -- skipping.")
        continue
    row = rows.iloc[0]
    n, k = row.get("n_refractive_index"), row.get("k_extinction_coefficient")
    if pd.isna(n):
        print(f"WARNING: {formula} has no refractive index on file -- skipping.")
        continue
    k = 0.0 if pd.isna(k) else float(k)
    m = complex(float(n), -k)

    qsca_grid = np.zeros((len(DIAMETERS_NM), len(WAVELENGTHS_NM)))
    for i, d in enumerate(DIAMETERS_NM):
        _, qsca, _, _ = miepython.efficiencies(m, float(d), WAVELENGTHS_NM, n_env=N_MATRIX)
        qsca_grid[i, :] = qsca

    solar_weighted_by_d = np.array([
        solar_weighted_mean(qsca_grid[i, :], np.ones_like(WAVELENGTHS_NM, dtype=bool))
        for i in range(len(DIAMETERS_NM))
    ])
    combined_curves[formula] = solar_weighted_by_d

    best_i = int(np.nanargmax(solar_weighted_by_d))
    d_opt = DIAMETERS_NM[best_i]
    qsca_at_opt = qsca_grid[best_i, :]

    q_solar = solar_weighted_by_d[best_i]
    q_vis = solar_weighted_mean(qsca_at_opt, VIS_MASK)
    q_nir1 = solar_weighted_mean(qsca_at_opt, NIR1_MASK)
    q_nir2 = solar_weighted_mean(qsca_at_opt, NIR2_MASK)

    results.append({
        "formula": formula,
        "d_opt_nm": d_opt,
        "Q_scat_solar_weighted": q_solar,
        "Q_scat_vis": q_vis,
        "Q_scat_NIR1": q_nir1,
        "Q_scat_NIR2": q_nir2,
    })

    fig, ax = plt.subplots(figsize=(8, 5))
    mesh = ax.pcolormesh(WAVELENGTHS_NM, DIAMETERS_NM, qsca_grid, shading="nearest", cmap="viridis")
    fig.colorbar(mesh, ax=ax, label="Q_scat")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Particle diameter (nm)")
    ax.set_title(f"{formula}: Q_scat(λ, d)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, f"heatmap_{formula}.png"), dpi=150)
    plt.close(fig)
    print(f"{formula}: d_opt={d_opt}nm, Q_scat_solar_weighted={q_solar:.3f} -> saved heatmap_{formula}.png")

# --- Combined comparison plot ---
fig, ax = plt.subplots(figsize=(9, 6))
for formula, curve in combined_curves.items():
    ax.plot(DIAMETERS_NM, curve, marker="o", label=formula)
ax.set_xlabel("Particle diameter (nm)")
ax.set_ylabel("Solar-weighted Q_scat (300-2500nm)")
ax.set_title("Solar-weighted Mie scattering efficiency vs. particle diameter")
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "optimal_particle_size_comparison.png"), dpi=150)
plt.close(fig)
print("Saved figures/optimal_particle_size_comparison.png")

# --- Summary CSV + ranked table ---
results_df = pd.DataFrame(results).sort_values("Q_scat_solar_weighted", ascending=False)
results_df.to_csv(os.path.join(PROJECT_DIR, "stage1_results.csv"), index=False)
print(f"\nSaved stage1_results.csv ({len(results_df)} rows)")

print("\nRanked table (at each material's optimal particle size):")
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
