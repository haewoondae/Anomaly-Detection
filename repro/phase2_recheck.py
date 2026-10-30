"""Recheck only seed jobs whose first detection was the recovery boundary."""
from concurrent.futures import ProcessPoolExecutor
import argparse
import json
import shutil
import time

import pandas as pd
from phase2 import OUT, synthetic_job, save_table, dump


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reason", choices=("boundary", "physical"), default="boundary")
    args = parser.parse_args()
    data = pd.read_csv(OUT / "synthetic_seeds.csv")
    affected = data[(data.kind != "spike") & (data.delay_seconds >= data.event_duration_s)] if args.reason == "boundary" else data[(data.kind != "variance_change") & (data.sign < 0)]
    if affected.empty:
        print("No boundary-affected jobs")
        return
    audit = OUT / ("audit/before_" + args.reason + "_recheck")
    audit.mkdir(parents=True, exist_ok=True)
    for name in ("synthetic_seeds.csv", "synthetic_sensitivity.csv", "synthetic_summary.csv"):
        shutil.copy2(OUT / name, audit / name)
    jobs = [(r.channel, r.kind, int(r.magnitude), int(r.seed)) for r in affected.itertuples()]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(synthetic_job, jobs))
    keys = set(jobs)
    keep = [tuple(row) not in keys for row in data[["channel", "kind", "magnitude", "seed"]].itertuples(index=False, name=None)]
    corrected = pd.concat([data[keep], pd.DataFrame([r for r, _ in results])], ignore_index=True)
    corrected.sort_values(["channel", "kind", "magnitude", "seed"]).to_csv(OUT / "synthetic_seeds.csv", index=False)
    sensitivity = pd.read_csv(OUT / "synthetic_sensitivity.csv")
    keep = [tuple(row) not in keys for row in sensitivity[["channel", "kind", "magnitude", "seed"]].itertuples(index=False, name=None)]
    pd.concat([sensitivity[keep], pd.DataFrame([s for _, rows in results for s in rows])], ignore_index=True).to_csv(OUT / "synthetic_sensitivity.csv", index=False)
    summary = corrected.groupby(["channel", "kind", "magnitude"]).agg(
        seeds=("seed", "nunique"), event_recall_mean=("event_recall", "mean"), event_recall_std=("event_recall", "std"),
        causal_recall_mean=("causal_recall", "mean"), delay_mean_s=("delay_seconds", "mean"),
        delay_std_s=("delay_seconds", "std"), delay_observed=("delay_seconds", "count"),
        chain_mean=("max_chain_points", "mean"), chain_std=("max_chain_points", "std")).reset_index()
    summary.to_csv(OUT / "synthetic_summary.csv", index=False)
    old_path = OUT / "synthetic_recheck_status.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {"jobs_rechecked": 0, "seconds": 0}
    stages = old.get("stages", [{"reason": "boundary", "jobs": old["jobs_rechecked"], "seconds": old["seconds"]}] if old["jobs_rechecked"] else [])
    elapsed = time.perf_counter() - t0
    stages.append({"reason": args.reason, "jobs": len(jobs), "seconds": elapsed})
    status = {"jobs_rechecked": old["jobs_rechecked"] + len(jobs), "latest_seed_jobs": jobs,
              "seconds": old["seconds"] + elapsed, "stages": stages,
              "unique_seed_jobs": len(corrected), "total_detector_executions": len(data) + old["jobs_rechecked"] + len(jobs),
              "reason": "Metric boundary and physically valid upward additive injection; detector unchanged"}
    dump("synthetic_recheck_status.json", status)
    print(json.dumps(status), flush=True)


if __name__ == "__main__":
    main()
