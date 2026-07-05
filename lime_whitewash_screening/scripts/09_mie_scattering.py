import os

import miepython
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master_path = os.path.join(PROJECT_DIR, "master_candidates.csv")

D_PARTICLE_NM = 400.0
LAMBDA_NM = 800.0
N_MATRIX = 1.59  # Ca(OH)2


def qscat(n, k):
    if pd.isna(n) or pd.isna(k):
        return None
    try:
        # miepython convention: m = n - ik (absorption gives negative imaginary part)
        m = complex(float(n), -float(k))
        _, qsca, _, _ = miepython.efficiencies(m, D_PARTICLE_NM, LAMBDA_NM, n_env=N_MATRIX)
        return float(qsca)
    except Exception:
        return None


# Also persist onto the per-source CSVs so per-variant (pre-dedup) lookups stay consistent.
mp_path = os.path.join(PROJECT_DIR, "mp_with_dielectric.csv")
jarvis_path = os.path.join(PROJECT_DIR, "jarvis_candidates.csv")

mp_df = pd.read_csv(mp_path)
if len(mp_df):
    mp_df["mie_qscat_800nm"] = mp_df.apply(
        lambda r: qscat(r.get("n_refractive_index"), r.get("k_extinction_coefficient")), axis=1
    )
    mp_df.to_csv(mp_path, index=False)

jarvis_df = pd.read_csv(jarvis_path)
if len(jarvis_df):
    jarvis_df["mie_qscat_800nm"] = jarvis_df.apply(
        lambda r: qscat(r.get("n"), r.get("k_extinction_coefficient")), axis=1
    )
    jarvis_df.to_csv(jarvis_path, index=False)

master = pd.read_csv(master_path)
master["mie_qscat_800nm"] = master.apply(
    lambda r: qscat(r.get("n_refractive_index"), r.get("k_extinction_coefficient")), axis=1
)
master = master.sort_values("mie_qscat_800nm", ascending=False, na_position="last")
master.to_csv(master_path, index=False)

n_valid = master["mie_qscat_800nm"].notna().sum()
print(f"Computed mie_qscat_800nm for {n_valid} of {len(master)} candidates "
      f"(particle d={D_PARTICLE_NM}nm, lambda={LAMBDA_NM}nm, n_matrix={N_MATRIX}).")
print("\nTop 10 by mie_qscat_800nm:")
print(master.head(10)[["formula", "band_gap", "n_refractive_index", "k_extinction_coefficient", "mie_qscat_800nm"]].to_string(index=False))
