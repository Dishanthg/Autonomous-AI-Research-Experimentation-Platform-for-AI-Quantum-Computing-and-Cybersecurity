"""Gap Analyzer API surface. No live
Neo4j exists in this environment (see ADR-007/008), so the "real" path is
tested end-to-end against the genuine (unreachable) client, honestly
failing loudly with 503 - and the success path is tested with a mocked
driver, exactly as the TODO item calls for."""

from contextlib import contextmanager


def _auth_headers(client, email, password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_project(client, headers):
    resp = client.post("/api/v1/projects", json={"title": "gap test", "domain": "AI"}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class _FakeSession:
    def __init__(self, sparse_rows, overlap_rows):
        self._sparse_rows = sparse_rows
        self._overlap_rows = overlap_rows

    def run(self, query, **params):
        return self._sparse_rows if "min_papers" in params else self._overlap_rows


class _FakeKGClient:
    def __init__(self, sparse_rows=None, overlap_rows=None):
        self._sparse_rows = sparse_rows or []
        self._overlap_rows = overlap_rows or []

    @contextmanager
    def session(self):
        yield _FakeSession(self._sparse_rows, self._overlap_rows)


def test_analyze_gaps_503_when_neo4j_genuinely_unavailable(client):
    """This environment has no live Neo4j (ADR-007/008) - the real,
    unmocked client must fail loudly, not silently return an empty list."""
    headers = _auth_headers(client, "gaps-unavailable@example.com")
    project = _create_project(client, headers)
    resp = client.post(
        "/api/v1/gaps/analyze", json={"project_id": project["id"], "min_papers": 1}, headers=headers
    )
    assert resp.status_code == 503
    assert "Knowledge graph unavailable" in resp.json()["detail"]


def test_analyze_gaps_404_for_missing_project(client):
    headers = _auth_headers(client, "gaps-404@example.com")
    resp = client.post(
        "/api/v1/gaps/analyze", json={"project_id": "does-not-exist"}, headers=headers
    )
    assert resp.status_code == 404


def test_analyze_gaps_persists_candidates_with_mocked_driver(client, monkeypatch):
    headers = _auth_headers(client, "gaps-mocked@example.com")
    project = _create_project(client, headers)

    fake_client = _FakeKGClient(
        sparse_rows=[{"method": "graph_enhanced_rf", "dataset": "synthetic_traffic_v1", "paper_count": 1}],
        overlap_rows=[{"method_a": "logistic_regression", "method_b": "graph_enhanced_rf"}],
    )
    monkeypatch.setattr("app.api.v1.gaps.get_kg_client", lambda: fake_client)

    resp = client.post(
        "/api/v1/gaps/analyze", json={"project_id": project["id"], "min_papers": 1}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    gaps = resp.json()
    assert len(gaps) == 2
    categories = {g["category"] for g in gaps}
    assert categories == {"unexplored_combination_of_methods", "missing_baseline"}
    assert all(g["human_verification_required"] is True for g in gaps)
    assert all(g["human_verified"] is False for g in gaps)

    resp = client.get(f"/api/v1/gaps?project_id={project['id']}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_analyze_gaps_narrate_503_when_llm_not_configured(client, monkeypatch):
    headers = _auth_headers(client, "gaps-narrate@example.com")
    project = _create_project(client, headers)

    fake_client = _FakeKGClient(
        sparse_rows=[{"method": "m", "dataset": "d", "paper_count": 1}], overlap_rows=[]
    )
    monkeypatch.setattr("app.api.v1.gaps.get_kg_client", lambda: fake_client)

    resp = client.post(
        "/api/v1/gaps/analyze",
        json={"project_id": project["id"], "min_papers": 1, "narrate": True},
        headers=headers,
    )
    assert resp.status_code == 503
    assert "LLM provider unavailable" in resp.json()["detail"]


def test_verify_gap_writes_decision_and_flips_human_verified(client, monkeypatch):
    headers = _auth_headers(client, "gaps-verify@example.com")
    project = _create_project(client, headers)

    fake_client = _FakeKGClient(sparse_rows=[{"method": "m", "dataset": "d", "paper_count": 1}])
    monkeypatch.setattr("app.api.v1.gaps.get_kg_client", lambda: fake_client)

    resp = client.post(
        "/api/v1/gaps/analyze", json={"project_id": project["id"], "min_papers": 1}, headers=headers
    )
    gap = resp.json()[0]
    assert gap["human_verified"] is False

    resp = client.post(
        f"/api/v1/gaps/{gap['id']}/verify",
        json={"verified": True, "rationale": "Confirmed by manual literature review."},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["human_verified"] is True


def test_verify_missing_gap_404(client):
    headers = _auth_headers(client, "gaps-verify-404@example.com")
    resp = client.post(
        "/api/v1/gaps/does-not-exist/verify", json={"verified": True}, headers=headers
    )
    assert resp.status_code == 404
