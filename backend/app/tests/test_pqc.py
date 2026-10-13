from app.pqc import classical, pqc_backend
from app.pqc.benchmark import run_comparison


def test_rsa_benchmark_produces_real_measurements():
    results = classical.benchmark_rsa(key_size=2048, n_runs=5)
    ops = {r.operation for r in results}
    assert ops == {"keygen", "sign", "verify"}
    for r in results:
        assert r.mean_seconds > 0
        assert r.artifact_size_bytes > 0


def test_ecdsa_benchmark_faster_than_rsa_signing():
    rsa_results = {r.operation: r for r in classical.benchmark_rsa(key_size=2048, n_runs=5)}
    ecdsa_results = {r.operation: r for r in classical.benchmark_ecdsa(n_runs=5)}
    # Well-known property: ECDSA signing is typically much faster than RSA signing
    assert ecdsa_results["sign"].mean_seconds < rsa_results["sign"].mean_seconds


def test_pqc_comparison_honestly_reports_unavailable_when_oqs_missing():
    report = run_comparison(n_runs=5)
    assert len(report.classical_results) == 6  # 3 ops x 2 schemes
    if not pqc_backend.OQS_AVAILABLE:
        assert report.pqc_available is False
        assert report.pqc_results == []
        assert "NOT_IMPLEMENTED" in report.status_note
    else:
        assert report.pqc_available is True
        assert len(report.pqc_results) > 0
