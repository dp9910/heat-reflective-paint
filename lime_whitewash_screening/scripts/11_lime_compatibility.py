import os
import sys

import pandas as pd
from pymatgen.core import Composition

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
master_path = os.path.join(PROJECT_DIR, "master_candidates.csv")

master = pd.read_csv(master_path)


def is_lime_compatible(formula):
    try:
        els = {str(e) for e in Composition(formula).elements}
    except Exception:
        return False
    return bool(els & {"Ca", "Si"})


master["lime_compatible"] = master["formula"].apply(is_lime_compatible)
master.to_csv(master_path, index=False)

print(f"lime_compatible=True for {int(master['lime_compatible'].sum())} of {len(master)} candidates "
      f"(formula contains Ca or Si).")
