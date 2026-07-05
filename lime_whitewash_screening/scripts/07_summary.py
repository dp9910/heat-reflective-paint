import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import normalize_formula

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

mp_candidates = pd.read_csv(os.path.join(PROJECT_DIR, "mp_candidates.csv"))
mp_dielectric = pd.read_csv(os.path.join(PROJECT_DIR, "mp_with_dielectric.csv"))
jarvis = pd.read_csv(os.path.join(PROJECT_DIR, "jarvis_candidates.csv"))
master = pd.read_csv(os.path.join(PROJECT_DIR, "master_candidates.csv"))

print("=" * 70)
print("ENHANCED LIME WHITEWASH - MATERIALS SCREENING SUMMARY")
print("=" * 70)

print(f"\nTotal candidates from Materials Project (Step 2 filter + BaSO4/CaCO3 targeted query): {len(mp_candidates)}")
print(f"Total candidates from JARVIS dft_3d (Step 4 filter):      {len(jarvis)}")

dielectric_count = len(mp_dielectric) + len(jarvis)
print(f"\nMaterials with pre-computed dielectric/optical data (zero new DFT needed): {dielectric_count}")
print(f"  - MP (dielectric tensor on file):      {len(mp_dielectric)}")
print(f"  - JARVIS (epsx/epsy/epsz on file):     {len(jarvis)}")

ir_mp = int(mp_dielectric["has_ir_data"].sum()) if "has_ir_data" in mp_dielectric else 0
ir_jarvis = int(jarvis["has_ir_data"].sum()) if "has_ir_data" in jarvis else 0
print(f"\nMaterials with mid-IR phonon data (8-13 micron window): {ir_mp + ir_jarvis}")
print(f"  - MP (phonon in has_props):             {ir_mp}")
print(f"  - JARVIS (max_ir_mode / dfpt_piezo):    {ir_jarvis}")

high = master[master["priority"] == "HIGH"].sort_values("mie_qscat_800nm", ascending=False)
print(f"\nHIGH priority candidates (mie_qscat_800nm>2.0 AND band_gap>3.5eV): {len(high)}")
if len(high) == 0:
    print("  None found.")
else:
    for _, row in high.head(5).iterrows():
        print(f"  {row['formula']:<12} band_gap={row['band_gap']:.2f} eV  "
              f"mie_qscat_800nm={row['mie_qscat_800nm']:.3f}  source={row['source']}  "
              f"lime_compatible={row['lime_compatible']}")

print("\nKnown whitewash-relevant compounds found (BaSO4, TiO2, SiO2, CaCO3, Y2O3, ZrO2):")
targets = ["BaSO4", "TiO2", "SiO2", "CaCO3", "Y2O3", "ZrO2"]
master_rank = {f: i + 1 for i, f in enumerate(master.sort_values("mie_qscat_800nm", ascending=False)["formula"])}

mp_candidates_norm = mp_candidates.copy()
mp_candidates_norm["_norm"] = mp_candidates_norm["formula"].apply(normalize_formula)

combined_raw = pd.concat([
    mp_dielectric.assign(source="MP", id_col=mp_dielectric.get("material_id")),
    jarvis.assign(source="JARVIS", id_col=jarvis.get("jid")),
], ignore_index=True)
combined_raw["_norm"] = combined_raw["formula"].apply(normalize_formula)

for target in targets:
    target_norm = normalize_formula(target)
    variants = combined_raw[combined_raw["_norm"] == target_norm]
    if len(variants) == 0:
        was_queried = (mp_candidates_norm["_norm"] == target_norm).any()
        if was_queried:
            print(f"  {target}: found on MP but no dielectric data on file -> "
                  f"no n/k available, so no Mie estimate could be computed (would need new DFT).")
        else:
            print(f"  {target}: 0 variants found (excluded by element filter - "
                  f"contains S or C, outside the allowed O+metal set).")
        continue
    best = variants.sort_values("mie_qscat_800nm", ascending=False).iloc[0]
    best_rank = master_rank.get(best["formula"], "deduplicated out of master")
    print(f"  {target}: {len(variants)} variant(s) found across MP+JARVIS "
          f"(Q_scat range {variants['mie_qscat_800nm'].min():.3f}-"
          f"{variants['mie_qscat_800nm'].max():.3f}). Best: {best['source']} "
          f"{best.get('id_col')}, mie_qscat_800nm={best['mie_qscat_800nm']:.3f}, "
          f"master rank={best_rank}.")

lime_compat = master[master["lime_compatible"]]
print(f"\nLime-compatible candidates (formula contains Ca or Si): {len(lime_compat)} of {len(master)}")
print("  (May chemically bond into the Ca(OH)2 matrix rather than just dispersing in it.)")
lime_high_medium = lime_compat[lime_compat["priority"].isin(["HIGH", "MEDIUM"])].sort_values(
    "mie_qscat_800nm", ascending=False
)
print(f"  Of these, {len(lime_high_medium)} are HIGH/MEDIUM priority. Top 5:")
for _, row in lime_high_medium.head(5).iterrows():
    print(f"    {row['formula']:<12} band_gap={row['band_gap']:.2f} eV  "
          f"mie_qscat_800nm={row['mie_qscat_800nm']:.3f}  priority={row['priority']}")

print("\n" + "=" * 70)
print(f"Full ranked list: master_candidates.csv ({len(master)} unique candidates)")
print("Plots: candidate_screening.png, top_candidates.png")
print("=" * 70)
