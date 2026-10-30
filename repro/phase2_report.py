"""Build anonymized Phase 2 tables and figures from ignored runtime results."""
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2 import OUT, FIXED, load, merge_events, points, save_table, dump


def table(frame):
    return frame.astype(object).where(pd.notna(frame), "-").to_markdown(index=False, floatfmt=".3f")


def burden():
    det = pd.read_csv(OUT / "fixed_detections.csv")
    rows, sensitivity = [], []
    for alias in ("VEL", "ACC", "ENV3"):
        frame = load(alias)
        low_count, low_events, low_seconds = 0, 0, 0.
        after_init_count = 0
        for rid, g in frame.groupby("run_id"):
            g = g.reset_index(drop=True)
            idx = det[(det.channel == alias) & (det.run_id == rid)].run_index.to_numpy(int)
            size = points(FIXED, float(g.timestamps.diff().median()))["train_size"]
            t = g.timestamps.to_numpy(float)
            x = g.value.to_numpy(float)
            cutoff = float(np.quantile(x[size:], .1))
            weights = np.diff(t, append=t[-1])
            online = np.arange(len(g)) >= size
            low = (x <= cutoff) & online
            low_idx = idx[low[idx]]
            low_count += len(low_idx)
            low_events += len(merge_events(g, low_idx))
            low_seconds += weights[low].sum()
            after_init_count += int((t[idx] <= t[size] + 3600).sum())
        rows.append({"channel": alias, "low_definition": "bottom decile per run online segment",
            "low_detected_points": low_count, "low_events": low_events, "low_exposure_days": low_seconds / 86400,
            "low_events_per_exposure_day": low_events / (low_seconds / 86400) if low_seconds else None,
            "first_hour_after_init_detected_points": after_init_count,
            "first_hour_after_gap": "not evaluable; reinitialization blind period",
            "ground_truth": "unconfirmed normal operation"})
        for minutes in (5, 10, 20):
            event_count, exposure = 0, 0.
            for rid, g in frame.groupby("run_id"):
                g = g.reset_index(drop=True)
                idx = det[(det.channel == alias) & (det.run_id == rid)].run_index.to_numpy(int)
                event_count += len(merge_events(g, idx, minutes))
                size = points(FIXED, float(g.timestamps.diff().median()))["train_size"]
                exposure += g.timestamps.iloc[-1] - g.timestamps.iloc[size]
            perday = event_count / (exposure / 86400)
            for threshold in (.5, 1, 2):
                sensitivity.append({"channel": alias, "merge_minutes": minutes, "events": event_count,
                    "events_per_online_day": perday, "allowance_per_day": threshold, "within_allowance": perday <= threshold})
    save_table("baseline_burden.csv", rows)
    save_table("baseline_sensitivity.csv", sensitivity)
    return pd.DataFrame(rows), pd.DataFrame(sensitivity)


def figures(syn):
    aliases = ("VEL", "ACC", "ENV3")
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2))
    for ax, kind in zip(axes, ("spike", "level_shift", "drift", "variance_change")):
        pivot = syn[syn.kind == kind].pivot(index="channel", columns="magnitude", values="event_recall_mean").reindex(aliases)
        ax.imshow(pivot.values, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        ax.set(title=kind, xticks=range(len(pivot.columns)), xticklabels=pivot.columns, yticks=range(3), yticklabels=aliases,
               xlabel="SD factor" if kind == "variance_change" else "MAD sigma factor")
        for i in range(3):
            for j in range(len(pivot.columns)):
                ax.text(j, i, f"{pivot.iloc[i,j]:.2f}", ha="center", va="center", color="white" if pivot.iloc[i,j] > .6 else "black")
    fig.suptitle("Site A / P-1: synthetic event recall (10 seeds, baseline-quiet placements)")
    fig.tight_layout()
    fig.savefig(OUT / "figures/synthetic_recall.png", dpi=160)
    plt.close(fig)
    case = pd.read_csv(OUT / "inputs/P-2_VEL.csv")
    det = pd.read_csv(OUT / "alarm_case_detections.csv")
    labels = pd.read_csv(OUT / "alarm_case_comparison.csv")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(pd.to_datetime(case.source_ts), case.value, lw=.7, label="Trend")
    idx = det["index"].to_numpy(int)
    if len(idx):
        ax.scatter(pd.to_datetime(case.source_ts.iloc[idx]), case.value.iloc[idx], s=15, label="Detected")
    for i, ts in enumerate(labels.source_ts):
        ax.axvline(pd.Timestamp(ts), color="crimson", linestyle="--", linewidth=.7, label="Weak alarm" if i == 0 else None)
    ax.set(title="Site C / P-2: nominal timestamps only (alignment unconfirmed)", ylabel="mm/s rms", xlabel="Source TS")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT / "figures/alarm_case.png", dpi=160)
    plt.close(fig)


def main():
    if (OUT / "STOP.json").exists():
        raise SystemExit("Stop condition recorded; do not generate a completed report")
    q = pd.read_csv(OUT / "quality.csv")
    fixed = pd.read_csv(OUT / "fixed_summary.csv")
    syn = pd.read_csv(OUT / "synthetic_summary.csv")
    seeds = pd.read_csv(OUT / "synthetic_seeds.csv")
    grid = pd.read_csv(OUT / "grid_summary.csv")
    bench = json.loads((OUT / "benchmark.json").read_text(encoding="utf-8"))
    gs = json.loads((OUT / "grid_status.json").read_text(encoding="utf-8"))
    ss = json.loads((OUT / "synthetic_status.json").read_text(encoding="utf-8"))
    lows, bs = burden()
    figures(syn)
    grid_range = grid.groupby("channel").agg(settings=("config_id", "count"), min_events=("events", "min"),
        max_events=("events", "max"), min_events_per_day=("events_per_online_day", "min"),
        max_events_per_day=("events_per_online_day", "max")).reset_index()
    grid_range["within_1_per_day_settings"] = [int((grid[grid.channel == ch].events_per_online_day <= 1).sum()) for ch in grid_range.channel]
    grid_range.to_csv(OUT / "grid_ranges.csv", index=False)
    sensitivity = pd.read_csv(OUT / "synthetic_sensitivity.csv")
    sens = sensitivity.groupby(["channel", "kind", "magnitude", "spike_window_minutes", "merge_minutes"]).agg(
        seeds=("seed", "nunique"), injected_event_recall_mean=("event_recall", "mean"),
        injected_event_recall_std=("event_recall", "std"), background_events_per_day_mean=("background_events_per_day", "mean"),
        background_events_per_day_std=("background_events_per_day", "std")).reset_index()
    sens.to_csv(OUT / "synthetic_sensitivity_summary.csv", index=False)
    known = pd.read_csv(OUT / "fixed_detections.csv")
    known = known[(known.channel == "VEL") & (known.source_ts == "2026-10-12 11:33:00")]
    loo = pd.read_csv(OUT / "replacement_loo.csv").groupby("channel").agg(loo_detections=("detections", "sum"), loo_events=("events", "sum"),
        loo_max_chain=("max_chain_points", "max")).reset_index()
    comparison = fixed[["channel", "detections", "events", "max_chain_points"]].merge(loo, on="channel")
    comparison.to_csv(OUT / "replacement_comparison.csv", index=False)
    save_table("chapter10_quality.csv", q.to_dict("records"))
    save_table("chapter10_normal_assumed.csv", fixed.to_dict("records"))
    save_table("chapter10_synthetic.csv", syn.to_dict("records"))
    case = pd.read_csv(OUT / "alarm_case_comparison.csv")
    case.to_csv(OUT / "chapter10_alarm_case.csv", index=False)
    recheck_path = OUT / "synthetic_recheck_status.json"
    recheck = json.loads(recheck_path.read_text(encoding="utf-8")) if recheck_path.exists() else {"jobs_rechecked": 0, "seconds": 0}
    dump("execution_counts.json", {"grid_settings_per_channel": 96, "grid_channel_setting_runs": len(grid),
        "grid_detector_calls": gs["detector_calls"], "synthetic_runs": len(seeds), "synthetic_seeds": list(range(10)),
        "fixed_channel_runs": 3, "fixed_detector_calls": 6, "benchmark_calls": 1,
        "replacement_comparison_calls": 6, "alarm_case_calls": 1, "auto_osESD_calls": 0,
        "synthetic_boundary_recheck_calls": recheck["jobs_rechecked"],
        "synthetic_actual_detector_executions": len(seeds) + recheck["jobs_rechecked"]})
    lines = ["# Phase 2 실제 진동 트렌드 결과", "", "2026-10-30 실행. 보고용 명칭은 사이트 A / 설비 P-1, 사이트 C / 설비 P-2다.", "",
        "## 결과와 해석", "",
        "고정 파라미터의 원본 검출 사건 수는 모든 채널에서 잠정 기준인 하루 1건 이하였지만, 확정 정상·고장 라벨이 없어 오탐률이나 실제 고장 재현율로 해석할 수 없다. 합성 평가 역시 아래 정의와 배치 조건에서의 결과다.", "",
        "## 환경과 실행 범위", "",
        "- 작업 시작 HEAD: `202ec36`. 검출기 관련 커밋: `18cacd4d8481bead728b49c5e5dacf19bd97f65f`. 알고리즘 소스 변경 없음.",
        f"- Python {bench['python']}, {bench['processor']}, 논리 CPU {bench['logical_cpus']}개. OMP/MKL/OpenBLAS/NumExpr 스레드 각 1, 워커 6개.",
        "- 기존 테스트 35개 통과. 실험 도구의 시간 환산·격자 수·사건 병합·MAD·종료 경계·물리적 주입 제약 테스트 6개 추가 통과.",
        "- 환경 freeze, 파일 해시, 실제 키, 원본 CSV 및 상세 결과는 Git 제외 대상인 `results/phase2/`와 `scratch/phase2/`에 로컬 보관한다. 기존 가이드/Git 이력에 이전에 커밋한 데이터 예시는 남아 있으며 이번 작업에서 새로 커밋하거나 이력을 재작성하지 않았다.",
        "- P-1 기간: 원본 TS 기준 2026-10-06 21:19 이상 ~ 2026-10-30 00:00 미만. 시간대 변환·0 채움·보간 없음. 원본 입력에 anomaly 열 없음.",
        "- `use_author_lambda=False`, `rep_at=author`, `sync_stats=False`. `legacy_cap`은 고정 검출기의 인자가 아니며 auto는 실행하지 않았다.", "",
        "## 채널 품질", "", table(q[["channel", "rows", "duplicate_ts", "null_values", "infinite_values", "zero_values", "interval_median_s", "interval_p95_s", "interval_p99_s", "interval_max_s", "gaps_gt_2min"]]), "",
        "각 채널에 1시간 초과 공백이 한 번, 1일 초과 공백은 없다. 1시간 이상 공백에서 분할해 채널당 2개, 총 6개 run으로 재초기화했다. run 길이와 원본 시각 경계는 `runs.csv`에 기록했다.", "",
        "단위는 현재 setpoint 메타데이터다. 입력 내부의 단위·집계 코드는 고정했지만 과거 메타데이터 변경 여부와 집계 의미는 미확정이다. 초기화 정상 여부도 미확정이다. 각 run의 12·24시간 초기화 후보에서 인접 차분의 중앙값 대비 10 MAD sigma 초과 급변은 없었다. 이는 현장 정상 확인을 대신하지 않는다.", "",
        "## 고정 설정과 원본 검출", "",
        "설정: size 24h, dwin 15분, rwin 1h, maxr 3, alpha 0.005, AND. run별 간격 중앙값으로 올림 환산한다. VEL의 61초 간격에서는 size=1417, dwin=15, rwin=60이다. 실제 초기화 시간 길이는 관측 간격 변동 때문에 목표 시간과 다르며 `fixed_parameters.csv`에 보존했다.", "",
        table(fixed[["channel", "detections", "events", "max_chain_points", "online_days", "events_per_online_day"]]), "",
        f"10/12 11:33의 원인 미확인 변화는 VEL에서 {'검출됐다' if len(known) else '검출되지 않았다'}. 원인이나 고장 여부는 확정하지 않았다.", "",
        "인접 검출 10분 이내를 같은 사건으로 병합한다. run 경계는 넘지 않는다. 일당 사건 수의 분모는 초기화 구간과 긴 공백을 제외한 온라인 관측 기간이다. 고정 알고리즘은 결정적이므로 동일 원본의 시드 반복을 독립 실험으로 세지 않았다.", "",
        table(lows[["channel", "low_detected_points", "low_events", "low_exposure_days", "low_events_per_exposure_day", "first_hour_after_init_detected_points"]]), "",
        "낮은 진동은 run별 온라인 값의 하위 10%로 정의했다. 해당 구간 역시 정상 확인 라벨은 없다. 공백 직후 첫 1시간은 재초기화 맹점이어서 오탐을 평가할 수 없다. 표의 첫 1시간 검출은 공백 직후가 아니라 초기화 종료 직후다.", "",
        "## 격자 실험", "",
        "사용자의 alpha=0.005 고정 선택을 적용했다. size {12h,24h}, dwin {5,15,30분}, rwin {0.5,1,2,4h}, maxr {3,5}, AND/OR로 채널당 96조합, 총 288회 설정 실행이다. run별 재초기화에 따른 실제 검출기 호출은 576회다. 변환한 점 수는 `grid_parameters.csv`에 남겼다.", "",
        table(grid_range), "", "이 격자는 경보 부담의 민감도 조사이며 실제 고장 성능으로 최적 설정을 선정한 결과가 아니다.", "",
        "## 합성 이상 다중 시드 평가", "",
        "고정 1설정에서 4유형 × 3크기 × 10시드 × 3채널 = 360회를 실행했다. 시드는 0~9다. 각 입력에 이벤트 1개를 주입해 입력 안의 이벤트 간 24시간 이격 조건은 자동 충족된다. 원본 고정 검출이 판정창에 존재하지 않는 초기화 이후 위치 중에서 시드로 무작위 선택했다. 이는 검출기가 조용한 구간을 고른 조건부 평가이며 독립적으로 검증된 정상 구간이 아니다.",
        "spike는 1점, level shift·drift·variance change는 6시간이다. 오프셋은 해당 run 초기화 구간의 MAD×1.4826의 3·5·10배다. RMS/PtP의 비음수 제약을 지키도록 가산형 이상은 증가 방향으로 고정한다. drift는 0에서 목표 오프셋까지 선형 증가 후 복귀한다. variance는 주입할 구간의 중앙값을 중심으로 표준편차를 2·3·5배 확대한다. 모든 합성 입력의 유한성·비음수성을 검사하며 0으로 클리핑하지 않는다. 원본 CSV는 변경하지 않는다.",
        "spike 판정은 ±5분, 지속형은 [시작, 시작+6시간)이다. 종료 시점의 원상복귀 검출은 지속형 검출로 인정하지 않는다. 별도로 주입 이후의 검출만 세는 causal recall도 보존했다. 지연 평균·표준편차는 검출된 시드에만 계산하며 미검출은 결측으로 남긴다. 표의 delay_observed가 지연 통계의 표본 수다. 지연 값이 없거나 검출 시드가 1개여서 표준편차를 정의할 수 없으면 '-'로 표시한다.",
        f"최초 집계의 종료 경계 포함 문제와 일부 하향 주입의 음수 RMS 문제를 확인했다. 종료 경계 영향 9회와 가산형 주입 방향 변경 81회를 재실행했다. 총 재실행은 {recheck['jobs_rechecked']}회, 합성 검출기 실제 호출은 {len(seeds) + recheck['jobs_rechecked']}회다. 최종 표는 물리적 제약과 수정한 판정을 적용한 360개 고유 시드 조합이며, 최초 표는 무효 참고용으로 audit 폴더에 보관했다. 알고리즘 변경이나 검출기 설정 추가 탐색은 없었다.", "",
        table(syn[["channel", "kind", "magnitude", "seeds", "event_recall_mean", "event_recall_std", "causal_recall_mean", "delay_mean_s", "delay_std_s", "delay_observed"]]), "",
        "시그마는 초기화 시점에 고정한 값이다. 원본에는 장기적인 수준 변화가 있어 이 값이 주입 시점의 변동 수준을 대표한다고 보장할 수 없다. 따라서 10 sigma라는 크기를 다른 운전 상태에서도 동일한 신호대잡음비로 해석하지 않는다.", "",
        "창 ±1·5·10분, 사건 병합 5·10·20분 및 허용치 0.5·1·2건/일을 비교했다. 원본의 `baseline_sensitivity.csv`, 주입 시드별 `synthetic_sensitivity.csv`, 집계 `synthetic_sensitivity_summary.csv`에 보존한다. 합성 입력의 배경 부담은 주입 사건과 이후 4시간을 제외한 해당 run의 정상 가정 구간으로 계산했다. 원본 경보 부담과 분모가 다르다.", "",
        "## 알람 사례와 파형 연결", "",
        "사이트 A와 B의 조사 범위에서는 연결할 정비·알람 이력을 찾지 못했다. 사이트 C의 사이트 단위 후보 조회는 201행 상한에 도달해 중단했고, 지정 포인트 및 하루 범위로 좁혀 알람 16건 중 채널 키·이름이 일치하는 3건을 P-2 사례로 연결했다. DB 오류는 없었고 한계에 걸린 후보 조회는 상세 트렌드 전체 추출로 확장하지 않았다.",
        "P-2는 3일 동안 339점, 중앙 간격 600초다. null·중복·0 없음, 최대 간격 2401초다. 이 채널의 VAL_TYPE은 2이며 의미는 미확정이다. P-1의 0과 혼합하지 않았다. 같은 시간 설정을 환산하면 size=144, dwin=2, rwin=6이다. 검출은 4점, 1사건이다.",
        f"P-2의 약한 알람 3건 중 원본 시각 ±5분 또는 ±10분에 검출이 일치한 것은 {int(case.detected_within_10min_raw_ts.sum())}건이다. 시간대 정합성이 미확정이므로 확정적인 미탐률·고장 조기경보 성능으로 해석하지 않는다. 오래전 검출을 임의로 고장 전조로 인정하지 않는다.",
        "P-1 변화 부근은 전체 키와 ±6시간으로 제한해 파형 스냅샷 메타데이터 1건만 읽었다. 원시 배열은 조회하지 않았다. 샘플 수 4096, sampling period·RPM 미기록이며 주파수 특징은 계산하지 않았다. 시간대 정합성과 실제 TP/FP/FN은 미확정이다.", "",
        "## 선택 비교와 실행 시간", "", table(comparison), "",
        "leave-one-out는 같은 고정 설정의 비교 실행만 수행했고 기본 치환은 author로 유지했다.", "",
        f"- 벤치마크: VEL 한 run {bench['rows']}점, {bench['seconds']:.2f}초. lambda cache를 비운 상태에서 시작했다.",
        f"- 벤치마크 기준 보수적 예상 전체 시간: {bench['estimated_total_seconds']/60:.1f}분으로 90분 이내였다.",
        f"- 1차 고정 3채널: 측정 시간 합 {fixed.seconds.sum():.2f}초.",
        f"- 격자 288회(6워커): 실제 벽시간 {gs['seconds']:.2f}초.",
        f"- 합성 360회(6워커): 실제 벽시간 {ss['seconds']:.2f}초.",
        f"- 합성 종료 경계·물리적 주입 제약 재검산 {recheck['jobs_rechecked']}회: {recheck['seconds']:.2f}초.",
        "- 조회·도구 작성·보고서 작성 시간은 위 계산 시간에 포함하지 않았다. 고정·벤치마크의 캐시 상태와 워커별 준비 비용은 다르며 캐시 상세는 benchmark.json에 남겼다.", "",
        "## 산출물과 한계", "",
        "`results/phase2/`에 입력 CSV 목록·품질·run·파라미터·검출 시점·사건·격자·시드별 지표·민감도 CSV와 그림 5개를 저장했다. 보고서 10장용 표는 `chapter10_quality.csv`, `chapter10_normal_assumed.csv`, `chapter10_synthetic.csv`, `chapter10_alarm_case.csv`다. 상세 지표와 원본을 포함하는 결과 폴더 전체는 Git 제외 대상이다.",
        "라벨 없음, 시간대·집계 의미·운전 조건·과거 단위 변경은 미확정이다. 초기화 구간은 detector의 탐지 맹점이다. 합성 이상 결과는 MAD 기준·배치 조건·고정 설정에 의존한다. auto_osESD는 별도 승인 대상이므로 실행하지 않았으며, 실행 전 앞 20%의 의심 이벤트를 확인해야 한다.", ""]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"report": "results/phase2/REPORT.md", "grid_runs": len(grid), "synthetic_runs": len(seeds),
                      "seeds_per_group": sorted(seeds.groupby(["channel", "kind", "magnitude"]).seed.nunique().unique().tolist())}), flush=True)


if __name__ == "__main__":
    main()
