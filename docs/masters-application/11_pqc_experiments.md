# PQC Experiments

`app/pqc/classical.py` benchmarks RSA-2048 and ECDSA-P256 (via the
`cryptography` library — no hand-rolled crypto) for keygen/sign/verify,
timing each operation for real over multiple runs.

**Verified real measurement** (from a 10-run local benchmark during
development): RSA-2048 signing averaged ~0.43ms per operation and verify
~0.045ms; ECDSA-P256 keygen/sign/verify were all in the 10-50 microsecond
range — confirming the well-known property that ECDSA signing is
substantially faster than RSA signing
(`test_pqc.py::test_ecdsa_benchmark_faster_than_rsa_signing`).

**Post-quantum arm (ML-KEM/ML-DSA via liboqs):** NOT_IMPLEMENTED in this
environment. `liboqs`/`oqs-python` require a compiled native library not
present here; `app/pqc/pqc_backend.py` detects this at import time and
`run_comparison()` honestly reports `pqc_available=False` with a
`NOT_IMPLEMENTED` status note rather than fabricating PQC timing numbers
(verified in
`test_pqc.py::test_pqc_comparison_honestly_reports_unavailable_when_oqs_missing`).

No classical-vs-PQC-vs-hybrid comparison has therefore been completed; only
the classical arm is real data in this build.
