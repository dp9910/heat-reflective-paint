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
D_SMALL = {"TiO2": 400, "ZrO2": 500, "BaSO4": 1000}
D_LARGE_RANGE = list(range(1000, 3001, 200))
WEIGHT_SMALL, WEIGHT_LARGE = 0.6, 0.4
RATIO_TARGET, QSOLAR_TARGET = 0.6, 2.5

spectrum = pd.read_csv(os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv"))
WAVELENGTHS_NM = spectrum["wavelength_nm"].values.astype(float)
IRRADIANCE = spectrum["irradiance_w_m2_nm"].values.astype(float)

NIR1_MASK = (WAVELENGTHS_NM > 700) & (WAVELENGTHS_NM <= 1400)
NIR2_MASK = WAVELENGTHS_NM > 1400

master = pd.read_csv(os.path.join(PROJECT_DIR, "master_candidates_clean.csv"))


def solar_weighted_mean(qsca, mask):
    wl, irr = WAVELENGTHS_NM[mask], IRRADIANCE[mask]
    denom = np.trapezoid(irr, wl)
    return float(np.trapezoid(qsca[mask] * irr, wl) / denom) if denom > 0 else None


def qsca_curve(m, d):
    _, qsca, _, _ = miepython.efficiencies(m, float(d), WAVELENGTHS_NM, n_env=N_MATRIX)
    return qsca


results = []

for formula, d_small in D_SMALL.items():
    row = master[master["formula"] == formula]
    if row.empty:
        print(f"WARNING: {formula} not found in master_candidates_clean.csv -- skipping.")
        continue
    row = row.iloc[0]
    n, k = row.get("n_refractive_index"), row.get("k_extinction_coefficient")
    if pd.isna(n):
        print(f"WARNING: {formula} has no refractive index on file -- skipping.")
        continue
    k = 0.0 if pd.isna(k) else float(k)
    m = complex(float(n), -k)

    qsca_small = qsca_curve(m, d_small)
    single_size_solar = solar_weighted_mean(qsca_small, np.ones_like(WAVELENGTHS_NM, dtype=bool))

    sweep_rows = []
    for d_large in D_LARGE_RANGE:
        qsca_large = qsca_curve(m, d_large)
        q_total_curve = WEIGHT_SMALL * qsca_small + WEIGHT_LARGE * qsca_large

        q_solar = solar_weighted_mean(q_total_curve, np.ones_like(WAVELENGTHS_NM, dtype=bool))
        q_nir1 = solar_weighted_mean(q_total_curve, NIR1_MASK)
        q_nir2 = solar_weighted_mean(q_total_curve, NIR2_MASK)
        ratio = q_nir2 / q_nir1 if q_nir1 else None

        sweep_rows.append({
            "d_large": d_large, "Q_solar": q_solar, "Q_NIR1": q_nir1,
            "Q_NIR2": q_nir2, "ratio": ratio, "curve": q_total_curve,
        })

    sweep_df = pd.DataFrame(sweep_rows)
    feasible = sweep_df[(sweep_df["ratio"] > RATIO_TARGET) & (sweep_df["Q_solar"] > QSOLAR_TARGET)]

    if len(feasible):
        best = feasible.loc[feasible["Q_solar"].idxmax()]
        status = "TARGET MET"
    else:
        best = sweep_df.loc[sweep_df["ratio"].idxmax()]
        status = "TARGET NOT MET in swept range (best available shown)"

    print(f"{formula}: {status} -- d_large={best['d_large']}nm, "
          f"Q_solar={best['Q_solar']:.3f}, ratio={best['ratio']:.3f}")

    results.append({
        "formula": formula,
        "d_small": d_small,
        "d_large": int(best["d_large"]),
        "weight_small": WEIGHT_SMALL,
        "weight_large": WEIGHT_LARGE,
        "Q_solar_weighted": best["Q_solar"],
        "Q_NIR1": best["Q_NIR1"],
        "Q_NIR2": best["Q_NIR2"],
        "NIR2_NIR1_ratio": best["ratio"],
        "target_met": len(feasible) > 0,
    })

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(WAVELENGTHS_NM, qsca_small, label=f"single-size (d={d_small}nm)", linestyle="--")
    ax.plot(WAVELENGTHS_NM, best["curve"], label=f"bimodal (d_small={d_small}, d_large={int(best['d_large'])})")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Q_scat")
    ax.set_title(f"{formula}: single-size vs. optimized bimodal mixture")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, f"bimodal_{formula}.png"), dpi=150)
    plt.close(fig)

results_df = pd.DataFrame(results).drop(columns=["target_met"]) if results else pd.DataFrame()
out_path = os.path.join(PROJECT_DIR, "stage1_bimodal_results.csv")
results_df.to_csv(out_path, index=False)
print(f"\nSaved {out_path}")
print(pd.DataFrame(results).to_string(index=False, float_format=lambda x: f"{x:.3f}" if isinstance(x, float) else str(x)))
