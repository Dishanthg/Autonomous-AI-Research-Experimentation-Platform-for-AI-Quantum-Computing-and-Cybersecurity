# PQC Benchmark (classical arm - real measurements)

PQC arm available: **False** — NOT_IMPLEMENTED: liboqs/oqs-python is not installed in this environment. Classical (RSA/ECDSA) results above are real measurements; no PQC numbers are reported or fabricated. Install liboqs + oqs-python to enable this arm.

| Scheme | Operation | Mean time (ms) | Artifact size (bytes) |
|---|---|---|---|
| RSA-2048 | keygen | 118.3351 | 294 |
| RSA-2048 | sign | 1.5439 | 256 |
| RSA-2048 | verify | 0.0976 | 294 |
| ECDSA-secp256r1 | keygen | 0.0445 | 91 |
| ECDSA-secp256r1 | sign | 0.0688 | 72 |
| ECDSA-secp256r1 | verify | 0.1913 | 91 |
