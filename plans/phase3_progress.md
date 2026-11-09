# Phase 3 Progress: 검출 이상 도메인 검증, 미검출 분석, 다변량 확장

## 현재 상태

- **단계**: Phase 3 전체 작업(작업 1, 작업 2, 작업 3) 및 `docs/PHASE3_RESULTS.md` 작성 완료

## 완료된 사전 점검 항목

- [x] `docs/PHASE2_RESULTS.md`, `docs/VIBRATION_DATA_PHASE2_GUIDE.md`, `docs/PHASE2_DB_EXTRACTION.md` 및 `repro/phase2*.py` 코드베이스 검토
- [x] `results/phase2/` 내 기존 추출 데이터(`P-1`, `P-2`) 및 알람 메타데이터 정합성 선행 확인
  - **핵심 발견 1 (작업 2-1 시간대 오프셋 조기 해결)**: `P-2` 알람 3건에는 `TRIGGER_VALUE` 필드가 이미 존재하며(`7.664248`, `7.098358`, `8.397837`), `P-2_VEL.csv`의 동일 시각(`ENTERED_DATE_TIME`, 오프셋 **0초**)의 `value`와 소수점 6자리까지 100% 일치함. 즉 SYS04 트렌드 `TS`와 알람 `ENTERED_DATE_TIME`은 시간대 불일치가 없으며(오프셋 0시간), 미검출 원인은 시간대 불일치가 아니라 **고진동 고원(plateau) 지속에 따른 윈도우 적응 및 c_data/t_data AND 기각**임을 확인.
  - **핵심 발견 2 (P-2 알람 조회 기간)**: 기존 Phase 2의 P-2 알람은 `2026-10-29` 하루치만 조회된 것이므로, P-2 포인트(`POINT_ID=2984`)에 대해 10월 전체(또는 10/27~10/30) 알람을 포인트 단위로 조회하면 `2026-10-28 11:24~11:54`(`8.52~8.76 mm/s rms`) 구간의 알람과 osESD의 실제 검출(`2026-10-28 11:24~12:34`)이 직접 매칭될 가능성이 매우 높음.
  - **핵심 발견 3 (P-1 채널 간 사건 중첩)**: `fixed_events.csv`에서 이미 `2026-10-12 11:32` 사건은 3채널(VEL, ACC, ENV3) 모두 일치하고, `2026-10-08 08:19~08:20` 및 `09:54` 사건은 ACC+ENV3 2채널이 일치함을 확인.
- [x] `phase3_plan.md` 및 `phase3_progress.md` 문서 생성

## 대기 및 다음 단계

- [x] 사용자 확인 질문(1~4번 + 기술적 보완 제안) 회신 수령 완료
  - Q1: P-1 사건 $\pm 6$시간 내 스냅샷 개수 및 `C_DATA` 원시 배열 모두 계산 승인
  - Q2: 사이트 A·B·C 모두 포함 (P-2 포인트 10월 전체 알람 재조회 포함) 승인
  - Q3: 에이전트가 직접 추가 측정점/설비 1~2곳 선정 승인
  - Q4: 기술적 보완안(SPE 차원 정의, 미검출 원인 세분화, 정량적 사건 형태 분류) 모두 적용 승인
- [x] 작업 2-1 및 P-2 포인트 전체 알람 매칭 실행 (`scratch/phase3/extract_phase3_db.py`, `scratch/phase3/task1_and_offset_local.py`)
- [x] 작업 1 (도메인 검증 및 파형 분석) 실행 (`scratch/phase3/run_task1_waveforms.py` 완료, 3.97초)
- [x] 작업 3 (다변량 확장 방식 A, B) 실행 (`scratch/phase3/run_task3_pca.py` 완료, 829.92초)
- [x] 작업 2-2, 2-3 (알람 후보 확대 및 약한 라벨 분석) 실행 (`scratch/phase3/run_task2_alarms.py` 완료, 433.18초)
- [x] `docs/PHASE3_RESULTS.md` 작성 완료 (익명화 규칙 및 Phase 2 정정 섹션 포함)
