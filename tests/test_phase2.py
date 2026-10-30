"""Small checks for the experiment wrapper; the detector is unchanged."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("phase2", Path(__file__).resolve().parents[1] / "repro/phase2.py")
phase2 = importlib.util.module_from_spec(spec)
sys.modules["phase2"] = phase2
spec.loader.exec_module(phase2)


def test_phase2_grid_count_and_alpha():
    assert len(phase2.GRID) == 96
    assert {p["alpha"] for p in phase2.GRID} == {0.005}


def test_phase2_time_conversion():
    p = phase2.points(phase2.FIXED, 61)
    assert (p["train_size"], p["dwins"], p["rwins"]) == (1417, 15, 60)


def test_phase2_event_merging_and_chains():
    frame = pd.DataFrame({"timestamps": [0, 600, 1201], "source_ts": ["a", "b", "c"]})
    events = phase2.merge_events(frame, np.array([0, 1, 2]), 10)
    assert [e["points"] for e in events] == [2, 1]
    assert phase2.max_chain(np.array([1, 2, 4, 5, 6])) == 3
    assert phase2.max_chain(np.array([], dtype=int)) == 0


def test_phase2_robust_sigma():
    assert phase2.mad([1, 2, 3]) == 1.4826


def test_phase2_event_end_is_not_recovery_credit():
    assert phase2.event_mask([-1, 0, 21599, 21600], "drift").tolist() == [False, True, True, False]
    assert phase2.event_mask([-300, 0, 300, 301], "spike").tolist() == [True, True, True, False]
    assert phase2.event_mask([-1, 0, 300], "spike", causal=True).tolist() == [False, True, True]


def test_phase2_injection_is_nonnegative_and_preserves_original():
    original = np.array([.01, .02, .03, .04])
    injected = phase2.inject_values(original, [0, 60, 120, 180], 1, 3, "level_shift", 10, .1)
    assert np.allclose(original, [.01, .02, .03, .04])
    assert np.allclose(injected, [.01, 1.02, 1.03, .04])
    scaled = phase2.inject_values([3., 4., 5., 6.], [0, 60, 120, 180], 0, 4, "variance_change", 2, .1)
    assert np.isclose(np.std(scaled), 2 * np.std([1., 2., 3., 4.]))
