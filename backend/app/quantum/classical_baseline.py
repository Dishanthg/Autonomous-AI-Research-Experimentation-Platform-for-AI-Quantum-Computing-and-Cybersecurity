"""Classical baseline for Demonstration 2 / Experiment 7 (Section 92/67).

Clearly distinguishes theoretical complexity from simulated/measured
behavior: this module reports THEORETICAL query counts for classical
exhaustive search, not a simulation artifact, and is labeled as such
wherever it's surfaced.
"""

from dataclasses import dataclass


@dataclass
class ClassicalSearchResult:
    search_space_size: int
    expected_queries: float  # average-case exhaustive/random search
    worst_case_queries: int
    label: str = "THEORETICAL_COMPLEXITY"


def classical_exhaustive_search_cost(n_qubits: int) -> ClassicalSearchResult:
    n = 2**n_qubits
    return ClassicalSearchResult(
        search_space_size=n,
        expected_queries=(n + 1) / 2,  # average case, one marked item
        worst_case_queries=n,
    )
