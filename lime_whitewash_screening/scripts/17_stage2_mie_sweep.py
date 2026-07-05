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

# ── DFT-corrected constants ────────────────────────────────────────────────────
N_MATRIX = 1.63   # Ca(OH)₂ portlandite, DFT PBE (was 1.59)
DFT_N = {
    "TiO2":  2.80,   # DFT average (was 2.834 from JARVIS)
    "ZrO2":  2.29,   # DFT average (was 2.490 from JARVIS)
    "SiO2":  1.57,   # DFT PBE quartz (was 2.094 from JARVIS)
    "BaSO4": 1.678,  # DFT PBE barite (was 1.763 from JARVIS)
}

DIAMETERS_NM  = [100, 200, 300, 400, 500, 600, 800, 1000]
CANDIDATES    = ["TiO2","ZrO2","YZr5O11","ZrTiO4","CaTiO3","ZrSiO4","SiO2","BaSO4","YZr4O9","MgWO4"]
BIMODAL_MATS  = ["TiO2", "ZrO2", "BaSO4"]

spectrum = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
WL  = spectrum["wavelength_nm"].values.astype(float)
IRR = spectrum["irradiance_w_m2_nm"].values.astype(float)

VIS_MASK  = WL <= 700
NIR1_MASK = (WL > 700) & (WL <= 1400)
NIR2_MASK = WL > 1400

master = pd.read_csv(os.path.join(PROJECT_DIR, "master_candidates_clean.csv"))
stage1 = pd.read_csv(os.path.join(PROJECT_DIR, "stage1_results.csv")).set_index("formula")


def solar_mean(qsca, mask):
    w, i = WL[mask], IRR[mask]
    d = np.trapezoid(i, w)
    return float(np.trapezoid(qsca[mask] * i, w) / d) if d > 0 else None


def qsca_curve(n, k, d):
    m = complex(float(n), -float(k))
    _, qs, _, _ = miepython.efficiencies(m, float(d), WL, n_env=N_MATRIX)
    return qs


# ── Stage 2 full sweep ──────────────────────────────────────────────────────────
results, curves, changed_flags = [], {}, []

for formula in CANDIDATES:
    row = master[master["formula"] == formula].iloc[0]
    n = DFT_N.get(formula, float(row["n_refractive_index"]))
    k = 0.0

    grid = np.array([qsca_curve(n, k, d) for d in DIAMETERS_NM])
    sw   = np.array([solar_mean(grid[i], np.ones(len(WL), bool)) for i in range(len(DIAMETERS_NM))])
    curves[formula] = sw

    best_i  = int(np.nanargmax(sw))
    d_opt   = DIAMETERS_NM[best_i]
    q_at    = grid[best_i]

    results.append({
        "formula":             formula,
        "n_used":              n,
        "n_source":            "DFT" if formula in DFT_N else "JARVIS/MP",
        "d_opt_nm":            d_opt,
        "Q_scat_solar_weighted": sw[best_i],
        "Q_scat_vis":          solar_mean(q_at, VIS_MASK),
        "Q_scat_NIR1":         solar_mean(q_at, NIR1_MASK),
        "Q_scat_NIR2":         solar_mean(q_at, NIR2_MASK),
    })

    # Flag d_opt change vs Stage 1
    if formula in stage1.index:
        old_dopt = int(stage1.loc[formula, "d_opt_nm"])
        delta    = abs(d_opt - old_dopt)
        if delta > 50:
            changed_flags.append((formula, old_dopt, d_opt, delta))

    # Heatmap
    fig, ax = plt.subplots(figsize=(8, 5))
    pc = ax.pcolormesh(WL, DIAMETERS_NM, grid, shading="nearest", cmap="viridis")
    fig.colorbar(pc, ax=ax, label="Q_scat")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Particle diameter (nm)")
    ax.set_title(f"{formula}: Q_scat(λ, d)  [n={n:.3f}, n_matrix={N_MATRIX}]")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, f"stage2_heatmap_{formula}.png"), dpi=150)
    plt.close(fig)

df = pd.DataFrame(results).sort_values("Q_scat_solar_weighted", ascending=False)
df.to_csv(os.path.join(PROJECT_DIR, "stage2_mie_results.csv"), index=False)

# ── Combined sweep plot ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))
for formula, sw in curves.items():
    src = "DFT" if formula in DFT_N else "DB"
    ax.plot(DIAMETERS_NM, sw, marker="o", label=f"{formula} ({src})")
ax.set_xlabel("Particle diameter (nm)")
ax.set_ylabel(f"Solar-weighted Q_scat  [n_matrix={N_MATRIX}]")
ax.set_title("Stage 2 Mie sweep — DFT-corrected optical constants")
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "stage2_particle_size_comparison.png"), dpi=150)
plt.close(fig)

# ── Bimodal optimisation with updated d_small from Stage 2 ────────────────────
COLORS = {"HIGH": "green", "MEDIUM": "orange", "LOW": "grey"}
bimodal_results = []

d_opt_map = {r["formula"]: r["d_opt_nm"] for r in results}

fig_bi, ax_bi = plt.subplots(figsize=(9, 5))

for formula in BIMODAL_MATS:
    n = DFT_N[formula]
    d_small = d_opt_map[formula]
    qs_small = qsca_curve(n, 0.0, d_small)

    sweep = []
    for d_large in range(1000, 3001, 200):
        qs_large  = qsca_curve(n, 0.0, d_large)
        q_total   = 0.6 * qs_small + 0.4 * qs_large
        q_solar   = solar_mean(q_total, np.ones(len(WL), bool))
        q_nir1    = solar_mean(q_total, NIR1_MASK)
        q_nir2    = solar_mean(q_total, NIR2_MASK)
        ratio     = q_nir2 / q_nir1 if q_nir1 else None
        sweep.append({"d_large": d_large, "q_solar": q_solar,
                      "q_nir1": q_nir1, "q_nir2": q_nir2,
                      "ratio": ratio, "curve": q_total})

    feasible = [s for s in sweep if s["ratio"] and s["ratio"] > 0.6 and s["q_solar"] > 2.5]
    best = max(feasible, key=lambda s: s["q_solar"]) if feasible else \
           max(sweep, key=lambda s: s["ratio"] or 0)
    target_met = len(feasible) > 0

    bimodal_results.append({
        "formula":            formula,
        "n_particle":         n,
        "n_matrix":           N_MATRIX,
        "d_small":            d_small,
        "d_large":            best["d_large"],
        "weight_small":       0.6,
        "weight_large":       0.4,
        "Q_solar_weighted":   best["q_solar"],
        "Q_NIR1":             best["q_nir1"],
        "Q_NIR2":             best["q_nir2"],
        "NIR2_NIR1_ratio":    best["ratio"],
        "target_met":         target_met,
    })

    xs = [s["d_large"] for s in sweep]
    qs = [s["q_solar"] for s in sweep]
    ax_bi.plot(xs, qs, marker="o", label=f"{formula} (d_small={d_small}nm)")

ax_bi.axhline(2.5, linestyle="--", color="k", linewidth=0.8)
ax_bi.axhline(2.5 * 0.9, linestyle=":", color="grey", linewidth=0.7)
ax_bi.set_xlabel("d_large (nm)")
ax_bi.set_ylabel("Solar-weighted Q_scat (bimodal 60/40)")
ax_bi.set_title(f"Stage 2 bimodal optimisation  [n_matrix={N_MATRIX}]")
ax_bi.legend()
fig_bi.tight_layout()
fig_bi.savefig(os.path.join(FIGURES_DIR, "stage2_bimodal_comparison.png"), dpi=150)
plt.close(fig_bi)

pd.DataFrame(bimodal_results).to_csv(
    os.path.join(PROJECT_DIR, "stage2_bimodal_results.csv"), index=False)

# ── Print outputs ───────────────────────────────────────────────────────────────
print("=" * 72)
print(f"STAGE 2 MIE SWEEP  [n_matrix={N_MATRIX}, DFT-corrected constants]")
print("=" * 72)
print(f"\n{'Material':<12} {'n':>6} {'Src':>5}  {'d_opt':>6}  {'Q_solar':>8}  "
      f"{'Q_vis':>7}  {'Q_NIR1':>7}  {'Q_NIR2':>7}  {'NIR2/1':>7}")
print("-" * 72)
for _, r in df.iterrows():
    s1_dopt = int(stage1.loc[r["formula"], "d_opt_nm"]) if r["formula"] in stage1.index else "—"
    flag = " ◄ CHANGED" if r["formula"] in [c[0] for c in changed_flags] else ""
    print(f"{r['formula']:<12} {r['n_used']:>6.3f} {r['n_source']:>5}  "
          f"{r['d_opt_nm']:>5}nm  {r['Q_scat_solar_weighted']:>8.3f}  "
          f"{r['Q_scat_vis']:>7.3f}  {r['Q_scat_NIR1']:>7.3f}  "
          f"{r['Q_scat_NIR2']:>7.3f}  "
          f"{r['Q_scat_NIR2']/r['Q_scat_NIR1']:>7.3f}{flag}")

print(f"\n{'d_opt changes > 50nm vs Stage 1':}")
if changed_flags:
    for formula, old, new, delta in sorted(changed_flags, key=lambda x: -x[3]):
        print(f"  {formula:<12}  {old}nm → {new}nm  (Δ={delta}nm)")
else:
    print("  None — all d_opt within 50nm of Stage 1")

print(f"\n{'Bimodal optimisation (60/40, d_large sweep 1000–3000nm)':}")
print(f"{'Material':<12} {'d_small':>8} {'d_large':>8} {'Q_solar':>8} "
      f"{'NIR2/1':>8} {'Target':>8}")
print("-" * 58)
for r in bimodal_results:
    status = "MET" if r["target_met"] else "NOT MET"
    print(f"{r['formula']:<12} {r['d_small']:>7}nm {r['d_large']:>7}nm "
          f"{r['Q_solar_weighted']:>8.3f} {r['NIR2_NIR1_ratio']:>8.3f} {status:>8}")

print(f"\nSaved: stage2_mie_results.csv, stage2_bimodal_results.csv")
print(f"Plots: stage2_heatmap_*.png, stage2_particle_size_comparison.png, "
      f"stage2_bimodal_comparison.png")
