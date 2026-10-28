import subprocess, sys

feats = ["win", "diff", "center"]
for f in feats:
    print(f"\n==========================================", flush=True)
    print(f"=== RUN DL FEAT: {f} ===", flush=True)
    print(f"==========================================\n", flush=True)
    cmd = [
        sys.executable, "-u", "repro/run_baselines.py",
        "gen_out/arima", "*.csv",
        "--models", "ae,vae,lstm",
        "--thr", "oracle",
        "--dl-feat", f,
        "--dl-fit", "all"
    ]
    subprocess.run(cmd, check=True)
