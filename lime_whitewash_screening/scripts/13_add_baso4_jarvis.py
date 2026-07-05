import os

import pandas as pd
from pymatgen.core import Composition

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jarvis_path = os.path.join(PROJECT_DIR, "jarvis_candidates.csv")


def is_missing(v):
    return v is None or v == "na" or v == ""


jarvis_df = pd.read_csv(jarvis_path)
existing_jids = set(jarvis_df["jid"])

rows = []
try:
    from jarvis.db.figshare import data as jarvis_data

    print("Searching JARVIS dft_3d directly for BaSO4 (bypassing the oxide-only element filter)...")
    dft_3d = jarvis_data("dft_3d")
    for entry in dft_3d:
        formula = entry.get("formula")
        if is_missing(formula):
            continue
        try:
            if Composition(formula).reduced_formula != "BaSO4":
                continue
        except Exception:
            continue
        if entry.get("jid") in existing_jids:
            continue

        epsx, epsy, epsz = entry.get("epsx"), entry.get("epsy"), entry.get("epsz")
        if is_missing(epsx):
            continue

        eps_vals = [float(v) for v in (epsx, epsy, epsz) if not is_missing(v)]
        n_refractive = (sum(eps_vals) / len(eps_vals)) ** 0.5 if eps_vals and min(eps_vals) >= 0 else None

        bandgap_mbj = entry.get("mbj_bandgap")
        bandgap_mbj = None if is_missing(bandgap_mbj) else float(bandgap_mbj)
        spillage = entry.get("spillage")
        spillage = None if is_missing(spillage) else float(spillage)

        rows.append({
            "jid": entry.get("jid"),
            "formula": formula,
            "bandgap_mbj": bandgap_mbj,
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
except Exception as e:
    print(f"WARNING: JARVIS BaSO4 lookup failed: {e}")

new_df = pd.DataFrame(rows, columns=["jid", "formula", "bandgap_mbj", "epsx", "epsy", "epsz", "n", "spillage",
                                      "max_ir_mode", "dfpt_piezo_max_dielectric"])
combined = pd.concat([jarvis_df.drop(columns=["estimated_reflectance", "k_extinction_coefficient",
                                               "has_ir_data", "mie_qscat_800nm"], errors="ignore"), new_df],
                     ignore_index=True)
combined.to_csv(jarvis_path, index=False)
print(f"Added {len(new_df)} new BaSO4 entries with usable epsx/epsy/epsz. jarvis_candidates.csv now has {len(combined)} rows.")
print(combined[combined["formula"] == "BaSO4"][["jid", "formula", "bandgap_mbj", "epsx", "epsy", "epsz", "n"]].to_string(index=False))
