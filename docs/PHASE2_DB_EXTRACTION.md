# Phase 2 DB 추출 및 재실행 안내

## 현재 완료 범위와 남은 실행

2026-11-03 로컬 실행 기록과 코드를 대조했다. 데이터 기준일은 기존 추출 종료일인 2026-10-30이며, 이번 확인에서 DB에 다시 접속하거나 기간을 연장하지 않았다.

| 작업 | 상태 | 근거 / 다음 단계 |
|---|---|---|
| 환경·추출·품질·run 분할·시간 파라미터 환산·벤치마크 | 완료 | P-1 세 채널, 채널별 두 run. 기존 테스트 35개와 실험 도구 테스트 6개 통과 기록 |
| 고정 설정 검출 | 완료 | 세 채널, 검출기 호출 6회 |
| 격자 실험 | 완료 | alpha=0.005, 채널당 96설정, 총 288회 설정 실행 / run별 검출기 호출 576회 |
| 합성 이상 다중 시드·사건 판정·민감도 | 완료 | 고유 360조합, 시드 0~9. 재검산 90회 포함 실제 검출기 호출 450회 |
| author / loo 치환 비교 | 완료 | 기본 author 유지, 동일 고정 설정에서만 비교 |
| 둘째 설비 알람 사례 | 완료 | P-2 약한 알람 3건 대조. 정비로 확정한 고장 라벨 아님 |
| 선택 파형 연결 | 부분 완료 | 제한 조회로 스냅샷 메타데이터 1건만 확인. 원시 배열·주파수 특징·TP/FP/FN 확인은 미실행 |
| `auto_osESD(labeled=False)` | 미실행 | 별도 승인 대상. 먼저 채널/run별 앞 20%의 의심 이벤트를 표시하고, 다중 시드·탐색 횟수·예상 시간을 정해 실행 |
| 보고서 10장 반영 | 표 제공 완료 | 집계표는 생성됨. Word 보고서 본문 편집과 최종 편집 검증은 별도 작업 |

필수 0~9단계에 재실행할 작업은 현재 없다. auto 실험과 파형 원시 신호 분석은 선택 작업이다. 라벨·시간대·운전 조건·집계 의미는 DB 수치만으로 확정하지 않는다. 파형의 sampling period와 RPM도 미기록이므로 주파수 특징을 확정값으로 보고할 수 없다.

세부 결과: [PHASE2_RESULTS.md](PHASE2_RESULTS.md).

## 접속정보: 이 프로젝트의 `.env` 사용

네 DB 조회 스크립트는 실행 디렉터리와 관계없이 이 프로젝트 루트의 `.env`를 기본으로 `dotenv_values()`로 읽는다. 셸 환경변수로 자동 대체하지 않으며, 코드에 접속정보를 넣지 않는다. 기본 파일 위치:

```text
Anomaly Detection/Python/.env
```

필요한 변수 이름은 아래 다섯 개다. 값은 로컬 `.env`에서만 관리하고 문서·로그·커밋에 복사하지 않는다.

```dotenv
DB_HOST=<DB 서버 주소>
DB_PORT=<포트 번호>
DB_USER=<읽기 전용 계정>
DB_PASSWORD=<비밀번호>
DB_NAME=<데이터베이스 이름>
```

기존 backend `.env`의 DB 변수 다섯 개만 복사해 로컬 파일을 생성했다. backend 파일 자체와 나머지 설정은 변경하지 않았다. 두 파일은 자동 동기화되지 않으므로 이후 이 프로젝트 접속정보는 이 프로젝트 `.env`에서 관리한다. 이 저장소의 `.env`, `.env.*`는 Git 제외 대상이다. 필요하면 `--env-file <경로>`로 명시할 수 있고, 기존 `--backend-env`도 호환 별칭으로만 유지한다. `autocommit=True`나 SELECT만 실행하는 코드 자체는 DB 계정의 읽기 전용 권한을 보장하지 않는다. 계정의 서버 측 권한은 미확인이다. 쓰기 권한이 없는 계정 사용을 권장한다. `START TRANSACTION` 등도 이번 스크립트에서는 보내지 않는다.

## 대상 키와 기간: Git 제외 로컬 JSON

접속정보는 `.env`, 실제 설비/채널 식별자와 승인된 기간은 `scratch/phase2/targets.proposed.json`에서 관리한다. 이름에 `proposed`가 있어도 실행 여부는 파일의 `status`로 검사한다. 실제 키를 `.env` 접속정보와 섞거나 공개 문서에 적지 않는다.

다음은 구조 설명용이며 실행 가능한 실제 설정이 아니다. 세 채널은 각각 독립된 항목으로 작성한다.

```json
{
  "status": "proposed",
  "from_ts_inclusive": "<원본 TS 기준 시작 시각>",
  "to_ts_exclusive": "<원본 TS 기준 종료 시각>",
  "channels": [
    {
      "alias": "VEL",
      "SYS1_ID": "<소스 키>",
      "COMPANY_ID": "<회사 키>",
      "API_PORT": "<SKF 포트 키>",
      "POINT_ID": "<포인트 키>",
      "MEASUREMENT_ID": "<측정 키>",
      "AGGR_TIME_CD": "<집계 코드>",
      "VAL_TYPE": "<값 유형>",
      "unit": "<현재 메타데이터의 단위와 일치>"
    }
  ]
}
```

키·기간의 승인 뒤에만 `status=approved`로 실행한다. P-1 추출기는 SKF 파일럿 전용이며 다른 소스용 범용 추출기가 아니다. 시작 포함·종료 제외(`TS >= start AND TS < end`), 최대 31일이다. 실제 승인 파일에는 VEL·ACC·ENV3 세 항목과 둘째 설비 후보 설정이 있다. 실제 키 파일은 Git에 올리지 않는다.

## P-1 추출 경로와 SQL 범위

실행 파일: [phase2_extract.py](../repro/phase2_extract.py).

1. 승인 상태와 기간을 확인하고 `.env`로 연결한다. 연결 8초, 읽기 30초 제한이다.
2. 기간과 전체 트렌드 키의 `EXISTS`를 사용해 `TB_TREE_ALL`에서 대상 범위를 확인한다(최대 3행, 정확히 1행 요구).
3. 해당 사이트의 `TB_MAINTENANCE_ACTION`, `TB_ALARM_EVENT`를 기간과 각 테이블의 사이트 키로 조사한다. 이 테이블에는 트렌드 전체 키가 없으므로 트렌드와 같은 키 조건이라고 주장하지 않는다. 각각 `LIMIT 201`; 200건 초과 시 중단하고 범위를 좁힌다.
4. `TB_EQUIP_SETPOINT`의 측정 메타데이터를 트렌드 `EXISTS`로 제한한다. 정확히 한 행이고 예상 단위와 일치해야 한다. 과거 단위 변경을 증명하는 검사는 아니다.
5. `TB_TREND_LOG_SKF`에서 채널별로 조회한다. 다음 조건을 모두 바인딩하며 `ORDER BY TS LIMIT 100001`을 사용한다. 0건 또는 100,000건 초과면 중단한다.

```sql
SELECT t.SYS1_ID, t.COMPANY_ID, t.API_PORT, t.POINT_ID,
       t.MEASUREMENT_ID, t.AGGR_TIME_CD, t.VAL_TYPE, t.TS, t.VAL
FROM TB_TREND_LOG_SKF t
WHERE t.SYS1_ID = %s AND t.COMPANY_ID = %s AND t.API_PORT = %s
  AND t.POINT_ID = %s AND t.MEASUREMENT_ID = %s
  AND t.AGGR_TIME_CD = %s AND t.VAL_TYPE = %s
  AND t.TS >= %s AND t.TS < %s
ORDER BY t.TS
LIMIT 100001
```

`%s`는 PyMySQL의 파라미터 바인딩 자리다. 실제 값으로 SQL 문자열을 조합하지 않는다. 추출기는 단일 SELECT인지 검사하며 INSERT/UPDATE/DELETE/DDL은 실행하지 않는다. LIMIT은 반환 행 상한일 뿐 DB 내부 스캔량을 보장하지 않으므로 느린 쿼리·접속 오류 시 범위를 넓혀 반복하지 말고 중단한다. 파형 테이블은 이 추출기에서 읽지 않는다.

## 실행 명령 (PowerShell)

작업 디렉터리: `Anomaly Detection/Python`. 아래 경로는 이 디렉터리 기준이다. backend의 설치된 Python 환경을 재사용하며 의존성을 새로 설치하거나 `.env` 내용을 출력하지 않는다.

```powershell
$phase2DbPython = '..\..\ifacts-vib\vibration-vib-backend-python\.venv\Scripts\python.exe'
$phase2DbEnv = '.\.env'

# 접속하지 않는 사용법 확인
& $phase2DbPython repro/phase2_extract.py --help

# 승인된 키/기간에서만 실행. 기존 로컬 입력을 덮어쓰므로 재추출 전 보존 여부 확인.
& $phase2DbPython repro/phase2_extract.py `
  --targets scratch/phase2/targets.proposed.json `
  --env-file $phase2DbEnv `
  --output results/phase2
if ($LASTEXITCODE -ne 0) { throw '추출 중단: 로컬 상태 파일을 확인하세요.' }

# DB 접속 없이 추출된 파일의 품질 검사와 초기화 급변 검사
py -3.11 repro/phase2.py quality
if ($LASTEXITCODE -ne 0) { throw '품질 검사 중단: 실험을 실행하지 마세요.' }
```

재추출은 필수가 아니다. 기존 결과를 재현하려면 기존 CSV를 유지한다. 신규 추출을 기존 결과와 섞지 않는다. 다른 `--output`을 쓸 수 있지만 분석 도구의 입력 경로는 `results/phase2`로 고정되어 있으므로 경로만 바꾸면 자동 연결되지 않는다. 검사 실패·동일 TS·의심 초기화 급변·단위/집계 변경이 확인되면 실험을 중단한다. 값이 동일하다는 이유로 중복 관측을 임의 삭제하지 않는다.

## 로컬 산출물과 공개 가능 범위

- `results/phase2/inputs/P-1_{VEL,ACC,ENV3}.csv`: 채널별 원본. `timestamps`는 첫 관측부터 경과 초, `value`는 VAL, `source_ts`는 원본 TS 문자열. 단위와 전체 키·VAL_TYPE을 함께 저장한다. anomaly 열·시간대 변환·결측 0 채움·채널 혼합 없음.
- `results/phase2/private/query_audit.json`: SQL과 실제 바인딩 값. 메타데이터·정비·알람 원문도 `private/`에 저장하므로 공개 금지.
- `input_manifest.json`, `extraction_status.json`: 입력 파일 목록과 성공/중단 상태. 실패 세부 메시지에도 접속정보나 식별정보가 포함될 수 있어 로컬에서만 확인한다.
- 품질 검사는 정렬 전 상태·중복·결측·비유한값·간격·공백·0·집계/단위 컬럼을 기록하고 1시간 이상 공백에서 run을 나눈다. 초기화 정상 여부는 현장 라벨이 아니라 급변 스크리닝이다.
- 공개 가능한 것은 익명 집계표와 보고서만이다. `results/phase2/`는 기본 제외지만 이전에 개별 허용하여 커밋한 집계표는 **이미 추적 중**이다. 재실행하면 변경분이 Git에 표시될 수 있으므로 `.gitignore`만 믿지 말고 `git diff`를 검토한다. 원본 폴더를 `git add -f`로 통째 추가하지 않는다.

## 둘째 설비·파형 스크립트의 제한

- `phase2_candidate.py`: SYS01/SYS04 후보 조사용. `--targets` 사용, 기본 `.env`는 프로젝트 루트이며 `--env-file`로 지정 가능하다. 실제 후보 파일은 `scratch/phase2/`에 보관한다. 사이트 조회에서 201행 상한에 도달한 이력이 있으므로 기존 넓은 후보 파일을 그대로 재실행하지 않는다. 좁힌 포인트·기간부터 검토한다.
- `phase2_alarm_case.py`: 기존 사이트 C 후보 결과 파일에 의존하며 심각도와 시작일·집계 코드가 해당 사례에 고정되어 있다. 범용적인 새 설비 추출 명령이 아니다. SYS04 트렌드는 API_PORT 컬럼을 사용하는 SKF와 조회 계약이 다르다.
- `phase2_waveform.py`: 기존 VEL 변화 시각이 코드에 고정된 사례 전용이다. 전체 채널 키와 ±6시간 및 트렌드 집계 코드의 EXISTS로 제한하고 최대 3행을 조회한다. 2행 초과 시 중단한다. `C_DATA`는 읽지 않는다. 새 시각/채널용으로 그대로 재사용하지 않는다.

이 세 도구도 같은 `.env`의 다섯 DB 변수를 읽는다. 실제 알람 시각·이름·키·파형 메타데이터는 공개 산출물에 넣지 않는다.
