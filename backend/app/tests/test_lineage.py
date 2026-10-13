"""Research Lineage / Timeline traversal
endpoint - Project -> ResearchQuestion -> Hypothesis -> Experiment ->
ExperimentRun -> Result -> StatisticalTest/Limitation."""


def _auth_headers(client, email, password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_lineage_walks_full_chain_after_execution(client):
    headers = _auth_headers(client, "lineage@example.com")

    resp = client.post("/api/v1/projects", json={"title": "lineage test", "domain": "AI"}, headers=headers)
    project = resp.json()

    resp = client.post(
        f"/api/v1/projects/{project['id']}/questions",
        json={"question_text": "Does X help?", "domain": "AI", "is_primary": True},
        headers=headers,
    )
    question = resp.json()

    resp = client.post(
        "/api/v1/hypotheses",
        json={
            "project_id": project["id"],
            "research_question_id": question["id"],
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

    resp = client.get(f"/api/v1/projects/{project['id']}/lineage", headers=headers)
    assert resp.status_code == 200, resp.text
    lineage = resp.json()

    assert lineage["project_id"] == project["id"]
    assert len(lineage["questions"]) == 1
    q = lineage["questions"][0]
    assert q["id"] == question["id"]
    assert len(q["hypotheses"]) == 1
    h = q["hypotheses"][0]
    assert h["id"] == hypothesis["id"]
    assert len(h["experiments"]) == 1
    e = h["experiments"][0]
    assert e["id"] == experiment["id"]
    assert len(e["runs"]) == 1
    assert e["runs"][0]["status"] == "COMPLETED"
    assert len(e["results"]) == 1
    assert e["results"][0]["conclusion_status"] in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE")
    assert len(e["results"][0]["statistical_tests"]) == 1
    assert lineage["unlinked_hypotheses"] == []


def test_lineage_includes_unlinked_hypotheses(client):
    headers = _auth_headers(client, "lineage-unlinked@example.com")
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

    resp = client.get(f"/api/v1/projects/{project['id']}/lineage", headers=headers)
    assert resp.status_code == 200
    lineage = resp.json()
    assert lineage["questions"] == []
    assert len(lineage["unlinked_hypotheses"]) == 1
    assert lineage["unlinked_hypotheses"][0]["id"] == hypothesis["id"]
    assert lineage["unlinked_hypotheses"][0]["experiments"] == []


def test_lineage_404_for_missing_project(client):
    headers = _auth_headers(client, "lineage-404@example.com")
    resp = client.get("/api/v1/projects/does-not-exist/lineage", headers=headers)
    assert resp.status_code == 404
