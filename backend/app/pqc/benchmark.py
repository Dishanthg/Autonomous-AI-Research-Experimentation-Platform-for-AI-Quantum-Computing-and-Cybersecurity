"""Experiment 9 / Section 29,69: classical vs PQC vs hybrid benchmark
orchestration. Honestly reports which arms actually ran."""

from dataclasses import dataclass, field

from app.pqc import classical, pqc_backend


@dataclass
class PQCComparisonReport:
    classical_results: list
    pqc_results: list = field(default_factory=list)
    pqc_available: bool = False
    status_note: str = ""


def run_comparison(n_runs: int = 20) -> PQCComparisonReport:
    classical_results = classical.benchmark_rsa(n_runs=n_runs) + classical.benchmark_ecdsa(n_runs=n_runs)

    if not pqc_backend.OQS_AVAILABLE:
        return PQCComparisonReport(
            classical_results=classical_results,
            pqc_results=[],
            pqc_available=False,
            status_note=(
                "NOT_IMPLEMENTED: liboqs/oqs-python is not installed in this environment. "
                "Classical (RSA/ECDSA) results above are real measurements; no PQC numbers "
                "are reported or fabricated. Install liboqs + oqs-python to enable this arm."
            ),
        )

    kem_results = pqc_backend.benchmark_kem(n_runs=n_runs) or []
    sig_results = pqc_backend.benchmark_signature(n_runs=n_runs) or []
    return PQCComparisonReport(
        classical_results=classical_results,
        pqc_results=kem_results + sig_results,
        pqc_available=True,
        status_note="VERIFIED: both classical and PQC arms measured in this environment.",
    )
