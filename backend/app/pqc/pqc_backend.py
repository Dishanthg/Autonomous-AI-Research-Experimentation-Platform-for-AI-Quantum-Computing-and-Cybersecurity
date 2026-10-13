"""Optional post-quantum crypto backend via liboqs (python `oqs` bindings).

liboqs requires a compiled native library and is NOT included in
requirements.txt (it commonly fails to install without system build tools
present). This module detects availability at import time and reports
honestly: if unavailable, PQC benchmark results are NOT_IMPLEMENTED rather
than simulated or faked with placeholder numbers (Rule 1/12).
"""

import time
from dataclasses import dataclass
from typing import Optional

try:
    import oqs  # type: ignore

    OQS_AVAILABLE = True
except ImportError:
    OQS_AVAILABLE = False


@dataclass
class PQCBenchmarkResult:
    scheme: str
    operation: str
    mean_seconds: float
    n_runs: int
    artifact_size_bytes: int


DEFAULT_KEM = "ML-KEM-768"  # NIST-selected (formerly Kyber)
DEFAULT_SIG = "ML-DSA-65"  # NIST-selected (formerly Dilithium)


def benchmark_kem(algorithm: str = DEFAULT_KEM, n_runs: int = 20) -> Optional[list[PQCBenchmarkResult]]:
    if not OQS_AVAILABLE:
        return None

    with oqs.KeyEncapsulation(algorithm) as kem:
        public_key = kem.generate_keypair()
        ciphertext, shared_secret = kem.encap_secret(public_key)

        def keygen():
            with oqs.KeyEncapsulation(algorithm) as k:
                k.generate_keypair()

        def encap():
            kem.encap_secret(public_key)

        def decap():
            kem.decap_secret(ciphertext)

        keygen_time = _time_it(keygen, max(1, n_runs // 5))
        encap_time = _time_it(encap, n_runs)
        decap_time = _time_it(decap, n_runs)

    return [
        PQCBenchmarkResult(algorithm, "keygen", keygen_time, max(1, n_runs // 5), len(public_key)),
        PQCBenchmarkResult(algorithm, "encapsulate", encap_time, n_runs, len(ciphertext)),
        PQCBenchmarkResult(algorithm, "decapsulate", decap_time, n_runs, len(shared_secret)),
    ]


def benchmark_signature(algorithm: str = DEFAULT_SIG, n_runs: int = 20) -> Optional[list[PQCBenchmarkResult]]:
    if not OQS_AVAILABLE:
        return None

    message = b"researchmind-q pqc benchmark payload"
    with oqs.Signature(algorithm) as signer:
        public_key = signer.generate_keypair()
        signature = signer.sign(message)

        def keygen():
            with oqs.Signature(algorithm) as s:
                s.generate_keypair()

        def sign():
            signer.sign(message)

        def verify():
            with oqs.Signature(algorithm) as v:
                v.verify(message, signature, public_key)

        keygen_time = _time_it(keygen, max(1, n_runs // 5))
        sign_time = _time_it(sign, n_runs)
        verify_time = _time_it(verify, n_runs)

    return [
        PQCBenchmarkResult(algorithm, "keygen", keygen_time, max(1, n_runs // 5), len(public_key)),
        PQCBenchmarkResult(algorithm, "sign", sign_time, n_runs, len(signature)),
        PQCBenchmarkResult(algorithm, "verify", verify_time, n_runs, len(public_key)),
    ]


def _time_it(fn, n_runs: int) -> float:
    start = time.perf_counter()
    for _ in range(n_runs):
        fn()
    return (time.perf_counter() - start) / n_runs
