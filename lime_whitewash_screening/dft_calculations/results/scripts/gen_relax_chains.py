import os, re, sys
sys.path.insert(0, '/data/scripts')
from pseudo_map import PSEUDO_MAP, PSEUDO_DIR
from mp_api.client import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.espresso import write_espresso_in

API_KEY = 'K8O05CEaGqQcMMtazJHYRawCP8mZ5vli'
adaptor = AseAtomsAdaptor()
BASE    = '/data/runs/tier3_emissivity'

# Materials needing vc-relax chain  (mpid, dir, ecut, erho, kmesh)
RELAX_NEEDED = [
    ('mp-3487',  'Ca3PO4_2', 50, 400, '4 4 4'),
    ('mp-7572',  'MgSO4',    50, 400, '4 4 4'),
]

def _fix(path):
    with open(path) as f: c = f.read()
    c = re.sub(r'&FCP\s*/\s*\n','',c)
    c = re.sub(r'&RISM\s*/\s*\n','',c)
    c = re.sub(r'/data/pseudopotentials/(\S+)',
               lambda m: os.path.basename(m.group(0)), c)
    with open(path,'w') as f: f.write(c)

def write_relax(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    params = {
        'control': {'calculation':'vc-relax','restart_mode':'from_scratch',
                    'prefix':atoms.get_chemical_formula(empirical=True),
                    'outdir':'./out2','pseudo_dir':PSEUDO_DIR,
                    'tprnfor':True,'tstress':True,
                    'forc_conv_thr':1e-4,'etot_conv_thr':1e-5,'disk_io':'low'},
        'system': {'ibrav':0,'ecutwfc':ecut,'ecutrho':erho,
                   'occupations':'smearing','smearing':'gaussian','degauss':0.005},
        'electrons': {'conv_thr':1e-8,'mixing_beta':0.3,'electron_maxstep':150},
        'ions': {'ion_dynamics':'bfgs'},
        'cell': {'cell_dynamics':'bfgs','press_conv_thr':0.5},
    }
    with open(path,'w') as f:
        write_espresso_in(f,atoms,input_data=params,pseudopotentials=pseudo,
                          kpts=[int(k) for k in kmesh.split()],koffset=(0,0,0))
    _fix(path)

def write_scf2(path, atoms, elems, ecut, erho, kmesh):
    pseudo = {e: PSEUDO_MAP[e] for e in elems}
    prefix = atoms.get_chemical_formula(empirical=True)
    params = {
        'control': {'calculation':'scf','restart_mode':'from_scratch',
                    'prefix':prefix,'outdir':'./out2','pseudo_dir':PSEUDO_DIR,
                    'tprnfor':True,'disk_io':'low'},
        'system': {'ibrav':0,'ecutwfc':ecut,'ecutrho':erho,
                   'occupations':'fixed','nosym':True},
        'electrons': {'conv_thr':1e-10,'mixing_beta':0.3,'electron_maxstep':200},
    }
    with open(path,'w') as f:
        write_espresso_in(f,atoms,input_data=params,pseudopotentials=pseudo,
                          kpts=[int(k) for k in kmesh.split()],koffset=(0,0,0))
    _fix(path)

def write_ph2(path, prefix):
    # NO recover=.true. — new relaxed geometry, phsave from old run is invalid
    content = (
        "&INPUTPH\n"
        f"  prefix    = '{prefix}',\n"
        f"  outdir    = './out2',\n"
        f"  fildyn    = '{prefix}_relax.dyn',\n"
        "  tr2_ph    = 1.0d-12,\n"
        "  ldisp     = .false.,\n"
        "  epsil     = .true.,\n"
        "  trans     = .true.,\n"
        "/\n"
        "0.0 0.0 0.0\n"
    )
    with open(path,'w') as f: f.write(content)

def write_dynmat2(path, prefix):
    with open(path,'w') as f:
        f.write(f"&INPUT\n  fildyn = '{prefix}_relax.dyn',\n  asr    = 'simple',\n/\n")

with MPRester(API_KEY) as mpr:
    for mpid, dirname, ecut, erho, kmesh in RELAX_NEEDED:
        struct = mpr.get_structure_by_material_id(mpid)
        atoms  = adaptor.get_atoms(struct)
        elems  = sorted(set(atoms.get_chemical_symbols()))
        prefix = atoms.get_chemical_formula(empirical=True)
        d      = f'{BASE}/{dirname}'
        os.makedirs(f'{d}/out2', exist_ok=True)

        missing = [e for e in elems if e not in PSEUDO_MAP]
        if missing:
            print(f'WARNING {dirname}: missing pseudos {missing}'); continue

        write_relax( f'{d}/relax.in',    atoms, elems, ecut, erho, kmesh)
        write_scf2(  f'{d}/scf2.in',     atoms, elems, ecut, erho, kmesh)
        write_ph2(   f'{d}/ph2.in',      prefix)
        write_dynmat2(f'{d}/dynmat2.in', prefix)

        run = (
            "#!/bin/bash\nset -euo pipefail\n"
            f"cd {d}\n"
            f"echo \"[$(date)] vc-relax {dirname}\"\n"
            "mpirun -np 8 pw.x -npool 2 < relax.in  > relax.out  2>&1\n"
            f"echo \"[$(date)] SCF {dirname}\"\n"
            "mpirun -np 8 pw.x -npool 2 < scf2.in   > scf2.out   2>&1\n"
            f"echo \"[$(date)] ph.x {dirname}\"\n"
            "mpirun -np 8 ph.x          < ph2.in    > ph2.out    2>&1\n"
            f"echo \"[$(date)] dynmat {dirname}\"\n"
            "dynmat.x                   < dynmat2.in > dynmat2.out 2>&1\n"
            f"echo \"[$(date)] {dirname} relaxed DONE\"\n"
        )
        with open(f'{d}/run_relax.sh','w') as f: f.write(run)
        os.chmod(f'{d}/run_relax.sh', 0o755)

        print(f'{dirname} ({mpid}): {len(atoms)} atoms {elems}  -> relax.in scf2.in ph2.in dynmat2.in run_relax.sh')

print('Done.')
