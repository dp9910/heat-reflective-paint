import os
import sys

import pandas as pd
from pymatgen.core import Composition

sys.path.insert(0, os.path.dirname(__file__))
from common import normalize_formula

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master_path = os.path.join(PROJECT_DIR, "master_candidates.csv")
clean_path = os.path.join(PROJECT_DIR, "master_candidates_clean.csv")

ALLOWED = {"Ca", "Ba", "Ti", "Si", "Zr", "Y", "Mg", "Al", "W", "Nb", "Ce", "Na", "K", "S", "C", "O"}
ALWAYS_KEEP = {normalize_formula("BaSO4"), normalize_formula("CaCO3")}

master = pd.read_csv(master_path)


def keep_row(formula):
    if normalize_formula(formula) in ALWAYS_KEEP:
        return True
    try:
        els = {str(e) for e in Composition(formula).elements}
    except Exception:
        return False
    return els.issubset(ALLOWED)


mask = master["formula"].apply(keep_row)
clean = master[mask]
removed = master[~mask]

clean.to_csv(clean_path, index=False)

print(f"Removed {len(removed)} rows with elements outside the allowed set.")
if len(removed):
    print("Removed formulas:", ", ".join(sorted(removed["formula"].unique())))
print(f"master_candidates_clean.csv saved with {len(clean)} rows (from {len(master)}).")
