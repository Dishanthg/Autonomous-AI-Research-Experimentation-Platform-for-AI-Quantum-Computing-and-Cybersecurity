"""Experiment 9 (Section 29/69): real PQC-domain research run through the
full pipeline. Compares real, individually-timed RSA-2048 vs. ECDSA-P256
signing latency (both via the real `cryptography` library - see
`app.services.execution.pqc_runner`).

Honesty note (Rule 1/12, see FINAL_RESEARCH_AUDIT.md): liboqs/oqs-python is
not installed in this environment, so the genuine post-quantum arm
('pqc_sig', ML-DSA-65) is NOT_IMPLEMENTED here - this script does not
attempt it and does not fabricate numbers for it. The execution path
(`pqc_runner.execute_pqc_config` with proposed="pqc_sig") is written and
unit-tested (see app/tests/test_quantum_pqc_pipeline.py) to raise a real
503-equivalent error rather than proceed. Once liboqs is installed, swap
`proposed="pqc_sig"` in the codegen_spec below to genuinely benchmark
ML-DSA-65 against a classical baseline through the exact same code path.
"""

import json
import sys

from app.models.enums import Domain
from app.pqc import pqc_backend
from scripts._pipeline import RESEARCH_DIR, ensure_schema, get_session, run_full_pipeline

NUM_RUNS = 30


def _experiment_9(db) -> dict:
    outcome = run_full_pipeline(
        db,
        domain=Domain.PQC,
        project_title="Experiment 9: classical signature signing-latency comparison "
        "(RSA-2048 vs. ECDSA-P256)",
        question_text="Is ECDSA-P256 signing latency lower than RSA-2048 signing latency?",
        null_hypothesis="ECDSA-P256 signing latency is not lower than RSA-2048 signing latency.",
        alternative_hypothesis="ECDSA-P256 signing latency is lower than RSA-2048 signing latency.",
        baseline="rsa",
        evaluation_metric="sign_latency_seconds",
        decision_rule={
            "metric": "sign_latency_seconds",
            "alpha": 0.05,
            "min_effect_size": 0.5,
            "direction": "less",
        },
        codegen_spec={"baseline": "rsa", "proposed": "ecdsa", "num_runs": NUM_RUNS},
        num_runs=NUM_RUNS,
        metrics_requested=["sign_latency_seconds"],
    )
    return {
        "experiment": "Experiment 9: RSA-2048 vs ECDSA-P256 signing latency",
        "pqc_available_this_run": pqc_backend.OQS_AVAILABLE,
        "status_note": (
            "VERIFIED: both classical schemes measured in this environment."
            if not pqc_backend.OQS_AVAILABLE
            else "VERIFIED: classical schemes measured; liboqs also available in this "
            "environment but this script deliberately runs the classical-only comparison "
            "(edit codegen_spec.proposed='pqc_sig' to run the genuine PQC arm)."
        ),
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
    }


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        exp9 = _experiment_9(db)
    finally:
        db.close()

    out_dir = RESEARCH_DIR / "pqc"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "experiment_9_classical_signing_latency.json"
    out_path.write_text(json.dumps(exp9, indent=2), encoding="utf-8")
    print(json.dumps(exp9, indent=2))
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
