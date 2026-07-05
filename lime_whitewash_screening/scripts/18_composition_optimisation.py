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
N_MATRIX   = 1.63
N_TIO2     = 2.80
N_ZRO2     = 2.29
K_EXT      = 0.0   # transparent in NIR for both

# Particle sizes — Stage 2 d_opt
D_TIO2_FINE   = 400    # nm
D_TIO2_COARSE = 1000   # nm
D_ZRO2_FINE   = 600    # nm
D_ZRO2_COARSE = 1400   # nm

# Densities g/cm³ — for wt% → volume fraction conversion
RHO = {"TiO2": 4.26, "ZrO2": 5.68, "SiO2": 2.65, "BaSO4": 4.49, "Lime": 2.24}

# Fixed components
SIO2_WT      = 5.0     # wt% fixed IR emitter — not swept
BASO4_LEVELS = [15.0, 20.0]   # wt% — two cases for IR emitter loading
LIME_MIN_WT  = 40.0
TOTAL_MAX_WT = 60.0    # max additive loading (lime = 100 - total)

# Sweep space
TIO2_LOADINGS   = [10, 15, 20, 25, 30]          # wt% total TiO₂
TIO2_FINE_FRACS = [0.4, 0.5, 0.6, 0.7]          # fraction of TiO₂ that is fine
ZRO2_LOADINGS   = [0, 5, 10, 15]                 # wt% total ZrO₂

# ── AM1.5G spectrum ────────────────────────────────────────────────────────────
spectrum = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
WL  = spectrum["wavelength_nm"].values.astype(float)
IRR = spectrum["irradiance_w_m2_nm"].values.astype(float)

VIS_MASK  = WL <= 700
NIR1_MASK = (WL > 700) & (WL <= 1400)
NIR2_MASK = WL > 1400


def solar_mean(q, mask=None):
    m = mask if mask is not None else np.ones(len(WL), bool)
    w, i = WL[m], IRR[m]
    d = np.trapezoid(i, w)
    return float(np.trapezoid(q[m] * i, w) / d) if d > 0 else 0.0


def qsca_spectrum(n, d_nm):
    m = complex(n, 0.0)
    _, qs, _, _ = miepython.efficiencies(m, float(d_nm), WL, n_env=N_MATRIX)
    return qs


# ── Pre-compute Q_scat spectra for the 4 particle types ───────────────────────
print("Pre-computing Mie spectra for 4 particle types …")
QS = {
    "TiO2_fine":   qsca_spectrum(N_TIO2, D_TIO2_FINE),
    "TiO2_coarse": qsca_spectrum(N_TIO2, D_TIO2_COARSE),
    "ZrO2_fine":   qsca_spectrum(N_ZRO2, D_ZRO2_FINE),
    "ZrO2_coarse": qsca_spectrum(N_ZRO2, D_ZRO2_COARSE),
}
Q_SOLAR = {k: solar_mean(v) for k, v in QS.items()}
Q_VIS   = {k: solar_mean(v, VIS_MASK) for k, v in QS.items()}
Q_NIR1  = {k: solar_mean(v, NIR1_MASK) for k, v in QS.items()}
Q_NIR2  = {k: solar_mean(v, NIR2_MASK) for k, v in QS.items()}

for k, q in Q_SOLAR.items():
    print(f"  {k:<16} Q_solar={q:.3f}  Q_vis={Q_VIS[k]:.3f}  "
          f"Q_NIR1={Q_NIR1[k]:.3f}  Q_NIR2={Q_NIR2[k]:.3f}")


def wt_to_vol_fracs(wt_dict):
    """Convert {component: wt%} to volume fractions."""
    vols = {k: wt / RHO[k] for k, wt in wt_dict.items()}
    total = sum(vols.values())
    return {k: v / total for k, v in vols.items()}


def scattering_score(vol_fracs, d_map, q_map, mask=None):
    """
    Kubelka-Munk-style scattering coefficient proxy:
      K_proxy = Σ_i  φ_i × Q_scat_i / d_i
    Higher K_proxy ↔ higher predicted reflectance for an optically thick coating.
    Units: 1/nm (cancel in ranking); we scale by 1e4 for readability.
    """
    score = 0.0
    for comp, phi in vol_fracs.items():
        if comp not in d_map:
            continue
        q = solar_mean(q_map[comp], mask)
        score += phi * q / d_map[comp]
    return score * 1e4


# Diameter maps (nm) and Q spectrum maps for scattering components only
D_MAP = {
    "TiO2_fine": D_TIO2_FINE, "TiO2_coarse": D_TIO2_COARSE,
    "ZrO2_fine": D_ZRO2_FINE, "ZrO2_coarse": D_ZRO2_COARSE,
}

# ── Sweep ──────────────────────────────────────────────────────────────────────
rows = []
for baso4_wt, tio2_wt, fine_frac, zro2_wt in product(
        BASO4_LEVELS, TIO2_LOADINGS, TIO2_FINE_FRACS, ZRO2_LOADINGS):

    total_additives = tio2_wt + zro2_wt + SIO2_WT + baso4_wt
    lime_wt = 100.0 - total_additives
    if total_additives > TOTAL_MAX_WT or lime_wt < LIME_MIN_WT:
        continue

    tio2_fine_wt   = tio2_wt * fine_frac
    tio2_coarse_wt = tio2_wt * (1 - fine_frac)
    zro2_fine_wt   = zro2_wt * 0.5   # 50/50 fine/coarse for ZrO₂ bimodal
    zro2_coarse_wt = zro2_wt * 0.5

    scatter_wt = {
        "TiO2_fine":   tio2_fine_wt,
        "TiO2_coarse": tio2_coarse_wt,
        "ZrO2_fine":   zro2_fine_wt,
        "ZrO2_coarse": zro2_coarse_wt,
        "Lime":        lime_wt,   # matrix volume matters for φ
    }
    # Include inert IR emitters in volume calc but exclude from Q sum
    all_wt = dict(scatter_wt, **{"SiO2": SIO2_WT, "BaSO4": baso4_wt})
    # Map to RHO keys
    rho_wt = {
        "TiO2":  tio2_wt,  "ZrO2":  zro2_wt,
        "SiO2":  SIO2_WT,  "BaSO4": baso4_wt, "Lime": lime_wt,
    }
    vol_all = wt_to_vol_fracs(rho_wt)
    vol_tio2_fine   = vol_all["TiO2"] * fine_frac
    vol_tio2_coarse = vol_all["TiO2"] * (1 - fine_frac)
    vol_zro2_fine   = vol_all["ZrO2"] * 0.5
    vol_zro2_coarse = vol_all["ZrO2"] * 0.5

    scatter_vols = {
        "TiO2_fine":   vol_tio2_fine,
        "TiO2_coarse": vol_tio2_coarse,
        "ZrO2_fine":   vol_zro2_fine,
        "ZrO2_coarse": vol_zro2_coarse,
    }

    # K_proxy scores
    k_solar = scattering_score(scatter_vols, D_MAP, QS)
    k_vis   = scattering_score(scatter_vols, D_MAP, QS, VIS_MASK)
    k_nir1  = scattering_score(scatter_vols, D_MAP, QS, NIR1_MASK)
    k_nir2  = scattering_score(scatter_vols, D_MAP, QS, NIR2_MASK)

    rows.append({
        "TiO2_wt":      tio2_wt,
        "TiO2_fine_frac": fine_frac,
        "TiO2_fine_wt": round(tio2_fine_wt, 1),
        "TiO2_coarse_wt": round(tio2_coarse_wt, 1),
        "ZrO2_wt":      zro2_wt,
        "BaSO4_wt":     baso4_wt,
        "SiO2_wt":      SIO2_WT,
        "Lime_wt":      round(lime_wt, 1),
        "K_solar":      k_solar,
        "K_vis":        k_vis,
        "K_NIR1":       k_nir1,
        "K_NIR2":       k_nir2,
        "NIR2_NIR1":    k_nir2 / k_nir1 if k_nir1 > 0 else 0,
        "ZrO2_present": zro2_wt > 0,
    })

df = pd.DataFrame(rows).sort_values("K_solar", ascending=False).reset_index(drop=True)
df["rank"] = df.index + 1
df.to_csv(os.path.join(PROJECT_DIR, "stage2_composition_results.csv"), index=False)

# ── ZrO₂ vs TiO₂-only comparison ─────────────────────────────────────────────
df_no_zro2   = df[~df["ZrO2_present"]].head(10)
df_with_zro2 = df[df["ZrO2_present"]].head(10)

best_no_zro2   = df_no_zro2.iloc[0]["K_solar"]
best_with_zro2 = df_with_zro2.iloc[0]["K_solar"] if len(df_with_zro2) else 0
improvement_pct = (best_with_zro2 - best_no_zro2) / best_no_zro2 * 100

# ── Sensitivity plot: K_solar vs ZrO₂ loading at best TiO₂ config ────────────
best_tio2_wt    = df[df["TiO2_wt"] == df.loc[0, "TiO2_wt"]]
best_baso4      = df.loc[0, "BaSO4_wt"]
pivot = best_tio2_wt[best_tio2_wt["BaSO4_wt"] == best_baso4].groupby("ZrO2_wt")["K_solar"].max()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax1, ax2 = axes

# Left: K_solar vs ZrO₂ loading
ax1.bar(pivot.index, pivot.values, width=3, color=["#2c7bb6" if z > 0 else "#d7191c" for z in pivot.index])
ax1.axhline(best_no_zro2, linestyle="--", color="red", label=f"TiO₂-only best ({best_no_zro2:.3f})")
ax1.set_xlabel("ZrO₂ loading (wt%)")
ax1.set_ylabel("Scattering score K_solar (proxy for reflectance)")
ax1.set_title(f"Effect of ZrO₂ loading\n(TiO₂={df.loc[0,'TiO2_wt']}wt%, BaSO₄={best_baso4}wt%)")
ax1.legend()

# Right: top 10 formulations horizontal bar
top10 = df.head(10).copy()
labels = [f"TiO₂{r.TiO2_wt}({r.TiO2_fine_frac:.0%}f)/ZrO₂{r.ZrO2_wt}/BS{r.BaSO4_wt}"
          for _, r in top10.iterrows()]
colors = ["#2c7bb6" if r.ZrO2_present else "#d7191c" for _, r in top10.iterrows()]
ax2.barh(range(10, 0, -1), top10["K_solar"].values, color=colors)
ax2.set_yticks(range(10, 0, -1))
ax2.set_yticklabels(labels, fontsize=7)
ax2.set_xlabel("K_solar (scattering score)")
ax2.set_title("Top 10 formulations\n(blue=with ZrO₂, red=TiO₂ only)")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "stage2_composition_optimisation.png"), dpi=150)
plt.close(fig)

# ── Print summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 78)
print("COMPOSITION OPTIMISATION  [n_TiO₂=2.80, n_ZrO₂=2.29, n_matrix=1.63]")
print("SiO₂ fixed at 5 wt% (IR emitter). BaSO₄ at 15 or 20 wt% (IR emitter).")
print("Scattering pigments swept: TiO₂ (400/1000nm bimodal), ZrO₂ (600/1400nm).")
print("=" * 78)
print(f"\n{'Rk':>2}  {'TiO₂':>5} {'fine%':>5} {'ZrO₂':>5} {'BaSO₄':>6} "
      f"{'SiO₂':>5} {'Lime':>5}  {'K_sol':>6}  {'K_NIR1':>6}  {'K_NIR2':>6}  "
      f"{'NIR2/1':>6}")
print("-" * 78)
for _, r in df.head(10).iterrows():
    marker = " ←ZrO₂" if r["ZrO2_present"] else ""
    print(f"{r['rank']:>2}  {r['TiO2_wt']:>4}% {r['TiO2_fine_frac']*100:>4.0f}% "
          f"{r['ZrO2_wt']:>4}% {r['BaSO4_wt']:>5}%  {r['SiO2_wt']:>4}%  "
          f"{r['Lime_wt']:>4}%  {r['K_solar']:>6.3f}  {r['K_NIR1']:>6.3f}  "
          f"{r['K_NIR2']:>6.3f}  {r['NIR2_NIR1']:>6.3f}{marker}")

print(f"\n─── ZrO₂ IMPACT ASSESSMENT ─────────────────────────────────────────────")
print(f"  Best TiO₂-only K_solar:       {best_no_zro2:.4f}")
print(f"  Best with-ZrO₂ K_solar:       {best_with_zro2:.4f}")
print(f"  Improvement from adding ZrO₂: {improvement_pct:+.1f}%")
print()
if improvement_pct < 3:
    print("  VERDICT: ZrO₂ gives MARGINAL improvement (<3%). The larger required")
    print("  particle sizes (600/1400nm vs 400/1000nm) add supply-chain complexity")
    print("  for minimal gain. Recommend TiO₂-only formulation for scattering.")
elif improvement_pct < 8:
    print("  VERDICT: ZrO₂ gives MODERATE improvement (3–8%). May be worth adding")
    print("  if ZrO₂ at 600nm is readily available — verify supplier specs before")
    print("  committing. TiO₂ alone is the safer default.")
else:
    print("  VERDICT: ZrO₂ gives MEANINGFUL improvement (>8%). Include in formulation.")

print(f"\n─── TOP 5 TiO₂-ONLY FORMULATIONS ───────────────────────────────────────")
for _, r in df_no_zro2.head(5).iterrows():
    print(f"  TiO₂={r['TiO2_wt']}wt%  fine/coarse={r['TiO2_fine_frac']:.0%}/{1-r['TiO2_fine_frac']:.0%}  "
          f"BaSO₄={r['BaSO4_wt']}wt%  K_solar={r['K_solar']:.4f}")

print(f"\nSaved: stage2_composition_results.csv  ({len(df)} formulations)")
print(f"Plot:  figures/stage2_composition_optimisation.png")
