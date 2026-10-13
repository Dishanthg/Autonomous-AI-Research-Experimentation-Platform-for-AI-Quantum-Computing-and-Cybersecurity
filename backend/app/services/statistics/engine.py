"""Deterministic statistical engine (Section 38/39/V).

No LLM is involved anywhere in this module. Every number here comes from
numpy/scipy computation over the raw metric values passed in. This is the
ONLY code path allowed to write app.models.result.StatisticalTest rows.
"""

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from scipy import stats


@dataclass
class DescriptiveStats:
    n: int
    mean: float
    median: float
    std: float
    ci_lower: float
    ci_upper: float
    ci_level: float


@dataclass
class ComparisonResult:
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    effect_size_type: str
    ci_lower: Optional[float]
    ci_upper: Optional[float]
    ci_level: float
    correction_method: Optional[str] = None


def describe(values: list[float], ci_level: float = 0.95) -> DescriptiveStats:
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    mean = float(np.mean(arr))
    median = float(np.median(arr))
    std = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    if n > 1:
        boot_means = _bootstrap_means(arr, n_boot=5000)
        lo_pct = (1 - ci_level) / 2 * 100
        hi_pct = (1 + ci_level) / 2 * 100
        ci_lower, ci_upper = np.percentile(boot_means, [lo_pct, hi_pct])
    else:
        ci_lower = ci_upper = mean

    return DescriptiveStats(
        n=n,
        mean=mean,
        median=median,
        std=std,
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        ci_level=ci_level,
    )


def _bootstrap_means(arr: np.ndarray, n_boot: int = 5000, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = len(arr)
    idx = rng.integers(0, n, size=(n_boot, n))
    return arr[idx].mean(axis=1)


def cohens_d(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n1, n2 = len(a_arr), len(b_arr)
    pooled_std = np.sqrt(
        ((n1 - 1) * np.var(a_arr, ddof=1) + (n2 - 1) * np.var(b_arr, ddof=1)) / (n1 + n2 - 2)
    )
    if pooled_std == 0:
        return 0.0
    return float((np.mean(a_arr) - np.mean(b_arr)) / pooled_std)


def compare_two_groups(
    a: list[float],
    b: list[float],
    method: Literal["auto", "t-test", "mann-whitney"] = "auto",
    ci_level: float = 0.95,
) -> ComparisonResult:
    """Compares group a (e.g. proposed method) against b (baseline).
    Chooses a parametric t-test when both groups pass a Shapiro-Wilk
    normality check (n>=3) and a non-parametric Mann-Whitney U otherwise -
    the choice itself is deterministic, not left to LLM judgment."""
    a_arr, b_arr = np.asarray(a, dtype=float), np.asarray(b, dtype=float)

    if method == "auto":
        method = _choose_test(a_arr, b_arr)

    effect = cohens_d(a, b)

    if method == "t-test":
        stat, p = stats.ttest_ind(a_arr, b_arr, equal_var=False)
        test_name = "welch_t_test"
    else:
        stat, p = stats.mannwhitneyu(a_arr, b_arr, alternative="two-sided")
        test_name = "mann_whitney_u"

    diff_ci = _bootstrap_diff_ci(a_arr, b_arr, ci_level=ci_level)

    return ComparisonResult(
        test_name=test_name,
        statistic=float(stat),
        p_value=float(p),
        effect_size=effect,
        effect_size_type="cohens_d",
        ci_lower=diff_ci[0],
        ci_upper=diff_ci[1],
        ci_level=ci_level,
    )


def _choose_test(a: np.ndarray, b: np.ndarray) -> str:
    if len(a) < 3 or len(b) < 3:
        return "mann-whitney"
    _, p_a = stats.shapiro(a)
    _, p_b = stats.shapiro(b)
    return "t-test" if (p_a > 0.05 and p_b > 0.05) else "mann-whitney"


def _bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, ci_level: float, n_boot: int = 5000, seed: int = 42):
    rng = np.random.default_rng(seed)
    na, nb = len(a), len(b)
    idx_a = rng.integers(0, na, size=(n_boot, na))
    idx_b = rng.integers(0, nb, size=(n_boot, nb))
    diffs = a[idx_a].mean(axis=1) - b[idx_b].mean(axis=1)
    lo_pct = (1 - ci_level) / 2 * 100
    hi_pct = (1 + ci_level) / 2 * 100
    lo, hi = np.percentile(diffs, [lo_pct, hi_pct])
    return float(lo), float(hi)


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Multiple-comparison correction (Section V). Returns adjusted p-values
    in the original order."""
    arr = np.asarray(p_values, dtype=float)
    n = len(arr)
    order = np.argsort(arr)
    adjusted = np.empty(n)
    running_max = 0.0
    for rank, idx in enumerate(order):
        adj = (n - rank) * arr[idx]
        running_max = max(running_max, adj)
        adjusted[idx] = min(running_max, 1.0)
    return adjusted.tolist()
