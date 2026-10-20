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

# replace() 후 residual 재계산: LOO 예측값으로 치환하면 해당 점의 잔차는 ~0이어야 함
r_before = r.last
r.replace(loo)
# 치환 후 마지막 점 잔차는 거의 0에 수렴해야 함 (< 1e-8)
check(abs(r.last) < 1e-8, f'TRES replace ok, new residual = {r.last:.2e} (< 1e-8)')

# -----------------------------------------------------------------------
# 3. SESD
# -----------------------------------------------------------------------
from models.osESD_Test import SESD, get_lambda

lam = get_lambda(0.05, 50)
print(f'\n[SESD] lambda(alpha=0.05, n=50) = {lam:.6f}')

# 정상값 검정: 가우시안 표준 정규분포 윈도우에서 검정 (거의 상수 윈도우 대신)
rng_sesd = np.random.default_rng(123)
normal_win = rng_sesd.standard_normal(50).tolist()
sesd_normal = SESD(normal_win, alpha=0.01, maxr=5)
# 평균 근처의 정상값(0.02) 입력 시 False여야 함
r_normal = sesd_normal.test(0.02)
check(r_normal == False, f'normal value in gaussian window flagged={r_normal} (expected False)')

# 마스킹 시나리오:
# 윈도우 안에 이미 큰 스파이크(5.0)가 존재하고, 새로 중간 이상치(2.2)가 들어옴.
# m=1에서는 이전 스파이크(5.0)가 잡혀서 m=2에서 새 점(2.2)이 이상치로 판별되어야 함.
win_mask = [0.1] * 48 + [5.0] + [0.1]
sesd_mask = SESD(win_mask, alpha=0.05, maxr=5)
r_masked = sesd_mask.test(2.2)
check(r_masked == True, f'masking scenario flagged={r_masked} (expected True)')

# replace_last: 이상치 입력 후 clean 값으로 치환 시 mean 감소 확인
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

# 레벨 시프트가 있는 시계열로 local_sd vs global_sd 비교
# 전반부(250): 표준편차 0.1, 후반부(250): 표준편차 2.0
ts_step = np.concatenate([
    np.random.default_rng(42).normal(0.0, 0.1, 250),
    np.random.default_rng(42).normal(10.0, 2.0, 250)
])
res_g = contaminate(ts_step, alpha=0.05, anom_percent=0.04, kind='bernoulli', seed=42, local_sd=False)
res_l = contaminate(ts_step, alpha=0.05, anom_percent=0.04, kind='bernoulli', seed=42, local_sd=True)

# local_sd와 global_sd에 의해 주입된 크기의 편차 차이 검증
diff_g = np.abs(res_g['value'] - ts_step)
diff_l = np.abs(res_l['value'] - ts_step)
check(not np.allclose(diff_g, diff_l), 'local_sd vs global_sd produce distinct anomaly magnitudes on step series')

# -----------------------------------------------------------------------
# 5. Detector end-to-end
# -----------------------------------------------------------------------
from models.osESD_Detector import osESD as run_osESD

print('\n[Detector]')
ts_full = np.cumsum(np.random.default_rng(99).standard_normal(500)).tolist()
ts_full[150] += 15.0
ts_full[300] += 15.0
anoms = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                  alpha=0.05, maxr=5, condition=False, rep_at='loo')
found_150 = any(140 <= a <= 160 for a in anoms)
found_300 = any(290 <= a <= 310 for a in anoms)
check(found_150, f'anomaly near 150: {anoms}')
check(found_300, f'anomaly near 300: {anoms}')

# rep_at='prev' (author style) 동작 확인
anoms_author_rep = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                             alpha=0.05, maxr=5, condition=False, rep_at='prev')
check(isinstance(anoms_author_rep, list), f'rep_at=prev ok, found={len(anoms_author_rep)}')

anoms_sync = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                       alpha=0.05, maxr=5, condition=False, sync_stats=True)
check(isinstance(anoms_sync, list), f'sync_stats=True ok, n={len(anoms_sync)}')

# Rosner vs author lambda 비교
anoms_author_lambda = run_osESD(ts_full, dwins=5, rwins=10, train_size=100,
                                alpha=0.05, maxr=5, condition=False, use_author_lambda=True)
print(f'  Rosner lambda detections : {len(anoms)}')
print(f'  Author lambda detections : {len(anoms_author_lambda)}')
check(isinstance(anoms_author_lambda, list), 'Author lambda execution ok')

# -----------------------------------------------------------------------
print()
if PASS:
    print('=== ALL CHECKS PASSED ===')
else:
    print('=== SOME CHECKS FAILED ===')
    sys.exit(1)
