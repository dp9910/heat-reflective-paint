import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import VISIBLE_NIR_BOUNDARY_EV, load_env

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_env(os.path.join(PROJECT_DIR, ".env"))
API_KEY = os.environ.get("material_project_api") or os.environ.get("MP_API_KEY")

candidates_path = os.path.join(PROJECT_DIR, "mp_candidates.csv")
out_path = os.path.join(PROJECT_DIR, "mp_with_dielectric.csv")

cand = pd.read_csv(candidates_path)
cand["has_props"] = cand["has_props"].fillna("")
dielectric_ids = cand.loc[cand["has_props"].str.contains("dielectric"), "material_id"].tolist()
print(f"{len(dielectric_ids)} of {len(cand)} MP candidates have 'dielectric' in has_props.")

if not API_KEY or not dielectric_ids:
    if not API_KEY:
        print("WARNING: no Materials Project API key found. Skipping dielectric fetch.")
    pd.DataFrame(columns=list(cand.columns) + [
        "n_refractive_index", "k_extinction_coefficient", "e_total", "e_ionic",
        "e_electronic", "has_full_dielectric_spectrum", "energies_ev_json",
        "eps1_real_json", "eps2_imag_json",
    ]).to_csv(out_path, index=False)
    print("Materials with pre-computed dielectric data: 0")
    sys.exit(0)

from mp_api.client import MPRester

n_k_by_id = {}
spectrum_by_id = {}

try:
    with MPRester(api_key=API_KEY) as mpr:
        print("Fetching static dielectric data...")
        diel_docs = mpr.materials.dielectric.search(
            material_ids=dielectric_ids,
            fields=["material_id", "n", "e_total", "e_ionic", "e_electronic"],
        )
        for d in diel_docs:
            n_k_by_id[str(d.material_id)] = {
                "n_static": d.n,
                "e_total": d.e_total,
                "e_ionic": d.e_ionic,
                "e_electronic": d.e_electronic,
            }

        absorption_ids = cand.loc[cand["has_props"].str.contains("absorption"), "material_id"].tolist()
        absorption_ids = [i for i in absorption_ids if i in n_k_by_id]
        if absorption_ids:
            print(f"Fetching full frequency-dependent dielectric function for {len(absorption_ids)} materials...")
            try:
                abs_docs = mpr.materials.absorption.search(
                    material_ids=absorption_ids,
                    fields=["material_id", "energies", "average_real_dielectric", "average_imaginary_dielectric"],
                )
                for ad in abs_docs:
                    if not ad.energies or not ad.average_real_dielectric or not ad.average_imaginary_dielectric:
                        continue
                    spectrum_by_id[str(ad.material_id)] = {
                        "energies": ad.energies,
                        "eps1": ad.average_real_dielectric,
                        "eps2": ad.average_imaginary_dielectric,
                    }
            except Exception as e:
                print(f"WARNING: absorption-spectrum fetch failed, continuing without it: {e}")
except Exception as e:
    print(f"WARNING: Materials Project dielectric query failed or timed out: {e}")
    print("Continuing with whatever data was retrieved.")

rows = []
for _, row in cand.iterrows():
    mid = row["material_id"]
    if mid not in n_k_by_id:
        continue
    info = n_k_by_id[mid]
    spectrum = spectrum_by_id.get(mid)

    n_val, k_val = info["n_static"], 0.0
    energies_json = eps1_json = eps2_json = None
    has_full_spectrum = False

    if spectrum:
        try:
            energies = np.array(spectrum["energies"], dtype=float)
            eps1 = np.array(spectrum["eps1"], dtype=float)
            eps2 = np.array(spectrum["eps2"], dtype=float)
            e1 = float(np.interp(VISIBLE_NIR_BOUNDARY_EV, energies, eps1))
            e2 = float(np.interp(VISIBLE_NIR_BOUNDARY_EV, energies, eps2))
            mag = (e1 ** 2 + e2 ** 2) ** 0.5
            n_val = (max(mag + e1, 0) / 2) ** 0.5
            k_val = (max(mag - e1, 0) / 2) ** 0.5
            energies_json = json.dumps([round(x, 4) for x in energies.tolist()])
            eps1_json = json.dumps([round(x, 4) for x in eps1.tolist()])
            eps2_json = json.dumps([round(x, 4) for x in eps2.tolist()])
            has_full_spectrum = True
        except Exception:
            n_val, k_val = info["n_static"], 0.0

    rows.append({
        **row.to_dict(),
        "n_refractive_index": n_val,
        "k_extinction_coefficient": k_val,
        "e_total": info["e_total"],
        "e_ionic": info["e_ionic"],
        "e_electronic": info["e_electronic"],
        "has_full_dielectric_spectrum": has_full_spectrum,
        "energies_ev_json": energies_json,
        "eps1_real_json": eps1_json,
        "eps2_imag_json": eps2_json,
    })

df = pd.DataFrame(rows)
df.to_csv(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")
print(f"Materials with pre-computed dielectric data (zero new DFT needed): {len(df)}")
print(f"  of which {sum(1 for r in rows if r['has_full_dielectric_spectrum'])} have a full frequency-dependent spectrum")
