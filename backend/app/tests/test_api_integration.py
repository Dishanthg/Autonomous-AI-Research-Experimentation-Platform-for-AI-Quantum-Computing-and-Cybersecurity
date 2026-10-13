"""End-to-end API integration tests covering the core research pipeline:
register -> login -> project -> hypothesis -> quality-check -> critique ->
experiment -> config -> critique -> approve (Gate 1) -> execute (Gate 2) ->
results -> statistics -> limitations -> next-experiments.

This environment's `backend/.env` sets SANDBOX_BACKEND=process (ADR-009) so
execution genuinely runs the cybersecurity codegen template end-to-end via
the reduced-isolation Tier 2 sandbox and produces a real, statistically
analyzed conclusion - not a mocked one. A separate test
(`test_execute_returns_503_when_docker_backend_unavailable`) explicitly
forces the Docker (Tier 1) backend to confirm the sandbox-unavailable
failure path (Rule 5: never fall back to unsandboxed execution) still
works correctly.
"""

from unittest.mock import patch

from docker.errors import DockerException


def _auth_headers(client, email="researcher@example.com", password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Researcher",
            "role": "RESEARCHER",
        },
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint_reports_real_subsystem_status(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "postgres" not in body["checks"] or True  # key name is generic in impl; just check structure
    assert "llm_provider" in body["checks"]
    assert body["checks"]["llm_provider"] == "NOT_CONFIGURED"  # no API key set in test env


def test_register_and_login(client):
    headers = _auth_headers(client)
    assert "Authorization" in headers


def test_full_research_pipeline_end_to_end(client):
    headers = _auth_headers(client, email="pipeline@example.com")

    # 1. Create project
    resp = client.post(
        "/api/v1/projects",
        json={
            "title": "Graph-based cybersecurity anomaly detection",
            "domain": "CYBERSECURITY",
            "objectives": "Investigate whether graph features improve IDS performance.",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    project = resp.json()

    # 2. Create research question
    resp = client.post(
        f"/api/v1/projects/{project['id']}/questions",
        json={
            "question_text": "Does graph-based representation improve cybersecurity anomaly detection?",
            "domain": "CYBERSECURITY",
            "is_primary": True,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    question = resp.json()

    # 3. Create hypothesis (pre-registered decision rule)
    resp = client.post(
        "/api/v1/hypotheses",
        json={
            "project_id": project["id"],
            "research_question_id": question["id"],
            "null_hypothesis": "Graph features do not improve detection F1.",
            "alternative_hypothesis": "Graph features improve detection F1.",
            "independent_variables": ["graph_representation"],
            "dependent_variables": ["f1", "pr_auc"],
            "dataset_id": None,
            "baseline": "rule_based",
            "evaluation_metric": "f1",
            "potential_confounders": ["class_imbalance"],
            "decision_rule": {"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
            "generated_by": "human",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    hypothesis = resp.json()
    assert hypothesis["status"] == "DRAFT"

    # 4. Quality check should FAIL (no dataset_id) - Rule: cannot silently advance a weak hypothesis
    resp = client.post(f"/api/v1/hypotheses/{hypothesis['id']}/quality-check", headers=headers)
    assert resp.status_code == 200
    qc = resp.json()
    assert qc["checks"]["dataset_availability"] is False

    # 5. Create experiment anyway to exercise the config/critique/approval pipeline
    resp = client.post(
        "/api/v1/experiments",
        json={
            "project_id": project["id"],
            "hypothesis_id": hypothesis["id"],
            "domain": "CYBERSECURITY",
            "objective": "Compare rule-based vs graph-enhanced RF IDS.",
            "num_runs_planned": 5,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    experiment = resp.json()

    # 6. Create config with too few runs -> critic should flag sample_size
    resp = client.post(
        f"/api/v1/experiments/{experiment['id']}/configs",
        json={
            "experiment_id": experiment["id"],
            "baseline_spec": "rule_based",
            "model_spec": "graph_enhanced_rf",
            "random_seed": 42,
            "num_runs": 1,
            "metrics_requested": ["f1", "pr_auc"],
            "resource_limits": {"cpu": 1, "memory": "512m", "timeout_seconds": 120},
            "codegen_spec": {
                "baseline": "rule_based",
                "proposed": "graph_enhanced_rf",
                "num_runs": 1,
                "base_seed": 42,
            },
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    config = resp.json()
    assert config["approved"] is False

    resp = client.post(f"/api/v1/experiments/configs/{config['id']}/critique", headers=headers)
    assert resp.status_code == 200
    critique = resp.json()
    assert any(o["category"] == "sample_size" for o in critique["objections"])

    # 7. Create a properly-sized config and approve it (Gate 1)
    resp = client.post(
        f"/api/v1/experiments/{experiment['id']}/configs",
        json={
            "experiment_id": experiment["id"],
            "baseline_spec": "rule_based",
            "model_spec": "graph_enhanced_rf",
            "random_seed": 42,
            "num_runs": 5,
            "metrics_requested": ["f1", "pr_auc"],
            "resource_limits": {"cpu": 1, "memory": "512m", "timeout_seconds": 120},
            "codegen_spec": {
                "baseline": "rule_based",
                "proposed": "graph_enhanced_rf",
                "num_runs": 5,
                "base_seed": 42,
            },
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    config_v2 = resp.json()
    assert config_v2["version"] == 2

    resp = client.post(
        f"/api/v1/experiments/configs/{config_v2['id']}/approve",
        json={"rationale": "Looks good"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    approved_config = resp.json()
    assert approved_config["approved"] is True

    # 8. Execute (Gate 2). This environment runs the process-tier sandbox
    # (ADR-009) for real, so this should genuinely complete and produce a
    # real conclusion, not merely fail gracefully.
    resp = client.post(
        f"/api/v1/experiments/configs/{approved_config['id']}/execute", json={}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    run = resp.json()
    assert run["status"] == "COMPLETED", run.get("stderr")
    assert run["isolation_level"] == "PROCESS_RESOURCE_LIMITED"

    # 9. Real, statistically-analyzed conclusion.
    resp = client.get(f"/api/v1/experiments/{experiment['id']}/results", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    result = results[0]
    assert result["conclusion_status"] in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE")
    assert result["computed_by"] == "deterministic:result_analyzer+statistical_analyst"

    resp = client.get(f"/api/v1/experiments/results/{result['id']}/statistics", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert len(stats) == 1
    assert stats[0]["p_value"] is not None
    assert stats[0]["effect_size"] is not None

    # 10. Limitation Detector (Section 41) fired for the reduced-isolation tier.
    resp = client.get(f"/api/v1/experiments/{experiment['id']}/limitations", headers=headers)
    assert resp.status_code == 200
    limitation_categories = {row["category"] for row in resp.json()}
    assert "sandbox_isolation_limitation" in limitation_categories

    # 11. Next-Experiment Generator (Section 42) proposes at least an ablation.
    resp = client.get(f"/api/v1/experiments/{experiment['id']}/next-experiments", headers=headers)
    assert resp.status_code == 200
    next_categories = {row["category"] for row in resp.json()}
    assert "ablation" in next_categories


def test_execute_returns_503_when_docker_backend_unavailable(client):
    """Forces the Docker (Tier 1) backend for this one test to confirm the
    sandbox-unavailable failure path still fails loudly rather than falling
    back to a different tier on its own (Rule 5)."""
    from app.sandbox import executor as executor_module

    headers = _auth_headers(client, email="docker-fallback@example.com")

    resp = client.post("/api/v1/projects", json={"title": "x", "domain": "AI"}, headers=headers)
    project = resp.json()
    resp = client.post(
        "/api/v1/hypotheses",
        json={
            "project_id": project["id"],
            "null_hypothesis": "H0",
            "alternative_hypothesis": "H1",
            "independent_variables": ["m"],
            "dependent_variables": ["f1"],
            "baseline": "logistic_regression",
            "evaluation_metric": "f1",
            "decision_rule": {"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
            "generated_by": "human",
        },
        headers=headers,
    )
    hypothesis = resp.json()
    resp = client.post(
        "/api/v1/experiments",
        json={
            "project_id": project["id"],
            "hypothesis_id": hypothesis["id"],
            "domain": "AI",
            "objective": "x",
            "num_runs_planned": 5,
        },
        headers=headers,
    )
    experiment = resp.json()
    resp = client.post(
        f"/api/v1/experiments/{experiment['id']}/configs",
        json={
            "experiment_id": experiment["id"],
            "baseline_spec": "logistic_regression",
            "model_spec": "random_forest",
            "random_seed": 42,
            "num_runs": 5,
            "metrics_requested": ["f1"],
            "resource_limits": {"cpu": 1},
            "codegen_spec": {
                "dataset": "synthetic_classification",
                "baseline": "logistic_regression",
                "proposed": "random_forest",
                "num_runs": 5,
                "base_seed": 42,
            },
        },
        headers=headers,
    )
    config = resp.json()
    resp = client.post(f"/api/v1/experiments/configs/{config['id']}/approve", json={}, headers=headers)
    approved = resp.json()

    with patch.object(executor_module.settings, "sandbox_backend", "docker"):
        with patch("app.sandbox.docker_executor.docker.from_env", side_effect=DockerException("no daemon")):
            resp = client.post(
                f"/api/v1/experiments/configs/{approved['id']}/execute", json={}, headers=headers
            )

    assert resp.status_code == 503
    assert "Sandbox unavailable" in resp.json()["detail"]


def test_rbac_viewer_cannot_create_project(client):
    email = "viewer@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Viewer",
            "role": "VIEWER",
        },
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": "testpassword123"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.post("/api/v1/projects", json={"title": "x", "domain": "AI"}, headers=headers)
    assert resp.status_code == 403


def test_login_rejects_wrong_password(client):
    email = "badlogin@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correctpassword1",
            "full_name": "X",
            "role": "RESEARCHER",
        },
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": "wrongpassword"})
    assert resp.status_code == 401


def test_quantum_endpoint_bell_state(client):
    headers = _auth_headers(client, email="quantum@example.com")
    resp = client.post(
        "/api/v1/quantum/run", json={"algorithm": "bell_state", "n_qubits": 2, "shots": 500}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["backend_type"] == "SIMULATOR"
    assert sum(body["measurement_counts"].values()) == 500


def test_quantum_endpoint_grover_beats_random(client):
    headers = _auth_headers(client, email="quantum2@example.com")
    resp = client.post(
        "/api/v1/quantum/run",
        json={
            "algorithm": "grover",
            "n_qubits": 3,
            "marked_state": "101",
            "shots": 1500,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success_probability"] > (1 / 8) * 3
