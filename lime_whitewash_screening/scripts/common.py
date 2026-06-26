import os

ALLOWED_METALS = {"Ba", "Ti", "Si", "Ca", "Al", "Mg", "Zr", "Y", "Ce", "Nb", "W"}
TOXIC_ELEMENTS = {"Pb", "Cd", "Cr", "Hg", "As"}
ALLOWED_ELEMENTS = ALLOWED_METALS | {"O"}

VISIBLE_NIR_BOUNDARY_EV = 1.77  # ~700 nm


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip("'\""))


def fresnel_reflectance(n, k):
    if n is None or k is None:
        return None
    try:
        n = float(n)
        k = float(k)
    except (TypeError, ValueError):
        return None
    return ((n - 1) ** 2 + k ** 2) / ((n + 1) ** 2 + k ** 2)


def normalize_formula(formula):
    if not formula:
        return None
    try:
        from pymatgen.core import Composition
        return Composition(formula).reduced_formula
    except Exception:
        return formula
