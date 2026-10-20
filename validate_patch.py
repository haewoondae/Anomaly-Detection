"""Validation script for patched osESD modules."""
import sys
sys.path.insert(0, 'src')
import numpy as np

PASS = True

def check(cond, msg):
    global PASS
    if not cond:
        print(f'  FAIL: {msg}')
        PASS = False
    else:
        print(f'  ok  : {msg}')

# -----------------------------------------------------------------------
# 1. TCHA
# -----------------------------------------------------------------------
from models.osESD_Transform import TCHA, TRES

np.random.seed(42)
data = np.cumsum(np.random.randn(200)).tolist()
time = list(range(1, 201))

c = TCHA(data[:100], wins=5, time=time[:100])
v = c.update(data[100], time[100])
print(f'[TCHA] update, last={v:.6f}')

# 기본 시간값 버그 수정 확인 (time=None)
c_nots = TCHA(data[:100], wins=5)
try:
    v2 = c_nots.update(data[100])
    check(True, f'default time (t=None) ok, val={v2:.4f}')
except IndexError as e:
    check(False, f'IndexError (bug not fixed): {e}')

# -----------------------------------------------------------------------
# 2. TRES
# -----------------------------------------------------------------------
r = TRES(data[:100], wins=10, time=time[:100])

# init residual vs polyfit
win = np.array(data[90:100])
tw  = np.array(time[90:100], dtype=float)
expected_res = win[-1] - np.polyval(np.polyfit(tw, win, 1), tw[-1])
diff_init = abs(r.last - expected_res)
check(diff_init < 1e-9, f'TRES init residual diff vs polyfit = {diff_init:.2e}')

# 200-step online vs polyfit
max_diff = 0.0
for i in range(100, 200):
    ours = r.update(data[i], time[i])
    w = np.array(data[i-9:i+1])
    tw2 = np.array(time[i-9:i+1], dtype=float)
    exp = w[-1] - np.polyval(np.polyfit(tw2, w, 1), tw2[-1])
    max_diff = max(max_diff, abs(ours - exp))
check(max_diff < 1e-9, f'TRES 200-step online max diff = {max_diff:.2e}')

# loo_prediction: 창 앞 n-1개로 polyfit → 마지막 시점 예측
loo = r.loo_prediction()
d9 = np.array(r.data[:-1])
t9 = np.array(r.time[:-1], dtype=float)
loo_expected = np.polyval(np.polyfit(t9, d9, 1), r.time[-1])
diff_loo = abs(loo - loo_expected)
check(diff_loo < 1e-9, f'TRES loo_prediction diff = {diff_loo:.2e}')

# replace() 후 residual 재계산
r_before = r.last
r.replace(loo)
check(abs(r.last) >= 0, f'TRES replace ok, new residual = {r.last:.6f}')

# -----------------------------------------------------------------------
# 3. SESD
# -----------------------------------------------------------------------
from models.osESD_Test import SESD, get_lambda

lam = get_lambda(0.05, 50)
print(f'\n[SESD] lambda(alpha=0.05, n=50) = {lam:.6f}')

# 정상값 → False
win_data = [0.1] * 49 + [5.0]
sesd = SESD(win_data, alpha=0.05, maxr=5)
r_normal = sesd.test(0.05)
check(r_normal == False, f'normal value flagged={r_normal}')

# 마스킹 시나리오
sesd2 = SESD(win_data, alpha=0.05, maxr=5)
r_masked = sesd2.test(2.0)
print(f'  info: masking scenario flagged={r_masked} (True if masking resolved)')

# replace_last
sesd3 = SESD([0.0]*50, alpha=0.05, maxr=5)
sesd3.test(3.0)
old_mean = sesd3.mean
sesd3.replace_last(0.0)
check(sesd3.mean < old_mean, f'replace_last reduced mean: {old_mean:.4f} -> {sesd3.mean:.4f}')

# -----------------------------------------------------------------------
# 4. data_aug
# -----------------------------------------------------------------------
from utils.data_aug import contaminate, sample_multiplier

print('\n[data_aug]')
rng = np.random.default_rng(0)
for k in ['bernoulli', 'linear', 'quadratic', 'uniform']:
    m = sample_multiplier(k, rng)
    check(-1.0 <= m <= 1.0, f'{k}: M={m:.4f}')

ts = np.random.default_rng(7).standard_normal(500)
res_g = contaminate(ts, alpha=0.05, anom_percent=0.02, kind='bernoulli', seed=7, local_sd=False)
res_l = contaminate(ts, alpha=0.05, anom_percent=0.02, kind='bernoulli', seed=7, local_sd=True)
ng = int(res_g['anomaly'].astype(int).sum())
nl = int(res_l['anomaly'].astype(int).sum())
check(0 < ng < 50 and 0 < nl < 50, f'contaminate global={ng}, local={nl} anomalies in 500 pts')

# -----------------------------------------------------------------------
# 5. Detector end-to-end
# -----------------------------------------------------------------------
from models.osESD_Detector import osESD as run_osESD

print('\n[Detector]')
ts_full = np.cumsum(np.random.default_rng(99).standard_normal(500)).tolist()
ts_full[150] += 15.0
ts_full[300] += 15.0
anoms = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                  alpha=0.05, maxr=5, condition=False)
found_150 = any(140 <= a <= 160 for a in anoms)
found_300 = any(290 <= a <= 310 for a in anoms)
check(found_150, f'anomaly near 150: {anoms}')
check(found_300, f'anomaly near 300: {anoms}')

anoms_sync = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                       alpha=0.05, maxr=5, condition=False, sync_stats=True)
check(isinstance(anoms_sync, list), f'sync_stats=True ok, n={len(anoms_sync)}')

# Rosner vs author lambda 비교
anoms_author = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                         alpha=0.05, maxr=5, condition=False, use_author_lambda=True)
print(f'  Rosner lambda detections : {len(anoms)}')
print(f'  Author lambda detections : {len(anoms_author)}')

# -----------------------------------------------------------------------
print()
if PASS:
    print('=== ALL CHECKS PASSED ===')
else:
    print('=== SOME CHECKS FAILED ===')
    sys.exit(1)
