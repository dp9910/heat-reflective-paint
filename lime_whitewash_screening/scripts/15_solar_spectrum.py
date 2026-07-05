import os

import numpy as np
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_path = os.path.join(PROJECT_DIR, "am1.5g_spectrum.csv")

WAVELENGTHS_NM = np.arange(300, 2501, 10)

local_xls_path = os.path.join(PROJECT_DIR, "astmg173.xls")

irradiance = None
if os.path.exists(local_xls_path):
    try:
        print(f"Reading local ASTM G173 file: {local_xls_path}")
        xls = pd.read_excel(local_xls_path, sheet_name="SMARTS2", header=None, skiprows=2)
        wl_raw, global_raw = xls[0].values.astype(float), xls[2].values.astype(float)
        irradiance = np.interp(WAVELENGTHS_NM, wl_raw, global_raw)
        print("Loaded local NREL spectrum file successfully.")
    except Exception as e:
        print(f"WARNING: failed to parse local astmg173.xls ({e}). Trying network download next.")

if irradiance is None:
    try:
        import requests
        print("Attempting direct download of ASTM G173 spectrum from NREL...")
        r = requests.get("https://www.nrel.gov/grid/solar-resource/assets/data/astmg173.xls", timeout=15)
        r.raise_for_status()
        xls = pd.read_excel(pd.io.common.BytesIO(r.content), sheet_name=0, skiprows=1)
        wl_col, glob_col = xls.columns[0], xls.columns[2]
        irradiance = np.interp(WAVELENGTHS_NM, xls[wl_col].values, xls[glob_col].values)
        print("Downloaded NREL spectrum successfully.")
    except Exception as e:
        print(f"WARNING: NREL direct download failed ({e}). Falling back to pvlib's bundled ASTM G173-03 reference spectrum.")
        import pvlib.spectrum as sp
        am15 = sp.get_reference_spectra(wavelengths=WAVELENGTHS_NM)
        irradiance = am15["global"].values

df = pd.DataFrame({"wavelength_nm": WAVELENGTHS_NM, "irradiance_w_m2_nm": irradiance})
df.to_csv(out_path, index=False)

total = np.trapezoid(irradiance, WAVELENGTHS_NM)
print(f"Saved {len(df)} points (300-2500nm, 10nm steps) to {out_path}")
print(f"Integrated irradiance over 300-2500nm: {total:.2f} W/m^2 (AM1.5G reference total is ~1000 W/m^2)")
