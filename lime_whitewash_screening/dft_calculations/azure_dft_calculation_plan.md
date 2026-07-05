# Azure DFT Calculation Plan
## Enhanced Lime Whitewash — Passive Building Cooling
**VM:** qe-dft-vm · Standard_D32as_v5 · 32 vCPU AMD EPYC · 128 GB RAM · Ubuntu 22.04 LTS  
**Budget:** $200 credit · ~$1.54/hr active · ~125 hrs total compute  
**Auto-shutdown:** 22:00 UTC daily

---

## Resources & Where to Get Everything

### Software — Install on VM

| Tool | Purpose | Get It |
|---|---|---|
| **Quantum ESPRESSO** | SCF, DFPT, phonon calculations | `sudo apt install quantum-espresso` or [quantumespresso.org](https://www.quantum-espresso.org/download) |
| **pymatgen** | Structure fetch, format conversion, post-processing | `pip install pymatgen` · [pymatgen.org](https://pymatgen.org) |
| **phonopy** | Phonon post-processing, IR spectrum plots | `pip install phonopy` · [phonopy-project.github.io](https://phonopy.github.io/phonopy) |
| **mp-api** | Materials Project API client | `pip install mp-api` · [api.materialsproject.org](https://api.materialsproject.org) |
| **matplotlib / numpy / scipy** | Plotting and analysis | `pip install matplotlib numpy scipy` |
| **ASE** | Atomic simulation environment, structure handling | `pip install ase` · [wiki.fysik.dtu.dk/ase](https://wiki.fysik.dtu.dk/ase) |

### Pseudopotentials — Download Before Running Anything

| Library | Why Use It | Download |
|---|---|---|
| **SSSP Efficiency v1.3 (PBE)** | Pre-tested, reliable for oxides, recommended for production runs | [materialscloud.org/discover/sssp](https://www.materialscloud.org/discover/sssp) · direct: `wget https://archive.materialscloud.org/record/file?filename=SSSP_1.3.0_PBE_efficiency.tar.gz` |
| **SSSP Precision v1.3 (PBE)** | Higher cutoffs, use for dielectric/optical property calculations | Same page, precision variant |
| **PseudoDojo (PBE NC)** | Norm-conserving pseudopotentials, needed for DFPT optical response | [pseudo-dojo.org](http://www.pseudo-dojo.org) |

Elements needed: **Ti, Zr, O, Si, Ba, S, Ca, Y, Mg, W, Nb, Ce, N**  
Download all upfront — saves interruptions mid-run.

### Crystal Structures — Fetch via API

| Source | What it has | Access |
|---|---|---|
| **Materials Project** | Relaxed structures for all your candidates | [materialsproject.org](https://materialsproject.org) · API key: your existing key · `MPRester("your_key")` |
| **JARVIS-DFT** | Alternative structures, some not in MP | `pip install jarvis-tools` · no key needed · [jarvis.nist.gov](https://jarvis.nist.gov) |
| **Crystallography Open Database (COD)** | Experimental structures for validation | [crystallography.net](http://www.crystallography.net/cod) · free, no key |

MP IDs for your key materials:  
`TiO₂ rutile: mp-2657` · `ZrO₂ monoclinic: mp-2858` · `SiO₂ quartz: mp-7000` · `BaSO₄: mp-22554` · `CaTiO₃: mp-4019` · `Ca(OH)₂: mp-561017` · `WO₃: mp-19418` · `MgWO₄: mp-19079` · `Ca₂SiO₄: mp-4340` · `CaZrO₃: mp-4240`

### Reference Data — For Validating Your Results

| Resource | Purpose | Link |
|---|---|---|
| **NIST Webbook** | Experimental IR spectra for TiO₂, SiO₂, ZrO₂ | [webbook.nist.gov](https://webbook.nist.gov) |
| **Phono3py database** | Computed phonon data for common oxides | [github.com/atztogo/phono3py](https://github.com/atztogo/phono3py) |
| **RRUFF database** | Raman + IR spectra for minerals (BaSO₄, SiO₂, CaCO₃) | [rruff.info](https://rruff.info) |
| **Purdue BaSO₄ paper** | Li et al. ACS AMI 2021 — your benchmark | DOI: 10.1021/acsami.0c21597 |
| **JARVIS phonon data** | Pre-computed phonon for many oxides — cross-check yours | [jarvis.nist.gov/jarvisdft](https://jarvis.nist.gov/jarvisdft) |

---

## Calculation Plan — Priority Ordered

> **Run Tier 1 first continuously. Validate outputs before launching Tier 2+. Once Tier 1 looks clean, launch Tier 2–3 jobs in parallel across 32 vCPUs.**

---

### Tier 1 — Must Run · Directly Feeds Paper · Est. 20–30 hrs

**Materials:** TiO₂ rutile, ZrO₂ monoclinic, SiO₂ quartz, BaSO₄  
**Goal:** Confirm IR-active phonon modes in 770–1250 cm⁻¹ (8–13 µm atmospheric window) for all four formulation components

| # | Calculation | Material | Purpose |
|---|---|---|---|
| 1 | Structure relaxation (vc-relax), PBE | TiO₂ rutile | Confirm geometry before phonon run |
| 2 | SCF ground state, converged k-mesh | TiO₂ rutile | Electronic ground state |
| 3 | DFPT phonon at Gamma point + IR intensities | TiO₂ rutile | Extract IR-active modes in 8–13 µm window |
| 4 | Structure relaxation (vc-relax), PBE | ZrO₂ monoclinic | Confirm geometry |
| 5 | SCF ground state | ZrO₂ monoclinic | Electronic ground state |
| 6 | DFPT phonon at Gamma point + IR intensities | ZrO₂ monoclinic | Extract IR-active modes in 8–13 µm window |
| 7 | SCF + DFPT phonon | SiO₂ alpha-quartz | Internal validation — known IR modes at 9.1 µm, compare to NIST |
| 8 | SCF + DFPT phonon | BaSO₄ | Internal validation — compare against Purdue paper's reported modes |

**Validation check after Tier 1:** SiO₂ should show strong IR modes near 1100 cm⁻¹ and 800 cm⁻¹. BaSO₄ should show modes near 1100–1200 cm⁻¹. If these match NIST/RRUFF data within ~5%, your setup is correct and Tier 2+ results are trustworthy.

---

### Tier 2 — High Value · Feeds Paper Discussion · Est. 30–40 hrs

**Goal:** Full optical spectra and phonon data for remaining formulation candidates

| # | Calculation | Material | Purpose |
|---|---|---|---|
| 9 | DFPT frequency-dependent dielectric function | TiO₂ rutile | Full n(λ), k(λ) from first principles, 300–2500 nm — replaces constant-n Mie approximation |
| 10 | DFPT frequency-dependent dielectric function | ZrO₂ monoclinic | Same — validates Stage 1 Mie results |
| 11 | Structure relax + SCF + DFPT phonon | CaTiO₃ | Lime-compatible candidate — check 8–13 µm IR activity |
| 12 | Structure relax + SCF + DFPT phonon | ZrTiO₄ | Mixed oxide candidate — confirm phonon activity |
| 13 | SCF + DFPT dielectric function | TiO₂ anatase | Compare optical spectrum vs rutile — confirms why rutile is preferred phase |
| 14 | SCF + DFPT phonon | Ca₂SiO₄ | Lime-compatible silicate — check IR emission in atmospheric window |
| 15 | SCF + DFPT phonon | CaZrO₃ | Lime-compatible zirconate — has IR flag in JARVIS, confirm it |
| 16 | SCF + DFPT phonon | Ca(OH)₂ portlandite | Binder baseline — optical properties of lime itself for Mie matrix correction |

---

### Tier 3 — Novel Results · Strengthens Novelty Claim · Est. 25–35 hrs

**Goal:** First-reported phonon data for novel candidates; validate or drop YZr₅O₁₁

| # | Calculation | Material | Purpose |
|---|---|---|---|
| 17 | Structure relax + SCF + DFPT phonon | YZr₅O₁₁ | First-ever reported phonon data for this mixed oxide — your novel DFT candidate |
| 18 | Structure relax + SCF + DFPT phonon | YZr₄O₉ | Confirm whether poor NIR-2 Mie score is intrinsic (absorption) or particle-size artefact |
| 19 | SCF + DFPT phonon | MgWO₄ | W-containing candidate, relevant to partner's WO₃ interest |
| 20 | SCF + DFPT phonon | WO₃ pure | Baseline for partner's doping experiments before Ti or Nb substitution |
| 21 | DFPT frequency-dependent dielectric | YZr₅O₁₁ | Optical spectrum — is it genuinely better than ZrO₂ across full 300–2500 nm? |

---

### Tier 4 — Doping Study · Highest Novelty · Est. 25–35 hrs

**Goal:** Predict effect of dopants on TiO₂ and WO₃ bandgap and NIR reflectance edge — directly guides partner's synthesis

> Build doped supercells using pymatgen `SupercellTransformation` + `SubstitutionTransformation`. All supercells: 2×2×2 of primitive cell.

| # | Calculation | Material | Dopant | Purpose |
|---|---|---|---|---|
| 22 | Supercell relax + SCF | TiO₂ rutile 2×2×2 | 3% Nb (Ti→Nb) | Bandgap shift at low doping — track NIR edge |
| 23 | Supercell relax + SCF | TiO₂ rutile 2×2×2 | 6% Nb (Ti→Nb) | Bandgap shift at higher doping — optimal doping level |
| 24 | Supercell relax + SCF | TiO₂ rutile 2×2×2 | 3% Ce (Ti→Ce) | Alternative dopant — wider gap shift predicted by screening |
| 25 | Supercell relax + SCF | TiO₂ rutile 2×2×2 | 3% N (O→N) | N-doping — known to extend visible absorption edge in literature |
| 26 | Supercell relax + SCF | ZrO₂ 2×2×2 | 5% Y (Zr→Y) | Y-stabilised ZrO₂ (YSZ) — check if stabilisation shifts optical properties |
| 27 | Supercell relax + SCF | WO₃ 2×2×2 | 5% Ti (W→Ti) | W₁₋ₓTiₓO₃ — partner's candidate, predict bandgap before synthesis |
| 28 | Supercell relax + SCF | WO₃ 2×2×2 | 5% Nb (W→Nb) | Alternative WO₃ dopant — check electrochromic vs reflective behavior |

---

### Tier 5 — Run if Budget Remains · Est. 10–15 hrs

| # | Calculation | Material | Purpose |
|---|---|---|---|
| 29 | Full phonon dispersion, 4×4×4 q-mesh | TiO₂ rutile | Higher-quality IR spectrum — publishable figure, full Brillouin zone |
| 30 | Born effective charges + full dielectric tensor | All Tier 1 materials | IR absorption intensities, not just frequencies — needed for quantitative emittance prediction |
| 31 | HSE06 single-point on Tier 1 materials | TiO₂, ZrO₂ | More accurate bandgap than PBE — validates band edges used in Mie calculations |

> **HSE06 note:** These are significantly more expensive than PBE — run only one material first to estimate actual cost before running all four.

---

## Running Order and Parallelism Strategy

```
Day 1 (Tier 1):
  Run calcs 1–3 sequentially for TiO₂ (each needs previous output)
  While TiO₂ phonon runs: start calcs 4–5 for ZrO₂ on separate cores
  Evening: launch calcs 7–8 (SiO₂ + BaSO₄) in parallel

Day 2 (validate Tier 1, launch Tier 2):
  Check Tier 1 outputs against NIST/RRUFF reference
  If validated: launch calcs 9–16 in parallel batches of 2–3 jobs
  Each job: mpirun -np 8 pw.x / ph.x (8 cores per job × 4 jobs = 32 cores fully used)

Day 3–4 (Tier 3):
  Launch calcs 17–21, YZr₅O₁₁ relax may take longer — monitor

Day 4–5 (Tier 4):
  Doping supercells — largest jobs, most cores per calculation
  Run 2 supercell jobs in parallel at 16 cores each

Day 6 (Tier 5, if budget allows):
  Full phonon dispersion + HSE06 — run overnight before auto-shutdown
```

---

## Critical Rules to Protect Budget

- **Deallocate the VM** (not just stop) between sessions — `az vm deallocate --resource-group dft-rg --name qe-dft-vm` — stopped-but-not-deallocated still charges full compute rate
- **Set Azure budget alerts** at $50, $100, $150 in Cost Management portal — [portal.azure.com](https://portal.azure.com) → Cost Management → Budgets
- **Script job chaining** so the next calculation launches automatically when the previous one finishes — no idle time between steps
- **Save all outputs to /data** (256 GB disk) not /home — if VM is rebuilt, /data persists
- **Checkpoint all QE runs** with `disk_io = 'low'` and `restart_mode = 'restart'` so a shutdown mid-run doesn't waste work
- **Run Tier 1 first** — validate physics before burning hours on Tier 3–4

---

## Output Files to Keep

For each material, the key outputs are:

| File | Contains | Keep for |
|---|---|---|
| `*.out` (pw.x SCF) | Total energy, converged wavefunction | Input to ph.x |
| `*.out` (ph.x) | Phonon frequencies, IR intensities, Born charges | Paper Section 2.5 |
| `matdyn.modes` | Mode eigenvectors | IR spectrum plot |
| `epsilon.out` | Frequency-dependent dielectric function ε(ω) | Optical spectrum n(λ), k(λ) |
| `*.xml` (charge density) | Restart files | Resume interrupted runs |

---

## What This Produces for the Paper

| Paper Section | Calculation | Status after runs |
|---|---|---|
| 2.1 Database screening | MP + JARVIS (already done) | ✅ Complete |
| 2.2 Mie scattering optimisation | Python/miepython (already done) | ✅ Complete |
| 2.3 Bimodal particle design | Python/miepython (already done) | ✅ Complete |
| 2.4 Role assignment | Mie + database (already done) | ✅ Complete |
| 2.5 IR phonon confirmation | Tier 1–2 DFPT | After Azure runs |
| 2.6 Optical spectra from first principles | Tier 2 dielectric calc | After Azure runs |
| 2.7 Doping study — bandgap tuning | Tier 4 supercells | After Azure runs |
| 3.x Experimental validation | Partner synthesis | In parallel now |

**Target journals:** Energy & Buildings · ACS Applied Materials & Interfaces · Solar Energy Materials and Solar Cells · Building and Environment

---

*All calculations use Quantum ESPRESSO with PBE functional and SSSP pseudopotentials unless noted. HSE06 only for Tier 5 bandgap validation.*
