import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import normalize_formula

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

mp_df = pd.read_csv(os.path.join(PROJECT_DIR, "mp_with_dielectric.csv"))
jarvis_df = pd.read_csv(os.path.join(PROJECT_DIR, "jarvis_candidates.csv"))

mp_rows = pd.DataFrame({
    "source": "MP",
    "id": mp_df.get("material_id"),
    "formula": mp_df.get("formula"),
    "band_gap": mp_df.get("band_gap"),
    "n_refractive_index": mp_df.get("n_refractive_index"),
    "k_extinction_coefficient": mp_df.get("k_extinction_coefficient"),
    "estimated_reflectance": mp_df.get("estimated_reflectance"),
    "has_ir_data": mp_df.get("has_ir_data"),
    "formation_energy_per_atom": mp_df.get("formation_energy_per_atom"),
    "density": mp_df.get("density"),
    "spillage": None,
}) if len(mp_df) else pd.DataFrame()

jarvis_rows = pd.DataFrame({
    "source": "JARVIS",
    "id": jarvis_df.get("jid"),
    "formula": jarvis_df.get("formula"),
    "band_gap": jarvis_df.get("bandgap_mbj"),
    "n_refractive_index": jarvis_df.get("n"),
    "k_extinction_coefficient": jarvis_df.get("k_extinction_coefficient"),
    "estimated_reflectance": jarvis_df.get("estimated_reflectance"),
    "has_ir_data": jarvis_df.get("has_ir_data"),
    "formation_energy_per_atom": None,
    "density": None,
    "spillage": jarvis_df.get("spillage"),
}) if len(jarvis_df) else pd.DataFrame()

master = pd.concat([mp_rows, jarvis_rows], ignore_index=True)
master["formula_normalized"] = master["formula"].apply(normalize_formula)

master = master.sort_values("estimated_reflectance", ascending=False, na_position="last")
master = master.drop_duplicates(subset="formula_normalized", keep="first")
master = master.drop(columns=["formula_normalized"])


def classify(row):
    bg, r = row["band_gap"], row["estimated_reflectance"]
    if pd.isna(bg) or pd.isna(r):
        return "LOW"
    if bg > 4 and r > 0.85:
        return "HIGH"
    if bg > 2.5 and r > 0.70:
        return "MEDIUM"
    return "LOW"


master["priority"] = master.apply(classify, axis=1)
master = master.sort_values("estimated_reflectance", ascending=False, na_position="last")

out_path = os.path.join(PROJECT_DIR, "master_candidates.csv")
master.to_csv(out_path, index=False)
print(f"Saved {len(master)} unique candidates to {out_path}")
print(f"  ({len(mp_rows)} from MP + {len(jarvis_rows)} from JARVIS -> {len(master)} after dedup by formula)")

print("\nTop 20 candidates by estimated_reflectance:")
top20 = master.head(20)[["formula", "band_gap", "estimated_reflectance", "priority"]]
print(top20.to_string(index=False))
