"""Dataset registry API."""


def _auth_headers(client, email="dataset-researcher@example.com", password="testpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role": "RESEARCHER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_and_list_dataset(client):
    headers = _auth_headers(client)
    resp = client.post(
        "/api/v1/datasets",
        json={
            "name": "breast_cancer_test",
            "source": "sklearn.datasets.load_breast_cancer",
            "license": "public domain / UCI",
            "description": "test dataset",
            "features": ["mean_radius", "mean_texture"],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    dataset = resp.json()
    assert dataset["name"] == "breast_cancer_test"

    resp = client.get("/api/v1/datasets", headers=headers)
    assert resp.status_code == 200
    assert any(d["id"] == dataset["id"] for d in resp.json())

    resp = client.get(f"/api/v1/datasets/{dataset['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == dataset["id"]


def test_duplicate_dataset_name_rejected(client):
    headers = _auth_headers(client, email="dup-dataset@example.com")
    payload = {"name": "digits_test", "source": "sklearn", "license": "public domain"}
    resp = client.post("/api/v1/datasets", json=payload, headers=headers)
    assert resp.status_code == 201
    resp = client.post("/api/v1/datasets", json=payload, headers=headers)
    assert resp.status_code == 409


def test_create_and_list_dataset_versions(client):
    headers = _auth_headers(client, email="dataset-version@example.com")
    resp = client.post(
        "/api/v1/datasets",
        json={"name": "synthetic_traffic_test", "source": "generated", "license": "N/A (generated)"},
        headers=headers,
    )
    dataset = resp.json()

    resp = client.post(
        f"/api/v1/datasets/{dataset['id']}/versions",
        json={
            "version_tag": "seed-7-n4000-f12",
            "checksum": "abc123",
            "preprocessing": "numpy rng seed=7",
            "row_count": 4000,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    version = resp.json()
    assert version["dataset_id"] == dataset["id"]
    assert version["row_count"] == 4000

    resp = client.get(f"/api/v1/datasets/{dataset['id']}/versions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_dataset_version_for_missing_dataset_404(client):
    headers = _auth_headers(client, email="dataset-404@example.com")
    resp = client.post(
        "/api/v1/datasets/does-not-exist/versions",
        json={"version_tag": "v1"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_viewer_cannot_create_dataset(client):
    email = "dataset-viewer@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "full_name": "V", "role": "VIEWER"},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": "testpassword123"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = client.post(
        "/api/v1/datasets", json={"name": "x", "source": "x", "license": "x"}, headers=headers
    )
    assert resp.status_code == 403
