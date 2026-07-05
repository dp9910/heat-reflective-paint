import os, sys, json
sys.path.insert(0, '/data/scripts')
from pseudo_map import PSEUDO_MAP, PSEUDO_DIR

from mp_api.client import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.espresso import write_espresso_in
import numpy as np

API_KEY = 'K8O05CEaGqQcMMtazJHYRawCP8mZ5vli'
RUNS_DIR = '/data/runs/tier1'

# Material: (mp-id, ecutwfc Ry, ecutrho Ry, k-mesh, degauss)
TIER1 = {
    'TiO2_rutile':    ('mp-2657',  50, 400, '6 6 10', 0.01),
    'ZrO2_monoclinic':('mp-2858',  40, 320, '4 4 4',  0.01),
    'SiO2_quartz':    ('mp-7000',  50, 400, '4 4 4',  0.01),
    'BaSO4':          ('mp-3164', 50, 400, '3 3 3',  0.01),
}

def write_relax(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: os.path.join(PSEUDO_DIR, PSEUDO_MAP[e]) for e in elems}
    params = {
        'control': {
            'calculation': 'vc-relax',
            'restart_mode': 'from_scratch',
            'prefix': atoms.get_chemical_formula(empirical=True),
            'outdir': './out',
            'pseudo_dir': PSEUDO_DIR,
            'tprnfor': True,
            'tstress': True,
            'forc_conv_thr': 1e-4,
            'etot_conv_thr': 1e-5,
            'disk_io': 'low',
        },
        'system': {
            'ibrav': 0,
            'ecutwfc': ecut,
            'ecutrho': erho,
            'occupations': 'smearing',
            'smearing': 'gaussian',
            'degauss': 0.005,
            'nspin': 1,
        },
        'electrons': {
            'conv_thr': 1e-8,
            'mixing_beta': 0.3,
            'electron_maxstep': 150,
        },
        'ions': {'ion_dynamics': 'bfgs'},
        'cell': {'cell_dynamics': 'bfgs', 'press_conv_thr': 0.5},
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(x) for x in kmesh.split()],
                          koffset=(0, 0, 0))

def write_scf(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: os.path.join(PSEUDO_DIR, PSEUDO_MAP[e]) for e in elems}
    params = {
        'control': {
            'calculation': 'scf',
            'restart_mode': 'from_scratch',
            'prefix': atoms.get_chemical_formula(empirical=True),
            'outdir': './out',
            'pseudo_dir': PSEUDO_DIR,
            'tprnfor': True,
            'tstress': True,
            'disk_io': 'low',
        },
        'system': {
            'ibrav': 0,
            'ecutwfc': ecut,
            'ecutrho': erho,
            'occupations': 'smearing',
            'smearing': 'gaussian',
            'degauss': 0.005,
        },
        'electrons': {
            'conv_thr': 1e-10,
            'mixing_beta': 0.3,
            'electron_maxstep': 200,
        },
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(x) for x in kmesh.split()],
                          koffset=(0, 0, 0))

def write_ph(path, prefix, nat):
    content = f"""&INPUTPH
  prefix    = '{prefix}',
  outdir    = './out',
  fildyn    = '{prefix}.dyn',
  tr2_ph    = 1.0d-14,
  ldisp     = .false.,
  epsil     = .true.,
  lraman    = .false.,
  trans     = .true.,
  asr       = 'simple',
/
0.0 0.0 0.0
"""
    with open(path, 'w') as f:
        f.write(content)

def write_dynmat(path, prefix, nat):
    content = f"""&INPUT
  fildyn = '{prefix}.dyn',
  asr    = 'simple',
  filout = '{prefix}.modes',
/
"""
    with open(path, 'w') as f:
        f.write(content)

adaptor = AseAtomsAdaptor()

with MPRester(API_KEY) as mpr:
    for name, (mpid, ecut, erho, kmesh, degauss) in TIER1.items():
        struct = mpr.get_structure_by_material_id(mpid)
        atoms = adaptor.get_atoms(struct)
        elems = sorted(set(atoms.get_chemical_symbols()))
        prefix = atoms.get_chemical_formula(empirical=True)

        calc_dir = os.path.join(RUNS_DIR, name)
        os.makedirs(os.path.join(calc_dir, 'out'), exist_ok=True)

        write_relax(f'{calc_dir}/relax.in',  atoms, elems, ecut, erho, kmesh)
        write_scf(  f'{calc_dir}/scf.in',    atoms, elems, ecut, erho, kmesh)
        write_ph(   f'{calc_dir}/ph.in',     prefix, len(atoms))
        write_dynmat(f'{calc_dir}/dynmat.in', prefix, len(atoms))

        # Run script: relax -> scf -> ph -> dynmat chained
        nproc = 8
        run = f"""#!/bin/bash
#--- Tier 1: {name} ({mpid}) ---
set -euo pipefail
cd {calc_dir}

echo "[$(date)] Starting vc-relax: {name}"
mpirun -np {nproc} pw.x -npool 2 < relax.in  > relax.out  2>&1
echo "[$(date)] relax done"

# Copy relaxed structure back as SCF input
cp out/{prefix}.save/data-file-schema.xml out/ 2>/dev/null || true

echo "[$(date)] Starting SCF: {name}"
mpirun -np {nproc} pw.x -npool 2 < scf.in    > scf.out    2>&1
echo "[$(date)] SCF done"

echo "[$(date)] Starting DFPT phonon: {name}"
mpirun -np {nproc} ph.x  -npool 1 < ph.in    > ph.out     2>&1
echo "[$(date)] phonon done"

echo "[$(date)] Running dynmat: {name}"
dynmat.x < dynmat.in > dynmat.out 2>&1
echo "[$(date)] dynmat done — IR modes in dynmat.out"
"""
        with open(f'{calc_dir}/run.sh', 'w') as f:
            f.write(run)
        os.chmod(f'{calc_dir}/run.sh', 0o755)

        print(f'{name}: {mpid}, {len(atoms)} atoms, elems={elems}')
        print(f'  ecutwfc={ecut} Ry, kmesh={kmesh}')
        print(f'  Files: relax.in, scf.in, ph.in, dynmat.in, run.sh')

print('\nAll Tier 1 input files written to /data/runs/tier1/')
