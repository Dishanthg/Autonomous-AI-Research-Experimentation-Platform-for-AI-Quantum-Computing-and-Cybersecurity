.PHONY: setup test lint literature research experiment quantum cybersecurity pqc reproduce demo db-up db-down migrate

setup:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

test:
	cd backend && pytest -v --tb=short

lint:
	cd backend && ruff check app && black --check app

db-up:
	docker compose up -d postgres neo4j

db-down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

literature:
	cd backend && python -m app.services.literature.cli $(ARGS)

research:
	cd backend && python -m scripts.run_research_pipeline $(ARGS)

experiment:
	cd backend && python -m scripts.run_experiment $(ARGS)

quantum:
	cd backend && python -m app.quantum.cli $(ARGS)

cybersecurity:
	cd backend && python -m scripts.run_cyber_experiment $(ARGS)

pqc:
	cd backend && python -m app.pqc.cli $(ARGS)

reproduce:
	cd backend && python -m scripts.reproduce_experiment $(ARGS)

demo:
	cd backend && python -m scripts.run_demo $(ARGS)
