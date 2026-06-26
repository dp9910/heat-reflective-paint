import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import fresnel_reflectance

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

mp_path = os.path.join(PROJECT_DIR, "mp_with_dielectric.csv")
jarvis_path = os.path.join(PROJECT_DIR, "jarvis_candidates.csv")

# --- Materials Project: Fresnel reflectance from n, k (k=0 fallback for static dielectric) ---
mp_df = pd.read_csv(mp_path)
if len(mp_df):
    mp_df["estimated_reflectance"] = mp_df.apply(
        lambda r: fresnel_reflectance(r.get("n_refractive_index"), r.get("k_extinction_coefficient")),
        axis=1,
    )
    mp_df["has_props"] = mp_df["has_props"].fillna("")
    mp_df["has_ir_data"] = mp_df["has_props"].str.contains("phonon")
    mp_df = mp_df.sort_values("estimated_reflectance", ascending=False, na_position="last")
else:
    mp_df["estimated_reflectance"] = []
    mp_df["has_ir_data"] = []
mp_df.to_csv(mp_path, index=False)
print(f"mp_with_dielectric.csv: added estimated_reflectance + has_ir_data, {len(mp_df)} rows.")

# --- JARVIS: same Fresnel calc; k assumed 0 (static dielectric, below absorption edge) ---
jarvis_df = pd.read_csv(jarvis_path)
if len(jarvis_df):
    jarvis_df["k_extinction_coefficient"] = 0.0
    jarvis_df["estimated_reflectance"] = jarvis_df.apply(
        lambda r: fresnel_reflectance(r.get("n"), r.get("k_extinction_coefficient")),
        axis=1,
    )
    jarvis_df["has_ir_data"] = jarvis_df["max_ir_mode"].notna() | jarvis_df["dfpt_piezo_max_dielectric"].notna()
    jarvis_df = jarvis_df.sort_values("estimated_reflectance", ascending=False, na_position="last")
else:
    jarvis_df["estimated_reflectance"] = []
    jarvis_df["has_ir_data"] = []
jarvis_df.to_csv(jarvis_path, index=False)
print(f"jarvis_candidates.csv: added estimated_reflectance + has_ir_data, {len(jarvis_df)} rows.")

mp_priority = int((mp_df["has_ir_data"] & (mp_df["estimated_reflectance"] > 0.85)).sum()) if len(mp_df) else 0
jarvis_priority = int((jarvis_df["has_ir_data"] & (jarvis_df["estimated_reflectance"] > 0.85)).sum()) if len(jarvis_df) else 0
print(f"MP materials with high reflectance (>0.85) AND ir data: {mp_priority}")
print(f"JARVIS materials with high reflectance (>0.85) AND ir data: {jarvis_priority}")
