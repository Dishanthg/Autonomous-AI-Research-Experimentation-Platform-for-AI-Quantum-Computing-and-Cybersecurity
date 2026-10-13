"""In-process PQC / classical cryptography benchmark execution.
Uses this platform's own reviewed benchmark
code (`app.pqc.*`, itself built on the real `cryptography` library and,
when available, real `oqs` bindings) - no sandbox tier applies here for the
same reason as `quantum_runner` (this is not untrusted/generated code).

Unlike `app.pqc.benchmark.run_comparison` (which reports a single mean
latency per operation), this module times each signing operation
individually so a real per-run distribution feeds the platform's actual
two-sample statistics engine (Section 39), producing a genuine
SUPPORTED/NOT_SUPPORTED/INCONCLUSIVE conclusion rather than a printed mean.

Honesty note (Rule 1/12): if a caller requests the 'pqc_sig' arm and
liboqs/oqs-python is not installed in this environment,
`PQCBackendUnavailableError` is raised - never a fabricated number.
"""

import time
from datetime import datetime, timezone
from typing import Callable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from app.models.enums import RunStatus
from app.models.experiment import ExperimentConfig, ExperimentRun
from app.pqc import pqc_backend

MESSAGE = b"researchmind-q pqc benchmark payload"


class PQCBackendUnavailableError(RuntimeError):
    """Raised when a PQC-scheme arm is requested but liboqs/oqs-python is
    not installed in this environment."""


def _rsa_sign_once_factory(key_size: int = 2048) -> Callable[[], float]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pss = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)

    def sign_once() -> float:
        start = time.perf_counter()
        key.sign(MESSAGE, pss, hashes.SHA256())
        return time.perf_counter() - start

    return sign_once


def _ecdsa_sign_once_factory(curve=None) -> Callable[[], float]:
    key = ec.generate_private_key(curve or ec.SECP256R1())

    def sign_once() -> float:
        start = time.perf_counter()
        key.sign(MESSAGE, ec.ECDSA(hashes.SHA256()))
        return time.perf_counter() - start

    return sign_once


def _pqc_sig_sign_once_factory(algorithm: str | None = None) -> Callable[[], float]:
    if not pqc_backend.OQS_AVAILABLE:
        raise PQCBackendUnavailableError(
            "liboqs/oqs-python is not installed in this environment; cannot benchmark the "
            f"post-quantum signature scheme '{algorithm or pqc_backend.DEFAULT_SIG}'. "
            "Install liboqs + oqs-python to enable this arm (see app/pqc/pqc_backend.py)."
        )
    import oqs  # type: ignore

    scheme = algorithm or pqc_backend.DEFAULT_SIG
    signer = oqs.Signature(scheme)
    signer.generate_keypair()

    def sign_once() -> float:
        start = time.perf_counter()
        signer.sign(MESSAGE)
        return time.perf_counter() - start

    return sign_once


_SIGNER_FACTORIES: dict[str, Callable[[], Callable[[], float]]] = {
    "rsa": _rsa_sign_once_factory,
    "ecdsa": _ecdsa_sign_once_factory,
    "pqc_sig": _pqc_sig_sign_once_factory,
}


def _measure_signing_latency(scheme: str, n_runs: int) -> list[float]:
    if scheme not in _SIGNER_FACTORIES:
        raise ValueError(
            f"Unknown PQC benchmark scheme '{scheme}' (supported: {sorted(_SIGNER_FACTORIES)})"
        )
    sign_once = _SIGNER_FACTORIES[scheme]()
    return [sign_once() for _ in range(n_runs)]


def execute_pqc_config(db, config: ExperimentConfig, spec: dict) -> tuple[ExperimentRun, dict | None]:
    baseline_scheme = spec.get("baseline", "rsa")
    proposed_scheme = spec.get("proposed", "ecdsa")
    num_runs = int(spec.get("num_runs") or config.num_runs or 20)

    run = ExperimentRun(
        experiment_id=config.experiment_id,
        config_id=config.id,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        seed_used=config.random_seed,
        isolation_level="IN_PROCESS_TRUSTED",
    )
    db.add(run)
    db.flush()

    try:
        baseline_values = _measure_signing_latency(baseline_scheme, num_runs)
        proposed_values = _measure_signing_latency(proposed_scheme, num_runs)
    except (PQCBackendUnavailableError, ValueError) as exc:
        run.status = RunStatus.FAILED
        run.stderr = str(exc)
        run.exit_code = 1
        run.finished_at = datetime.now(timezone.utc)
        db.flush()
        if isinstance(exc, PQCBackendUnavailableError):
            raise
        return run, None

    run.finished_at = datetime.now(timezone.utc)
    run.exit_code = 0
    run.status = RunStatus.COMPLETED
    run.stdout = (
        f"pqc in-process signing-latency benchmark: baseline={baseline_scheme} "
        f"proposed={proposed_scheme} num_runs={num_runs}"
    )
    run.stderr = ""
    run.resource_usage = {}
    db.flush()

    metrics_json = {
        "results": {
            "baseline": {"sign_latency_seconds": baseline_values},
            "proposed": {"sign_latency_seconds": proposed_values},
        },
        "meta": {
            "baseline_scheme": baseline_scheme,
            "proposed_scheme": proposed_scheme,
            "num_runs": num_runs,
            "pqc_available": pqc_backend.OQS_AVAILABLE,
        },
    }
    return run, metrics_json
