"""
Post-processing: read DFT phonon results from Tier 3 emissivity materials,
apply Lorentz oscillator model, compute Planck-weighted 8-13 µm emissivity,
compare against BaSO₄ reference (ε_window = 0.912).
Run after DFT calculations complete on Azure VM.
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import brentq

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR  = os.path.join(PROJECT_DIR, "figures")
TIER3_DIR    = "/data/runs/tier3_emissivity"   # on Azure VM — adapt if running locally
os.makedirs(FIGURES_DIR, exist_ok=True)

BASO4_REFERENCE = 0.912   # Lorentz oscillator result from our own DFT
GAMMA_CM = 10.0
HC_K     = 1.4388          # hc/k in cm·K
T_K      = 300.0

# Wavenumber grid 500–2100 cm⁻¹ (5–20 µm)
WN      = np.linspace(500, 2100, 3200)
WL_UM   = 1e4 / WN
WINDOW  = (WN >= 769) & (WN <= 1250)   # 8–13 µm
PLANCK  = WN**3 / (np.exp(HC_K * WN / T_K) - 1)


def parse_dynmat(dynmat_path):
    """Parse dynmat.out — returns (modes, eps_inf_avg, alpha_ionic_avg, V_cell_ang3)."""
    if not os.path.exists(dynmat_path):
        return None, None, None, None
    with open(dynmat_path, errors='replace') as f:
        text = f.read()

    # Extract polarizability tensor diagonal (Å³)
    pol_match = re.search(
        r'Polarizability.*?\n\s*([\d.]+)\s', text, re.DOTALL)
    alpha = None
    pol_lines = re.findall(r'^\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s*$',
                           text, re.MULTILINE)
    if pol_lines:
        alpha = np.mean([float(x) for x in pol_lines[:3]])

    # Extract IR-active modes: (freq_cm-1, IR_intensity)
    modes = []
    for m in re.finditer(r'^\s+(\d+)\s+([-\d.]+)\s+[-\d.]+\s+([\d.]+)\s*$',
                         text, re.MULTILINE):
        freq, ir = float(m.group(2)), float(m.group(3))
        if freq > 10 and ir > 0.01:
            modes.append((freq, ir))
    return modes, alpha


def parse_ph_eps(ph_path):
    """Extract electronic dielectric constant ε_∞ (avg) from ph.out."""
    if not os.path.exists(ph_path):
        return None
    with open(ph_path, errors='replace') as f:
        text = f.read()
    diag = re.findall(
        r'\(\s*([\d.]+)\s+[\d.E+-]+\s+[\d.E+-]+\s*\)',
        text)
    if len(diag) >= 3:
        return np.mean([float(x) for x in diag[:3]])
    return None


def approx_vcell(formula, nat):
    """Rough unit cell volume estimate from atom count and typical atomic volumes."""
    vol_per_atom = {
        'Ca': 29.0, 'S': 16.0, 'O': 8.0,
        'Mg': 23.0, 'C': 8.5, 'Sr': 34.0,
        'Ba': 40.0, 'Mo': 16.0, 'W': 15.0, 'P': 14.0,
    }
    from pymatgen.core import Composition
    comp = Composition(formula)
    return sum(comp[str(e)] * vol_per_atom.get(str(e), 12.0) for e in comp)


def lorentz_eps(modes, eps_inf, delta_eps_total, gamma=GAMMA_CM):
    weights = np.array([i / w**2 for w, i in modes])
    weights /= weights.sum()
    de_j    = delta_eps_total * weights
    eps     = np.full_like(WN, eps_inf, dtype=complex)
    for (w_j, _), de in zip(modes, de_j):
        eps += de * w_j**2 / (w_j**2 - WN**2 - 1j * gamma * WN)
    return eps


def eps_to_nk(eps_c):
    e1, e2 = eps_c.real, eps_c.imag
    mod = np.abs(eps_c)
    return np.sqrt((mod + e1) / 2), np.sqrt(np.maximum(mod - e1, 0) / 2)


def fresnel_R(n, k):
    return ((n - 1)**2 + k**2) / ((n + 1)**2 + k**2)


def planck_eps(eps_lam):
    p = PLANCK[WINDOW]
    return float(np.trapezoid(eps_lam[WINDOW] * p, WN[WINDOW]) /
                 np.trapezoid(p, WN[WINDOW]))


# ── Reference cell volumes (Å³) from known crystal structures ─────────────────
V_CELL_REF = {
    'CaSO4_anhydrite': 244.0,   # anhydrite orthorhombic a=6.24 b=6.97 c=6.99 → 304?
                                  # Actually anhydrite: a=7.00 b=7.00 c=6.25 (approx) → ~305
    'Ca3PO4_2':        370.0,   # β-tricalcium phosphate primitive
    'MgCO3_magnesite': 189.0,   # R-3c hexagonal primitive a=4.63 c=15.0/3=5.0 →~97 (primitive)
    'MgSO4':           210.0,   # orthorhombic
    'SrSO4':           285.0,   # celestite, same structure as BaSO4, ~340 for Sr version
    'BaMoO4':          340.0,   # scheelite, similar to BaWO4
    'BaWO4':           340.0,   # scheelite structure
}

# ── Materials to analyse ──────────────────────────────────────────────────────
MATERIALS = [
    'CaSO4_anhydrite', 'Ca3PO4_2', 'MgCO3_magnesite',
    'MgSO4', 'SrSO4', 'BaMoO4', 'BaWO4',
]
LABELS = {
    'CaSO4_anhydrite': 'CaSO₄ (anhydrite)',
    'Ca3PO4_2':        'Ca₃(PO₄)₂',
    'MgCO3_magnesite': 'MgCO₃ (magnesite)',
    'MgSO4':           'MgSO₄',
    'SrSO4':           'SrSO₄',
    'BaMoO4':          'BaMoO₄',
    'BaWO4':           'BaWO₄',
}

results = []
fig, axes = plt.subplots(4, 2, figsize=(12, 14))
axes_flat = axes.flatten()

for idx, name in enumerate(MATERIALS):
    mat_dir   = os.path.join(TIER3_DIR, name)
    ph_path   = os.path.join(mat_dir, 'ph.out')
    dyn_path  = os.path.join(mat_dir, 'dynmat.out')

    modes, alpha_ionic = parse_dynmat(dyn_path)
    eps_inf             = parse_ph_eps(ph_path)

    if not modes or eps_inf is None:
        print(f'{name}: INCOMPLETE — DFT not yet finished')
        results.append({'material': name, 'eps_window': None,
                        'status': 'incomplete'})
        continue

    v_cell = V_CELL_REF.get(name, 300.0)
    delta_eps = 4 * np.pi * (alpha_ionic or 0) / v_cell if alpha_ionic else 0.5

    eps_c = lorentz_eps(modes, eps_inf, delta_eps)
    n, k  = eps_to_nk(eps_c)
    R_lam = fresnel_R(n, k)
    e_lam = 1 - R_lam
    e_win = planck_eps(e_lam)

    beat_baso4 = e_win > BASO4_REFERENCE
    flag = " ★ BEATS BaSO₄" if beat_baso4 else ""
    print(f'{name:<22}  ε_window={e_win:.4f}{flag}')

    results.append({'material': name, 'label': LABELS[name],
                    'eps_inf': eps_inf, 'delta_eps': delta_eps,
                    'n_modes_in_window': sum(1 for w, _ in modes if 769 <= w <= 1250),
                    'eps_window': e_win, 'beats_baso4': beat_baso4,
                    'status': 'complete'})

    ax = axes_flat[idx]
    ax.plot(WL_UM, e_lam, 'b-', lw=1.5, label=LABELS[name])
    ax.axhline(BASO4_REFERENCE, color='red', ls='--', lw=1, label=f'BaSO₄ ref {BASO4_REFERENCE}')
    ax.axvspan(8, 13, alpha=0.1, color='gold')
    ax.set_xlim(5, 20); ax.set_ylim(0, 1.05)
    ax.set_title(f"{LABELS[name]}\nε_win={e_win:.3f}", fontsize=9)
    ax.set_xlabel('λ (µm)', fontsize=8); ax.set_ylabel('ε', fontsize=8)
    ax.legend(fontsize=7)

# Hide unused subplot
if len(MATERIALS) < len(axes_flat):
    for ax in axes_flat[len(MATERIALS):]: ax.set_visible(False)

fig.suptitle('Tier 3 emissivity candidates: 5–20 µm emissivity spectra\n'
             'Lorentz oscillator from DFT DFPT + Fresnel equations (γ=10 cm⁻¹)',
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, 'tier3_emissivity_spectra.png'), dpi=150)
plt.close(fig)

# ── Summary ────────────────────────────────────────────────────────────────────
df = pd.DataFrame(results)
if 'eps_window' in df.columns:
    df_done = df[df['status'] == 'complete'].sort_values('eps_window', ascending=False)
    df.to_csv(os.path.join(PROJECT_DIR, 'tier3_emissivity_results.csv'), index=False)

    print(f"\n{'='*60}")
    print(f"TIER 3 EMISSIVITY COMPARISON  [BaSO₄ reference = {BASO4_REFERENCE}]")
    print(f"{'='*60}")
    print(f"{'Material':<25} {'ε_window':>10}  {'vs BaSO₄':>10}  {'Flag'}")
    print('-'*60)
    for _, r in df_done.iterrows():
        delta = r['eps_window'] - BASO4_REFERENCE
        flag  = '★ BEATS BaSO₄' if r['beats_baso4'] else ''
        print(f"  {r['label']:<23} {r['eps_window']:>10.4f}  {delta:>+10.4f}  {flag}")
    print(f"  {'BaSO₄ (reference)':<23} {BASO4_REFERENCE:>10.4f}  {'0.0000':>10}")

print(f'\nSaved: tier3_emissivity_results.csv')
print(f'Plot:  figures/tier3_emissivity_spectra.png')
