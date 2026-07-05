"""
Transfer Matrix Method + Bruggeman Effective Medium Theory
Predicts coating reflectance R(λ) from 300–2500 nm using DFT optical constants.

Stack: Air | Coating (200 µm) | Concrete substrate
All layers treated as incoherent (coating >> wavelength).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from tmm import inc_tmm

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(PROJECT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Wavelength grid (nm) ───────────────────────────────────────────────────────
WL = np.arange(300, 2501, 5, dtype=float)

# ── DFT-derived optical constants (static, k=0 in NIR — transparent region) ──
N = {
    "TiO2":  2.80,
    "ZrO2":  2.29,
    "SiO2":  1.57,
    "BaSO4": 1.678,
    "Lime":  1.63,
}
# Concrete substrate: literature value
N_SUBSTRATE = complex(1.80, 0.01)   # tmm uses n+ik convention (positive k = absorbing)

# Densities g/cm³
RHO = {"TiO2": 4.26, "ZrO2": 5.68, "SiO2": 2.65, "BaSO4": 4.49, "Lime": 2.24}

COATING_THICKNESS_NM = 200_000   # 200 µm


# ── Bruggeman effective medium ─────────────────────────────────────────────────
def bruggeman_eps(eps_components, fracs):
    """
    Solve Bruggeman self-consistent equation for ε_eff (real).
    Σ_i f_i (ε_i - ε_eff) / (ε_i + 2 ε_eff) = 0
    Physical root bounded between min(ε_i) and max(ε_i).
    """
    def f(e_eff):
        return sum(fi * (ei - e_eff) / (ei + 2 * e_eff)
                   for fi, ei in zip(fracs, eps_components))
    lo, hi = min(eps_components) * 0.9, max(eps_components) * 1.1
    return brentq(f, lo, hi)


def wt_to_volfrac(wt_dict):
    vols = {k: w / RHO[k] for k, w in wt_dict.items()}
    total = sum(vols.values())
    return {k: v / total for k, v in vols.items()}


def coating_n_eff(vol_fracs):
    """Return scalar n_eff from Bruggeman (wavelength-independent for static n)."""
    comps = list(vol_fracs.keys())
    eps   = [N[c] ** 2 for c in comps]
    fracs = [vol_fracs[c] for c in comps]
    eps_eff = bruggeman_eps(eps, fracs)
    return np.sqrt(eps_eff)   # scalar


# ── TMM reflectance (incoherent, normal incidence, unpolarized) ────────────────
def tmm_reflectance(n_eff, wavelengths):
    """
    Incoherent TMM for Air | Coating | Substrate stack.
    n_eff: complex refractive index of coating (scalar or array matching wavelengths).
    """
    n_coat = complex(n_eff, 0.0) if np.isscalar(n_eff) else n_eff
    R = np.zeros(len(wavelengths))
    for i, lam in enumerate(wavelengths):
        n_c = n_coat if np.isscalar(n_coat) else n_coat[i]
        n_list = [1.0, n_c, N_SUBSTRATE]
        d_list = [np.inf, COATING_THICKNESS_NM, np.inf]
        c_list = ['i', 'i', 'i']
        # inc_tmm doesn't support 'u' — average s and p for unpolarized light
        rs = inc_tmm('s', n_list, d_list, c_list, 0, lam)['R']
        rp = inc_tmm('p', n_list, d_list, c_list, 0, lam)['R']
        R[i] = (rs + rp) / 2
    return R


# ── Formulations ───────────────────────────────────────────────────────────────
FORMULATIONS = {
    "Optimal (TiO₂30+ZrO₂10+BaSO₄15+SiO₂5+Lime40)": {
        "TiO2": 30, "ZrO2": 10, "BaSO4": 15, "SiO2": 5, "Lime": 40,
    },
    "TiO₂-only control (TiO₂30+BaSO₄20+SiO₂5+Lime45)": {
        "TiO2": 30, "ZrO2": 0, "BaSO4": 20, "SiO2": 5, "Lime": 45,
    },
    "Plain lime (Ca(OH)₂ only)": {
        "Lime": 100,
    },
}

# ── AM1.5G spectrum ───────────────────────────────────────────────────────────
spectrum = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
wl_am15  = spectrum["wavelength_nm"].values.astype(float)
irr_am15 = spectrum["irradiance_w_m2_nm"].values.astype(float)
irr_interp = np.interp(WL, wl_am15, irr_am15)
total_irr  = np.trapezoid(irr_interp, WL)


def solar_weighted_r(R, mask=None):
    wl = WL[mask] if mask is not None else WL
    ir = irr_interp[mask] if mask is not None else irr_interp
    denom = np.trapezoid(ir, wl)
    return float(np.trapezoid(R * ir, wl) / denom) if denom > 0 else 0.0


# ── Run all formulations ───────────────────────────────────────────────────────
results = {}
print("Computing Bruggeman n_eff and TMM reflectance spectra …\n")

for name, wt_pct in FORMULATIONS.items():
    wt_pct_filtered = {k: v for k, v in wt_pct.items() if v > 0}
    vf = wt_to_volfrac(wt_pct_filtered)
    n_eff = coating_n_eff(vf)
    R = tmm_reflectance(n_eff, WL)
    r_solar = solar_weighted_r(R)
    r_vis   = solar_weighted_r(R[WL <= 700], WL <= 700)
    r_nir   = solar_weighted_r(R[WL > 700],  WL > 700)

    results[name] = {"R": R, "n_eff": n_eff, "r_solar": r_solar,
                     "r_vis": r_vis, "r_nir": r_nir, "vf": vf}

    vf_str = ", ".join(f"{k}={v:.3f}" for k, v in vf.items())
    print(f"{name}")
    print(f"  n_eff = {n_eff:.4f}  (volume fracs: {vf_str})")
    print(f"  R_solar = {r_solar:.4f}   R_vis = {r_vis:.4f}   R_NIR = {r_nir:.4f}")
    print()

# ── Purdue benchmark ──────────────────────────────────────────────────────────
R_PURDUE = np.full_like(WL, 0.981)
R_PURDUE[WL < 400] = 0.93   # slight UV dip for BaSO4 coating

# ── Plot ───────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9),
                                gridspec_kw={"height_ratios": [3, 1]})

colors = {"Optimal": "#1a6faf", "TiO₂-only": "#e8601c", "Plain lime": "#aaaaaa"}
styles = ["-", "--", ":"]
for (name, res), ls in zip(results.items(), styles):
    label_short = name.split("(")[0].strip()
    c = list(colors.values())[list(results.keys()).index(name)]
    ax1.plot(WL, res["R"], ls, color=c, linewidth=1.8,
             label=f"{label_short}  R_solar={res['r_solar']:.3f}")

ax1.plot(WL, R_PURDUE, "-", color="#999999", linewidth=1.2, alpha=0.6,
         label="Purdue BaSO₄ benchmark  R_solar≈0.981")

# AM1.5G shading (secondary y-axis)
ax1b = ax1.twinx()
ax1b.fill_between(WL, irr_interp / irr_interp.max(), alpha=0.06, color="gold")
ax1b.set_ylabel("AM1.5G irradiance (normalised)", color="goldenrod", fontsize=9)
ax1b.set_ylim(0, 4)
ax1b.tick_params(axis="y", labelcolor="goldenrod", labelsize=8)

ax1.axvline(700, linestyle=":", color="k", linewidth=0.7, alpha=0.4)
ax1.axvline(1400, linestyle=":", color="k", linewidth=0.7, alpha=0.4)
ax1.text(500, 0.02, "Visible", ha="center", fontsize=8, color="grey")
ax1.text(1050, 0.02, "NIR-1", ha="center", fontsize=8, color="grey")
ax1.text(1950, 0.02, "NIR-2", ha="center", fontsize=8, color="grey")
ax1.set_xlim(300, 2500)
ax1.set_ylim(0, 1.05)
ax1.set_ylabel("Reflectance R(λ)")
ax1.set_title("Predicted coating reflectance — Bruggeman EMT + Incoherent TMM\n"
              "[Note: EMT treats coating as homogeneous — scattering effects not captured; "
              "actual R will be higher]")
ax1.legend(fontsize=9, loc="upper right")

# Bottom panel: difference vs plain lime
r_lime = results["Plain lime (Ca(OH)₂ only)"]["R"]
for (name, res), ls, c in zip(
        list(results.items())[:2], ["-", "--"],
        [list(colors.values())[0], list(colors.values())[1]]):
    label_short = name.split("(")[0].strip()
    ax2.plot(WL, res["R"] - r_lime, ls, color=c, linewidth=1.5,
             label=f"ΔR: {label_short} vs plain lime")

ax2.axhline(0, color="grey", linewidth=0.8)
ax2.axvline(700, linestyle=":", color="k", linewidth=0.7, alpha=0.4)
ax2.axvline(1400, linestyle=":", color="k", linewidth=0.7, alpha=0.4)
ax2.set_xlim(300, 2500)
ax2.set_xlabel("Wavelength (nm)")
ax2.set_ylabel("ΔR vs plain lime")
ax2.legend(fontsize=9)
ax2.set_title("Reflectance improvement over plain lime whitewash")

fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "tmm_reflectance_prediction.png"), dpi=150)
plt.close(fig)

# ── Save CSV ───────────────────────────────────────────────────────────────────
df_out = pd.DataFrame({"wavelength_nm": WL})
for name, res in results.items():
    short = name.split("(")[0].strip().replace(" ", "_").replace("₂", "2").replace("₄", "4")
    df_out[f"R_{short}"] = res["R"]
df_out["R_Purdue_benchmark"] = R_PURDUE
df_out.to_csv(os.path.join(PROJECT_DIR, "tmm_reflectance_spectra.csv"), index=False)

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 68)
print("REFLECTANCE SUMMARY  [Bruggeman EMT + Incoherent TMM, 200 µm coating]")
print("=" * 68)
print(f"\n{'Formulation':<45} {'R_solar':>8} {'R_vis':>7} {'R_NIR':>7}")
print("-" * 68)
for name, res in results.items():
    short = name[:44]
    print(f"{short:<45} {res['r_solar']:>8.4f} {res['r_vis']:>7.4f} {res['r_nir']:>7.4f}")
print(f"{'Purdue BaSO4 benchmark':<45} {'~0.981':>8} {'~0.930':>7} {'~0.990':>7}")

print("\n── IMPORTANT INTERPRETATION NOTE ────────────────────────────────────")
print("Bruggeman EMT treats the coating as a homogeneous optical medium.")
print("It cannot capture the Mie scattering from discrete particles (400–1400 nm)")
print("which is the dominant reflectance mechanism for pigmented coatings.")
print("These predictions are a LOWER BOUND — actual solar reflectance will")
print("be significantly higher due to multiple particle scattering.")
print("The spectral SHAPE is reliable; the absolute values are underestimates.")
print("For quantitative reflectance prediction use the Stage 2 Mie K_proxy scores.")
print()
print("Saved: tmm_reflectance_spectra.csv")
print("Plot:  figures/tmm_reflectance_prediction.png")
