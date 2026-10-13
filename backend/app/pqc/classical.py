"""Classical cryptography benchmark baseline (Section 29/S/69).

Uses the `cryptography` library's real RSA and ECDSA implementations - no
hand-rolled crypto primitives (per the project's own security rule against
introducing crypto vulnerabilities).
"""

import time
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


@dataclass
class BenchmarkResult:
    scheme: str
    operation: str
    mean_seconds: float
    n_runs: int
    artifact_size_bytes: int


def _time_it(fn, n_runs: int) -> float:
    start = time.perf_counter()
    for _ in range(n_runs):
        fn()
    return (time.perf_counter() - start) / n_runs


def benchmark_rsa(key_size: int = 2048, n_runs: int = 20) -> list[BenchmarkResult]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    public_key = private_key.public_key()
    message = b"researchmind-q pqc benchmark payload"

    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    sign_time = _time_it(
        lambda: private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        ),
        n_runs,
    )
    verify_time = _time_it(
        lambda: public_key.verify(
            signature,
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        ),
        n_runs,
    )
    keygen_time = _time_it(
        lambda: rsa.generate_private_key(public_exponent=65537, key_size=key_size), max(1, n_runs // 5)
    )

    return [
        BenchmarkResult(f"RSA-{key_size}", "keygen", keygen_time, max(1, n_runs // 5), len(pub_bytes)),
        BenchmarkResult(f"RSA-{key_size}", "sign", sign_time, n_runs, len(signature)),
        BenchmarkResult(f"RSA-{key_size}", "verify", verify_time, n_runs, len(pub_bytes)),
    ]


def benchmark_ecdsa(curve=ec.SECP256R1(), n_runs: int = 20) -> list[BenchmarkResult]:
    private_key = ec.generate_private_key(curve)
    public_key = private_key.public_key()
    message = b"researchmind-q pqc benchmark payload"

    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    sign_time = _time_it(lambda: private_key.sign(message, ec.ECDSA(hashes.SHA256())), n_runs)
    verify_time = _time_it(lambda: public_key.verify(signature, message, ec.ECDSA(hashes.SHA256())), n_runs)
    keygen_time = _time_it(lambda: ec.generate_private_key(curve), n_runs)

    return [
        BenchmarkResult(f"ECDSA-{curve.name}", "keygen", keygen_time, n_runs, len(pub_bytes)),
        BenchmarkResult(f"ECDSA-{curve.name}", "sign", sign_time, n_runs, len(signature)),
        BenchmarkResult(f"ECDSA-{curve.name}", "verify", verify_time, n_runs, len(pub_bytes)),
    ]
