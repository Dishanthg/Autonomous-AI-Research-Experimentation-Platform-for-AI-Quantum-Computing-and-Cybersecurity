"""Central configuration. All settings are read from environment variables
(see .env.example). No secret ever has a hardcoded fallback value that would
work in production - defaults here are development-only conveniences.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    # Database
    # Defaults to a local SQLite file so the platform runs without Docker or
    # a separately-installed Postgres server (disk-constrained local dev).
    # Set DATABASE_URL to a postgresql+psycopg://... URL for production/docker.
    database_url: str = "sqlite:///./researchmind_dev.db"

    # Knowledge graph
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    # Auth
    jwt_secret_key: str = "insecure-dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # LLM provider
    llm_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    llm_model: str = "claude-sonnet-5"

    # Literature sources
    arxiv_api_base: str = "https://export.arxiv.org/api/query"
    semantic_scholar_api_base: str = "https://api.semanticscholar.org/graph/v1"
    crossref_api_base: str = "https://api.crossref.org"

    # Sandbox
    # "docker" (Tier 1, full isolation - required for arbitrary/LLM-authored
    # code) or "process" (Tier 2, reduced isolation - ADR-009, only for this
    # platform's own reviewed codegen templates in Docker-unavailable dev
    # environments). Defaults to "docker" for production safety.
    sandbox_backend: str = "docker"
    allow_process_sandbox: bool = False
    sandbox_enabled: bool = True
    sandbox_cpu_limit: float = 1.0
    sandbox_memory_limit: str = "1g"
    sandbox_timeout_seconds: int = 300
    sandbox_network_mode: str = "none"

    # Quantum
    quantum_default_backend: str = "aer_simulator"
    quantum_allow_hardware: bool = False
    quantum_hardware_allowlist: str = ""

    # Rate limiting (Section 56/87). Defaults to disabled so local dev/test
    # runs (which reuse one client identity across many rapid requests -
    # see app/tests/conftest.py) are never spuriously throttled; production
    # deployments should set RATE_LIMIT_ENABLED=true (docker-compose.yml
    # does this for the `backend` service).
    rate_limit_enabled: bool = False
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "10/minute"

    @property
    def llm_configured(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
