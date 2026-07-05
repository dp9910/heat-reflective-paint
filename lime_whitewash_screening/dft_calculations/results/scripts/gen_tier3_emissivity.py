import os, sys, re
sys.path.insert(0, '/data/scripts')
from pseudo_map import PSEUDO_MAP, PSEUDO_DIR
from mp_api.client import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.espresso import write_espresso_in

API_KEY  = 'K8O05CEaGqQcMMtazJHYRawCP8mZ5vli'
RUNS_DIR = '/data/runs/tier3_emissivity'
adaptor  = AseAtomsAdaptor()

MATERIALS = [
    ('CaSO4_anhydrite', 'mp-4406',  50, 400, '4 4 4'),
    ('Ca3PO4_2',        'mp-3487',  50, 400, '4 4 4'),
    ('MgCO3_magnesite', 'mp-5348',  50, 400, '4 4 4'),
    ('MgSO4',           'mp-7572',  50, 400, '4 4 4'),
    ('SrSO4',           'mp-5285',  50, 400, '3 3 3'),
    ('BaMoO4',          'mp-19276', 60, 480, '4 4 4'),
    ('BaWO4',           'mp-19048', 60, 480, '4 4 4'),
]

def _fix(path):
    with open(path) as f: c = f.read()
    c = re.sub(r'&FCP\s*/\s*\n', '', c)
    c = re.sub(r'&RISM\s*/\s*\n', '', c)
    c = re.sub(r'/data/pseudopotentials/(\S+)',
               lambda m: os.path.basename(m.group(0)), c)
    with open(path, 'w') as f: f.write(c)

def write_scf(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    params = {
        'control': {'calculation': 'scf', 'restart_mode': 'from_scratch',
                    'prefix': atoms.get_chemical_formula(empirical=True),
                    'outdir': './out', 'pseudo_dir': PSEUDO_DIR,
                    'tprnfor': True, 'disk_io': 'low'},
        'system': {'ibrav': 0, 'ecutwfc': ecut, 'ecutrho': erho,
                   'occupations': 'fixed', 'nosym': True},
        'electrons': {'conv_thr': 1e-10, 'mixing_beta': 0.3, 'electron_maxstep': 200},
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(k) for k in kmesh.split()], koffset=(0,0,0))
    _fix(path)

def write_ph(path, prefix):
    content = (
        "&INPUTPH\n"
        f"  prefix    = '{prefix}',\n"
        f"  outdir    = './out',\n"
        f"  fildyn    = '{prefix}.dyn',\n"
        "  tr2_ph    = 1.0d-12,\n"
        "  ldisp     = .false.,\n"
        "  epsil     = .true.,\n"
        "  trans     = .true.,\n"
        "  recover   = .true.,\n"
        "/\n"
        "0.0 0.0 0.0\n"
    )
    with open(path, 'w') as f: f.write(content)

def write_dynmat(path, prefix):
    with open(path, 'w') as f:
        f.write(f"&INPUT\n  fildyn = '{prefix}.dyn',\n  asr    = 'simple',\n/\n")

def write_run(path, dirname, mpid, nat, d):
    content = (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f"cd {d}\n"
        f"echo \"[$(date)] SCF: {dirname} ({mpid}, {nat} atoms)\"\n"
        "mpirun -np 8 pw.x -npool 2 < scf.in > scf.out 2>&1\n"
        f"echo \"[$(date)] DFPT phonon: {dirname}\"\n"
        "mpirun -np 8 ph.x < ph.in > ph.out 2>&1\n"
        f"echo \"[$(date)] dynmat: {dirname}\"\n"
        "dynmat.x < dynmat.in > dynmat.out 2>&1\n"
        f"echo \"[$(date)] {dirname} DONE\"\n"
    )
    with open(path, 'w') as f: f.write(content)
    os.chmod(path, 0o755)

with MPRester(API_KEY) as mpr:
    for dirname, mpid, ecut, erho, kmesh in MATERIALS:
        struct = mpr.get_structure_by_material_id(mpid)
        atoms  = adaptor.get_atoms(struct)
        elems  = sorted(set(atoms.get_chemical_symbols()))
        prefix = atoms.get_chemical_formula(empirical=True)
        nat    = len(atoms)
        d      = f'{RUNS_DIR}/{dirname}'
        os.makedirs(f'{d}/out', exist_ok=True)

        missing = [e for e in elems if e not in PSEUDO_MAP]
        if missing:
            print(f'WARNING {dirname}: missing pseudos for {missing} -- skipping')
            continue

        write_scf(f'{d}/scf.in',    atoms, elems, ecut, erho, kmesh)
        write_ph( f'{d}/ph.in',     prefix)
        write_dynmat(f'{d}/dynmat.in', prefix)
        write_run(f'{d}/run.sh', dirname, mpid, nat, d)

        print(f'{dirname:<22} {mpid}  {prefix:<18} {nat:>2}at  elems={elems}  ecut={ecut}Ry')

print('\nAll input files written.')
