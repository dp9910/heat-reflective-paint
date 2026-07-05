# Enhanced Lime Whitewash — Passive Building Cooling
## Computation, Formulation & Experimental Plan
**Goal:** Computationally derive formulation → experimentally validate → file IP  
**Rule:** No public disclosure before provisional patent is filed

---

## How We Arrived at the Formulation

We screened 784 inorganic oxide candidates from Materials Project and JARVIS databases, filtering for wide bandgap (>2.5 eV), earth abundance, and no toxic elements. This gave 94 candidates. We then ran Mie scattering calculations for each in a Ca(OH)₂ matrix across eight particle sizes and the full AM1.5 solar spectrum, which ranked TiO₂ as the strongest scatterer and revealed that BaSO₄ and SiO₂ have too little optical contrast with lime to scatter effectively. DFPT phonon calculations confirmed which components emit in the 8–13 µm atmospheric window — only SiO₂ and BaSO₄ — cleanly separating the formulation into a scattering system (TiO₂ + ZrO₂) and a sky cooling system (BaSO₄ + SiO₂). A bimodal particle size optimisation then showed that a single particle size leaves 1400–2500 nm underserved, and that combining fine + coarse fractions recovers full spectral coverage. Finally, a 144-formulation composition sweep using Kubelka-Munk scattering theory identified optimal weight loadings, with lime constrained to 40 wt% minimum for brushability and adhesion.

---

## DFT Results

### Optical Constants

| Material | n (DFT) | n (Expt) | Error | Role |
|---|---|---|---|---|
| TiO₂ rutile | 2.80 | 2.90 | −3% | Primary NIR scatterer |
| ZrO₂ monoclinic | 2.29 | 2.1–2.2 | +4% | Secondary NIR scatterer |
| SiO₂ quartz | 1.57 | 1.54–1.55 | +1.5% | IR emitter only |
| BaSO₄ | 1.678 | 1.634–1.648 | +2% | IR emitter only |
| Ca(OH)₂ | 1.630 | 1.545–1.574 | +4% | Binder |

> **Key correction:** JARVIS reported n=2.09 for SiO₂ (a high-pressure polymorph) and n=1.763 for BaSO₄. DFT corrected both. At n=1.57, SiO₂ is actually lower refractive index than the lime matrix (n=1.63) — it cannot scatter. This collapsed SiO₂ Mie Q from 2.92 to 0.156 (19× drop) and removed it entirely from the scattering role. All Mie calculations use DFT-confirmed n values.

### Phonon Results — 8–13 µm Atmospheric Window (770–1250 cm⁻¹)

| Material | Modes in window | Sky cooling | Note |
|---|---|---|---|
| SiO₂ quartz | 1081, 1091 cm⁻¹ (intensity 42–44) | ✅ Strong | NIST validated to 0.1% — confirms DFT setup reliable |
| BaSO₄ | 1080–1180 cm⁻¹ | ✅ Strong | Matches Purdue 2021 literature |
| TiO₂ rutile | Highest mode 516 cm⁻¹ | ❌ None | Literature confirmed · DFT completing as record |
| ZrO₂ monoclinic | Highest mode 732 cm⁻¹ | ❌ None | DFT confirmed |
| Ca(OH)₂ | Highest mode 604 cm⁻¹ | ❌ None | Transparent in window — ideal binder behaviour |

**The lime binder is transparent in the 8–13 µm window.** It neither absorbs nor competes with sky cooling emission from BaSO₄ and SiO₂. This is explicitly claimable in the patent.

---

## Mie Scattering & Particle Size Optimisation

Using DFT-confirmed n values and corrected matrix index (n_matrix = 1.63), we ran Mie scattering calculations across 300–2500 nm and particle diameters 100–3000 nm, weighted by the AM1.5 solar spectrum.

**Single-size rankings at d_opt:**

| Material | Q_solar | d_opt | Notes |
|---|---|---|---|
| TiO₂ rutile | 3.226 | 400 nm | Clear leader |
| ZrO₂ monoclinic | 2.990 | 600 nm | d_opt shifted from initial screening due to corrected n |
| SiO₂ | 0.156 | 1000 nm | Removed from scattering role |
| BaSO₄ | 0.109 | 1000 nm | Removed from scattering role |

**Bimodal optimisation:** All candidates fell below NIR2/NIR1 = 0.5 at single particle size — the 1400–2500 nm band was systematically underserved because AM1.5-weighted optimisation favours smaller particles peaking in NIR-1. Adding a coarse fraction sized for NIR-2 resolved this. Both TiO₂ and ZrO₂ met the NIR2/NIR1 > 0.6 target:

| Material | d_small | d_large | NIR2/NIR1 | Q_solar |
|---|---|---|---|---|
| TiO₂ | 400 nm | 1000 nm | 0.705 | 3.008 |
| ZrO₂ | 600 nm | 1400 nm | 0.692 | 2.842 |

**ZrO₂ verdict:** Including ZrO₂ gives 18.9% higher K_solar than TiO₂ alone (16.14 vs 13.57). TiO₂ fine (400 nm) peaks in visible/NIR-1. ZrO₂ coarse (1400 nm) fills NIR-2. The combination covers 300–2500 nm more evenly than either alone.

---

## Final Formulation — Five Experimental Variants

Derived from a 144-formulation Kubelka-Munk composition sweep. Lime minimum 40 wt% confirmed by sweep — optimiser pushed lime to floor in every top-10 result.

| Code | TiO₂ | Fine/Coarse | ZrO₂ | BaSO₄ | SiO₂ | Lime | Purpose |
|---|---|---|---|---|---|---|---|
| **ELW-1** | 30% | 70/30 | 10% | 15% | 5% | 40% | Best overall predicted performance |
| **ELW-2** | 30% | 70/30 | 5% | 20% | 5% | 40% | Sky cooling emphasis — higher BaSO₄ |
| **ELW-3** | 25% | 70/30 | 15% | 15% | 5% | 40% | NIR-2 emphasis — higher ZrO₂ |
| **ELW-4** | 30% | 50/50 | 10% | 15% | 5% | 40% | Best NIR-2/NIR-1 balance (ratio 0.555) |
| **ELW-C** | 30% | 70/30 | 0% | 20% | 5% | 45% | Control — validates ZrO₂ benefit experimentally |

---

## Materials to Buy

| Material | Specification | Qty | Supplier |
|---|---|---|---|
| TiO₂ rutile fine | ≥99% rutile, d50 = 350–450 nm | 500 g | Sigma-Aldrich 224227 · Kronos 2310 |
| TiO₂ rutile coarse | ≥99% rutile, d50 = 900–1100 nm | 300 g | Sigma-Aldrich 204757 |
| ZrO₂ fine | ≥99% monoclinic, d50 = 550–650 nm | 300 g | Sigma-Aldrich 544760 |
| ZrO₂ coarse | ≥99%, d50 = 1300–1500 nm | 200 g | Ball mill from coarse grade if not available |
| BaSO₄ precipitated | ≥99%, d50 = 800–1200 nm | 500 g | Sigma-Aldrich 243353 · Solvay Blanc Fixe N |
| SiO₂ fumed | Hydrophilic, d50 = 200–400 nm | 200 g | Sigma-Aldrich S5505 · Evonik AEROSIL 200 |
| Ca(OH)₂ slaked lime | ≥95%, construction grade | 2 kg | Local builders merchant |
| Concrete roof tiles | Identical, 30×30 cm | 20 pieces | Local builders merchant |
| Galvanised steel sheet | 0.5 mm, 30×30 cm | 15 pieces | Local steel merchant |
| Sodium silicate solution | 37–40% waterglass | 500 mL | Chemical supplier — metal adhesion |

**Equipment:** IR thermometer (±0.5°C) · precision balance (±0.01 g) · 4× temperature loggers · UV-Vis-NIR spectrometer with integrating sphere (borrow — essential)

---

## Experimental Plan

**Mixing protocol:** Weigh dry components separately → pre-mix dry pigments → add lime → add water gradually (~60–80 mL per 100 g dry) → mix 3 min → rest 5 min → apply immediately. Two coats, target 150–200 µm dry. For steel: add sodium silicate (10 wt%) before water.

**Experiment 0 — Baseline:** Plain lime on concrete and steel tiles. Surface temperature 9am–4pm. Spectrometer R(λ). All results are delta from this — do not use literature values as baseline.

**Experiment 1 — Single components:** Each additive alone at 20 wt% in lime. Validates DFT predictions: TiO₂ bimodal should outperform single-size. BaSO₄ alone should show temperature effect without meaningful reflectance change (sky cooling only). SiO₂ alone should show negligible improvement — confirms it cannot scatter in lime.

**Experiment 2 — Five ELW formulations:** Run ELW-1 through ELW-C simultaneously on the same day. Measure surface temperature at 10am, 1pm, 3pm for minimum 3 clear days. Key comparison: ELW-1 vs ELW-C validates ZrO₂ benefit — DFT predicts 18.9% better scattering.

**Experiment 3 — Composition refinement:** Best performer from Experiment 2 gets 5 variants at ±5 wt% per component. Narrows optimal composition to ±2.5 wt% — sufficient for patent claim ranges.

**Experiment 4 — Durability (parallel):** Best formulation on concrete and steel. Rain simulation (10 cycles) · UV ageing (30 days) · thermal cycling (steel: 15°C–80°C, 20 cycles) · tape adhesion test ASTM D3359. Pass criterion: <5% reflectance loss, no delamination.

**Experiment 5 — Box test:** Two identical 30×30×30 cm boxes, concrete and steel. Box 1: plain lime. Box 2: best ELW. Temperature logger inside. Log every 15 min for 3 clear days. **This gives the indoor temperature reduction — the commercial headline figure for paint companies.**

---

## Decision Gate for IP Filing

```
Box test indoor ΔT > 4°C consistently across 3 days
  → File provisional patent immediately
  → Approach Asian Paints, Berger, Nippon Paint, Kansai Nerolac

Box test ΔT < 4°C
  → Check spectrometer R(λ) — is scattering performing as predicted?
  → Check night-time ΔT — is sky cooling active?
  → Adjust BaSO₄ or TiO₂ loading and retest before filing
```

---

*Internal use only · Do not distribute before provisional patent filing*
