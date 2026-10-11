"""Cost preview: back-test against past billed runs and basic consistency."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hongik_selfheal.cost_estimate import HIGH, LOW, estimate_run  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402

MODELS = dict(primary_model="claude-sonnet-5", other_models=("gpt-5.4", "gemini-3.6-flash"), redteam_model="gpt-5.4")


def _usd(profile, **kw):
    return estimate_run(initial_srs_v1(), n_repeat=1, profile=profile, **MODELS, **kw)["usd"]


def test_past_runs_fall_inside_the_no_saving_range():
    # 12차 billed $4.33 (no caching), 10차 billed $41.66
    for kw, billed in [(dict(n_per_category=2, max_rounds=3, adaptive_n=1), 4.33),
                       (dict(n_per_category=3, max_rounds=15, adaptive_n=5), 41.66)]:
        assert _usd(LOW, **kw)["plain"] <= billed <= _usd(HIGH, **kw)["plain"]


def test_savings_are_ordered_and_scale_with_size():
    small = _usd(LOW, n_per_category=3, max_rounds=3, adaptive_n=1)
    big = _usd(LOW, n_per_category=10, max_rounds=15, adaptive_n=15)
    assert small["cache_batch"] < small["cache"] < small["plain"]
    assert big["plain"] > 5 * small["plain"]


def test_estimate_only_needs_no_api_key():
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_experiment.py"), "--estimate-cost"],
        capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0 and "예상 비용" in proc.stdout, proc.stderr[-500:]
