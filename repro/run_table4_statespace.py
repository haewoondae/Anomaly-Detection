import subprocess, sys

sig100_files = [
    "gen_out/statespace/statespace_sig100_ber_11.csv",
    "gen_out/statespace/statespace_sig100_uni_12.csv",
    "gen_out/statespace/statespace_sig100_lin_1.csv",
    "gen_out/statespace/statespace_sig100_quad_10.csv",
]

sig300_files = [
    "gen_out/statespace/statespace_sig300_ber_10.csv",
    "gen_out/statespace/statespace_sig300_uni_11.csv",
    "gen_out/statespace/statespace_sig300_lin_12.csv",
    "gen_out/statespace/statespace_sig300_quad_1.csv",
]

print("=== Table 4 State-space sig=100 ===", flush=True)
subprocess.run([sys.executable, "-u", "repro/auto_table4.py"] + sig100_files, check=True)

print("\n=== Table 4 State-space sig=300 ===", flush=True)
subprocess.run([sys.executable, "-u", "repro/auto_table4.py"] + sig300_files, check=True)
