import os

import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master_path = os.path.join(PROJECT_DIR, "master_candidates.csv")

master = pd.read_csv(master_path)


def classify(row):
    q, bg = row.get("mie_qscat_800nm"), row.get("band_gap")
    if pd.isna(q) or pd.isna(bg):
        return "LOW"
    if q > 2.0 and bg > 3.5:
        return "HIGH"
    if q > 1.0 and bg > 2.5:
        return "MEDIUM"
    return "LOW"


master["priority"] = master.apply(classify, axis=1)
master = master.sort_values("mie_qscat_800nm", ascending=False, na_position="last")
master.to_csv(master_path, index=False)

counts = master["priority"].value_counts()
print("Priority recalibrated using mie_qscat_800nm + band_gap thresholds:")
print(f"  HIGH:   {counts.get('HIGH', 0)}  (mie_qscat_800nm > 2.0 AND band_gap > 3.5 eV)")
print(f"  MEDIUM: {counts.get('MEDIUM', 0)}  (mie_qscat_800nm > 1.0 AND band_gap > 2.5 eV)")
print(f"  LOW:    {counts.get('LOW', 0)}")

print("\nTop 15 candidates after recalibration:")
print(master.head(15)[["formula", "band_gap", "mie_qscat_800nm", "priority"]].to_string(index=False))
