import os
import sys

import pandas as pd
from pymatgen.core import Composition

sys.path.insert(0, os.path.dirname(__file__))
from common import ALLOWED_ELEMENTS

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_ELEMENTS = {"Ba", "Ti", "Si", "Ca", "Al", "Mg", "Zr", "Y"}


def is_missing(v):
    return v is None or v == "na" or v == ""


rows = []
try:
    from jarvis.db.figshare import data as jarvis_data

    print("Loading JARVIS dft_3d dataset (downloads automatically on first run, ~500MB)...")
    dft_3d = jarvis_data("dft_3d")
    print(f"Loaded {len(dft_3d)} JARVIS dft_3d entries.")

    for entry in dft_3d:
        try:
            bandgap_mbj = entry.get("bandgap_mbj", entry.get("mbj_bandgap"))
            if is_missing(bandgap_mbj) or float(bandgap_mbj) <= 2.5:
                continue

            formula = entry.get("formula")
            if is_missing(formula):
                continue
            try:
                els = {str(e) for e in Composition(formula).elements}
            except Exception:
                continue
            if not (els & TARGET_ELEMENTS):
                continue
            if "O" not in els or not els.issubset(ALLOWED_ELEMENTS):
                continue

            epsx, epsy, epsz = entry.get("epsx"), entry.get("epsy"), entry.get("epsz")
            if is_missing(epsx):
                continue

            eps_vals = [float(v) for v in (epsx, epsy, epsz) if not is_missing(v)]
            n_refractive = (sum(eps_vals) / len(eps_vals)) ** 0.5 if eps_vals and min(eps_vals) >= 0 else None

            spillage = entry.get("spillage")
            spillage = None if is_missing(spillage) else float(spillage)

            rows.append({
                "jid": entry.get("jid"),
                "formula": formula,
                "bandgap_mbj": float(bandgap_mbj),
                "epsx": None if is_missing(epsx) else float(epsx),
                "epsy": None if is_missing(epsy) else float(epsy),
                "epsz": None if is_missing(epsz) else float(epsz),
                "n": n_refractive,
                "spillage": spillage,
                "max_ir_mode": None if is_missing(entry.get("max_ir_mode")) else float(entry.get("max_ir_mode")),
                "dfpt_piezo_max_dielectric": (
                    None if is_missing(entry.get("dfpt_piezo_max_dielectric"))
                    else float(entry.get("dfpt_piezo_max_dielectric"))
                ),
            })
        except Exception:
            continue
except Exception as e:
    print(f"WARNING: JARVIS dataset download or processing failed: {e}")
    print("Continuing with whatever data was retrieved.")

df = pd.DataFrame(rows, columns=[
    "jid", "formula", "bandgap_mbj", "epsx", "epsy", "epsz", "n", "spillage",
    "max_ir_mode", "dfpt_piezo_max_dielectric",
])
out_path = os.path.join(PROJECT_DIR, "jarvis_candidates.csv")
df.to_csv(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")
print(f"Candidates found: {len(df)}")
