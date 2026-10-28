# Table 2 Comparison Baseline v2 Plan (Threshold Sensitivity & Oracle-k)

## 1. 배경 및 목표
- Table 2의 Score 기반 모델(IF, RRCF, AE, VAE, LSTM-ED)에 대해 두 가지 임계값 판정 규칙을 동시 산출:
  1. `train`: 학습 구간 평균 + 3*표준편차 (배포 가능한 규칙)
  2. `oracle`: 시험 구간 실제 이상치 개수 k에 맞춰 상위 k개 선택 (`<model>@oracle`, 레이블 활용)
- IF의 Recall과 Precision이 논문 전 그룹에서 1.0에 가까운 현상(R/P ~ 1.00)을 바탕으로, "논문 IF가 이상치 비율 contamination 또는 상위 k개 선택(oracle-k)이었을 가능성"에 대한 가설 검증.
- Total 행의 가중 평균 재계산 및 REPRODUCTION.md 문서 업데이트.

## 2. 작업 절차 및 현황
1. **코드 수정**:
   - `repro/baselines.py`: `topk_pred` 추가, `return_scores=True` 추가, IF 및 DL 특징/피팅 인자 확장 완료.
   - `repro/run_baselines.py`: v2 하네스 교체 (`--thr train|oracle|both`, `--if-feat`, `--if-fit`, `--dl-feat`, `--dl-fit`) 완료.
2. **실행 1: IF 4종 특징 탐색 및 전수 평가 (ARIMA, State-space, Yahoo S5)** (완료):
   - 4개 특징: win(32점 윈도우), raw(원값), rawdiff(원값+차분), diff(차분)
   - 거리 평가 결과: raw가 평균 절대 오차 0.051, Spearman 순위 상관 약 0.94로 가장 근접(가중 Total 0.386 대 논문 0.347).
   - 제약 사항: 4종 탐색 자유도 및 3개 가정(점 특징, 전체학습, oracle-k) 결합 한계 명시.
3. **네 모델 Total 순위 비교표 확정** (완료):
   - osESD(0.728/0.762) > HW-A(0.544/0.513) > Z-Score(0.543/0.509) > IF(0.386/0.347). 순서와 간격 구조 일치.
4. **실행 2: 딥러닝 점수 위치 오류 수정 및 3종 특징 재평가 (ARIMA 96개, GPU)** (진행 중):
   - **오류 원인 규명**: 윈도우 32개의 평균 오차를 윈도우 마지막 점(`i+w-1`)에 일괄 부여하던 기존 방식은 이상치 스파이크가 윈도우에 걸쳐 있을 때 점수가 최대 31칸 떨어진 점들에 분산 부여되어 top-k 정밀도가 무작위 수준(0.08)으로 급락하는 구현 결함이었음.
   - **수정 내용**: 각 윈도우 내 위치별 제곱오차를 산출하고, 각 점의 점수를 그 점을 덮는 모든 윈도우들의 해당 위치 오차 평균으로 산출하도록 수정 완료.
   - **재평가 실행**: `win`, `diff`, `center` 3종 특징에 대해 `fit="all"`, `oracle-k`로 ARIMA 96개 전수 재평가(1회 한정).
   - **판정 기준**: LSTM-ED >= 0.4 및 AE/VAE < 0.3 달성 시 가설 지지, 미달 시 "구현 가정 의존"으로 종결. (결과가 양호할 경우 RRCF 윈도우 점수 방식도 점검).
5. **이후 순서**:
   - Table 3 Yahoo 행(ablation 변형 3종: sosESD, oGESD, norep) 및 가중 Total 행 산출.
   - 3.3절·3.4절 수식 유도 이론 검증.
   - REPRODUCTION.md 최종판 완성.
