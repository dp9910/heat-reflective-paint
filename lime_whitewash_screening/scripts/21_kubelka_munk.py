"""
Kubelka-Munk reflectance prediction for ELW formulations.
Uses Mie Q_scat, Q_abs, and asymmetry g computed at each wavelength from miepython.
Applies KM with finite-thickness correction for 200 µm coating on concrete substrate.
"""
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

# ── Wavelength grid ────────────────────────────────────────────────────────────
WL = np.arange(300, 2501, 10, dtype=float)   # nm, 221 points

# ── Optical constants (DFT-corrected, Stage 2) ────────────────────────────────
N_MATRIX = 1.63   # Ca(OH)₂ binder
PARTICLES = {
    # name: (n, k, d_nm)
    "TiO2_fine":   (2.80, 0.0,  400),
    "TiO2_coarse": (2.80, 0.0, 1000),
    "ZrO2_fine":   (2.29, 0.0,  600),
    "ZrO2_coarse": (2.29, 0.0, 1400),
    "BaSO4":       (1.678, 0.0, 1000),
    "SiO2":        (1.57,  0.0,  800),
}

# ── Densities for wt% → volume fraction ───────────────────────────────────────
RHO = {"TiO2": 4.26, "ZrO2": 5.68, "SiO2": 2.65, "BaSO4": 4.49, "Lime": 2.24}

# ── Formulations (wt%) ────────────────────────────────────────────────────────
# ELW-1 to ELW-5: top 5 from Stage 2 composition optimisation
# ELW-C: TiO₂-only control (no ZrO₂)
# Fine fraction = fraction of total TiO₂ that is the fine grade
# ZrO₂ split 50/50 fine/coarse

FORMULATIONS = {
    "ELW-1": dict(TiO2=30, TiO2_fine_frac=0.70, ZrO2=10, BaSO4=15, SiO2=5, Lime=40),
    "ELW-2": dict(TiO2=30, TiO2_fine_frac=0.70, ZrO2= 5, BaSO4=20, SiO2=5, Lime=40),
    "ELW-3": dict(TiO2=30, TiO2_fine_frac=0.60, ZrO2=10, BaSO4=15, SiO2=5, Lime=40),
    "ELW-4": dict(TiO2=25, TiO2_fine_frac=0.70, ZrO2=15, BaSO4=15, SiO2=5, Lime=40),
    "ELW-5": dict(TiO2=30, TiO2_fine_frac=0.50, ZrO2=10, BaSO4=15, SiO2=5, Lime=40),
    "ELW-C": dict(TiO2=30, TiO2_fine_frac=0.70, ZrO2= 0, BaSO4=20, SiO2=5, Lime=45),
}

# Substrate and constants
R_G    = 0.30           # concrete substrate reflectance (grey, approximate)
D_NM   = 200_000.0      # coating thickness in nm (200 µm)
K_MIN  = 1e-8           # minimum absorption [1/nm] for numerical stability (K/S << 1)


def wt_to_vol(formulation):
    """Convert wt% spec to per-particle-type volume fractions (within all solids+lime)."""
    wt = formulation
    # Expand TiO2 into fine/coarse, ZrO2 into fine/coarse
    raw = {
        "TiO2_fine":   wt["TiO2"] * wt["TiO2_fine_frac"],
        "TiO2_coarse": wt["TiO2"] * (1 - wt["TiO2_fine_frac"]),
        "ZrO2_fine":   wt["ZrO2"] * 0.5,
        "ZrO2_coarse": wt["ZrO2"] * 0.5,
        "BaSO4":       wt["BaSO4"],
        "SiO2":        wt["SiO2"],
        "Lime":        wt["Lime"],
    }
    # Component density mapping
    rho_map = {
        "TiO2_fine": RHO["TiO2"], "TiO2_coarse": RHO["TiO2"],
        "ZrO2_fine": RHO["ZrO2"], "ZrO2_coarse": RHO["ZrO2"],
        "BaSO4": RHO["BaSO4"], "SiO2": RHO["SiO2"], "Lime": RHO["Lime"],
    }
    vols = {k: v / rho_map[k] for k, v in raw.items() if v > 0}
    total_vol = sum(vols.values())
    return {k: v / total_vol for k, v in vols.items()}


# ── Pre-compute Mie spectra for all particle types ─────────────────────────────
print("Computing Mie Q_scat, Q_abs, g for 6 particle types × 221 wavelengths …")
MIE = {}
for name, (n_p, k_p, d_nm) in PARTICLES.items():
    m = complex(n_p, 0.0)   # k_p = 0 for all (transparent in NIR)
    Q_ext_arr = np.zeros(len(WL))
    Q_sca_arr = np.zeros(len(WL))
    g_arr     = np.zeros(len(WL))
    for i, lam in enumerate(WL):
        qe, qs, qb, g = miepython.efficiencies(m, float(d_nm), lam, n_env=N_MATRIX)
        Q_ext_arr[i] = qe
        Q_sca_arr[i] = qs
        g_arr[i]     = g
    Q_abs_arr = np.clip(Q_ext_arr - Q_sca_arr, 0, None)
    MIE[name] = {"Q_sca": Q_sca_arr, "Q_abs": Q_abs_arr, "g": g_arr, "d_nm": d_nm}
    print(f"  {name}: peak Q_sca={Q_sca_arr.max():.3f} at λ={WL[Q_sca_arr.argmax()]:.0f}nm, "
          f"max|g|={abs(g_arr).max():.3f}")


def km_S_K(vol_fracs):
    """
    KM scattering S(λ) and absorption K(λ) from Mie coefficients.

    S(λ) = Σ_i (3/4) × φ_i × (1−g_i) × Q_sca_i / d_i     [1/nm]
    K(λ) = Σ_i (3/2) × φ_i × Q_abs_i / d_i                [1/nm]

    Factor (1−g) accounts for forward scattering in Mie regime.
    Factor 3/4 and 3/2 from sphere geometry + KM vs radiative-transfer conventions.
    Lime matrix (φ_Lime) contributes no scattering (n_particle = n_matrix).
    """
    S = np.zeros(len(WL))
    K = np.zeros(len(WL))
    for name, phi in vol_fracs.items():
        if name == "Lime" or name not in MIE:
            continue
        md = MIE[name]
        d = md["d_nm"]
        S += (3.0/4.0) * phi * (1 - md["g"]) * md["Q_sca"] / d
        K += (3.0/2.0) * phi * md["Q_abs"] / d
    K = np.maximum(K, K_MIN)   # numerical floor
    return S, K


def km_reflectance(S, K, d_nm=D_NM, R_g=R_G):
    """
    KM reflectance for finite coating of thickness d_nm on substrate R_g.
    Uses hyperbolic solution of the 2-flux KM ODE.
    """
    KoverS = K / np.maximum(S, 1e-30)
    a  = 1.0 + KoverS
    b  = np.sqrt(np.maximum(a**2 - 1, 0))

    # Scattering optical depth
    Sd = S * d_nm
    bSd = b * Sd

    # coth(bSd): handle small bSd to avoid numerical issues
    with np.errstate(over="ignore", invalid="ignore"):
        coth_bSd = np.where(bSd > 0.001, 1.0 / np.tanh(np.minimum(bSd, 700)), 1.0 / bSd)

    numer = 1.0 - R_g * (a - b * coth_bSd)
    denom = a - R_g + b * coth_bSd
    R = numer / np.where(np.abs(denom) > 1e-30, denom, 1e-30)
    return np.clip(R, 0, 1)


# ── AM1.5G spectrum ────────────────────────────────────────────────────────────
spectrum  = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
IRR_FULL  = np.interp(WL, spectrum["wavelength_nm"].values, spectrum["irradiance_w_m2_nm"].values)
TOTAL_IRR = np.trapezoid(IRR_FULL, WL)


def solar_R(R, mask=None):
    wl = WL[mask] if mask is not None else WL
    ir = IRR_FULL[mask] if mask is not None else IRR_FULL
    d  = np.trapezoid(ir, wl)
    return float(np.trapezoid(R * ir, wl) / d) if d > 0 else 0.0


# ── Run all formulations ───────────────────────────────────────────────────────
print("\nComputing KM reflectance for all formulations …")
results = {}
for label, spec in FORMULATIONS.items():
    vf = wt_to_vol(spec)
    S, K = km_S_K(vf)
    R    = km_reflectance(S, K)
    r_sol = solar_R(R)
    results[label] = {"R": R, "S": S, "K": K, "vf": vf,
                      "r_solar": r_sol,
                      "r_vis":  solar_R(R[WL <= 700], WL <= 700),
                      "r_nir1": solar_R(R[(WL > 700) & (WL <= 1400)], (WL > 700) & (WL <= 1400)),
                      "r_nir2": solar_R(R[WL > 1400], WL > 1400),
                      "spec":   spec}

# ── Solar-weighted reflectance of plain lime (literature) ─────────────────────
R_LIME_LIT  = 0.65   # Athens paper and general literature
R_PURDUE    = 0.981  # Purdue BaSO₄ super-white paint


# ── Plot ───────────────────────────────────────────────────────────────────────
COLORS = {
    "ELW-1": "#1a6faf", "ELW-2": "#2ca02c", "ELW-3": "#d62728",
    "ELW-4": "#9467bd", "ELW-5": "#e8601c", "ELW-C": "#8c564b",
}

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9),
                                gridspec_kw={"height_ratios": [2.5, 1]})

for label, res in results.items():
    ax1.plot(WL, res["R"], color=COLORS[label], linewidth=1.6,
             label=f"{label}  R={res['r_solar']:.3f}")

ax1.axhline(R_LIME_LIT, color="grey",  linestyle=":", lw=1.5, label=f"Plain lime  R≈{R_LIME_LIT:.2f} (lit.)")
ax1.axhline(R_PURDUE,   color="black", linestyle="--", lw=1.2, label=f"Purdue BaSO₄  R={R_PURDUE:.3f}")

ax1b = ax1.twinx()
ax1b.fill_between(WL, IRR_FULL / IRR_FULL.max(), alpha=0.06, color="gold")
ax1b.set_ylabel("AM1.5G (normalised)", color="goldenrod", fontsize=9)
ax1b.set_ylim(0, 4); ax1b.tick_params(axis="y", labelcolor="goldenrod", labelsize=8)
ax1b.set_yticks([])

ax1.axvline(700,  linestyle=":", color="k", lw=0.6, alpha=0.4)
ax1.axvline(1400, linestyle=":", color="k", lw=0.6, alpha=0.4)
ax1.text(500,  0.04, "Vis",  ha="center", fontsize=8, color="grey")
ax1.text(1050, 0.04, "NIR-1", ha="center", fontsize=8, color="grey")
ax1.text(1950, 0.04, "NIR-2", ha="center", fontsize=8, color="grey")
ax1.set_xlim(300, 2500); ax1.set_ylim(0, 1.05)
ax1.set_ylabel("Reflectance R(λ)")
ax1.set_title("Kubelka-Munk reflectance prediction — ELW formulations\n"
              "(Mie Q_sca, Q_abs, g + KM 2-flux, 200 µm coating, R_substrate=0.30)")
ax1.legend(fontsize=9, ncol=2)

# Bottom: improvement over plain lime
for label, res in results.items():
    ax2.plot(WL, res["R"] - R_LIME_LIT, color=COLORS[label], linewidth=1.4, label=label)
ax2.axhline(0, color="grey", lw=0.8, linestyle=":")
ax2.axvline(700,  linestyle=":", color="k", lw=0.6, alpha=0.4)
ax2.axvline(1400, linestyle=":", color="k", lw=0.6, alpha=0.4)
ax2.set_xlim(300, 2500); ax2.set_xlabel("Wavelength (nm)")
ax2.set_ylabel("ΔR vs plain lime")
ax2.set_title("Spectral reflectance improvement over plain lime whitewash")
ax2.legend(fontsize=8, ncol=3)

fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "km_reflectance_prediction.png"), dpi=150)
plt.close(fig)

# ── Save CSV ───────────────────────────────────────────────────────────────────
df = pd.DataFrame({"wavelength_nm": WL})
for label, res in results.items():
    df[f"R_{label}"] = res["R"]
df["R_plain_lime_lit"]     = R_LIME_LIT
df["R_purdue_benchmark"]   = R_PURDUE
df["AM1.5G_irr_W_m2_nm"]  = IRR_FULL
df.to_csv(os.path.join(PROJECT_DIR, "km_reflectance_spectra.csv"), index=False)

summary_rows = []
for label, res in results.items():
    s = res["spec"]
    summary_rows.append({
        "formulation": label,
        "TiO2_wt": s["TiO2"], "TiO2_fine_frac": s["TiO2_fine_frac"],
        "ZrO2_wt": s["ZrO2"], "BaSO4_wt": s["BaSO4"], "SiO2_wt": s["SiO2"],
        "Lime_wt": s["Lime"],
        "R_solar": res["r_solar"], "R_vis": res["r_vis"],
        "R_NIR1": res["r_nir1"], "R_NIR2": res["r_nir2"],
        "delta_R_vs_lime": res["r_solar"] - R_LIME_LIT,
        "gap_to_purdue":   R_PURDUE - res["r_solar"],
    })
pd.DataFrame(summary_rows).to_csv(os.path.join(PROJECT_DIR, "km_results.csv"), index=False)

# ── Print summary ──────────────────────────────────────────────────────────────
print("\n" + "="*72)
print("KUBELKA-MUNK REFLECTANCE PREDICTIONS  [200 µm, R_substrate=0.30]")
print("="*72)
print(f"\n{'Label':<7} {'TiO₂':>5} {'f%':>4} {'ZrO₂':>5} {'BS':>4} {'Si':>3} "
      f"  {'R_sol':>6} {'R_vis':>6} {'R_NIR1':>7} {'R_NIR2':>7}  {'ΔR_lime':>7}  {'→Purdue':>8}")
print("-"*72)
for label, res in results.items():
    s = res["spec"]
    print(f"{label:<7} {s['TiO2']:>4}% {s['TiO2_fine_frac']*100:>3.0f}% "
          f"{s['ZrO2']:>4}% {s['BaSO4']:>3}% {s['SiO2']:>2}%  "
          f"  {res['r_solar']:>6.4f} {res['r_vis']:>6.4f} {res['r_nir1']:>7.4f} "
          f"{res['r_nir2']:>7.4f}  {res['r_solar']-R_LIME_LIT:>+7.4f}  "
          f"{R_PURDUE-res['r_solar']:>+8.4f}")

print(f"\n{'Plain lime (literature)':>40}  ~{R_LIME_LIT:.3f}")
print(f"{'Purdue BaSO₄ benchmark':>40}   {R_PURDUE:.3f}")

best = max(results.items(), key=lambda x: x[1]["r_solar"])
print(f"\nBest formulation: {best[0]}  R_solar={best[1]['r_solar']:.4f}")
print(f"  Improvement over plain lime: +{best[1]['r_solar']-R_LIME_LIT:.4f} "
      f"({(best[1]['r_solar']/R_LIME_LIT - 1)*100:.1f}%)")
print(f"  Gap to Purdue:               {R_PURDUE - best[1]['r_solar']:.4f}")
print(f"\nSaved: km_results.csv, km_reflectance_spectra.csv")
print(f"Plot:  figures/km_reflectance_prediction.png")
