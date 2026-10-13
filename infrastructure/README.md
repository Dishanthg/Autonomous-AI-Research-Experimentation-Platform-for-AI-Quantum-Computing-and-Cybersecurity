# Infrastructure

## Observability (Section 82) - VERIFIED
`backend/app/main.py` wires `prometheus-fastapi-instrumentator`, exposing
real request-count/latency metrics at `GET /metrics` in standard Prometheus
text format. Verified by `backend/app/tests/test_observability.py` with no
external Prometheus server required. `prometheus.yml` in this directory is
the scrape config for a real Prometheus instance, when one is deployed
alongside the backend (not run in this build's environment - no
Grafana/Prometheus containers were stood up here, consistent with the
Docker-avoidance constraint - see ADR-008).

## What's intentionally NOT here
No Terraform/Kubernetes manifests - this project has not been deployed to
any cloud environment, and shipping unverified IaC would misrepresent this
build's actual deployment status (see `docs/deployment/deployment-guide.md`
for the honest current state: `docker-compose.yml` is the one topology
that's actually documented and partially exercised).
