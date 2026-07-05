import os, sys
sys.path.insert(0, '/data/scripts')

from mp_api.client import MPRester
from pymatgen.io.espresso.inputs import PWInput
from pseudo_map import PSEUDO_MAP, PSEUDO_DIR

API_KEY = 'K8O05CEaGqQcMMtazJHYRawCP8mZ5vli'

TIER1 = {
    'TiO2_rutile':   'mp-2657',
    'ZrO2_monoclinic': 'mp-2858',
    'SiO2_quartz':   'mp-7000',
    'BaSO4':         'mp-22554',
}

os.makedirs('/data/structures', exist_ok=True)

with MPRester(API_KEY) as mpr:
    for name, mpid in TIER1.items():
        struct = mpr.get_structure_by_material_id(mpid)
        cif_path = f'/data/structures/{name}.cif'
        struct.to(fmt='cif', filename=cif_path)
        elems = sorted(set(str(s.specie) for s in struct.sites))
        print(f'{name} ({mpid}): {struct.formula}, {len(struct.sites)} sites, elements={elems}')
        for el in elems:
            if el not in PSEUDO_MAP:
                print(f'  WARNING: no pseudopotential for {el}')

print('Structures saved to /data/structures/')
