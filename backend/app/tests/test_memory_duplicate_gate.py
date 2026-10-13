"""Research Memory actually influencing the pipeline - Gate 1 approval is
blocked when an identical
(domain, baseline, proposed, dataset) experiment already exists in the
project, unless explicitly overridden."""


def _auth_headers(client, email, password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_experiment_with_config(client, headers, project_id, baseline, proposed):
    resp = client.post(
        "/api/v1/hypotheses",
        json={
            "project_id": project_id,
            "null_hypothesis": "H0",
            "alternative_hypothesis": "H1",
            "independent_variables": ["m"],
            "dependent_variables": ["f1"],
            "baseline": baseline,
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
            "project_id": project_id,
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
            "baseline_spec": baseline,
            "model_spec": proposed,
            "random_seed": 42,
            "num_runs": 5,
            "metrics_requested": ["f1"],
            "resource_limits": {"cpu": 1},
            "codegen_spec": {
                "dataset": "synthetic_classification",
                "baseline": baseline,
                "proposed": proposed,
                "num_runs": 5,
                "base_seed": 42,
            },
        },
        headers=headers,
    )
    return experiment, resp.json()


def test_second_identical_experiment_blocked_at_gate1_without_override(client):
    headers = _auth_headers(client, "dup-gate@example.com")
    resp = client.post("/api/v1/projects", json={"title": "dup test", "domain": "AI"}, headers=headers)
    project = resp.json()

    exp1, config1 = _create_experiment_with_config(
        client, headers, project["id"], "logistic_regression", "random_forest"
    )
    resp = client.post(f"/api/v1/experiments/configs/{config1['id']}/approve", json={}, headers=headers)
    assert resp.status_code == 200, resp.text

    exp2, config2 = _create_experiment_with_config(
        client, headers, project["id"], "logistic_regression", "random_forest"
    )
    resp = client.post(f"/api/v1/experiments/configs/{config2['id']}/approve", json={}, headers=headers)
    assert resp.status_code == 409, resp.text
    detail = resp.json()["detail"]
    assert "Research Memory" in detail["message"]
    assert detail["duplicate"]["experiment_id"] == exp1["id"]

    # Explicit override proceeds.
    resp = client.post(
        f"/api/v1/experiments/configs/{config2['id']}/approve",
        json={"override_duplicate_warning": True},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["approved"] is True


def test_new_config_version_of_same_experiment_not_flagged_as_its_own_duplicate(client):
    """Re-approving a revised version of the SAME experiment must not
    trip the duplicate check against its own earlier config version."""
    headers = _auth_headers(client, "dup-self@example.com")
    resp = client.post("/api/v1/projects", json={"title": "self-dup test", "domain": "AI"}, headers=headers)
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
            "num_runs_planned": 1,
        },
        headers=headers,
    )
    experiment = resp.json()

    def _make_config(num_runs):
        resp = client.post(
            f"/api/v1/experiments/{experiment['id']}/configs",
            json={
                "experiment_id": experiment["id"],
                "baseline_spec": "logistic_regression",
                "model_spec": "random_forest",
                "random_seed": 42,
                "num_runs": num_runs,
                "metrics_requested": ["f1"],
                "resource_limits": {"cpu": 1},
                "codegen_spec": {
                    "dataset": "synthetic_classification",
                    "baseline": "logistic_regression",
                    "proposed": "random_forest",
                    "num_runs": num_runs,
                    "base_seed": 42,
                },
            },
            headers=headers,
        )
        return resp.json()

    config_v1 = _make_config(1)
    resp = client.post(f"/api/v1/experiments/configs/{config_v1['id']}/critique", headers=headers)
    assert any(o["category"] == "sample_size" for o in resp.json()["objections"])

    config_v2 = _make_config(10)
    resp = client.post(f"/api/v1/experiments/configs/{config_v2['id']}/approve", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
