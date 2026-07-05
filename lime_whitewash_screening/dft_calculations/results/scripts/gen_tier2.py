import os, sys
sys.path.insert(0, '/data/scripts')
from pseudo_map import PSEUDO_MAP, PSEUDO_DIR
from mp_api.client import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.espresso import write_espresso_in

API_KEY = 'K8O05CEaGqQcMMtazJHYRawCP8mZ5vli'
RUNS = '/data/runs/tier2'
adaptor = AseAtomsAdaptor()

# ── Material definitions ────────────────────────────────────────────
# (mp_id, dir_name, ecutwfc, ecutrho, kmesh_relax, kmesh_scf, do_phonon, do_eps)
TIER2 = [
    # Group A — optical spectra (reuse Tier 1 SCF for rutile/monoclinic)
    ('mp-390',    'TiO2_anatase',        50, 400, '6 6 4',  '8 8 6',  False, True),
    # Group B — new phonon materials
    ('mp-4019',   'CaTiO3',              50, 400, '4 4 4',  '6 6 6',  True,  False),
    ('mp-4481',   'Ca2SiO4',             50, 400, '4 4 4',  '6 6 4',  True,  False),
    ('mp-4571',   'CaZrO3',              50, 400, '4 4 4',  '6 6 6',  True,  False),
    ('mp-23879',  'Ca_OH_2',             50, 400, '4 4 4',  '6 6 6',  True,  False),
    ('mp-753891', 'ZrTiO4',              50, 400, '4 4 4',  '6 6 4',  True,  False),
]

def write_relax(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    params = {
        'control': {'calculation': 'vc-relax', 'restart_mode': 'from_scratch',
                    'prefix': atoms.get_chemical_formula(empirical=True),
                    'outdir': './out', 'pseudo_dir': PSEUDO_DIR,
                    'tprnfor': True, 'tstress': True,
                    'forc_conv_thr': 1e-4, 'etot_conv_thr': 1e-5, 'disk_io': 'low'},
        'system': {'ibrav': 0, 'ecutwfc': ecut, 'ecutrho': erho,
                   'occupations': 'smearing', 'smearing': 'gaussian', 'degauss': 0.005},
        'electrons': {'conv_thr': 1e-8, 'mixing_beta': 0.3, 'electron_maxstep': 150},
        'ions': {'ion_dynamics': 'bfgs'},
        'cell': {'cell_dynamics': 'bfgs', 'press_conv_thr': 0.5},
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(x) for x in kmesh.split()], koffset=(0,0,0))
    _strip_fcp_rism(path)
    _fix_pseudo_paths(path)

def write_scf(path, atoms, elems, ecut, erho, kmesh, nosym=True):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    params = {
        'control': {'calculation': 'scf', 'restart_mode': 'from_scratch',
                    'prefix': atoms.get_chemical_formula(empirical=True),
                    'outdir': './out', 'pseudo_dir': PSEUDO_DIR,
                    'tprnfor': True, 'tstress': True, 'disk_io': 'low'},
        'system': {'ibrav': 0, 'ecutwfc': ecut, 'ecutrho': erho,
                   'occupations': 'fixed', 'nosym': nosym},
        'electrons': {'conv_thr': 1e-10, 'mixing_beta': 0.3, 'electron_maxstep': 200},
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(x) for x in kmesh.split()], koffset=(0,0,0))
    _strip_fcp_rism(path)
    _fix_pseudo_paths(path)

def write_nscf(path, atoms, elems, ecut, erho, kmesh, nbnd):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    params = {
        'control': {'calculation': 'nscf', 'restart_mode': 'from_scratch',
                    'prefix': atoms.get_chemical_formula(empirical=True),
                    'outdir': './out', 'pseudo_dir': PSEUDO_DIR, 'disk_io': 'low'},
        'system': {'ibrav': 0, 'ecutwfc': ecut, 'ecutrho': erho,
                   'occupations': 'tetrahedra', 'nbnd': nbnd, 'nosym': True},
        'electrons': {'conv_thr': 1e-10, 'mixing_beta': 0.3},
    }
    with open(path, 'w') as f:
        write_espresso_in(f, atoms, input_data=params,
                          pseudopotentials=pseudo,
                          kpts=[int(x) for x in kmesh.split()], koffset=(0,0,0))
    _strip_fcp_rism(path)
    _fix_pseudo_paths(path)

def write_eps(path, prefix):
    content = f"""&inputpp
  prefix     = '{prefix}',
  outdir     = './out',
  calculation= 'eps',
/
&energy_grid
  smeartype  = 'gauss',
  intersmear = 0.1,
  wmax       = 30.0,
  wmin       = 0.0,
  nw         = 1000,
/
"""
    with open(path, 'w') as f:
        f.write(content)

def write_ph(path, prefix):
    content = f"""&INPUTPH
  prefix    = '{prefix}',
  outdir    = './out',
  fildyn    = '{prefix}.dyn',
  tr2_ph    = 1.0d-12,
  ldisp     = .false.,
  epsil     = .true.,
  trans     = .true.,
/
0.0 0.0 0.0
"""
    with open(path, 'w') as f:
        f.write(content)

def write_dynmat(path, prefix):
    with open(path, 'w') as f:
        f.write(f"&INPUT\n  fildyn = '{prefix}.dyn',\n  asr    = 'simple',\n/\n")

def _strip_fcp_rism(path):
    import re
    with open(path) as f:
        c = f.read()
    c = re.sub(r'&FCP\s*/\s*\n', '', c)
    c = re.sub(r'&RISM\s*/\s*\n', '', c)
    with open(path, 'w') as f:
        f.write(c)

def _fix_pseudo_paths(path):
    import os as _os
    with open(path) as f:
        c = f.read()
    # Replace absolute paths in ATOMIC_SPECIES with basenames
    import re
    c = re.sub(r'/data/pseudopotentials/(\S+)', lambda m: _os.path.basename(m.group(0)), c)
    with open(path, 'w') as f:
        f.write(c)

with MPRester(API_KEY) as mpr:
    for mpid, dirname, ecut, erho, km_relax, km_scf, do_ph, do_eps in TIER2:
        struct = mpr.get_structure_by_material_id(mpid)
        atoms  = adaptor.get_atoms(struct)
        elems  = sorted(set(atoms.get_chemical_symbols()))
        prefix = atoms.get_chemical_formula(empirical=True)
        nat    = len(atoms)
        d      = f'{RUNS}/{dirname}'
        os.makedirs(f'{d}/out', exist_ok=True)

        missing = [e for e in elems if e not in PSEUDO_MAP]
        if missing:
            print(f'WARNING {dirname}: missing pseudos for {missing}')
            continue

        write_relax(f'{d}/relax.in', atoms, elems, ecut, erho, km_relax)
        write_scf(f'{d}/scf.in',   atoms, elems, ecut, erho, km_scf)

        if do_eps:
            # Denser k-mesh and extra bands for optical spectrum
            km_nscf = ' '.join([str(int(k)*2) for k in km_scf.split()])
            nbnd = max(nat * 6, 60)
            write_nscf(f'{d}/nscf.in', atoms, elems, ecut, erho, km_nscf, nbnd)
            write_eps(f'{d}/epsilon.in', prefix)

        if do_ph:
            write_ph(f'{d}/ph.in', prefix)
            write_dynmat(f'{d}/dynmat.in', prefix)

        # Run script
        steps = []
        steps.append(f'mpirun -np 8 pw.x -npool 2 < relax.in  > relax.out  2>&1')
        steps.append(f'mpirun -np 8 pw.x -npool 2 < scf.in    > scf.out    2>&1')
        if do_eps:
            steps.append(f'mpirun -np 8 pw.x -npool 2 < nscf.in   > nscf.out   2>&1')
            steps.append(f'epsilon.x                  < epsilon.in > epsilon.out 2>&1')
        if do_ph:
            steps.append(f'mpirun -np 8 ph.x          < ph.in     > ph.out     2>&1')
            steps.append(f'dynmat.x                   < dynmat.in > dynmat.out 2>&1')

        run = '#!/bin/bash\nset -euo pipefail\n'
        run += f'cd {d}\necho "[$(date)] Starting {dirname}"\n'
        for s in steps:
            run += f'echo "[$(date)] {s.split()[2]}"\n{s}\n'
        run += f'echo "[$(date)] {dirname} DONE"\n'
        with open(f'{d}/run.sh', 'w') as f:
            f.write(run)
        os.chmod(f'{d}/run.sh', 0o755)

        print(f'{dirname} ({mpid}): {nat} atoms, elems={elems}')
        print(f'  Files: {[x for x in ["relax.in","scf.in","nscf.in","epsilon.in","ph.in","dynmat.in"] if os.path.exists(f"{d}/{x}")]}')

print('\nAll Tier 2 inputs written.')
