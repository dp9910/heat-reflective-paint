import os

import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = pd.read_csv(os.path.join(PROJECT_DIR, "stage1_results.csv"))

results["NIR2_NIR1_ratio"] = results["Q_scat_NIR2"] / results["Q_scat_NIR1"]
results = results.sort_values("NIR2_NIR1_ratio", ascending=False)

print("Q_scat_NIR2 / Q_scat_NIR1 ratio (long-NIR performance relative to short-NIR):")
for _, row in results.iterrows():
    flag = " <-- needs BaSO4 gap fill confirmed" if row["NIR2_NIR1_ratio"] < 0.5 else ""
    print(f"  {row['formula']:<10} ratio={row['NIR2_NIR1_ratio']:.3f}  "
          f"(Q_NIR1={row['Q_scat_NIR1']:.3f}, Q_NIR2={row['Q_scat_NIR2']:.3f}){flag}")

below = results[results["NIR2_NIR1_ratio"] < 0.5]
print(f"\n{len(below)} of {len(results)} materials underperform in 1400-2500nm (ratio < 0.5): "
      f"{', '.join(below['formula'])}")
