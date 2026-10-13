import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from app.services.codegen.ai_templates import render_model_comparison_script
from app.services.codegen.cyber_templates import render_intrusion_detection_script


def _run_script(script: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        (workdir / "experiment.py").write_text(script, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "experiment.py"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "EXPERIMENT_COMPLETE" in result.stdout
        return json.loads((workdir / "output" / "metrics.json").read_text())


def test_ai_model_comparison_script_runs_and_emits_metrics():
    script = render_model_comparison_script(
        dataset="synthetic_classification",
        baseline="logistic_regression",
        proposed="random_forest",
        num_runs=3,
        base_seed=42,
        n_samples=500,
        n_features=10,
    )
    data = _run_script(script)
    assert len(data["results"]["baseline"]["f1"]) == 3
    assert len(data["results"]["proposed"]["f1"]) == 3
    assert all(0.0 <= v <= 1.0 for v in data["results"]["baseline"]["f1"])


def test_ai_model_comparison_rejects_unsupported_baseline():
    with pytest.raises(ValueError):
        render_model_comparison_script(
            dataset="synthetic_classification",
            baseline="not_a_real_model",
            proposed="random_forest",
            num_runs=1,
            base_seed=1,
        )


def test_cyber_intrusion_detection_script_runs_and_emits_metrics():
    script = render_intrusion_detection_script(
        baseline="rule_based",
        proposed="random_forest",
        num_runs=3,
        base_seed=1,
        n_samples=800,
        n_features=8,
    )
    data = _run_script(script)
    assert len(data["results"]["baseline"]["f1"]) == 3
    assert "false_positive_rate" in data["results"]["proposed"]


def test_cyber_script_rejects_unsupported_detector():
    with pytest.raises(ValueError):
        render_intrusion_detection_script(
            baseline="quantum_magic", proposed="random_forest", num_runs=1, base_seed=1
        )
