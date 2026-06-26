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

print(f"\nTotal candidates from Materials Project (Step 2 filter): {len(mp_candidates)}")
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

high = master[master["priority"] == "HIGH"].sort_values("estimated_reflectance", ascending=False)
print(f"\nHIGH priority candidates (band_gap>4eV AND estimated_reflectance>0.85): {len(high)}")
if len(high) == 0:
    print("  None found. CAVEAT: estimated_reflectance is single-interface, normal-incidence")
    print("  Fresnel reflectance at one photon energy (700 nm proxy) -- it models specular")
    print("  reflection off a flat bulk crystal, not the diffuse multi-particle scattering")
    print("  that gives real whitewash pigments (e.g. TiO2, CaCO3) their >0.85 reflectance.")
    print("  Treat estimated_reflectance as a RELATIVE ranking signal, not an absolute")
    print("  prediction of paint performance; thresholds may need recalibration.")
    print("\n  Top 5 candidates by estimated_reflectance (priority shown as classified):")
    for _, row in master.sort_values("estimated_reflectance", ascending=False).head(5).iterrows():
        print(f"    {row['formula']:<12} band_gap={row['band_gap']:.2f} eV  "
              f"estimated_reflectance={row['estimated_reflectance']:.3f}  priority={row['priority']}")
else:
    for _, row in high.head(5).iterrows():
        print(f"  {row['formula']:<12} band_gap={row['band_gap']:.2f} eV  "
              f"estimated_reflectance={row['estimated_reflectance']:.3f}  source={row['source']}")

print("\nKnown whitewash-relevant compounds found (BaSO4, TiO2, SiO2, CaCO3, Y2O3, ZrO2):")
targets = ["BaSO4", "TiO2", "SiO2", "CaCO3", "Y2O3", "ZrO2"]
master_norm = master.copy()
master_norm["_norm"] = master_norm["formula"].apply(normalize_formula)
master_rank = {f: i + 1 for i, f in enumerate(master.sort_values("estimated_reflectance", ascending=False)["formula"])}

combined_raw = pd.concat([
    mp_dielectric.assign(source="MP", id_col=mp_dielectric.get("material_id")),
    jarvis.assign(source="JARVIS", id_col=jarvis.get("jid")),
], ignore_index=True)
combined_raw["_norm"] = combined_raw["formula"].apply(normalize_formula)

for target in targets:
    target_norm = normalize_formula(target)
    variants = combined_raw[combined_raw["_norm"] == target_norm]
    if len(variants) == 0:
        print(f"  {target}: 0 variants found (excluded by element filter - "
              f"likely contains S or C, outside the allowed O+metal set).")
        continue
    best = variants.sort_values("estimated_reflectance", ascending=False).iloc[0]
    best_rank = master_rank.get(best["formula"], "deduplicated out of master")
    print(f"  {target}: {len(variants)} variant(s) found across MP+JARVIS "
          f"(reflectance range {variants['estimated_reflectance'].min():.3f}-"
          f"{variants['estimated_reflectance'].max():.3f}). Best: {best['source']} "
          f"{best.get('id_col')}, estimated_reflectance={best['estimated_reflectance']:.3f}, "
          f"master rank={best_rank}.")

print("\n" + "=" * 70)
print(f"Full ranked list: master_candidates.csv ({len(master)} unique candidates)")
print("Plots: candidate_screening.png, top_candidates.png")
print("=" * 70)
