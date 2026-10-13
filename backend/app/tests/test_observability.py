def test_metrics_endpoint_exposes_prometheus_format(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "python_gc_objects_collected_total" in resp.text


def test_metrics_endpoint_tracks_http_requests(client):
    client.get("/api/v1/health")
    resp = client.get("/metrics")
    assert "http_requests_total" in resp.text or "http_request_duration_seconds" in resp.text
