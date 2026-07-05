"""
Dual-objective composition sweep: maximise scattering K_solar AND sky-cooling ε_window.
Dual objective = 0.5 × (K_solar/K_max) + 0.5 × (ε_window/ε_max)

ε_window = volume-fraction weighted average of component atmospheric emissivities:
  TiO₂: 0.90  ZrO₂: 0.90  BaSO₄: 0.912  SiO₂: 0.770  (Lorentz/literature values)
  Normalised by total pigment volume fraction (excluding lime matrix).

BaSO₄ swept to 25 wt% (extended from Stage 2's 20 wt% max) to map the Pareto front.
"""
import os
from itertools import product

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import miepython
import numpy as np
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(PROJECT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
N_MATRIX = 1.63
D_OPT    = {"TiO2_fine": 400, "TiO2_coarse": 1000,
             "ZrO2_fine": 600, "ZrO2_coarse": 1400}
N_PART   = {"TiO2_fine": 2.80, "TiO2_coarse": 2.80,
             "ZrO2_fine": 2.29, "ZrO2_coarse": 2.29}
RHO      = {"TiO2": 4.26, "ZrO2": 5.68, "SiO2": 2.65, "BaSO4": 4.49, "Lime": 2.24}

# Component atmospheric window emissivities (from Lorentz/literature)
EPS_WIN  = {"TiO2": 0.90, "ZrO2": 0.90, "BaSO4": 0.912, "SiO2": 0.770}

# Fixed components
SIO2_WT      = 5.0
LIME_MIN_WT  = 40.0
TOTAL_MAX_WT = 60.0

# Sweep space — BaSO₄ extended to 25 wt% to map Pareto front
TIO2_LOADINGS    = [10, 15, 20, 25, 30]
TIO2_FINE_FRACS  = [0.4, 0.5, 0.6, 0.7]
ZRO2_LOADINGS    = [0, 5, 10, 15]
BASO4_LEVELS     = [15.0, 20.0, 25.0]   # extended to 25 wt%

# Pareto flag threshold — equivalent to Stage 2 K_proxy > 12.0 in KM-corrected units
# (Stage 2 used Q_sca/d without (1-g) factor; KM-corrected values are ~3.3× smaller)
K_SOLAR_THRESHOLD = 3.5   # ≈ top-third of KM-corrected K_solar distribution

# ── AM1.5G spectrum ────────────────────────────────────────────────────────────
spectrum   = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
WL         = spectrum["wavelength_nm"].values.astype(float)
IRR        = spectrum["irradiance_w_m2_nm"].values.astype(float)
TOTAL_IRR  = np.trapezoid(IRR, WL)


def solar_mean(q):
    return float(np.trapezoid(q * IRR, WL) / TOTAL_IRR)


# ── Pre-compute solar-weighted Q_scat/d for each particle type ─────────────────
print("Computing Mie solar-weighted Q_scat for 4 particle types …")
QS_SOLAR = {}
for name, d in D_OPT.items():
    n = N_PART[name]
    m = complex(n, 0.0)
    _, qs, _, g = miepython.efficiencies(m, float(d), WL, n_env=N_MATRIX)
    # KM scattering coefficient per unit volume fraction: (3/4) × (1-g) × Q_sca / d
    ks = (3.0/4.0) * (1 - g) * qs / d   # [1/nm]
    QS_SOLAR[name] = solar_mean(ks)      # scalar solar mean
    print(f"  {name:<16}: K_solar/phi = {QS_SOLAR[name]*1e4:.4f} ×10⁻⁴/nm")


def wt_to_volfrac(wt_dict):
    vols = {k: v / RHO.get(k.split("_")[0], RHO[k] if k in RHO else 1.0)
            for k, v in wt_dict.items()}
    # Use proper rho keys
    rho_map = {
        "TiO2_fine": RHO["TiO2"], "TiO2_coarse": RHO["TiO2"],
        "ZrO2_fine": RHO["ZrO2"], "ZrO2_coarse": RHO["ZrO2"],
        "BaSO4": RHO["BaSO4"], "SiO2": RHO["SiO2"], "Lime": RHO["Lime"],
    }
    vols = {k: v / rho_map[k] for k, v in wt_dict.items()}
    total = sum(vols.values())
    return {k: v / total for k, v in vols.items()}


def compute_k_solar(vol_fracs):
    """KM scattering strength proxy (proportional to solar reflectance)."""
    return sum(vol_fracs.get(name, 0.0) * qs for name, qs in QS_SOLAR.items()) * 1e4


def compute_eps_window(vol_fracs, wt_fracs):
    """
    ε_window = Σ_i (ε_i × φ_i) / Σ_i φ_i   (over TiO₂, ZrO₂, BaSO₄, SiO₂ only).
    Uses volume fractions from wt% conversion.
    """
    phi_tio2  = vol_fracs.get("TiO2_fine", 0) + vol_fracs.get("TiO2_coarse", 0)
    phi_zro2  = vol_fracs.get("ZrO2_fine", 0) + vol_fracs.get("ZrO2_coarse", 0)
    phi_baso4 = vol_fracs.get("BaSO4", 0)
    phi_sio2  = vol_fracs.get("SiO2",  0)
    phi_total_pigment = phi_tio2 + phi_zro2 + phi_baso4 + phi_sio2
    if phi_total_pigment < 1e-10:
        return 0.0
    numer = (EPS_WIN["TiO2"]  * phi_tio2 +
             EPS_WIN["ZrO2"]  * phi_zro2 +
             EPS_WIN["BaSO4"] * phi_baso4 +
             EPS_WIN["SiO2"]  * phi_sio2)
    return numer / phi_total_pigment


# ── Sweep ──────────────────────────────────────────────────────────────────────
rows = []
for baso4_wt, tio2_wt, fine_frac, zro2_wt in product(
        BASO4_LEVELS, TIO2_LOADINGS, TIO2_FINE_FRACS, ZRO2_LOADINGS):

    total_additives = tio2_wt + zro2_wt + SIO2_WT + baso4_wt
    lime_wt = 100.0 - total_additives
    if total_additives > TOTAL_MAX_WT or lime_wt < LIME_MIN_WT:
        continue

    wt_dict = {
        "TiO2_fine":   tio2_wt * fine_frac,
        "TiO2_coarse": tio2_wt * (1 - fine_frac),
        "ZrO2_fine":   zro2_wt * 0.5,
        "ZrO2_coarse": zro2_wt * 0.5,
        "BaSO4": baso4_wt,
        "SiO2":  SIO2_WT,
        "Lime":  lime_wt,
    }
    # Filter out zero entries
    wt_dict = {k: v for k, v in wt_dict.items() if v > 0}
    vf = wt_to_volfrac(wt_dict)

    k_sol  = compute_k_solar(vf)
    eps_w  = compute_eps_window(vf, wt_dict)

    rows.append({
        "TiO2_wt": tio2_wt, "TiO2_fine_frac": fine_frac,
        "ZrO2_wt": zro2_wt, "BaSO4_wt": baso4_wt,
        "SiO2_wt": SIO2_WT, "Lime_wt": round(lime_wt, 1),
        "K_solar": k_sol, "eps_window": eps_w,
    })

df = pd.DataFrame(rows)
print(f"\nTotal valid formulations: {len(df)}")

# ── Normalise and dual objective ───────────────────────────────────────────────
K_MAX   = df["K_solar"].max()
EPS_MAX = df["eps_window"].max()
df["K_solar_norm"]   = df["K_solar"] / K_MAX
df["eps_window_norm"]= df["eps_window"] / EPS_MAX
df["dual_obj"]       = 0.5 * df["K_solar_norm"] + 0.5 * df["eps_window_norm"]

# Pareto flag: BaSO₄ > 20 wt% AND K_solar > threshold
df["pareto_flag"] = (df["BaSO4_wt"] > 20) & (df["K_solar"] >= K_SOLAR_THRESHOLD)

df = df.sort_values("dual_obj", ascending=False).reset_index(drop=True)
df["row_rank"] = df.index + 1
df.to_csv(os.path.join(PROJECT_DIR, "dual_objective_results.csv"), index=False)

# ── Scatter plot: ε_window vs K_solar coloured by BaSO₄ loading ────────────────
fig, ax = plt.subplots(figsize=(9, 6))
baso4_vals = sorted(df["BaSO4_wt"].unique())
cmap = plt.cm.RdYlGn
norm = plt.Normalize(min(baso4_vals), max(baso4_vals))

for bv in baso4_vals:
    sub = df[df["BaSO4_wt"] == bv]
    sc  = ax.scatter(sub["K_solar"], sub["eps_window"],
                     c=[bv]*len(sub), cmap=cmap, norm=norm,
                     alpha=0.7, s=40, edgecolors="none",
                     label=f"BaSO₄={bv:.0f}%")

# Highlight Pareto-optimal
pareto = df[df["pareto_flag"]]
if len(pareto):
    ax.scatter(pareto["K_solar"], pareto["eps_window"],
               marker="*", s=160, c="black", zorder=5, label=f"Pareto-optimal (n={len(pareto)})")

# Top 10 by dual objective
top10 = df.head(10)
for _, r in top10.iterrows():
    label_str = (f"TiO₂{r.TiO2_wt:.0f}/"
                 f"ZrO₂{r.ZrO2_wt:.0f}/"
                 f"BS{r.BaSO4_wt:.0f}")
    ax.annotate(label_str, (r.K_solar, r.eps_window),
                fontsize=6, xytext=(4, 2), textcoords="offset points")

cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
cbar.set_label("BaSO₄ loading (wt%)")
ax.axvline(K_SOLAR_THRESHOLD, linestyle="--", color="grey", lw=1,
           label=f"K_solar = {K_SOLAR_THRESHOLD}")
ax.set_xlabel("K_solar (scattering coefficient proxy, ↑ = higher NIR reflectance)")
ax.set_ylabel("ε_window (atmospheric window emissivity, ↑ = better sky cooling)")
ax.set_title("Pareto front: scattering performance vs atmospheric window emissivity\n"
             "(all 3-level BaSO₄ sweep formulations, coloured by BaSO₄ loading)")
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "pareto_front_scatter_sky_cooling.png"), dpi=150)
plt.close(fig)

# ── Print results ──────────────────────────────────────────────────────────────
print("\n" + "=" * 76)
print("DUAL-OBJECTIVE SWEEP  [0.5×K_norm + 0.5×ε_norm]")
print(f"K_max={K_MAX:.3f}  ε_max={EPS_MAX:.4f}")
print("=" * 76)
print(f"\n{'Rk':>3}  {'TiO₂':>5} {'f%':>4} {'ZrO₂':>5} {'BaSO₄':>6} "
      f"{'Lime':>5}  {'K_solar':>8}  {'ε_win':>7}  {'DualObj':>8}  {'Pareto':>7}")
print("-" * 76)
for _, r in df.head(10).iterrows():
    pareto_str = "★ PARETO" if r["pareto_flag"] else ""
    print(f"{r['row_rank']:>3}  {r.TiO2_wt:>4.0f}% {r.TiO2_fine_frac*100:>3.0f}% "
          f"{r.ZrO2_wt:>4.0f}% {r.BaSO4_wt:>5.0f}%  {r.Lime_wt:>4.0f}%  "
          f"{r.K_solar:>8.3f}  {r.eps_window:>7.4f}  {r.dual_obj:>8.4f}  {pareto_str}")

# Pareto-optimal candidates
print(f"\n── PARETO-OPTIMAL CANDIDATES (BaSO₄>20%, K_solar≥{K_SOLAR_THRESHOLD}) ──")
pareto_df = df[df["pareto_flag"]].head(10)
if len(pareto_df):
    for _, r in pareto_df.iterrows():
        print(f"  Rank {r['row_rank']:3d}: TiO₂={r.TiO2_wt:.0f}%({r.TiO2_fine_frac*100:.0f}%f)  "
              f"ZrO₂={r.ZrO2_wt:.0f}%  BaSO₄={r.BaSO4_wt:.0f}%  "
              f"Lime={r.Lime_wt:.0f}%  "
              f"K={r.K_solar:.3f}  ε={r.eps_window:.4f}  obj={r.dual_obj:.4f}")
else:
    print("  None found — no formulation meets both criteria simultaneously.")

# ── BaSO₄ loading impact analysis ─────────────────────────────────────────────
print("\n── BaSO₄ LOADING IMPACT ON ε_window AND K_solar ──")
for bv in baso4_vals:
    sub = df[df["BaSO4_wt"] == bv]
    print(f"  BaSO₄={bv:.0f}wt%:  ε_window {sub.eps_window.min():.4f}–{sub.eps_window.max():.4f}  "
          f"K_solar {sub.K_solar.min():.2f}–{sub.K_solar.max():.2f}  "
          f"n={len(sub)} formulations")

print(f"\nSaved: dual_objective_results.csv")
print(f"Plot:  figures/pareto_front_scatter_sky_cooling.png")
