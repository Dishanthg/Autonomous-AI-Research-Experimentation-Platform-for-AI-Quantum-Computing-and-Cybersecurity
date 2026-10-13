"""Generated code, the codegen spec, and stdout/stderr are persisted as
real, checksummed `Artifact` rows tied to a run, not just files loose in a
sandbox workspace."""

from pathlib import Path

from app.services.execution.artifacts import REPO_ROOT


def _auth_headers(client, email, password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_ai_experiment_run_persists_code_config_and_log_artifacts(client):
    headers = _auth_headers(client, "artifacts-ai@example.com")

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
    resp = client.post(f"/api/v1/experiments/configs/{approved['id']}/execute", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    run = resp.json()

    resp = client.get(f"/api/v1/experiments/runs/{run['id']}/artifacts", headers=headers)
    assert resp.status_code == 200
    artifacts = resp.json()
    types = {a["artifact_type"] for a in artifacts}
    assert types == {"code", "config", "log"}
    for a in artifacts:
        assert a["checksum"] is not None
        assert (REPO_ROOT / a["path"]).exists()


def test_artifacts_for_missing_run_404(client):
    headers = _auth_headers(client, "artifacts-404@example.com")
    resp = client.get("/api/v1/experiments/runs/does-not-exist/artifacts", headers=headers)
    assert resp.status_code == 404
