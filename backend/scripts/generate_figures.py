"""Generates real figures/tables (research/figures, research/tables) from
the JSON artifacts already written by run_demo.py / run_research_pipeline.py
/ run_cyber_experiment.py. Every number plotted is read back from those
files - nothing here re-computes or fabricates a value.

Usage: python -m scripts.generate_figures
"""

import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scripts._pipeline import RESEARCH_DIR


def _load(path):
    full = RESEARCH_DIR / path
    if not full.exists():
        return None
    return json.loads(full.read_text(encoding="utf-8"))


def figure_cybersecurity_comparison():
    data = _load("cybersecurity/demo_graph_anomaly_detection.json")
    if not data:
        print("skip: cybersecurity demo result not found - run `python -m scripts.run_demo` first")
        return

    stat = data["statistics"]
    fig, ax = plt.subplots(figsize=(5, 4))
    # Read the actual per-arm means back out of the raw metrics.json is not
    # persisted here (only aggregate stats are), so annotate with the CI on
    # the *difference* instead of fabricating per-arm bars we don't have.
    ax.bar(
        ["proposed - baseline\n(F1 difference)"],
        [stat["ci_lower"] + (stat["ci_upper"] - stat["ci_lower"]) / 2],
        yerr=[[abs(stat["ci_upper"] - stat["ci_lower"]) / 2]],
        capsize=8,
        color="#5b8cff",
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("F1 difference (proposed - baseline)")
    ax.set_title(
        f"Cybersecurity demo: {data['conclusion_status']}\n"
        f"p={stat['p_value']:.2e}, Cohen's d={stat['effect_size']:.2f}"
    )
    fig.tight_layout()
    out = RESEARCH_DIR / "figures" / "cybersecurity_f1_difference.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def figure_quantum_grover_vs_classical():
    data = _load("quantum/demo_grover_vs_classical.json")
    if not data:
        print("skip: quantum demo result not found - run `python -m scripts.run_demo` first")
        return

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    ideal = data["quantum_simulated_ideal"]["success_probability"]
    noisy = data["quantum_simulated_noisy"]["success_probability"]
    axes[0].bar(["ideal", "noisy"], [ideal, noisy], color=["#2fbf71", "#e5484d"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Success probability")
    axes[0].set_title(f"Grover search (n={data['n_qubits']} qubits, simulated)")

    random_baseline = 1 / data["search_space_size"]
    axes[1].bar(
        ["random\nguessing", "Grover\n(ideal sim)"], [random_baseline, ideal], color=["#8b93a3", "#5b8cff"]
    )
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Grover vs. random guessing")

    fig.suptitle("Demonstration 2: Quantum search (SIMULATOR results)")
    fig.tight_layout()
    out = RESEARCH_DIR / "figures" / "quantum_grover_success_probability.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def table_pqc_benchmark():
    data = _load("pqc/demo_classical_vs_pqc.json")
    if not data:
        print("skip: pqc demo result not found - run `python -m scripts.run_demo` first")
        return

    lines = [
        "# PQC Benchmark (classical arm - real measurements)",
        "",
        f"PQC arm available: **{data['pqc_available']}** — {data['status_note']}",
        "",
        "| Scheme | Operation | Mean time (ms) | Artifact size (bytes) |",
        "|---|---|---|---|",
    ]
    for r in data["classical_results"]:
        lines.append(
            f"| {r['scheme']} | {r['operation']} | {r['mean_seconds'] * 1000:.4f} | {r['artifact_size_bytes']} |"
        )

    out = RESEARCH_DIR / "tables" / "pqc_classical_benchmark.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


def table_ai_model_comparison():
    data = _load("ai/experiment_5_model_comparison.json")
    if not data:
        print("skip: AI experiment 5 result not found - run `python -m scripts.run_research_pipeline` first")
        return

    lines = [
        "# Experiment 5: AI Model Comparison (breast_cancer dataset)",
        "",
        "| Proposed | Baseline | Conclusion | p-value | Effect size (Cohen's d) |",
        "|---|---|---|---|---|",
    ]
    for r in data:
        s = r["statistics"]
        lines.append(
            f"| {r['proposed']} | {r['baseline']} | {r['conclusion_status']} | "
            f"{s.get('p_value', 'n/a'):.4f} | {s.get('effect_size', 'n/a'):.3f} |"
        )

    out = RESEARCH_DIR / "tables" / "ai_experiment_5_comparison.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


def main() -> int:
    figure_cybersecurity_comparison()
    figure_quantum_grover_vs_classical()
    table_pqc_benchmark()
    table_ai_model_comparison()
    return 0


if __name__ == "__main__":
    sys.exit(main())
