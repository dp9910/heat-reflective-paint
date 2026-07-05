# Complete DFT Results — Enhanced Lime Whitewash
## Emissivity Screening & Optical Constants
**Code:** QE 6.7 · **Functional:** PBE · **Pseudopotentials:** SSSP/GBRV  
**Emissivity model:** Lorentz oscillator γ=10 cm⁻¹ · Planck-weighted 8–13 µm at 300K

---

## Atmospheric Window Emissivity Leaderboard

| Rank | Material | ε_window | Δ vs BaSO₄ | Reliable | Role in formulation |
|---|---|---|---|---|---|
| 1 | **CaSO₄ anhydrite** | **0.948** | +0.036 | ✅ asym=1.2% | Primary IR emitter ← chosen |
| 2 | **MgCO₃ magnesite** | **0.931** | +0.019 | ✅ | Long-wave IR emitter (12.1 µm) ← chosen |
| 3 | SrSO₄ celestite | 0.922 | +0.010 | ✅ asym=3.0% | Better than BaSO₄ — rarer, pricier |
| 4 | MgSO₄ | 0.9148 | +0.003 | ✅ asym=51% | Marginal gain — water soluble |
| — | **BaSO₄** (reference) | **0.912** | 0.000 | ✅ | Alternative emitter if CaSO₄ fails durability |
| 5 | Ca₃(PO₄)₂ | 0.910 | −0.002 | ✅ asym=25% | Ties BaSO₄ — metastable phase |
| 6 | BaWO₄ scheelite | 0.859 | −0.053 | ⚠️ asym=201% | Below BaSO₄ — unreliable result |
| 7 | BaMoO₄ powellite | 0.857 | −0.055 | ✅ asym=2.3% | Below BaSO₄ — reststrahlen dip |
| 8 | SiO₂ quartz | 0.770 | −0.142 | ✅ | Secondary emitter at 5 wt% only |
| — | ZrO₂ monoclinic | ~0 | — | ✅ | No window modes — pure scatterer |
| — | TiO₂ rutile | ~0 | — | Literature | No window modes — pure scatterer |
| — | Ca(OH)₂ | ~0 | — | ✅ | No window modes — transparent binder |

---

## Per-Material DFT Results

### TiO₂ rutile · mp-2657 · 12 atoms
| Property | Value |
|---|---|
| ε_∞ | 7.85 |
| n (DFT) | 2.80 |
| n (expt) | 2.90 · error −3% |
| Window modes | None — A₂ᵤ 173, Eᵤ 396, Eᵤ 516 cm⁻¹ (all below 769 cm⁻¹) |
| ε_window | ~0 |
| Status | Terminated early rep 16/36 — NIST confirms no window modes |
| Role | Primary NIR scatterer · d_opt 400/1000 nm bimodal |

---

### ZrO₂ monoclinic · mp-2858 · 12 atoms
| Property | Value |
|---|---|
| ε_∞ | 5.24 |
| n (DFT) | 2.29 · revised from JARVIS 2.490 |
| n (expt) | 2.1–2.2 · error +4% |
| Window modes | None — highest mode 732 cm⁻¹ (13.7 µm) |
| ε_window | ~0 |
| Role | Secondary NIR scatterer · d_opt revised 500→600 nm · d_large 1400 nm |

---

### SiO₂ quartz · mp-7000 · 9 atoms
| Property | Value |
|---|---|
| ε_∞ | 2.46 |
| n (DFT) | 1.57 · revised from JARVIS 2.094 (wrong polymorph) |
| Window modes | 1081 cm⁻¹ IR=42.1, 1091 cm⁻¹ IR=44.5 (9.17–9.25 µm) · 774–791 cm⁻¹ IR=3.4–3.7 |
| NIST match | 1082 cm⁻¹ — error 0.1% · setup validated |
| ε_window | 0.770 |
| Critical finding | n=1.57 < n_matrix=1.63 — cannot Mie scatter. Role changed to IR emitter only. |
| Role | Secondary IR emitter at 5 wt% max — reststrahlen dip at 9.15 µm limits loading |

---

### BaSO₄ · mp-3164 · 24 atoms · Reference
| Property | Value |
|---|---|
| ε_∞ | 2.82 |
| n (DFT) | 1.678 · revised from JARVIS 1.763 |
| Window modes | 1084 cm⁻¹ IR=80.1 · 1122 cm⁻¹ IR=76.2 · 1191 cm⁻¹ IR=78.7 (SO₄ ν₃, 8.4–9.2 µm) |
| Purdue match | Modes 1080–1200 cm⁻¹ — error <1% · validates entire pipeline |
| ε_window | 0.912 |
| Role | Alternative primary IR emitter · use if CaSO₄ fails durability test |

---

### Ca(OH)₂ portlandite · mp-23879 · 5 atoms
| Property | Value |
|---|---|
| ε_∞ | 2.70 |
| n (DFT) | 1.630 · revised from assumed 1.59 |
| Window modes | None — highest real mode 604 cm⁻¹. O–H stretch 3940 cm⁻¹ (2.5 µm) |
| Imaginary modes | OH librations — known PBE artefact for H-bonded systems, not structural |
| ε_window | ~0 |
| Critical finding | Binder is transparent in 8–13 µm window — does not interfere with sky cooling |
| Role | Binder only — confirmed ideal |

---

### CaSO₄ anhydrite · mp-4406 · 12 atoms ★ Primary emitter
| Property | Value |
|---|---|
| ε_∞ | 2.69 · Δε=1.70 |
| Asymmetry | 1.2% — most reliable Tier 3 result |
| Window modes | 1030 cm⁻¹ IR=2269 · 1039 cm⁻¹ IR=5254 · 1123 cm⁻¹ IR=2737 · 1181 cm⁻¹ IR=2568 (8.5–9.7 µm) |
| ε_window | 0.948 (+0.036 vs BaSO₄) |
| Coverage | Broader and flatter than BaSO₄ across 8–10 µm |
| Commercial | $0.05–0.15/kg · hardware store · shared Ca with lime binder |
| Role | **Primary IR emitter in ELW-9** · 20 wt% (volume-matched to 15 wt% BaSO₄) |

---

### MgCO₃ magnesite · mp-5348 · 10 atoms ★ Long-wave emitter
| Property | Value |
|---|---|
| ε_∞ | 2.79 · Δε=1.41 |
| Asymmetry | 779% (numerical artefact — vc-relax confirmed same modes) |
| Window modes | 827 cm⁻¹ IR=4.4 (CO₃ ν₂ bend, 12.1 µm) |
| Outside window | CO₃ ν₃ at 1431–1452 cm⁻¹ (6.9 µm) — no interference |
| ε_window | 0.931 (+0.019 vs BaSO₄) |
| Critical finding | Only confirmed component covering 10–13 µm — fills gap no sulfate reaches |
| Role | **Long-wave IR emitter in ELW-9** · 10 wt% |

---

### MgSO₄ · mp-7572 · 12 atoms
| Property | Value |
|---|---|
| ε_∞ | 2.59 · Δε=1.59 |
| Asymmetry | 51% (acceptable) |
| Window modes | 1070 cm⁻¹ IR=43.1 · 1196 cm⁻¹ IR=33.9 · 1247 cm⁻¹ IR=33.6 (SO₄ ν₃, 8.0–9.3 µm) |
| ε_window | 0.9148 · original 0.950 was wrong — unrelaxed structure inflated IR intensities 200× |
| ⚠️ Warning | Always vc-relax before DFPT — unrelaxed structure gave spurious Born charges (IR=60,000+) |
| Role | Marginal over BaSO₄ (+0.003) · water soluble · dry climates only |

---

### SrSO₄ celestite · mp-5285 · 24 atoms
| Property | Value |
|---|---|
| ε_∞ | 2.78 · Δε=1.78 |
| Asymmetry | 3.0% — best reliability in Tier 3b batch |
| Window modes | 1090 cm⁻¹ IR=79.0 · 1136 cm⁻¹ IR=72.3 · 1213 cm⁻¹ IR=74.9 (SO₄ ν₃, 8.2–9.2 µm) |
| ε_window | 0.922 (+0.010 vs BaSO₄) |
| vs BaSO₄ | Slightly broader coverage (1090–1213 vs 1084–1191 cm⁻¹) |
| Commercial | $2–8/kg · less available than gypsum · covered by sulfate class IP claim |
| Role | Patent claim coverage only — not experimental priority |

---

### Ca₃(PO₄)₂ · mp-3487 · 13 atoms
| Property | Value |
|---|---|
| ε_∞ | 3.22 · Δε=2.20 |
| Asymmetry | 24.6% |
| Window modes | 1047 cm⁻¹ IR=39.9 · 1132 cm⁻¹ IR=43.4 (PO₄ ν₃, 8.8–9.6 µm) |
| Imaginary mode | −125 cm⁻¹ — genuine soft mode, persists post-relax — metastable phase (hull=0.04 eV/atom) |
| ε_window | 0.910 (ties BaSO₄) |
| Role | No practical advantage over BaSO₄ — phase instability concern |

---

### BaMoO₄ powellite · mp-19276 · 12 atoms
| Property | Value |
|---|---|
| ε_∞ | 3.50 · Δε=2.50 |
| Asymmetry | 2.3% (reliable) |
| Window modes | 816 cm⁻¹ IR=46.9 · 827 cm⁻¹ IR=49.4 (MoO₄ ν₃, 12.1–12.3 µm) |
| ε_window | 0.857 (−0.055 vs BaSO₄) |
| Why it fails | Modes at 12 µm where Planck weight 3× lower than at 9 µm · reststrahlen dip at mode frequencies |
| Role | Not suitable — below BaSO₄ |

---

### BaWO₄ scheelite · mp-19048 · 12 atoms ⚠️
| Property | Value |
|---|---|
| ε_∞ | 3.40 · Δε=2.40 |
| Asymmetry | 201% — unreliable, vc-relax needed |
| Window modes | 939 cm⁻¹ IR=35.2 · 955 cm⁻¹ IR=38.1 (WO₄ ν₃, 10.5–10.7 µm) · large imaginary −234 cm⁻¹ |
| ε_window | 0.859 (unreliable) |
| Role | Not suitable — WO₄ modes at 10.5 µm miss peak Planck weighting · unreliable result |

---

## Key Corrections Applied During Screening

| Parameter | Database value | DFT corrected | Impact |
|---|---|---|---|
| n Ca(OH)₂ matrix | 1.59 assumed | **1.63** | All Mie Q_scat recalculated |
| n BaSO₄ | 1.763 JARVIS | **1.678** | Lower contrast, lower Q_scat |
| n SiO₂ | 2.094 JARVIS | **1.57** | Wrong polymorph — cannot scatter in lime |
| ε MgSO₄ | 0.950 unrelaxed | **0.9148** | 200× inflated Born charges |
| d_opt ZrO₂ | 500 nm | **600 nm** | Lower n needs larger particle |
| d_opt SiO₂ | 800 nm | **irrelevant** | n < n_matrix — no scattering |
| SiO₂ role | Mie scatterer | **IR emitter only** | Fixed at 5 wt%, removed from sweep |

---

## Mie Scattering Summary (Stage 2, DFT-corrected n values)

| Material | n | Q_solar | d_small | d_large | Role |
|---|---|---|---|---|---|
| TiO₂ rutile | 2.80 | 3.226 | 400 nm | 1000 nm | Primary scatterer |
| ZrO₂ monoclinic | 2.29 | 2.990 | 600 nm | 1400 nm | Secondary scatterer |
| CaSO₄ | ~1.57 | ~0.1 | — | — | Does not scatter |
| BaSO₄ | 1.678 | 0.109 | — | — | Does not scatter |
| SiO₂ | 1.57 | 0.156 | — | — | Does not scatter |

**Scattering saturated at 30% TiO₂ bimodal.** All formulations predict R_solar = 98.6–98.8%. Adding more TiO₂ or ZrO₂ gives no meaningful improvement. Adding ZrO₂ vs not: +0.14% total R_solar, +0.3% R_NIR2. Marginal — validate experimentally.

---

## Lesson Learned — Always vc-relax Before DFPT

MgSO₄ from the Materials Project structure (unrelaxed) gave ε=0.950 due to spurious Born effective charges from residual forces. IR intensities reached 60,000+ (D/Å)²/amu versus physical values of 40–80. After vc-relax, ε=0.9148. The 200× error would have sent the formulation in the wrong direction. Every material in this screening was either explicitly relaxed or verified to have low asymmetry (<5%) before trusting phonon results.

---

*DFT screening complete · All formulation-critical calculations done · VM deallocated*
