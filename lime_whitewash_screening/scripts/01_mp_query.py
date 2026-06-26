import os
import sys

import pandas as pd
from pymatgen.core import Composition

sys.path.insert(0, os.path.dirname(__file__))
from common import ALLOWED_ELEMENTS, TOXIC_ELEMENTS, load_env

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_env(os.path.join(PROJECT_DIR, ".env"))

API_KEY = os.environ.get("material_project_api") or os.environ.get("MP_API_KEY")
if not API_KEY:
    print("WARNING: no Materials Project API key found in .env. Skipping MP query.")
    pd.DataFrame(columns=[
        "material_id", "formula", "band_gap", "formation_energy_per_atom",
        "energy_above_hull", "has_props", "density", "structure_cif",
    ]).to_csv(os.path.join(PROJECT_DIR, "mp_candidates.csv"), index=False)
    print("Candidates found: 0")
    sys.exit(0)

from mp_api.client import MPRester

rows = []
try:
    with MPRester(api_key=API_KEY) as mpr:
        print("Querying Materials Project summary endpoint (lightweight pass)...")
        light_docs = mpr.materials.summary.search(
            elements=["O"],
            exclude_elements=list(TOXIC_ELEMENTS),
            band_gap=(2.5, 12),
            energy_above_hull=(0, 0.05),
            formation_energy=(-10, -1.0),
            fields=["material_id", "formula_pretty"],
        )

        filtered_ids = []
        for d in light_docs:
            try:
                els = {str(e) for e in Composition(d.formula_pretty).elements}
            except Exception:
                continue
            if els.issubset(ALLOWED_ELEMENTS):
                filtered_ids.append(d.material_id)

        print(f"{len(light_docs)} raw oxide hits -> {len(filtered_ids)} after element-subset filter.")

        print("Fetching full fields (incl. structure) for filtered candidates...")
        full_docs = mpr.materials.summary.search(
            material_ids=filtered_ids,
            fields=[
                "material_id", "formula_pretty", "band_gap",
                "formation_energy_per_atom", "energy_above_hull",
                "has_props", "density", "structure",
            ],
        )

        for d in full_docs:
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
    print(f"WARNING: Materials Project query failed or timed out: {e}")
    print("Continuing with whatever candidates were retrieved before the failure.")

df = pd.DataFrame(rows, columns=[
    "material_id", "formula", "band_gap", "formation_energy_per_atom",
    "energy_above_hull", "has_props", "density", "structure_cif",
])
out_path = os.path.join(PROJECT_DIR, "mp_candidates.csv")
df.to_csv(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")
print(f"Candidates found: {len(df)}")
