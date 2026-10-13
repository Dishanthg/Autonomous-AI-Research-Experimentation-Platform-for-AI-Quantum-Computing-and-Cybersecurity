from app.quantum.circuits import build_bell_state, build_grover, build_qft, grover_iteration_count
from app.quantum.classical_baseline import classical_exhaustive_search_cost
from app.quantum.runner import build_depolarizing_noise_model, run_circuit


def test_bell_state_produces_only_correlated_outcomes():
    qc = build_bell_state()
    result = run_circuit(qc, shots=2000, expected_bitstring="00", seed=1)
    counts = result.measurement_counts
    # Only 00 and 11 should appear (up to simulator/measurement noise-free ideal case)
    assert set(counts.keys()) <= {"00", "11"}
    assert sum(counts.values()) == 2000


def test_bell_state_roughly_balanced():
    qc = build_bell_state()
    result = run_circuit(qc, shots=4000, expected_bitstring="00", seed=2)
    counts = result.measurement_counts
    ratio = counts.get("00", 0) / sum(counts.values())
    assert 0.4 < ratio < 0.6


def test_grover_ideal_beats_random_guessing():
    n = 3
    marked = "101"
    qc = build_grover(n, marked)
    result = run_circuit(qc, shots=2000, expected_bitstring=marked, seed=3)
    random_baseline = 1 / (2**n)
    assert result.success_probability > random_baseline * 3


def test_grover_noisy_success_probability_lower_than_ideal():
    n = 3
    marked = "110"
    qc = build_grover(n, marked)
    ideal = run_circuit(qc, shots=3000, expected_bitstring=marked, seed=4)
    noise = build_depolarizing_noise_model(0.05)
    noisy = run_circuit(
        qc, shots=3000, noise_model=noise, noise_label="depolarizing_0.05", expected_bitstring=marked, seed=4
    )
    assert noisy.success_probability <= ideal.success_probability
    assert noisy.error_rate >= ideal.error_rate


def test_qft_runs_and_produces_valid_distribution():
    qc = build_qft(3)
    result = run_circuit(qc, shots=1000, seed=5)
    assert sum(result.measurement_counts.values()) == 1000
    assert all(len(bitstring) == 3 for bitstring in result.measurement_counts)


def test_grover_iteration_count_grows_with_search_space():
    assert grover_iteration_count(2) <= grover_iteration_count(4) <= grover_iteration_count(6)


def test_classical_exhaustive_search_cost_matches_theory():
    r = classical_exhaustive_search_cost(3)
    assert r.search_space_size == 8
    assert r.worst_case_queries == 8
    assert r.expected_queries == 4.5
    assert r.label == "THEORETICAL_COMPLEXITY"


def test_quantum_run_always_labeled_simulator():
    qc = build_bell_state()
    result = run_circuit(qc, shots=100)
    assert result.backend_type == "SIMULATOR"
