# Full Computation & Experimental Plan
## Enhanced Lime Whitewash — Passive Building Cooling
**Goal:** Computationally validate formulation → experimentally confirm → file IP  
**Rule:** Do not publish or present publicly before provisional patent is filed

---

## Part 1 — Computational Plan

> **Running on:** qe-dft-vm · Azure Standard_D32as_v5 · 32 vCPU · 128 GB RAM · $200 credit  
> **Auto-shutdown:** 22:00 UTC daily · deallocate VM between sessions, never just stop

---

### Tier 1 — Phonon Confirmation · Currently Running · Est. 20–30 hrs

**Question:** Do all four formulation components have IR-active phonon modes in the 8–13 µm atmospheric window?

| Job | Material | MP ID | Calculation Chain | Target |
|---|---|---|---|---|
| 1 | TiO₂ rutile | mp-2657 | vc-relax → SCF → DFPT phonon → dynmat | IR modes in 770–1250 cm⁻¹ |
| 2 | ZrO₂ monoclinic | mp-2858 | vc-relax → SCF → DFPT phonon → dynmat | IR modes in 770–1250 cm⁻¹ |
| 3 | SiO₂ quartz | mp-7000 | SCF → DFPT phonon → dynmat | Validate ~1100 cm⁻¹ vs NIST |
| 4 | BaSO₄ | mp-3164 | SCF → DFPT phonon → dynmat | Validate ~1100–1200 cm⁻¹ vs Purdue |

**Validation gate:** SiO₂ must show strong modes at ~1100 cm⁻¹ matching NIST data within 5% before trusting any other Tier 1 result.

**What it tells you:** Whether TiO₂ and ZrO₂ — your primary scatterers — also contribute to sky cooling. If yes, every component in your formulation is multifunctional. If no, sky cooling comes only from BaSO₄ and SiO₂, confirming the role split.

---

### Tier 2 — Full Optical Spectra · Run After Tier 1 Validated · Est. 30–40 hrs

**Question:** What are the real wavelength-dependent optical constants n(λ) and k(λ) for each component across 300–2500 nm?

| Job | Material | Calculation | Purpose |
|---|---|---|---|
| 5 | TiO₂ rutile | DFPT frequency-dependent dielectric ε(ω) | Replace constant-n Mie approximation with real n(λ), k(λ) |
| 6 | ZrO₂ monoclinic | DFPT frequency-dependent dielectric ε(ω) | Same — validate Stage 1 Mie particle size predictions |
| 7 | TiO₂ anatase | SCF + DFPT dielectric | Compare optical spectrum vs rutile — confirms phase choice |
| 8 | CaTiO₃ | Structure relax + SCF + DFPT phonon | Lime-compatible candidate — check 8–13 µm IR activity |
| 9 | Ca₂SiO₄ | SCF + DFPT phonon | Lime-compatible silicate — check atmospheric window emission |
| 10 | CaZrO₃ | SCF + DFPT phonon | Lime-compatible zirconate — JARVIS flagged IR activity, confirm |
| 11 | Ca(OH)₂ portlandite | SCF + DFPT phonon + dielectric | Does the lime binder itself emit in 8–13 µm? First time this has been calculated |
| 12 | ZrTiO₄ | Structure relax + SCF + DFPT phonon | Mixed oxide — does combining Zr and Ti give better phonon activity? |

**What it tells you:** Real optical spectra to feed into the optical simulation (Part 2). Also answers whether Ca(OH)₂ — your binder — is itself an IR emitter. If yes, your formulation has five emitting components, not two. That's a stronger IP claim.

---

### Tier 3 — Novel Candidates & Partner's WO₃ Hypothesis · Est. 25–35 hrs

**Question:** Is YZr₅O₁₁ better than ZrO₂? Does WO₃ doping make it viable?

| Job | Material | Calculation | Purpose |
|---|---|---|---|
| 13 | YZr₅O₁₁ | Structure relax + SCF + DFPT phonon + dielectric | First-ever reported optical + phonon data — does it beat ZrO₂? |
| 14 | YZr₄O₉ | SCF + DFPT phonon | Confirm if poor NIR-2 Mie score is intrinsic or particle-size artefact |
| 15 | WO₃ pure | SCF + DFPT phonon + dielectric | Baseline for partner's doping hypothesis — bandgap 2.7 eV, absorbs visible |
| 16 | MgWO₄ | SCF + DFPT phonon | W-containing, ranked well in screening, check phonon activity |

**Commercial note on YZr₅O₁₁:** Not commercially available as a pure phase. If DFT shows it beats ZrO₂, flag as future synthesis target — do not delay experiments waiting for it. ZrO₂ remains the default.

**Commercial note on WO₃:** Your partner's original hypothesis. DFT on pure WO₃ will likely confirm it absorbs visible light and is a poor reflector. The doping calculations in Tier 4 test whether this can be fixed. Run this before telling your partner to synthesise anything WO₃-based.

---

### Tier 4 — Doping Study · Directly Guides Partner's Synthesis · Est. 25–35 hrs

**Question:** Can doping TiO₂ or WO₃ push optical properties in a commercially useful direction?

> All supercells: 2×2×2 of primitive cell. Built using pymatgen SubstitutionTransformation.

| Job | Base Material | Dopant | Concentration | What You're Looking For |
|---|---|---|---|---|
| 17 | TiO₂ rutile | Nb (Ti→Nb) | 3% | Bandgap shift — does NIR absorption edge move? |
| 18 | TiO₂ rutile | Nb (Ti→Nb) | 6% | Higher doping — find optimal concentration |
| 19 | TiO₂ rutile | Ce (Ti→Ce) | 3% | Alternative dopant — wider gap shift predicted |
| 20 | TiO₂ rutile | N (O→N) | 3% | N-doping — known to modify visible absorption |
| 21 | ZrO₂ | Y (Zr→Y) | 5% | Y-stabilised ZrO₂ — does stabilisation shift optical properties? |
| 22 | WO₃ | Ti (W→Ti) | 5% | Partner's candidate — can Ti doping widen WO₃ bandgap to >3 eV? |
| 23 | WO₃ | Nb (W→Nb) | 5% | Alternative WO₃ dopant — electrochromic vs reflective behaviour |

**What it tells you:** Exact doping concentrations for your partner to synthesise. If Nb at 6% shifts TiO₂ bandgap from 3.0 to 3.4 eV, that's a specific synthesis target. If Ti-doped WO₃ at 5% reaches bandgap >3.0 eV, it becomes a new viable candidate. This is where computation most directly guides bench work.

---

### Tier 5 — High Quality + Validation · Run if Budget Remains · Est. 10–15 hrs

| Job | Material | Calculation | Purpose |
|---|---|---|---|
| 24 | TiO₂ rutile | Full phonon dispersion, 4×4×4 q-mesh | Complete IR spectrum — publishable figure, full Brillouin zone |
| 25 | All Tier 1 materials | Born effective charges + full dielectric tensor | IR absorption intensities not just frequencies — quantitative emittance prediction |
| 26 | TiO₂, ZrO₂ | HSE06 single-point | Accurate bandgap — validates PBE band edges used in Mie calculations |

> **HSE06 note:** Run one material first to estimate cost before running both. These are 3–5x more expensive than PBE jobs.

---

## Part 2 — Optical & Thermal Simulation

> **Runs after Tier 2 completes. Zero compute cost — pure Python on any laptop.**  
> **Uses DFT outputs directly. No additional Azure time needed.**

---

### Step A — Effective Medium Optical Constants

**What:** Convert individual particle optical constants into effective coating optical constants using Bruggeman effective medium theory.

**Input:** n(λ), k(λ) for each component from Tier 2 DFT outputs  
**Volume fractions for baseline formulation:**

| Component | Volume fraction |
|---|---|
| TiO₂ fine (400 nm) | 0.08 |
| TiO₂ coarse (1000 nm) | 0.06 |
| ZrO₂ (500 + 1000 nm) | 0.07 |
| BaSO₄ (1000 nm) | 0.10 |
| SiO₂ (800 nm) | 0.03 |
| Ca(OH)₂ matrix | 0.66 |

**Output:** n_eff(λ) and k_eff(λ) for the full coating mixture

**Tool:** Python, no packages beyond numpy/scipy

---

### Step B — Transfer Matrix Reflectance Simulation

**What:** Model the coating as a layered optical stack on a concrete substrate. Compute reflectance and emittance spectra.

**Stack model:**
```
Air (semi-infinite)
  ↓
Coating layer — 200 µm — n_eff(λ), k_eff(λ) from Step A
  ↓
Concrete substrate — semi-infinite — n=1.8, k=0.01
```

**Output:**
- R(λ) reflectance spectrum 300–2500 nm
- E(λ) emittance spectrum 8–13 µm
- Solar-weighted reflectance vs AM1.5 spectrum
- Comparison plot: your formulation vs plain lime (R=0.65 flat) vs Purdue BaSO₄ benchmark (R=0.981)

**Tool:** `pip install tmm` — transfer matrix method package

---

### Step C — Surface Temperature Prediction

**What:** Steady-state radiative heat balance — predicts surface temperature of coated roof under real conditions.

**Physics:**
```
Solar absorbed   = ∫ I_solar(λ) × [1 - R(λ)] dλ
Thermal emitted  = ε × σ × T_surface⁴
Sky absorbed     = ε × σ × T_sky⁴  (T_sky ≈ 250–270 K for clear sky)
Convective loss  = h × (T_surface - T_ambient)

Steady state: Solar absorbed + Sky absorbed = Thermal emitted + Convective loss
Solve for T_surface
```

**Parameter sweep:**

| Parameter | Range | Steps |
|---|---|---|
| Ambient temperature | 25–45°C | 5°C |
| Wind speed | 0–3 m/s | 0.5 m/s |
| Solar irradiance | 600–1000 W/m² | 200 W/m² |
| Coating thickness | 100–400 µm | 100 µm |

**Output:**
- Heatmap: ΔT (your formulation vs plain lime) vs ambient temperature and wind speed
- Best case / worst case / typical case temperature reduction
- Predicted indoor temperature reduction (apply 0.3–0.5 multiplier from roof surface to indoor air — literature-derived)

**This is your primary commercial result before experimental data arrives.**

---

### Step D — Composition Optimisation Simulation

**What:** Sweep component loadings computationally to find the optimal formulation before your partner mixes anything.

**Sweep space:**

| Component | Range | Steps |
|---|---|---|
| TiO₂ total loading | 10–30 wt% | 5% |
| TiO₂ fine/coarse ratio | 40/60 to 70/30 | 10% |
| BaSO₄ loading | 10–25 wt% | 5% |
| SiO₂ loading | 0–10 wt% | 2.5% |
| ZrO₂ loading | 0–15 wt% | 5% |

**Constraint:** All loadings sum to ≤60 wt% additives (remaining is lime binder, minimum 40 wt%)

**Output:**
- Ranked table of top 20 formulations by predicted solar reflectance
- Ranked table of top 20 by predicted surface temperature reduction
- Pareto front: formulations that maximise reflectance AND minimise cost simultaneously
- Top 5 formulations to test experimentally — these become your experimental matrix

**This directly tells your partner which 5 mixtures to prepare first instead of guessing.**

---

## Part 3 — Materials to Buy

> **Buy all of these before mixing. Verify particle size with supplier datasheet or SEM if available.**

### Primary Components

| Material | Specification | Why This Grade | Supplier Options | Approx. Cost |
|---|---|---|---|---|
| **TiO₂ rutile (fine)** | 99% rutile phase, d50 = 300–450 nm | Rutile not anatase — higher n, more stable | Sigma-Aldrich 224227 · Kronos 2310 · Tayca MT-100 | $15–40/kg |
| **TiO₂ rutile (coarse)** | 99% rutile, d50 = 900–1200 nm | Coarse fraction for NIR-2 coverage | Sigma-Aldrich 204757 · US Research Nanomaterials | $20–50/kg |
| **ZrO₂** | ≥99%, d50 = 400–600 nm, monoclinic phase | Monoclinic — matches your DFT structure | Sigma-Aldrich 544760 · US Research Nanomaterials TR-ZR-02 | $25–60/kg |
| **BaSO₄** | ≥99%, d50 = 800–1200 nm, precipitated grade | Precipitated = purer and more controlled size than barite ore | Sigma-Aldrich 243353 · Solvay Blanc Fixe N | $5–15/kg |
| **SiO₂** | Fumed silica, d50 = 700–900 nm, hydrophilic | Fumed = high purity, controlled particle size | Sigma-Aldrich S5505 · Evonik AEROSIL 200 | $10–20/kg |
| **Ca(OH)₂** | ≥95% slaked lime, construction grade | Construction grade is fine — no need for analytical grade | Local builders merchant · Sigma-Aldrich 239232 | $0.10–0.50/kg |

### Optional / Tier 4 Doping Study

| Material | Specification | Purpose | Supplier |
|---|---|---|---|
| **Nb₂O₅** | ≥99.5%, fine powder | Precursor for Nb-doped TiO₂ synthesis | Sigma-Aldrich 203920 |
| **CeO₂** | ≥99%, nanopowder | Precursor for Ce-doped TiO₂ | Sigma-Aldrich 544841 |
| **WO₃** | ≥99.9%, powder | Your partner's original candidate — test pure first | Sigma-Aldrich 206831 |
| **Y₂O₃** | ≥99.99%, nanopowder | For YSZ synthesis if YZr₅O₁₁ DFT result is promising | Sigma-Aldrich 204927 |

### Equipment Needed

| Item | Purpose | Source |
|---|---|---|
| **IR thermometer** (±0.5°C accuracy) | Surface temperature measurement | Amazon / local electronics — $20–50 |
| **Concrete roof tiles** (≥10 identical) | Substrate for all experiments | Local builders merchant — near zero cost |
| **Precision balance** (±0.01g) | Accurate formulation mixing | Lab supply or Amazon — $30–100 |
| **Paintbrushes** (25 mm, flat) | Coating application | Hardware store |
| **Mixing containers** (100–500 mL) | Formulation preparation | Hardware store |
| **UV-Vis-NIR spectrometer** (300–2500 nm) | Measure actual reflectance spectrum | University instrument loan · Ideally integrating sphere accessory |
| **Digital thermometer logger** | Continuous temperature recording | Amazon — $20–50 |
| **Vernier caliper or thickness gauge** | Measure dry coating thickness | Hardware store — $10–20 |

> **Spectrometer note:** If your institution doesn't have a UV-Vis-NIR with integrating sphere, contact your nearest materials engineering or chemistry department. This is the one instrument you cannot substitute — it's essential for validating reflectance computationally predicted. A UV-Vis without integrating sphere is not sufficient for diffuse reflectance measurement of coatings.

---

## Part 4 — Experimental Plan

---

### Experiment 0 — Baseline Characterisation (Before Anything Else)

**Purpose:** Establish what plain lime whitewash actually achieves on your specific tiles and lime source. Every other experiment is measured against this.

**What to do:**
- Apply standard lime whitewash (lime + water only, brushed to 150–200 µm dry thickness) to 3 tiles
- Measure surface temperature every 30 min from 9am to 4pm, outdoor direct sun
- Measure with spectrometer if available — record R(λ) from 300–2500 nm
- Record ambient temperature, wind conditions, cloud cover for every measurement session
- Photograph tiles before and after

**Why this matters:** The Athens 2008 paper measured lime at ~65% solar reflectance. Your lime from your local source in your climate may differ. You need your own baseline, not literature values.

---

### Experiment 1 — Single Component Addition (Week 1)

**Purpose:** Understand what each additive contributes individually before combining them.

**Formulations to test:**

| Mix | Composition | Tests |
|---|---|---|
| A | Lime only (baseline) | Temperature, reflectance |
| B | Lime + TiO₂ fine 20 wt% | Does fine TiO₂ alone improve NIR? |
| C | Lime + TiO₂ coarse 20 wt% | Does coarse TiO₂ alone improve NIR-2? |
| D | Lime + BaSO₄ 20 wt% | Does BaSO₄ alone reduce temperature? |
| E | Lime + SiO₂ 10 wt% | Does SiO₂ alone contribute? |
| F | Lime + ZrO₂ 20 wt% | How does ZrO₂ compare to TiO₂ individually? |

**What to record:** Surface temperature (every 30 min, 9am–4pm), tile appearance, coating uniformity, any cracking or delamination after drying.

**What it tells you:** Which single additive gives the biggest temperature drop. This validates or challenges the Mie scattering rankings from your computational screening. TiO₂ should outperform ZrO₂ slightly (Q=3.24 vs 3.19). BaSO₄ alone should give minimal temperature improvement (low Mie Q) but may show effect in long IR. If BaSO₄ alone gives a measurable temperature drop, that confirms sky cooling is active even without the scattering contribution.

---

### Experiment 2 — Bimodal vs Monomodal (Week 1–2)

**Purpose:** Validate the key computational finding — that bimodal particle size distribution outperforms a single particle size.

| Mix | Composition | Tests |
|---|---|---|
| G | Lime + TiO₂ fine only, 20 wt% (400 nm) | Single size baseline |
| H | Lime + TiO₂ coarse only, 20 wt% (1000 nm) | Single size coarse |
| I | Lime + TiO₂ bimodal 20 wt% (12% fine + 8% coarse) | Computationally optimised |
| J | Lime + ZrO₂ bimodal 20 wt% (12% fine + 8% coarse) | ZrO₂ equivalent |

**What it tells you:** Whether the bimodal distribution actually outperforms single-size experimentally. This is your most important computational prediction to validate. If Mix I outperforms Mix G and H, the computational optimisation is confirmed. If not, the Mie model needs revision.

---

### Experiment 3 — Composition Matrix (Week 2–3)

**Purpose:** Find the optimal loading of each component. This is your core IP experiment — the composition that performs best is what you patent.

Use the top 5 formulations from Step D optical simulation as starting points, then expand around the best performer.

**Phase 1 — Simulate first, then test these 8 formulations:**

| Mix | TiO₂ (wt%) | ZrO₂ (wt%) | BaSO₄ (wt%) | SiO₂ (wt%) | Lime (wt%) |
|---|---|---|---|---|---|
| K | 20 (bimodal) | 0 | 15 | 5 | 60 |
| L | 20 (bimodal) | 0 | 20 | 5 | 55 |
| M | 15 (bimodal) | 10 (bimodal) | 15 | 5 | 55 |
| N | 15 (bimodal) | 10 (bimodal) | 20 | 5 | 50 |
| O | 25 (bimodal) | 0 | 20 | 5 | 50 |
| P | 20 (bimodal) | 5 (bimodal) | 20 | 5 | 50 |
| Q | 20 (bimodal) | 0 | 20 | 10 | 50 |
| R | 15 (bimodal) | 0 | 25 | 5 | 55 |

**Phase 2 — Once best performer from Phase 1 identified:**
Run 5 additional formulations varying ±5 wt% around the winner in each component. This narrows the optimal composition to ±2.5 wt% precision — sufficient for patent claims.

**What to record for each mix:**
- Surface temperature at peak solar (12pm–2pm)
- Temperature reduction vs Experiment 0 baseline
- Visual appearance — whiteness, uniformity, coverage
- Wet viscosity — is it brushable? Does it sag or drip?
- Dry time — how long until surface is dry to touch?

---

### Experiment 4 — Durability (Run in Parallel with Experiment 3)

**Purpose:** Patent claims for a building coating must address durability. Paint companies will ask this immediately.

**Tests to run on your best performing mix from Experiment 3:**

| Test | Protocol | What you're checking |
|---|---|---|
| Rain simulation | 10 cycles of water spray (2 min) + dry (30 min) | Does coating wash off? Does reflectance change? |
| UV ageing | Leave coated tiles in direct sun for 30 days | Does whiteness degrade? Does TiO₂ photocatalyse lime? |
| Temperature cycling | 5 cycles of 5°C → 60°C → 5°C (oven + fridge) | Does coating crack or delaminate on thermal expansion? |
| Mechanical adhesion | Tape test (cross-hatch per ASTM D3359) | Does coating adhere adequately to concrete? |
| Wet scrub | 10 passes with damp cloth | Is the coating fragile when wet? |

**Measurement:** Photograph + IR thermometer reading before and after each test. Spectrometer measurement if available.

**Commercial importance:** A paint company licensing your IP needs to know the coating lasts at least one monsoon season. Even basic durability data from 30 days of testing is better than nothing.

---

### Experiment 5 — Real Building Simulation (Week 3–4)

**Purpose:** Move from tiles to something that represents actual building conditions.

**Setup:**
- Build or source two identical small concrete boxes (30×30×30 cm, open top, concrete walls 5 cm thick) — represents a simplified room
- Apply plain lime to Box 1, best formulation from Experiment 3 to Box 2
- Cover top with identical concrete lid coated accordingly
- Place a small temperature logger inside each box
- Place both outdoors in direct sun, same orientation
- Record internal air temperature every 15 minutes for 3 consecutive clear days

**What it tells you:** The indoor temperature difference between the two boxes. This is the number that matters commercially — not surface temperature reduction, but indoor air temperature reduction. This is what you tell paint companies and what you put in your patent: "reduces indoor temperature by X°C under Y conditions."

**Expected result:** Based on literature, surface temperature reduction of 8–12°C from a well-performing PDRC coating translates to roughly 2–5°C indoor air temperature reduction in a poorly insulated concrete structure. If you achieve 3°C+ indoor reduction, that's enough to make a ceiling fan effective in conditions where plain lime whitewash fails.

---

### Experiment 6 — Application Method (Week 4)

**Purpose:** Confirm the coating can be applied by an unskilled person with a standard brush, which is essential for developing-world deployment.

**Tests:**
- Apply coating at 100 µm, 200 µm, 300 µm dry thickness — does performance scale with thickness?
- Apply by brush vs roller vs spray — does application method affect uniformity and performance?
- Apply on wet concrete vs dry concrete — does substrate moisture matter?
- Apply single coat vs double coat — is double coat significantly better?

**What it tells you:** Optimal coating thickness and application instructions for the patent. Also tells you whether the product needs professional application or is genuinely self-applicable.

---

## Part 5 — Decision Points

After each experiment, make an explicit go/no-go decision before proceeding.

```
After Experiment 1:
  Does any single additive reduce surface temp by >3°C vs baseline?
  YES → proceed to Experiment 2
  NO  → re-examine particle size specs, check dispersion quality, 
         possibly revisit computational assumptions

After Experiment 2:
  Does bimodal outperform single-size by measurable margin (>1°C)?
  YES → computational prediction confirmed, proceed to Experiment 3
  NO  → re-examine whether particle sizes were correctly specified 
         by supplier (SEM check if possible)

After Experiment 3:
  Does best formulation reduce surface temp by >6°C vs plain lime?
  YES → proceed to Experiments 4, 5, 6 in parallel
  NO  → revisit loading ratios, check for agglomeration issues

After Experiment 5:
  Does best formulation reduce indoor temp by >2°C consistently?
  YES → file provisional patent, approach paint companies
  NO  → analyse heat balance — is the issue reflectance, emittance, 
         or building thermal mass? Adjust formulation or setup.
```

---

## Part 6 — What the Computational + Experimental Results Together Give You

| What you'll have | Why it matters commercially |
|---|---|
| Predicted reflectance spectrum (DFT + optical simulation) | Technical basis for patent claims — specific performance thresholds |
| Predicted surface temperature reduction by ambient/wind conditions | Sales tool for paint companies — performance envelope |
| Confirmed phonon modes for all components (Tier 1 DFT) | Explains why the formulation works — patent specification language |
| Doping study results for TiO₂ and WO₃ (Tier 4) | Next-generation IP — improved formulations your partner can synthesise |
| Measured reflectance spectrum of best formulation | Validates computational prediction — essential for patent |
| Measured surface temperature reduction (Experiments 1–3) | Core experimental claim in patent |
| Measured indoor temperature reduction (Experiment 5) | Commercial headline number |
| Durability data (Experiment 4) | Answers first question any paint company asks |
| Composition range that works (Experiment 3 Phase 2) | Defines patent claim breadth — too narrow is easy to design around |

---

## Part 7 — IP Filing Checklist

**Before filing provisional patent:**
- [ ] Experiments 1–3 complete with documented temperature data
- [ ] At least one formulation shows >5°C surface temperature reduction vs plain lime
- [ ] Composition range tested sufficiently to define claim boundaries
- [ ] Lab notebook with dated entries for all experimental work
- [ ] No public disclosure, presentations, or preprints filed

**Provisional patent contents:**
- [ ] Full formulation description including component ranges
- [ ] Particle size specifications for each component
- [ ] Application method description
- [ ] Experimental temperature reduction data
- [ ] Computational backing for particle size choices (Mie optimisation)
- [ ] Claims distinguishing from: lime alone, polymer-binder systems, single-pigment systems

**Target patent attorneys:** Search for patent attorneys specialising in coatings, construction materials, or green building technology. Many offer free initial consultations.

---

*Document version 1.0 · Internal use only · Do not distribute before provisional patent filing*
