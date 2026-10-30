"""Phase 2 local quality gates and corrected-osESD experiments.

Usage: py -3.11 repro/phase2.py quality|benchmark|fixed|grid|synthetic
Runtime outputs are ignored. This module never connects to a database.
"""
import os
for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from models.osESD_Detector import osESD as detector
from models.osESD_Test import get_lambda

OUT = ROOT / "results/phase2"
FIXED = dict(size_h=24, dwin_min=15, rwin_h=1, maxr=3, alpha=0.005, condition=True)
GRID = [dict(zip(("size_h", "dwin_min", "rwin_h", "maxr", "alpha", "condition"), v))
        for v in itertools.product((12, 24), (5, 15, 30), (.5, 1, 2, 4), (3, 5), (.005,), (True, False))]


def dump(name, obj):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str, allow_nan=False), encoding="utf-8")


def save_table(name, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def mad(x):
    x = np.asarray(x, float)
    return float(1.4826 * np.median(abs(x - np.median(x))))


def load(alias):
    df = pd.read_csv(OUT / "inputs" / ("P-1_" + alias + ".csv"), dtype={"source_ts": str})
    df["parsed_ts"] = pd.to_datetime(df.source_ts, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if df.parsed_ts.isna().any() or not np.isfinite(df.value.to_numpy(float)).all():
        raise ValueError("Invalid timestamp or value: " + alias)
    df = df.sort_values("parsed_ts", kind="stable").reset_index(drop=True)
    if df.parsed_ts.duplicated().any():
        raise ValueError("Duplicate timestamps: " + alias)
    dt = df.parsed_ts.diff().dt.total_seconds()
    df["run_id"] = (dt.fillna(0) >= 3600).cumsum().astype(int)
    return df


def points(config, median):
    return {"train_size": max(4, math.ceil(config["size_h"] * 3600 / median)),
            "dwins": max(2, math.ceil(config["dwin_min"] * 60 / median)),
            "rwins": max(3, math.ceil(config["rwin_h"] * 3600 / median)),
            "maxr": config["maxr"], "alpha": config["alpha"], "condition": config["condition"]}


def run_detector(frame, config, values=None, rep_at="author"):
    median = float(frame.timestamps.diff().median())
    params = points(config, median)
    if not max(params["dwins"], params["rwins"]) < params["train_size"] < len(frame):
        raise ValueError("Run too short or invalid window relationship")
    x = frame.value.to_numpy(float) if values is None else values
    idx = detector(data=x.tolist(), time=frame.timestamps.to_numpy(float).tolist(),
                   use_author_lambda=False, rep_at=rep_at, sync_stats=False, **params)
    return np.asarray(idx, dtype=int), params


def merge_events(frame, idx, minutes=10):
    if not len(idx):
        return []
    groups = np.split(idx, np.flatnonzero(np.diff(frame.timestamps.to_numpy()[idx]) > minutes * 60) + 1)
    return [{"start": str(frame.source_ts.iloc[g[0]]), "end": str(frame.source_ts.iloc[g[-1]]),
             "points": int(len(g)), "span_seconds": float(frame.timestamps.iloc[g[-1]] - frame.timestamps.iloc[g[0]])}
            for g in groups]


def max_chain(idx):
    if not len(idx):
        return 0
    return max(map(len, np.split(idx, np.flatnonzero(np.diff(idx) != 1) + 1)))


def event_mask(relative, kind, window_min=5, duration=21600, causal=False):
    relative = np.asarray(relative)
    if kind == "spike":
        return (relative >= (0 if causal else -window_min * 60)) & (relative <= window_min * 60)
    # The first unchanged point at the end is recovery, not part of the injected event.
    return (relative >= 0) & (relative < duration)


def inject_values(values, timestamps, start, end, kind, magnitude, sigma):
    x = np.asarray(values, float).copy()
    t = np.asarray(timestamps, float)
    if kind == "spike":
        x[start] += magnitude * sigma
    elif kind == "level_shift":
        x[start:end] += magnitude * sigma
    elif kind == "drift":
        x[start:end] += magnitude * sigma * (t[start:end] - t[start]) / 21600
    elif kind == "variance_change":
        center = np.median(x[start:end])
        x[start:end] = center + magnitude * (x[start:end] - center)
    else:
        raise ValueError("Unknown injection kind")
    if not np.isfinite(x).all() or (x < 0).any():
        raise ValueError("Nonphysical synthetic RMS/PtP series")
    return x


def quality():
    all_quality, runs, gates, inputs = [], [], [], []
    hard_stop = []
    for alias in ("VEL", "ACC", "ENV3"):
        path = OUT / "inputs" / ("P-1_" + alias + ".csv")
        raw = pd.read_csv(path, dtype={"source_ts": str})
        parsed = pd.to_datetime(raw.source_ts, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        x = pd.to_numeric(raw.value, errors="coerce").to_numpy(float)
        dt = parsed.sort_values().diff().dt.total_seconds().dropna()
        meta_changes = {k: int(raw[k].nunique(dropna=False)) for k in
                        ("SYS1_ID", "COMPANY_ID", "API_PORT", "POINT_ID", "MEASUREMENT_ID", "AGGR_TIME_CD", "VAL_TYPE", "unit")}
        q = {"channel": alias, "rows": len(raw), "ts_sorted": bool(parsed.is_monotonic_increasing),
             "duplicate_ts": int(parsed.duplicated().sum()), "null_values": int(raw.value.isna().sum()),
             "nan_or_nonnumeric": int(np.isnan(x).sum()), "infinite_values": int(np.isinf(x).sum()),
             "bad_ts": int(parsed.isna().sum()), "zero_values": int((x == 0).sum()),
             "interval_median_s": float(dt.median()), "interval_p95_s": float(dt.quantile(.95)),
             "interval_p99_s": float(dt.quantile(.99)), "interval_max_s": float(dt.max()),
             "gaps_gt_2min": int((dt > 120).sum()), "gaps_gt_1h": int((dt > 3600).sum()),
             "gaps_gt_1day": int((dt > 86400).sum()), "aggr_unit_columns_constant": all(v == 1 for v in meta_changes.values()),
             "historical_unit_or_aggr_changes": "unconfirmed; unit is current setpoint metadata; aggregation filtered by extraction"}
        all_quality.append(q)
        inputs.append({"channel": alias, "file": path.relative_to(OUT).as_posix(), "rows": len(raw),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        if any(q[k] for k in ("duplicate_ts", "nan_or_nonnumeric", "infinite_values", "bad_ts")) or not q["aggr_unit_columns_constant"]:
            hard_stop.append(alias + ": invalid input")
            continue
        frame = load(alias)
        for rid, g in frame.groupby("run_id"):
            g = g.reset_index(drop=True)
            median = float(g.timestamps.diff().median())
            runs.append({"channel": alias, "run_id": int(rid), "rows": len(g),
                         "start": g.source_ts.iloc[0], "end": g.source_ts.iloc[-1],
                         "interval_median_s": median, "duration_hours": float((g.timestamps.iloc[-1] - g.timestamps.iloc[0]) / 3600),
                         "initialization_normal": "unconfirmed"})
            for h in (12, 24):
                size = points(dict(FIXED, size_h=h), median)["train_size"]
                a = g.value.to_numpy()[:size]
                delta = np.diff(a)
                scale = mad(delta)
                # A screen, not a normal-state label: sudden increments over 10 robust sigmas stop execution.
                suspect = abs(delta - np.median(delta)) > 10 * scale if scale > 0 else abs(delta - np.median(delta)) > 0
                row = {"channel": alias, "run_id": int(rid), "size_hours": h, "size_points": size,
                       "mad_sigma": mad(a), "increment_mad_sigma": scale, "suspect_jumps": int(suspect.sum()),
                       "normal_state": "unconfirmed", "screen": "increment deviation >10 MAD sigma", "sufficient_length": len(g) > size}
                gates.append(row)
                if suspect.any() or len(g) <= size or mad(a) <= 0:
                    hard_stop.append(alias + ": suspect or insufficient initialization")
    save_table("quality.csv", all_quality)
    save_table("runs.csv", runs)
    save_table("initialization.csv", gates)
    save_table("input_files.csv", inputs)
    dump("quality_gate.json", {"status": "stopped" if hard_stop else "passed", "reasons": hard_stop,
         "normal_status": "unconfirmed", "unit_history": "unconfirmed"})
    print(json.dumps({"quality_gate": "stopped" if hard_stop else "passed", "runs": len(runs), "reasons": hard_stop}), flush=True)
    if hard_stop:
        raise SystemExit(2)


def benchmark():
    frame = load("VEL")
    run = frame[frame.run_id == 0].reset_index(drop=True)
    get_lambda.cache_clear()
    before = get_lambda.cache_info()._asdict()
    t0 = time.perf_counter()
    idx, params = run_detector(run, FIXED)
    elapsed = time.perf_counter() - t0
    longest = max(len(load(ch)) for ch in ("VEL", "ACC", "ENV3"))
    # Conservative adjustment: full channel length, twice measured cost, process overhead allowance.
    channel_seconds = elapsed * longest / len(run)
    estimate = channel_seconds * (3 + 288 + 360) / 6 * 2 + 120
    result = {"channel": "VEL", "run_id": 0, "rows": len(run), "seconds": elapsed,
              "detections": len(idx), "parameters": params, "workers": 6, "cache_before": before,
              "cache_after": get_lambda.cache_info()._asdict(), "processor": platform.processor(),
              "logical_cpus": os.cpu_count(), "python": platform.python_version(), "platform": platform.platform(),
              "estimated_total_seconds": estimate, "within_90min": estimate <= 5400,
              "estimate_formula": "2 * t1 * longest_channel_rows/benchmark_run_rows * (3+288+360)/6 + 120",
              "detector_options": {"use_author_lambda": False, "rep_at": "author", "sync_stats": False}}
    dump("benchmark.json", result)
    print(json.dumps(result), flush=True)
    if estimate > 5400:
        raise SystemExit(2)


def original_job(job):
    alias, config_id, config = job
    frame = load(alias)
    count, events, records, param_rows = 0, [], [], []
    chain, online_seconds = 0, 0.
    t0 = time.perf_counter()
    for rid, g in frame.groupby("run_id"):
        g = g.reset_index(drop=True)
        idx, params = run_detector(g, config)
        count += len(idx)
        chain = max(chain, max_chain(idx))
        events.extend(dict(e, run_id=int(rid)) for e in merge_events(g, idx))
        online_seconds += float(g.timestamps.iloc[-1] - g.timestamps.iloc[params["train_size"]])
        param_rows.append(dict(channel=alias, config_id=config_id, run_id=int(rid), **params,
                               actual_init_span_s=float(g.timestamps.iloc[params["train_size"] - 1] - g.timestamps.iloc[0])))
        if config_id == "fixed":
            records.extend({"channel": alias, "run_id": int(rid), "run_index": int(i),
                            "source_ts": g.source_ts.iloc[i], "value": float(g.value.iloc[i])} for i in idx)
    return {"channel": alias, "config_id": config_id, **config, "detections": count,
            "events": len(events), "max_chain_points": chain, "online_days": online_seconds / 86400,
            "events_per_online_day": len(events) / (online_seconds / 86400), "seconds": time.perf_counter() - t0,
            "detector_calls": int(frame.run_id.nunique()), "event_rows": events,
            "detection_rows": records, "parameter_rows": param_rows}


def fixed():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    results, detections, events, params = [], [], [], []
    for alias in ("VEL", "ACC", "ENV3"):
        r = original_job((alias, "fixed", FIXED))
        detections.extend(r.pop("detection_rows"))
        events.extend(dict(e, channel=alias) for e in r.pop("event_rows"))
        params.extend(r.pop("parameter_rows"))
        results.append(r)
        f = load(alias)
        fig, ax = plt.subplots(figsize=(12, 4))
        for _, g in f.groupby("run_id"):
            ax.plot(g.parsed_ts, g.value, color="steelblue", linewidth=.5)
        d = [x for x in detections if x["channel"] == alias]
        if d:
            ax.scatter(pd.to_datetime([x["source_ts"] for x in d]), [x["value"] for x in d], s=7, c="darkorange", label="Detected")
        ax.axvline(pd.Timestamp("2026-10-12 11:33:00"), color="crimson", linestyle="--", linewidth=.8, label="Unconfirmed change")
        ax.set(title="Site A / P-1 / " + alias, ylabel=f.unit.iloc[0], xlabel="Source TS (timezone unconfirmed)")
        ax.legend(loc="upper right")
        fig.autofmt_xdate()
        fig.tight_layout()
        dest = OUT / "figures" / (alias + "_fixed.png")
        dest.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(dest, dpi=160)
        plt.close(fig)
        print(json.dumps(r), flush=True)
    save_table("fixed_summary.csv", results)
    save_table("fixed_detections.csv", detections)
    save_table("fixed_events.csv", events)
    save_table("fixed_parameters.csv", params)


def grid():
    jobs = [(ch, i, cfg) for ch in ("VEL", "ACC", "ENV3") for i, cfg in enumerate(GRID)]
    summary, params = [], []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(original_job, j) for j in jobs]
        for fut in as_completed(futures):
            r = fut.result()
            r.pop("detection_rows")
            r.pop("event_rows")
            params.extend(r.pop("parameter_rows"))
            summary.append(r)
            if len(summary) % 24 == 0:
                save_table("grid_summary.csv", summary)
                print("grid", len(summary), "/", len(jobs), "seconds", round(time.perf_counter() - t0, 1), flush=True)
    save_table("grid_summary.csv", sorted(summary, key=lambda r: (r["channel"], r["config_id"])))
    save_table("grid_parameters.csv", params)
    dump("grid_status.json", {"status": "complete", "settings_per_channel": len(GRID), "channel_setting_runs": len(summary),
         "detector_calls": sum(r["detector_calls"] for r in summary), "workers": 6, "alpha": .005,
         "seconds": time.perf_counter() - t0, "deterministic_seeds": "not applicable"})


_SYNTH_CACHE = {}


def synthetic_job(job):
    alias, kind, magnitude, seed = job
    if alias not in _SYNTH_CACHE:
        frame = load(alias)
        baseline = pd.read_csv(OUT / "fixed_detections.csv")
        baseline = baseline[baseline.channel == alias]
        _SYNTH_CACHE[alias] = (frame, baseline)
    frame, baseline = _SYNTH_CACHE[alias]
    groups = {int(r): g.reset_index(drop=True) for r, g in frame.groupby("run_id")}
    eligible = []
    # One event per injected input. With one event, the >=24h inter-event rule is vacuous.
    # Candidate placement is baseline-quiet, not independently verified normal operation.
    for rid, g in groups.items():
        size = points(FIXED, float(g.timestamps.diff().median()))["train_size"]
        ts = g.timestamps.to_numpy(float)
        mask = (np.arange(len(g)) >= size) & (ts + 21600 <= ts[-1])
        original_idx = baseline[baseline.run_id == rid].run_index.to_numpy(int)
        for i in original_idx:
            mask &= ~((ts - 300 <= ts[i]) & (ts + 21600 >= ts[i]))
        eligible.extend((rid, int(i)) for i in np.flatnonzero(mask))
    if not eligible:
        raise ValueError("No baseline-quiet post-initialization injection candidate")
    rng = np.random.default_rng(seed)
    rid, start = eligible[int(rng.integers(len(eligible)))]
    sign = 1  # RMS and PtP are nonnegative; additive anomalies are upward changes.
    g = groups[rid]
    t = g.timestamps.to_numpy(float)
    size = points(FIXED, float(g.timestamps.diff().median()))["train_size"]
    sigma = mad(g.value.to_numpy(float)[:size])
    if sigma <= 0:
        raise ValueError("Zero initial MAD")
    end = start + 1 if kind == "spike" else int(np.searchsorted(t, t[start] + 21600, side="left"))
    x = inject_values(g.value.to_numpy(float), t, start, end, kind, magnitude, sigma)
    t0 = time.perf_counter()
    idx, params = run_detector(g, FIXED, x)
    elapsed = time.perf_counter() - t0
    duration = 0 if kind == "spike" else 21600
    relative = t[idx] - t[start]
    hit_mask = event_mask(relative, kind, duration=duration)
    causal = relative[event_mask(relative, kind, duration=duration, causal=True)]
    row = {"channel": alias, "kind": kind, "magnitude": magnitude, "seed": seed, "run_id": rid,
           "event_start": str(g.source_ts.iloc[start]), "event_duration_s": duration,
           "event_index": start, "event_end_index_exclusive": end, "sign": sign, "initial_sigma": sigma,
           "eligible_start_count": len(eligible), "placement": "baseline-quiet post-initialization",
           "event_recall": int(hit_mask.any()), "causal_recall": int(len(causal) > 0),
           "delay_seconds": float(causal.min()) if len(causal) else None,
           "detections": len(idx), "max_chain_points": max_chain(idx), "seconds": elapsed}
    rows = []
    for window_min in (1, 5, 10):
        for merge_min in (5, 10, 20):
            hit = event_mask(relative, kind, window_min, duration)
            events = merge_events(g, idx, merge_min)
            # Exclude the entire synthetic affected tail from background burden; retain it as a separate count.
            background = idx[(relative < -window_min * 60) | (relative > duration + 4 * 3600)]
            background_events = len(merge_events(g, background, merge_min))
            exposure = (t[-1] - t[params["train_size"]]) - min(duration + 4 * 3600 + window_min * 60,
                               t[-1] - t[start] + window_min * 60)
            perday = background_events / (exposure / 86400) if exposure > 0 else None
            rows.append({"channel": alias, "kind": kind, "magnitude": magnitude, "seed": seed,
                         "spike_window_minutes": window_min, "merge_minutes": merge_min,
                         "event_recall": int(hit.any()), "events": len(events), "background_events_per_day": perday,
                         "background_status": "normal assumed; event plus 4h tail excluded",
                         **{"within_" + str(v) + "_events_per_day": bool(perday <= v) if perday is not None else None for v in (.5, 1, 2)}})
    return row, rows


def synthetic():
    jobs = [(ch, kind, size, seed) for ch in ("VEL", "ACC", "ENV3")
            for kind in ("spike", "level_shift", "drift", "variance_change")
            for size in ((2, 3, 5) if kind == "variance_change" else (3, 5, 10)) for seed in range(10)]
    results, sensitivity = [], []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(synthetic_job, j) for j in jobs]
        for fut in as_completed(futures):
            r, s = fut.result()
            results.append(r)
            sensitivity.extend(s)
            if len(results) % 30 == 0:
                save_table("synthetic_seeds.csv", results)
                print("synthetic", len(results), "/", len(jobs), "seconds", round(time.perf_counter() - t0, 1), flush=True)
    save_table("synthetic_seeds.csv", sorted(results, key=lambda r: (r["channel"], r["kind"], r["magnitude"], r["seed"])))
    save_table("synthetic_sensitivity.csv", sensitivity)
    df = pd.DataFrame(results)
    summary = df.groupby(["channel", "kind", "magnitude"]).agg(
        seeds=("seed", "nunique"), event_recall_mean=("event_recall", "mean"), event_recall_std=("event_recall", "std"),
        causal_recall_mean=("causal_recall", "mean"), delay_mean_s=("delay_seconds", "mean"),
        delay_std_s=("delay_seconds", "std"), delay_observed=("delay_seconds", "count"),
        chain_mean=("max_chain_points", "mean"), chain_std=("max_chain_points", "std")).reset_index()
    summary.to_csv(OUT / "synthetic_summary.csv", index=False)
    dump("synthetic_status.json", {"status": "complete", "channel_seed_runs": len(results), "seeds": list(range(10)),
         "settings": [FIXED], "events_per_input": 1, "seconds": time.perf_counter() - t0,
         "variance_definition": "standard deviation factor around injected-segment median",
         "sigma_definition": "MAD*1.4826 of that run's initialization prefix", "placement": "baseline-quiet, not verified normal"})


def supplemental():
    """Optional replacement comparison and one weak-alarm case; default stays author."""
    comparisons = []
    for alias in ("VEL", "ACC", "ENV3"):
        for rid, g in load(alias).groupby("run_id"):
            g = g.reset_index(drop=True)
            t0 = time.perf_counter()
            idx, _ = run_detector(g, FIXED, rep_at="loo")
            comparisons.append({"channel": alias, "run_id": int(rid), "rep_at": "loo",
                "detections": len(idx), "events": len(merge_events(g, idx)),
                "max_chain_points": max_chain(idx), "seconds": time.perf_counter() - t0})
    save_table("replacement_loo.csv", comparisons)
    p = OUT / "inputs/P-2_VEL.csv"
    if not p.exists():
        return
    g = pd.read_csv(p, dtype={"source_ts": str})
    g["parsed_ts"] = pd.to_datetime(g.source_ts)
    if g.parsed_ts.duplicated().any() or not np.isfinite(g.value).all():
        raise ValueError("Invalid case input")
    dt = g.timestamps.diff()
    if (dt >= 3600).any():
        raise ValueError("Split case runs before executing")
    size = points(FIXED, float(dt.median()))["train_size"]
    delta = np.diff(g.value.to_numpy(float)[:size])
    s = mad(delta)
    if s == 0 or (abs(delta - np.median(delta)) > 10 * s).any():
        dump("STOP.json", {"reason": "suspect case initialization"})
        raise ValueError("Suspect case initialization")
    idx, params = run_detector(g, FIXED)
    labels = json.loads((OUT / "alarm_case_labels.json").read_text(encoding="utf-8"))
    det_times = g.parsed_ts.iloc[idx]
    cases = []
    for label in labels:
        ts = pd.Timestamp(label["source_ts"])
        rel = (det_times - ts).dt.total_seconds()
        prev = rel[rel <= 0]
        cases.append({"site": "site_C", "equipment": "P-2", **label,
            "detected_within_5min_raw_ts": bool((abs(rel) <= 300).any()),
            "detected_within_10min_raw_ts": bool((abs(rel) <= 600).any()),
            "previous_detection_lead_s": float(-prev.max()) if len(prev) else None,
            "timestamp_alignment": "unconfirmed; raw string comparison only"})
    save_table("alarm_case_comparison.csv", cases)
    save_table("alarm_case_detections.csv", [{"source_ts": g.source_ts.iloc[i], "index": int(i)} for i in idx])
    dump("alarm_case_analysis.json", {"site": "site_C", "equipment": "P-2", "rows": len(g),
        "duplicates": 0, "null": 0, "infinite": 0, "zeros": int((g.value == 0).sum()),
        "interval_median_s": float(dt.median()), "interval_p95_s": float(dt.quantile(.95)),
        "interval_p99_s": float(dt.quantile(.99)), "interval_max_s": float(dt.max()),
        "gaps_gt_2min": int((dt > 120).sum()), "gaps_gt_1h": int((dt > 3600).sum()),
        "gaps_gt_1day": int((dt > 86400).sum()), "parameters": params,
        "value_type": int(g.VAL_TYPE.iloc[0]), "unit": str(g.unit.iloc[0]),
        "initialization": "10 MAD increment screen passed; normal unconfirmed",
        "detections": len(idx), "events": len(merge_events(g, idx)), "max_chain_points": max_chain(idx),
        "labels": "weak alarm, not confirmed failure", "timezone": "unconfirmed"})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("quality", "benchmark", "fixed", "grid", "synthetic", "supplemental"))
    a = p.parse_args()
    if a.stage != "quality":
        gate = json.loads((OUT / "quality_gate.json").read_text(encoding="utf-8"))
        if gate["status"] != "passed":
            raise SystemExit("Quality gate not passed")
    if a.stage in ("fixed", "grid", "synthetic"):
        bench = json.loads((OUT / "benchmark.json").read_text(encoding="utf-8"))
        if not bench["within_90min"]:
            raise SystemExit("Runtime estimate exceeds 90 minutes")
    globals()[a.stage]()


if __name__ == "__main__":
    main()
