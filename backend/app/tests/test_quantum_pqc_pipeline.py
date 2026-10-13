"""QUANTUM and PQC are real research domains, not standalone tools - a
QUANTUM/PQC hypothesis/experiment/config
goes through the exact same approval-gated pipeline as AI/CYBERSECURITY and
produces a real, persisted `QuantumRun` row (quantum) or a real conclusion
computed from genuinely measured per-run data (both), never a stateless
CLI-in/JSON-out call.
"""

from app.models.experiment import ExperimentRun
from app.models.quantum import QuantumExperiment, QuantumRun


def _auth_headers(client, email, password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _run_pipeline_to_execution(client, headers, *, domain, codegen_spec, num_runs, decision_rule):
    resp = client.post("/api/v1/projects", json={"title": f"{domain} pipeline test", "domain": domain}, headers=headers)
    assert resp.status_code == 201, resp.text
    project = resp.json()

    resp = client.post(
        "/api/v1/hypotheses",
        json={
            "project_id": project["id"],
            "null_hypothesis": "H0",
            "alternative_hypothesis": "H1",
            "independent_variables": ["method"],
            "dependent_variables": [decision_rule["metric"]],
            "baseline": codegen_spec.get("baseline", "baseline"),
            "evaluation_metric": decision_rule["metric"],
            "decision_rule": decision_rule,
            "generated_by": "human",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    hypothesis = resp.json()

    resp = client.post(
        "/api/v1/experiments",
        json={
            "project_id": project["id"],
            "hypothesis_id": hypothesis["id"],
            "domain": domain,
            "objective": f"Test {domain} pipeline",
            "num_runs_planned": num_runs,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    experiment = resp.json()

    resp = client.post(
        f"/api/v1/experiments/{experiment['id']}/configs",
        json={
            "experiment_id": experiment["id"],
            "baseline_spec": codegen_spec.get("baseline", "baseline"),
            "model_spec": codegen_spec.get("proposed", "proposed"),
            "random_seed": codegen_spec.get("base_seed", 42),
            "num_runs": num_runs,
            "metrics_requested": [decision_rule["metric"]],
            "resource_limits": {"cpu": 1, "memory": "512m", "timeout_seconds": 120},
            "codegen_spec": codegen_spec,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    config = resp.json()

    resp = client.post(
        f"/api/v1/experiments/configs/{config['id']}/approve", json={"rationale": "ok"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    approved = resp.json()

    resp = client.post(
        f"/api/v1/experiments/configs/{approved['id']}/execute", json={}, headers=headers
    )
    return experiment, resp


def test_quantum_noise_ablation_pipeline_produces_real_quantum_run_and_conclusion(client, db_session):
    headers = _auth_headers(client, "quantum-pipeline@example.com")
    experiment, resp = _run_pipeline_to_execution(
        client,
        headers,
        domain="QUANTUM",
        codegen_spec={
            "algorithm": "grover",
            "n_qubits": 3,
            "marked_state": "101",
            "shots": 512,
            "num_runs": 5,
            "base_seed": 42,
            "comparison": "noise_ablation",
            "noise_error_rate": 0.1,
            "baseline": "ideal",
            "proposed": "noisy",
        },
        num_runs=5,
        decision_rule={
            "metric": "success_probability",
            "alpha": 0.05,
            "min_effect_size": 0.05,
            "direction": "less",
        },
    )
    assert resp.status_code == 200, resp.text
    run = resp.json()
    assert run["status"] == "COMPLETED"
    assert run["isolation_level"] == "IN_PROCESS_TRUSTED"

    resp = client.get(f"/api/v1/experiments/{experiment['id']}/results", headers=headers)
    results = resp.json()
    assert len(results) == 1
    assert results[0]["conclusion_status"] in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE")

    db = db_session
    quantum_exp = db.query(QuantumExperiment).filter(
        QuantumExperiment.experiment_id == experiment["id"]
    ).one_or_none()
    assert quantum_exp is not None
    assert quantum_exp.algorithm == "grover"
    assert quantum_exp.qubit_count == 3

    db_run = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == experiment["id"]).one()
    quantum_runs = db.query(QuantumRun).filter(QuantumRun.run_id == db_run.id).all()
    # 5 num_runs x 2 arms (ideal + noisy) = 10 real QuantumRun rows
    assert len(quantum_runs) == 10
    assert all(qr.backend_type.value == "SIMULATOR" for qr in quantum_runs)
    assert all(qr.success_probability is not None for qr in quantum_runs)


def test_quantum_vs_classical_random_pipeline(client):
    headers = _auth_headers(client, "quantum-classical@example.com")
    experiment, resp = _run_pipeline_to_execution(
        client,
        headers,
        domain="QUANTUM",
        codegen_spec={
            "algorithm": "grover",
            "n_qubits": 3,
            "marked_state": "110",
            "shots": 512,
            "num_runs": 5,
            "base_seed": 7,
            "comparison": "vs_classical_random",
            "baseline": "classical_random_guess",
            "proposed": "grover_quantum",
        },
        num_runs=5,
        decision_rule={
            "metric": "success_probability",
            "alpha": 0.05,
            "min_effect_size": 0.1,
            "direction": "greater",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"

    resp = client.get(f"/api/v1/experiments/{experiment['id']}/results", headers=headers)
    result = resp.json()[0]
    # Grover should genuinely and substantially beat classical random guessing here.
    assert result["conclusion_status"] == "SUPPORTED"


def test_pqc_signing_latency_pipeline_produces_real_conclusion(client):
    headers = _auth_headers(client, "pqc-pipeline@example.com")
    experiment, resp = _run_pipeline_to_execution(
        client,
        headers,
        domain="PQC",
        codegen_spec={"baseline": "rsa", "proposed": "ecdsa", "num_runs": 10},
        num_runs=10,
        decision_rule={
            "metric": "sign_latency_seconds",
            "alpha": 0.05,
            "min_effect_size": 0.2,
            "direction": "less",
        },
    )
    assert resp.status_code == 200, resp.text
    run = resp.json()
    assert run["status"] == "COMPLETED"
    assert run["isolation_level"] == "IN_PROCESS_TRUSTED"

    resp = client.get(f"/api/v1/experiments/{experiment['id']}/results", headers=headers)
    result = resp.json()[0]
    # ECDSA signing is well-known to be much faster than RSA signing.
    assert result["conclusion_status"] == "SUPPORTED"

    resp = client.get(f"/api/v1/experiments/results/{result['id']}/statistics", headers=headers)
    stats = resp.json()[0]
    assert stats["p_value"] is not None
    assert stats["effect_size"] is not None


def test_pqc_pipeline_raises_503_when_liboqs_unavailable(client):
    from app.pqc import pqc_backend

    if pqc_backend.OQS_AVAILABLE:
        import pytest

        pytest.skip("liboqs is installed in this environment; unavailability path not exercised")

    headers = _auth_headers(client, "pqc-unavailable@example.com")
    _, resp = _run_pipeline_to_execution(
        client,
        headers,
        domain="PQC",
        codegen_spec={"baseline": "rsa", "proposed": "pqc_sig", "num_runs": 5},
        num_runs=5,
        decision_rule={"metric": "sign_latency_seconds", "alpha": 0.05, "min_effect_size": 0.2, "direction": "less"},
    )
    assert resp.status_code == 503
    assert "PQC backend unavailable" in resp.json()["detail"]
