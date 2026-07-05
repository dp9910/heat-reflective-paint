import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import load_env

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_env(os.path.join(PROJECT_DIR, ".env"))
API_KEY = os.environ.get("material_project_api") or os.environ.get("MP_API_KEY")

candidates_path = os.path.join(PROJECT_DIR, "mp_candidates.csv")
cand = pd.read_csv(candidates_path)

rows = []
if not API_KEY:
    print("WARNING: no Materials Project API key found. Skipping BaSO4/CaCO3 query.")
else:
    from mp_api.client import MPRester
    try:
        with MPRester(api_key=API_KEY) as mpr:
            print("Querying MP directly for BaSO4 and CaCO3 (bypassing the general oxide/element filters)...")
            docs = mpr.materials.summary.search(
                formula=["BaSO4", "CaCO3"],
                fields=[
                    "material_id", "formula_pretty", "band_gap",
                    "formation_energy_per_atom", "energy_above_hull",
                    "has_props", "density", "structure",
                ],
            )
            for d in docs:
                try:
                    has_props = d.has_props or {}
                    has_props_str = ",".join(
                        str(k.value if hasattr(k, "value") else k)
                        for k, v in has_props.items() if v
                    )
                except Exception:
                    has_props_str = ""
                try:
                    structure_cif = d.structure.to(fmt="cif") if d.structure else None
                except Exception:
                    structure_cif = None
                rows.append({
                    "material_id": str(d.material_id),
                    "formula": d.formula_pretty,
                    "band_gap": d.band_gap,
                    "formation_energy_per_atom": d.formation_energy_per_atom,
                    "energy_above_hull": d.energy_above_hull,
                    "has_props": has_props_str,
                    "density": d.density,
                    "structure_cif": structure_cif,
                })
    except Exception as e:
        print(f"WARNING: targeted MP query for BaSO4/CaCO3 failed: {e}")

new_df = pd.DataFrame(rows, columns=cand.columns)
existing_ids = set(cand["material_id"])
new_df = new_df[~new_df["material_id"].isin(existing_ids)]

combined = pd.concat([cand, new_df], ignore_index=True)
combined.to_csv(candidates_path, index=False)

print(f"Added {len(new_df)} new entries (BaSO4: {(new_df['formula'] == 'BaSO4').sum()}, "
      f"CaCO3: {(new_df['formula'] == 'CaCO3').sum()}).")
print(f"mp_candidates.csv now has {len(combined)} total rows.")
