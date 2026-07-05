"""
Mid-IR dielectric function from DFT phonon data via Lorentz oscillator model.
Computes n(λ), k(λ), reflectance R(λ), and emissivity ε(λ) = 1−R(λ)
for BaSO₄, SiO₂, and the coating mixture in the 5–20 µm range.
Integrates atmospheric window emissivity weighted by Planck B(300K) over 8–13 µm.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
from scipy.optimize import fsolve

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(PROJECT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── DFT phonon modes from dynmat.out ─────────────────────────────────────────
# (freq_cm-1, IR_intensity_D2/A2/amu)  — IR-active only (I > 0.001)
# Imaginary acoustic modes discarded; near-zero acoustic included but won't affect IR window

BASO4_MODES_ALL = [
    # All IR-active modes including ones below atmospheric window
    (88.02, 3.4739), (109.44, 0.1484), (127.73, 8.9079), (130.11, 1.7136),
    (141.13, 10.0048), (156.11, 1.4725), (157.75, 12.1753), (189.77, 0.3927),
    (444.71, 0.0195),
    (573.66, 10.3203), (578.25, 9.0600), (579.80, 0.3024), (600.76, 11.3944),
    (618.47, 0.0095), (998.38, 0.3283), (1000.21, 1.3770),
    (1084.13, 80.1249), (1122.40, 76.1741), (1138.76, 0.0202),
    (1190.58, 78.7077), (1250.61, 0.5707),
]

SIO2_MODES_ALL = [
    (243.17, 0.2001), (245.75, 0.2090), (339.27, 4.7774),
    (372.76, 3.4786), (372.76, 3.4464), (424.35, 7.5874), (424.54, 7.6319),
    (469.26, 8.6889), (691.60, 0.6891), (691.93, 0.6804),
    (774.34, 3.7319), (790.48, 3.3780), (790.69, 3.4069),
    (1080.84, 42.1478), (1080.97, 42.1764), (1091.05, 44.5142),
    (1168.16, 0.5422), (1168.17, 0.5518),
]

# ── Electronic dielectric constants ε_∞ (from DFT ph.x) ─────────────────────
# These are the clamped-ion (high-frequency electronic) values printed by ph.x
EPS_INF = {
    "BaSO4":  2.817,   # average of (2.802, 2.799, 2.851)
    "SiO2":   2.458,   # ordinary ray (quartz uniaxial: 2.458, 2.458, 2.494)
    "TiO2":   7.85,    # average of DFT ε tensor (8.783, 7.384, 7.387)
    "ZrO2":   5.244,   # average of DFT ε tensor (5.381, 5.395, 4.956)
    "Lime":   2.66,    # Ca(OH)2: 1.63² from our DFT (real part only)
}

# ── Unit cell volumes (Å³) for oscillator strength normalization ──────────────
# BaSO4 (Pnma, 4 f.u. = 24 atoms): a=8.88, b=5.46, c=7.15 Å → V≈347 Å³
# SiO2  (P3_121, 3 f.u. = 9 atoms): a=4.91, c=5.40 Å → V=a²csin60°≈113 Å³
V_CELL = {"BaSO4": 347.0, "SiO2": 113.0}

# ── Ionic polarizabilities from dynmat.out ────────────────────────────────────
# dynmat prints the ionic polarizability per unit cell in Å³
# Δε_total_ionic = 4π × α_ionic / V_cell
ALPHA_IONIC = {"BaSO4": 50.25, "SiO2": 13.18}   # Å³, mean from tensor diagonal

# Compute total ionic Δε for each material
DELTA_EPS_TOTAL = {
    mat: 4 * np.pi * ALPHA_IONIC[mat] / V_CELL[mat]
    for mat in ("BaSO4", "SiO2")
}

print("Total ionic dielectric contributions:")
for mat, de in DELTA_EPS_TOTAL.items():
    print(f"  {mat}: ε_∞={EPS_INF[mat]:.3f}  Δε_ionic={de:.3f}  "
          f"ε_0={EPS_INF[mat]+de:.3f}  n_static={np.sqrt(EPS_INF[mat]+de):.3f}")

GAMMA_CM = 10.0   # damping parameter (cm⁻¹), from user specification


# ── Lorentz oscillator model ──────────────────────────────────────────────────
def lorentz_eps(omega_grid, modes_all, eps_inf, delta_eps_total, gamma=GAMMA_CM):
    """
    Build complex dielectric function ε(ω) from phonon modes.

    Oscillator strengths Δε_j normalized so that Σ_j Δε_j = delta_eps_total
    (sum rule: total ionic contribution to static dielectric).
    Distribution weighted by I_j/ω_j² (standard from linear response theory).
    """
    modes = [(w, i) for w, i in modes_all if w > 1.0]   # skip imaginary/acoustic
    weights = np.array([i / w**2 for w, i in modes])
    weights /= weights.sum()
    delta_eps_j = delta_eps_total * weights

    eps = np.full_like(omega_grid, eps_inf, dtype=complex)
    for (w_j, _), de_j in zip(modes, delta_eps_j):
        eps += de_j * w_j**2 / (w_j**2 - omega_grid**2 - 1j * gamma * omega_grid)
    return eps


def eps_to_nk(eps_complex):
    """Extract n and k from complex ε = ε₁ + iε₂."""
    eps1 = eps_complex.real
    eps2 = eps_complex.imag
    modulus = np.abs(eps_complex)
    n = np.sqrt((modulus + eps1) / 2)
    k = np.sqrt((modulus - eps1) / 2)
    return n, k


def fresnel_R(n, k):
    """Normal-incidence Fresnel reflectance for semi-infinite slab (air interface)."""
    return ((n - 1)**2 + k**2) / ((n + 1)**2 + k**2)


# ── Wavelength / wavenumber grids ─────────────────────────────────────────────
WN   = np.linspace(500, 2100, 3200)   # wavenumber cm⁻¹ (5–20 µm)
WL_UM = 1e4 / WN                      # wavelength µm
WL_NM = WL_UM * 1e3                   # wavelength nm

WINDOW_MASK = (WN >= 769) & (WN <= 1250)   # 8–13 µm atmospheric window

# ── Planck blackbody at 300 K (in wavenumber space) ──────────────────────────
T_K = 300.0
HC_K = 1.4388   # hc/k in cm·K
PLANCK_300K = WN**3 / (np.exp(HC_K * WN / T_K) - 1)

# ── Pure-material optical constants ──────────────────────────────────────────
print("\nComputing Lorentz oscillator spectra …")
eps_baso4 = lorentz_eps(WN, BASO4_MODES_ALL, EPS_INF["BaSO4"], DELTA_EPS_TOTAL["BaSO4"])
eps_sio2  = lorentz_eps(WN, SIO2_MODES_ALL,  EPS_INF["SiO2"],  DELTA_EPS_TOTAL["SiO2"])
eps_tio2  = np.full_like(WN, EPS_INF["TiO2"],  dtype=complex)   # transparent in window
eps_zro2  = np.full_like(WN, EPS_INF["ZrO2"],  dtype=complex)   # transparent in window
eps_lime  = np.full_like(WN, EPS_INF["Lime"],  dtype=complex)   # transparent in window

n_baso4, k_baso4 = eps_to_nk(eps_baso4)
n_sio2,  k_sio2  = eps_to_nk(eps_sio2)

# ── Bruggeman EMT for full coating in mid-IR ──────────────────────────────────
# Volume fractions (optimal formulation, from Stage 2 composition optimization)
VOL_FRACS = {"TiO2": 0.221, "ZrO2": 0.055, "BaSO4": 0.105, "SiO2": 0.059, "Lime": 0.560}
EPS_COMPONENTS = {
    "TiO2": eps_tio2, "ZrO2": eps_zro2,
    "BaSO4": eps_baso4, "SiO2": eps_sio2, "Lime": eps_lime,
}

def bruggeman_complex(eps_eff_guess, fracs, eps_comps):
    """Bruggeman self-consistent equation (complex ε_eff)."""
    return sum(f * (e - eps_eff_guess) / (e + 2*eps_eff_guess)
               for f, e in zip(fracs, eps_comps))

print("Computing Bruggeman EMT for coating mixture …")
fracs = list(VOL_FRACS.values())
eps_coating = np.zeros_like(WN, dtype=complex)
# Weighted mean as initial guess for each wavenumber
eps_mean = sum(f * e for f, e in zip(fracs, EPS_COMPONENTS.values()))

for i, (wn_i, guess) in enumerate(zip(WN, eps_mean)):
    comps_i = [EPS_COMPONENTS[mat][i] for mat in VOL_FRACS]
    def eq(x):
        xc = x[0] + 1j*x[1]
        val = bruggeman_complex(xc, fracs, comps_i)
        return [val.real, val.imag]
    sol = fsolve(eq, [guess.real, guess.imag], full_output=False)
    eps_coating[i] = sol[0] + 1j*sol[1]

n_coat, k_coat = eps_to_nk(eps_coating)

# ── Reflectance and emissivity ────────────────────────────────────────────────
def emissivity_stats(n, k, label):
    R = fresnel_R(n, k)
    eps_lam = 1 - R
    # Atmospheric window integrated emissivity (Planck weighted at 300K)
    plank_win = PLANCK_300K[WINDOW_MASK]
    eps_win = np.trapezoid(eps_lam[WINDOW_MASK] * plank_win, WN[WINDOW_MASK]) / \
              np.trapezoid(plank_win, WN[WINDOW_MASK])
    # Full 8-13µm mean (unweighted)
    eps_win_mean = eps_lam[WINDOW_MASK].mean()
    print(f"  {label}:")
    print(f"    Window emissivity (Planck-weighted, 8-13 µm, 300K): {eps_win:.4f}")
    print(f"    Window emissivity (unweighted mean):                 {eps_win_mean:.4f}")
    print(f"    Peak k:  {k.max():.3f} at {1e4/WN[k.argmax()]:.2f} µm")
    print(f"    Peak n:  {n[WINDOW_MASK].mean():.3f} (mean in window)")
    return R, eps_lam, eps_win

print("\n── EMISSIVITY RESULTS ──────────────────────────────────────────────────")
R_baso4, eps_baso4_lam, ew_baso4 = emissivity_stats(n_baso4, k_baso4, "BaSO₄ (pure)")
R_sio2,  eps_sio2_lam,  ew_sio2  = emissivity_stats(n_sio2,  k_sio2,  "SiO₂  (pure)")
R_coat,  eps_coat_lam,  ew_coat  = emissivity_stats(n_coat,  k_coat,  "Coating mixture (optimal)")

print(f"\n  Purdue BaSO₄ benchmark: ε = 0.95")
print(f"  Our BaSO₄ (pure):       ε = {ew_baso4:.4f}")
print(f"  Our SiO₂ (pure):        ε = {ew_sio2:.4f}")
print(f"  Coating mixture:        ε = {ew_coat:.4f}")

# ── Plots ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(10, 11))

# 1. n(λ) and k(λ)
ax = axes[0]
ax.plot(WL_UM, n_baso4, "b-",  label="n BaSO₄", linewidth=1.5)
ax.plot(WL_UM, k_baso4, "b--", label="k BaSO₄", linewidth=1.5)
ax.plot(WL_UM, n_sio2,  "r-",  label="n SiO₂",  linewidth=1.5)
ax.plot(WL_UM, k_sio2,  "r--", label="k SiO₂",  linewidth=1.5)
ax.plot(WL_UM, n_coat,  "g-",  label="n coating", linewidth=1.2, alpha=0.8)
ax.plot(WL_UM, k_coat,  "g--", label="k coating", linewidth=1.2, alpha=0.8)
ax.axvspan(8, 13, alpha=0.08, color="gold", label="8–13 µm window")
ax.set_xlim(5, 20); ax.set_ylim(0, None)
ax.set_xlabel("Wavelength (µm)"); ax.set_ylabel("n, k")
ax.set_title("DFT-derived complex refractive index (Lorentz oscillator model, γ=10 cm⁻¹)")
ax.legend(ncol=3, fontsize=8)

# 2. Emissivity ε(λ) = 1 − R(λ)
ax = axes[1]
planck_norm = PLANCK_300K / PLANCK_300K[WINDOW_MASK].max()
ax.plot(WL_UM, eps_baso4_lam, "b-", label=f"BaSO₄  ε_window={ew_baso4:.3f}", lw=1.8)
ax.plot(WL_UM, eps_sio2_lam,  "r-", label=f"SiO₂   ε_window={ew_sio2:.3f}",  lw=1.8)
ax.plot(WL_UM, eps_coat_lam,  "g-", label=f"Coating ε_window={ew_coat:.3f}", lw=1.8)
ax.axhline(0.95, color="grey", linestyle="--", lw=1.2, label="Purdue benchmark ε=0.95")
ax2 = ax.twinx()
ax2.fill_between(WL_UM, planck_norm, alpha=0.08, color="orange")
ax2.set_ylabel("Planck B(300K) normalised", color="orange", fontsize=9)
ax2.set_ylim(0, 3); ax2.tick_params(axis="y", labelcolor="orange", labelsize=8)
ax.axvspan(8, 13, alpha=0.08, color="gold")
ax.set_xlim(5, 20); ax.set_ylim(0, 1.05)
ax.set_xlabel("Wavelength (µm)"); ax.set_ylabel("Emissivity ε(λ) = 1 − R(λ)")
ax.set_title("Mid-IR emissivity from Lorentz dielectric function + Fresnel equations")
ax.legend(fontsize=9)

# 3. Atmospheric window zoom
ax = axes[2]
mask_zoom = (WL_UM >= 7.5) & (WL_UM <= 14)
ax.plot(WL_UM[mask_zoom], eps_baso4_lam[mask_zoom], "b-", lw=2, label="BaSO₄")
ax.plot(WL_UM[mask_zoom], eps_sio2_lam[mask_zoom],  "r-", lw=2, label="SiO₂")
ax.plot(WL_UM[mask_zoom], eps_coat_lam[mask_zoom],  "g-", lw=2, label="Coating mixture")
ax.axhline(0.95, color="grey", linestyle="--", lw=1.2, label="Purdue ε=0.95")
ax.axvspan(8, 13, alpha=0.12, color="gold", label="8–13 µm window")
# Mark phonon mode wavelengths
for wn_mode, label_m, color in [
    (1084, "SO₄ 1084", "blue"), (1122, "SO₄ 1122", "blue"), (1191, "SO₄ 1191", "blue"),
    (1081, "Si-O 1081", "red"), (1091, "Si-O 1091", "red"),
]:
    ax.axvline(1e4/wn_mode, color=color, linestyle=":", alpha=0.5, lw=1)
ax.set_xlim(7.5, 14); ax.set_ylim(0, 1.05)
ax.set_xlabel("Wavelength (µm)"); ax.set_ylabel("Emissivity ε(λ)")
ax.set_title("Atmospheric window zoom: 7.5–14 µm")
ax.legend(fontsize=9, ncol=2)

fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "midir_emissivity.png"), dpi=150)
plt.close(fig)

# ── Save CSV ──────────────────────────────────────────────────────────────────
import pandas as pd
df = pd.DataFrame({
    "wavenumber_cm-1": WN, "wavelength_um": WL_UM,
    "n_BaSO4": n_baso4, "k_BaSO4": k_baso4, "emissivity_BaSO4": eps_baso4_lam,
    "n_SiO2":  n_sio2,  "k_SiO2":  k_sio2,  "emissivity_SiO2":  eps_sio2_lam,
    "n_coating": n_coat, "k_coating": k_coat, "emissivity_coating": eps_coat_lam,
    "planck_300K_norm": PLANCK_300K / PLANCK_300K.max(),
})
df.to_csv(os.path.join(PROJECT_DIR, "midir_emissivity_spectra.csv"), index=False)

print(f"\nSaved: midir_emissivity_spectra.csv")
print(f"Plot:  figures/midir_emissivity.png")
print(f"\nPurdue benchmark comparison:")
print(f"  BaSO₄ pure:  {ew_baso4:.3f} / 0.950  →  gap = {0.950 - ew_baso4:+.3f}")
print(f"  Coating mix: {ew_coat:.3f} / 0.950  →  gap = {0.950 - ew_coat:+.3f}")
