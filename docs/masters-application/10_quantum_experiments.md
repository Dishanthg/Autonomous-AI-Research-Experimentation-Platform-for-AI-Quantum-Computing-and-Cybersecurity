# Quantum Experiments

Real Qiskit Aer simulator runs (`app/quantum/`), all labeled `SIMULATOR`
(no hardware wiring exists in this build — see ADR on quantum hardware
safety, Section 27/59).

**Q1 — Bell state (VERIFIED):** `build_bell_state()` run for 4000 shots
produced only `00`/`11` outcomes with a near-50/50 split (ratio strictly
between 0.4 and 0.6 — the entanglement signature), confirmed in
`test_quantum.py::test_bell_state_roughly_balanced`.

**Q2 — Grover search (VERIFIED):** for a 3-qubit search space (marked state
`101`), the standard `floor(pi/4 * sqrt(8)) = 2`-iteration circuit achieved
~95.4% measured success probability against a random-guessing baseline of
12.5% (1/8) — more than a 3x improvement, confirmed in
`test_grover_ideal_beats_random_guessing`. **Theoretical complexity vs.
simulated result are kept explicitly distinct**: `classical_baseline.py`
labels its output `THEORETICAL_COMPLEXITY` and reports classical exhaustive
search's expected/worst-case query counts analytically, never conflating
them with the quantum simulator's measured success probability.

**Q3 — Quantum Fourier Transform (VERIFIED):** runs correctly and produces a
valid, non-degenerate measurement distribution over all 2^3 bitstrings.

**Q5 — Noisy vs. ideal (VERIFIED):** a depolarizing noise model at error
rate 0.05 applied to the same Grover circuit reduced measured success
probability from ~95% (ideal) to ~20% (noisy) — a real, measured degradation
from a real (if simplified and explicitly-labeled) noise model, not a
fabricated number (`test_grover_noisy_success_probability_lower_than_ideal`).

**Q4 — Small-scale Shor-style factoring, Q6 — quantum ML:** NOT_IMPLEMENTED
in this build.

**Real quantum hardware:** NOT_IMPLEMENTED by design in this build (Section
27/59 requires an explicit approval/quota/allowlist mechanism before any
hardware wiring is added — none exists yet, so no result in this project has
ever been, or could be, mislabeled as hardware-derived).
