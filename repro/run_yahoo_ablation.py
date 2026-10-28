import subprocess, sys

groups = ["A1", "A2", "A3", "A4"]
for g in groups:
    print(f"\n==========================================", flush=True)
    print(f"=== Table 3 Ablation: {g}Benchmark ===", flush=True)
    print(f"==========================================\n", flush=True)
    cmd = [
        sys.executable, "-u", "repro/ablation.py",
        "docs/Data", f"{g}Benchmark/*.csv",
        "50,2,5,3,0.01,1", "1"
    ]
    subprocess.run(cmd, check=True)
