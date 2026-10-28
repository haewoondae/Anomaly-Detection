import os, sys

p = 'docs/REPRODUCTION.md'
with open(p, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix bell characters (\x07)
text = text.replace('\x07lpha', 'alpha')
text = text.replace('\x07pprox', 'approx')

# 2. Fix Table 2 ARIMA wording
old_arima = "• 단, 논문 수치는 미공개 파라미터에 대한 후보군(T-A) 탐색 결과 기반임"
new_arima = "• 본 재현 수치는 후보 설정(T-A) 중 선택한 결과임 (논문은 파라미터 미공개)"
text = text.replace(old_arima, new_arima)

# 3. Fix t4 14자리 -> 16자리 완전 일치
text = text.replace("소수점 14자리 일치", "소수점 16자리 완전 일치")

# 4. Add Cache Equivalence Verification to Section 2.1
old_s21 = """### 2.1 포팅 동치성 (Equivalence to PyPI 1.1.6)
- **강한 증거**: PyPI 1.1.6 원본과 5개 대형 파일(길이 10,000)에서 `auto_osESD` 144조합 그리드 튜닝 후 최종 산출된 이상치 인덱스가 완벽히 동일함을 확인하였습니다.
- **포팅 범위**: `legacy_cap=True`, 저자식 $\\lambda$ 식, 저자식 치환(`rep_at="author"`)을 적용했을 때 원본 PyPI 구현과 수치적/알고리즘적 동치가 성립합니다."""

new_s21 = """### 2.1 포팅 동치성 및 캐시 후 동일성 검증 (Equivalence to PyPI 1.1.6)
- **PyPI 동치성 및 골든 테스트 27개 100% 통과**:
  - `legacy_cap=True`, 저자식 lambda 식, 저자식 치환(`rep_at="author"`) 모드에서 PyPI 1.1.6 원본과 5개 대형 파일(길이 10,000) 144조합 자동 튜닝 전수 대조 시 탐지 인덱스가 100% 일치함을 확인하였습니다.
  - 원저자 R 패키지(`osESD_R/data`)의 9개 데이터셋을 대상으로 한 골든 회귀 테스트 27개(`tests/test_pypi_golden.py`) 전수 통과(35/35 passed).
- **scipy.stats.t.ppf LRU 캐싱 후 수치/엔드투엔드 완전 동일성 확정**:
  - **함수 비트 동일성**: alpha 4종 x size 4~259 (총 2,048회) 평가에서 표준 Rosner 및 저자 lambda 모두 비트 단위(Bit-for-bit) 완전 일치(`tests/test_lambda_cache.py` 통과).
  - **엔드투엔드 골든 27개 통과**: 캐시 적용 후 `$env:OSESD_DATA="osESD_R/data"; pytest -q` 재실행 결과 35 passed in 22.66s로 골든 27개 인덱스 100% 동일 유지.
  - **부록 예제 t2, t4 결과값 일치**:
    - `t2`: 온라인 구간 P=1.0, R=1.0, F1=1.0 (98/98 일치, 0.918초).
    - `t4`: 전체 구간 P=1.0, R=98/99 (= 0.98989898989899), F1=0.9949238578680203 (소수점 16자리 완전 일치, 27.7초 / 단독 12.58초).
  - **결론**: LRU 캐시 적용 후 알고리즘적/수치적 100% 결과 동일성 확정."""

text = text.replace(old_s21, new_s21)

# 5. Calibrate Section 2.8 and 2.9 qualitative interpretations
old_s28_29 = """### 2.8 Table 5 이벤트 길이 민감도 평가 ($L \\in \\{5, 10, 20, 40\\}$, $\\sigma_\\epsilon=100$, 축소 그리드)
- **배경**: 논문 본문에 이상치 이벤트 길이($L$)가 수치로 명시되지 않아 기존 실험에서는 $L=10$으로 가정함. 이벤트 길이에 따른 정밀도 하락 폭 및 전략 간 순위 민감도를 점검함.
- **실측 결과 요약 ($n=4$)**:
  - **ARIMA1 (Bernoulli)**:
    - $L=5$: `drift` $P=0.897 \\pm 0.081, F_1=0.937$ / `block` $P=0.955 \\pm 0.065, F_1=0.970$
    - $L=10$: `drift` $P=0.849 \\pm 0.097, F_1=0.907$ / `block` $P=0.920 \\pm 0.127, F_1=0.945$
    - $L=20$: `drift` $P=0.822 \\pm 0.135, F_1=0.894$ / `block` $P=0.853 \\pm 0.128, F_1=0.906$
    - $L=40$: `drift` $P=0.802 \\pm 0.127, F_1=0.866$ / `block` **$P=0.783 \\pm 0.076, F_1=0.873$** (논문: `drift` $P=0.678$ / `block` $P=0.651$)
    - $\\rightarrow$ $L$이 커질수록 Drift와 Block 모두 정밀도 하락 폭이 점진적으로 확대되어 논문 수준($P \\approx 0.65\\sim 0.68$)으로 수렴하는 경향이 뚜렷함. 특히 **$L=40$에서 Block 정밀도($0.783$)가 Drift 정밀도($0.802$) 아래로 역전**되어 논문의 상대적 정밀도 순위(`own` > `drift` > `block`)와 일치하기 시작함.
  - **ARIMA1 (Linear)**:
    - $L=5 \\to 40$으로 증가함에 따라 `drift` 정밀도가 $0.911 \\to 0.773$으로 대폭 하락하여 논문 보고치($P=0.815$)에 정확히 도달함.

### 2.9 State-space 노이즈 민감도 평가 ($\\sigma_\\epsilon \\in \\{1, 100, 300\\}$, $L=10$)
- **배경**: State-space 모델의 관측 노이즈 $\\sigma_\\epsilon$ 증가에 따른 이상치 탐지 성능 변화를 점검함 ($n=6\\sim 7$).
- **실측 결과 요약**:
  - **State-space (Bernoulli)**:
    - $\\sigma_\\epsilon=1$: `ber` F1 $0.970 \\pm 0.029$, `drift` $0.986 \\pm 0.008$, `block` $0.987 \\pm 0.004$
    - $\\sigma_\\epsilon=100$: `ber` F1 $0.978 \\pm 0.019$, `drift` $0.968 \\pm 0.017$, `block` $0.987 \\pm 0.014$
    - $\\sigma_\\epsilon=300$: `ber` F1 $0.956 \\pm 0.039$, `drift` **$P=0.909 \\pm 0.037, F_1=0.923 \\pm 0.046$** (논문: $P=0.893, F_1=0.928$), `block` F1 $0.937 \\pm 0.054$
    - $\\rightarrow$ $\\sigma_\\epsilon=300$ 고노이즈 조건에서 `drift`의 정밀도($0.909$)와 F1($0.923$)이 **논문 수치($P=0.893, F_1=0.928$)와 오차 $\\pm 0.01$ 내에서 정밀하게 일치**함.
  - **State-space (Linear)**:
    - $\\sigma_\\epsilon=1$: `lin` F1 $0.989 \\pm 0.007$, `drift` $0.978 \\pm 0.013$, `block` $0.976 \\pm 0.008$
    - $\\sigma_\\epsilon=100$: `lin` F1 $0.961 \\pm 0.025$, `drift` $0.951 \\pm 0.025$, `block` $0.963 \\pm 0.025$
    - $\\sigma_\\epsilon=300$: `lin` F1 **$0.934 \\pm 0.064$** (논문 0.892), `drift` F1 **$0.906 \\pm 0.054$** (논문 0.889), `block` F1 **$0.930 \\pm 0.062$** (논문 0.897)
    - $\\rightarrow$ 노이즈가 $\\sigma_\\epsilon=300$까지 증가함에 따라 F1이 $0.989 \\to 0.961 \\to 0.906\\sim 0.934$로 지속 하강하여 논문의 0.89 성능 영역으로 성공적으로 진입함."""

new_s28_29 = """### 2.8 Table 5 이벤트 길이 민감도 평가 (L in {5, 10, 20, 40}, sigma_eps=100, 축소 그리드)
- **배경 및 평가 원칙**:
  - 논문 본문에 이상치 이벤트 길이(L)가 수치로 명시되지 않아 기존에는 L=10으로 가정함.
  - 타깃별로 L을 다르게 고르면 테스트 결과에 파라미터를 맞추는 사후 보정(overfitting)이 되므로, 전체 12개 칸에 대해 단일 전역 L을 적용하고 평균 절대 오차(MAE, |Delta F1|)로 평가해야 함.
- **실측 결과 및 해석 ($n=4$)**:
  - **ARIMA1 (Bernoulli)**:
    - L이 5에서 40으로 길어질수록 drift 정밀도(0.897 -> 0.802)와 block 정밀도(0.955 -> 0.783)가 하락하지만, L=40에서도 논문 보고치(0.65~0.68) 대비 0.1 이상 높음 (L=80, 160 추가 확인 필요).
    - L=40에서 block 정밀도(0.783 +/- 0.076)와 drift 정밀도(0.802 +/- 0.127)는 표준편차 범위 내에 있으며, F1은 여전히 block(0.873) > drift(0.866)로 논문(drift 0.808 > block 0.788)과 반대임.
  - **ARIMA1 (Linear)**:
    - block은 L이 길수록 정밀도가 0.856(L=10~20)에서 0.908(L=40)로 오히려 상승하여 논문(0.802)에서 멀어짐.
    - drift 정밀도는 0.773~0.790 수준으로 논문 보고치(0.815)보다 낮게 형성됨.
  - 타깃마다 적합한 L의 방향이 상이하므로, L in {5, 10, 20, 40, 80, 160} 전수 평가를 통해 12개 칸 전체의 평균 절대 오차를 최소화하는 전역 L을 도출하기로 함.

### 2.9 State-space 노이즈 민감도 평가 (sigma_eps in {1, 100, 300}, L=10)
- **배경 및 평가 성격**:
  - 논문 미공개 모수인 sigma_eps에 대한 단서를 얻기 위한 탐색적 분석이며, 특정 칸의 부분 일치를 근거로 재현 성공을 확정할 수 없음.
- **논문 대비 F1 평균 절대 오차 (Bernoulli 3칸 + Linear 3칸)**:
  - sigma_eps = 1: 평균 |Delta F1| = 0.056
  - sigma_eps = 100: 평균 |Delta F1| = 0.041
  - sigma_eps = 300: 평균 |Delta F1| = 0.030
- **해석**:
  - sigma_eps=300에서 Bernoulli drift F1(0.923)이 논문(0.928)과 0.005 차이로 유사한 것은 6개 칸 중 하나가 우연히 근접한 것으로, 같은 조건에서 Bernoulli block은 0.937로 논문(0.990) 대비 -0.053 어긋나며 순위(ber > block)도 역전됨.
  - 전체 오차가 sigma_eps 증가에 따라 단조 감소(0.056 -> 0.041 -> 0.030)하므로 최적 노이즈가 구간 외부에 있을 가능성이 있어 sigma_eps=1000까지 추가 확인을 진행함.
  - 또한 순위 판정의 통계적 유의성을 위해 paired difference(동일 파일 내 own, drift, block 차이) 분석을 병행함."""

text = text.replace(old_s28_29, new_s28_29)

with open(p, 'w', encoding='utf-8') as f:
    f.write(text)

print("docs/REPRODUCTION.md updated successfully with clean UTF-8!")
