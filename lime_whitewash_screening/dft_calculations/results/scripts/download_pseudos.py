import urllib.request, os, sys

PSEUDO_DIR = '/data/pseudopotentials'
BASE_QE = 'https://pseudopotentials.quantum-espresso.org/upf_files'
BASE_GBRV = 'https://www.physics.rutgers.edu/gbrv/all_pbe_UPF_v1.5'

# SSSP 1.3 efficiency recommended pseudopotentials
PSEUDOS = {
    'O':  ('O.pbe-n-kjpaw_psl.0.1.UPF', BASE_QE),
    'Ti': ('ti_pbe_v1.4.uspp.F.UPF',     BASE_GBRV),
    'Zr': ('zr_pbe_v1.uspp.F.UPF',       BASE_GBRV),
    'Si': ('Si.pbe-n-kjpaw_psl.1.0.0.UPF', BASE_QE),
    'Ba': ('Ba.pbe-spn-kjpaw_psl.1.0.0.UPF', BASE_QE),
    'S':  ('s_pbe_v1.4.uspp.F.UPF',      BASE_GBRV),
    'Ca': ('Ca.pbe-spn-kjpaw_psl.1.0.0.UPF', BASE_QE),
    'Y':  ('y_pbe_v1.uspp.F.UPF',        BASE_GBRV),
    'Mg': ('mg_pbe_v1.4.uspp.F.UPF',     BASE_GBRV),
    'W':  ('w_pbe_v1.2.uspp.F.UPF',      BASE_GBRV),
    'Nb': ('Nb.pbe-spn-kjpaw_psl.0.3.0.UPF', BASE_QE),
    'N':  ('n_pbe_v1.2.uspp.F.UPF',      BASE_GBRV),
    'Ce': ('Ce.GGA-PBE-paw-v1.0.UPF',    BASE_QE),
}

for elem, (fname, base) in PSEUDOS.items():
    dest = os.path.join(PSEUDO_DIR, fname)
    if os.path.exists(dest):
        print(f'  {elem}: already exists, skipping')
        continue
    url = f'{base}/{fname}'
    try:
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest)
        print(f'  {elem}: {fname} ({size//1024} KB)')
    except Exception as e:
        print(f'  {elem}: FAILED - {e}')
