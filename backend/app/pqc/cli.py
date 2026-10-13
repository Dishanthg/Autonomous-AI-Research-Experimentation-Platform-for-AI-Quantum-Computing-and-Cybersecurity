"""`make pqc` - CLI for the classical-vs-post-quantum crypto benchmark
(Section 29/69). Reports real measurements for the classical arm always;
honestly reports NOT_IMPLEMENTED for the PQC arm if liboqs is unavailable.

Usage: python -m app.pqc.cli --runs 20
"""

import argparse
import sys

from app.pqc.benchmark import run_comparison


def main() -> int:
    parser = argparse.ArgumentParser(description="ResearchMind-Q PQC benchmark CLI")
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    report = run_comparison(n_runs=args.runs)

    print("=== Classical (real measurements) ===")
    for r in report.classical_results:
        print(
            f"  {r.scheme:20s} {r.operation:12s} {r.mean_seconds * 1000:10.4f} ms  "
            f"({r.artifact_size_bytes} bytes, n={r.n_runs})"
        )

    print("\n=== Post-quantum ===")
    if not report.pqc_available:
        print(f"  {report.status_note}")
    else:
        for r in report.pqc_results:
            print(
                f"  {r.scheme:20s} {r.operation:12s} {r.mean_seconds * 1000:10.4f} ms  "
                f"({r.artifact_size_bytes} bytes, n={r.n_runs})"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
