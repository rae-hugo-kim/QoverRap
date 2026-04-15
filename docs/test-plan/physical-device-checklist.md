# 물리 디바이스 테스트 체크리스트 (A-ENV1 & MET-1)

**목적**: QR 오버래핑 기술이 실제 스마트폰 환경에서 작동하는지 검증하고, 측정 프로토콜(MET-1: 스캔 성공률 >= 95%, 200회)의 기준을 만족하는지 확인한다.

**범위**:
- A-ENV1: 화면 표시·조도 변화별 판독 가능성
- MET-1: 스캔 성공률 (200회 시도, 최소 2종 디바이스, 최소 2개 조명 조건)
- 독립 판독 경로: 기본 카메라 앱과 확장 디코더 동작 검증

**선행 조건**: 생성 스크립트(`generate_test_qrs.py`), 각 디바이스 카메라 앱, QR 출력(화면 또는 인쇄)

---

## 1. 목적

Phase A 실현 가능성 스파이크 범위 내에서:

1. **A-ENV1 검증**: 오버래핑 QR이 화면 표시와 조도 변화에서 읽히는지 확인
2. **MET-1 프로토콜 실행**: 200회 스캔 성공률 >= 95% 달성 여부 측정
3. **독립 판독 경로 확인**: Layer A는 기본 카메라 앱으로 읽히고, B/C는 확장 경로에서만 복원되는지 검증

---

## 2. 준비물

### 2.1 디바이스

최소 2종 이상의 다른 디바이스를 사용한다. 예시(필수 아님):

| # | 디바이스 모델 | OS | 카메라 해상도 | 기기명 칸 |
|----|------------|-----|------------|---------|
| 1  | 예: iPhone 14 | iOS 17 | 12 MP | ________________ |
| 2  | 예: Samsung Galaxy S23 | Android 14 | 50 MP | ________________ |
| 3  | (선택사항) | | | ________________ |

**요구사항**:
- 각 기기의 기본 카메라 앱이 정상 작동
- 최소 한 기기는 iOS, 한 기기는 Android (서로 다른 QR 라이브러리 스택 검증)

### 2.2 QR 생성 및 출력

#### 생성 스크립트 사용법

```bash
# 프로젝트 루트에서
python scripts/generate_test_qrs.py \
  --output=docs/test-plan/qr-samples \
  --payload-sizes small,medium,large,overlapping \
  --ecc M \
  --count 25
```

**출력**: `docs/test-plan/qr-samples/` 디렉토리에 다음 파일 생성:
- `small_*.png`: 작은 페이로드 (Layer A만, ~80B)
- `medium_*.png`: 중간 페이로드 (3층, ~400B)
- `large_*.png`: 큰 페이로드 (3층, ~800B)
- `overlapping_*.png`: 오버래핑 케이스 (다층 표현, ~600B)

각 `*` 뒤에는 번호(01~25)가 붙는다.

#### 출력 방식 (두 가지 선택)

| 방식 | 권장 크기 | 장점 | 단점 |
|------|---------|-----|------|
| **화면 표시** (A-ENV1 중심) | 200×200 ~ 400×400 px | 조도 제어 가능, 즉시 테스트 | 반사 영향, 화면 밝기 편차 |
| **인쇄** (MET-1 중심) | 5cm × 5cm (200 DPI 기준 ~400×400 px) | 일관된 대비, 재사용 가능 | 인쇄 품질 편차, 종이 매질 영향 |

**권장**: A-ENV1은 화면 표시(최소 1대 디바이스 또는 모니터), MET-1은 인쇄(확실한 결과) 또는 화면(빠른 반복)

### 2.3 조명 환경

최소 2개 조건을 선택한다:

| 조건명 | 설명 | 예시 | 측정값 |
|--------|------|------|--------|
| **실내 일반** (Normal Indoor) | 사무실, 밝은 실내 조명 | 형광등 또는 LED 천장등, 균등 조도 | _____ lux |
| **저조도** (Low Light) | 희미한 조명, 야간 실내 | 침실 간접등, 어두운 카페 | _____ lux |
| **역광** (Backlight) | 광원이 카메라 뒤에 있음 | 햇빛 창문 배경, 실외 밝은 빛 | _____ lux |

각 조건당 최소 25회 스캔을 수행한다 (2 디바이스 × 2 조건 × 25회 = 100회 최소; 200회 권장).

---

## 3. A-ENV1 테스트 절차: 화면 표시·조도별 판독

### 3.1 목적
오버래핑 QR이 다양한 화면 표시 환경과 조명에서 읽히는지 확인 (기본 정보는 "공개 레이어만 노출" 조건).

### 3.2 준비

1. 각 디바이스에 테스트 QR 이미지를 로드한다:
   - 테스트 케이스: `small_01.png`, `medium_01.png`, `large_01.png`, `overlapping_01.png` (각 4개)
   - 로드 방법: 파일 전송(AirDrop, 메일, 클라우드) 또는 웹 페이지에 업로드 후 저장

2. 조명 환경을 준비한다:
   - 밝기 미터 또는 스마트폰 조도 앱 설치 (선택, 측정용)
   - 각 조건에서의 조도(lux) 기록

### 3.3 Step-by-Step 절차

#### Step 1: 기본 카메라 앱으로 Layer A 읽기

1. 디바이스의 기본 **카메라 앱** (또는 포함된 스캐너)을 열기
2. QR 코드가 화면에 표시되거나 인쇄된 상태에서 대기
3. **카메라 프리뷰**에서 QR이 인식되는지 확인:
   - iOS: 알림(노란 배너) 또는 팝업이 나타나는가?
   - Android: 알림 또는 자동 스캔 표시가 나타나는가?
4. **자동 스캔** 또는 사용자가 링크를 열 때, **Layer A 페이로드만** 표시되는지 확인
   - 예시: `https://qoverwrap.example.com/v1/card?id=abc123&seq=...`
   - **B/C 데이터는 절대 노출되지 않아야 함** (정책 위반이면 기록)

#### Step 2: 조도 변화별 반복

| 조건 | 조도 (lux) | 디바이스별 시도 | 기록 |
|------|-----------|---------|------|
| 실내 일반 | _____ | 각 1회 | 아래 템플릿 사용 |
| 저조도 | _____ | 각 1회 | 아래 템플릿 사용 |
| 역광 | _____ | 각 1회 | 아래 템플릿 사용 |

#### Step 3: 페이로드 크기별 테스트

각 조명 조건에서 다음 4가지 페이로드를 테스트:

1. **small** (Layer A만, ~80B)
2. **medium** (3층, ~400B)
3. **large** (3층, ~800B)
4. **overlapping** (다층 표현, ~600B)

### 3.4 기록 템플릿

A-ENV1 결과를 표에 기록한다. 최소 각 조건별 1회 이상:

```markdown
## A-ENV1 결과

### 조건: 실내 일반 (조도 _____ lux)

| # | 디바이스 | 페이로드 | Layer A 정확 | Layer B/C 노출 | 비고 |
|----|---------|---------|------------|-------------|------|
| 1  | Device1 | small   | ✓ / ✗      | ✓ / ✗       | ___ |
| 2  | Device1 | medium  | ✓ / ✗      | ✓ / ✗       | ___ |
| 3  | Device1 | large   | ✓ / ✗      | ✓ / ✗       | ___ |
| 4  | Device1 | overlapping | ✓ / ✗   | ✓ / ✗       | ___ |
| 5  | Device2 | small   | ✓ / ✗      | ✓ / ✗       | ___ |
| ... | ... | ... | ... | ... | ... |

### 조건: 저조도 (조도 _____ lux)
[같은 형식]

### 조건: 역광 (조도 _____ lux)
[같은 형식]
```

### 3.5 Pass/Fail 기준 (A-ENV1)

각 조명 조건에서:
- **PASS**: 모든 디바이스에서 Layer A 읽기 성공, Layer B/C 미노출
- **FAIL**: 어느 한 디바이스에서 실패 또는 정책 위반 (B/C 노출)
- **경고**: 일부 페이로드 크기에서만 실패 → 크기 제한 문서화

---

## 4. MET-1 테스트 절차: 200회 스캔 성공률

### 4.1 목적
오버래핑 QR의 스캔 성공률을 정확히 측정하고, >= 95% 달성 여부 확인.

### 4.2 프로토콜 개요

| 항목 | 고정값 |
|------|--------|
| 총 시도 수 | **200회** |
| 디바이스 | 최소 **2종** |
| 조명 조건 | 최소 **2개** |
| 페이로드 크기 | 4종 (small/medium/large/overlapping) |
| 성공 정의 | Layer A payload 오류 없이 읽음 |
| 실패 정의 | 타임아웃, 미스캔, 체크섬 실패, 무응답 |
| 목표 | >= 95% 성공률 (200회 중 최소 190회 성공) |

### 4.3 시도 분배 예시

다음은 200회를 분배하는 한 가지 방식이다:

```
총 200회 = 디바이스 2종 × 조명 2조건 × 페이로드 4종 × 5회
         = 2 × 2 × 4 × 5 = 80회 (부족)

더 높은 반복을 위해:
200회 = 디바이스 2종 × 조명 2조건 × 페이로드 4종 × 6.25회 (반올림하여 6~7회)
      ≈ 2 × 2 × 4 × 6.25 ≈ 200회

또는 더 단순하게:
200회 = 디바이스 2종 × 조명 2조건 × 25회
      = 2 × 2 × 25 = 100회 (최소, 권장은 추가 반복)

확장 (400회 권장):
400회 = 디바이스 2종 × 조명 2조건 × 페이로드 4종 × 12.5회 ≈ 2 × 2 × 4 × 12~13회
```

**권장**: 페이로드 크기별 분석을 위해 최소 **400회** 시도 (각 크기당 100회 이상).

### 4.4 자동화된 측정 스크립트

(준비 중) `tests/feasibility/test_device_minio.py` 등에서 제공할 예정.

현재는 수동 기록을 사용한다.

### 4.5 Step-by-Step 절차

#### 준비 단계

1. QR 이미지 세트 생성 (위의 2.2 참고):
   ```bash
   python scripts/generate_test_qrs.py \
     --output=docs/test-plan/qr-samples \
     --payload-sizes small,medium,large,overlapping \
     --ecc M \
     --count 50
   ```
   (각 크기당 50개, 반복 가능)

2. 각 디바이스에서 QR 앱 준비:
   - **기본 카메라 앱** (또는 내장 스캐너) 사용
   - 확장 테스트 (선택): PoC 디코더 앱 설치

3. 측정 환경 고정:
   - 카메라-QR 거리: ~20cm (일정하게 유지)
   - 촬영 시간: 각 시도당 최대 3초 (자동 스캔 시간초과)

#### 실행 단계

**세션 1: 디바이스1 × 조명조건1 × 페이로드_small × 25회**

1. QR 이미지 세트 준비: `small_01.png` ~ `small_25.png`
2. 화면(또는 인쇄)에 첫 번째 QR 표시
3. 디바이스1의 카메라를 20cm 거리에서 정면 촬영
4. 자동 스캔 또는 사용자 행동으로 QR 읽기
5. 결과 기록 (성공/실패)
6. 다음 QR로 진행
7. 25회 반복

**세션 2~N: 다른 조합**

디바이스1/조명2, 디바이스2/조명1, 디바이스2/조명2 등 반복.

### 4.6 기록 템플릿

다음 표 형식으로 기록한다. (마크다운 또는 CSV)

#### 요약 시트

```markdown
## MET-1 스캔 성공률 — 요약

| 디바이스 | 조명 | 페이로드 | 총시도 | 성공 | 실패 | 성공률 | Pass/Fail |
|---------|------|---------|--------|------|------|--------|-----------|
| Device1 | 실내일반 | small | 25 | 24 | 1 | 96% | ✓ |
| Device1 | 실내일반 | medium | 25 | 24 | 1 | 96% | ✓ |
| Device1 | 실내일반 | large | 25 | 23 | 2 | 92% | ✗ |
| Device1 | 실내일반 | overlapping | 25 | 25 | 0 | 100% | ✓ |
| Device1 | 저조도 | small | 25 | 20 | 5 | 80% | ✗ |
| ... | ... | ... | ... | ... | ... | ... | ... |
| **전체** | | | 200 | **190+** | **10-** | **≥95%** | **PASS** |
```

#### 상세 기록 시트 (세션별)

```markdown
### 상세 기록: Device1 × 실내일반 × small

| # | QR ID | 카메라 피드 인식 | 자동 스캔 | 수동 스캔 | Layer A 정확 | 실패 사유 | 비고 |
|----|-------|---------|---------|---------|-----------|---------|------|
| 1 | small_01 | ✓ | ✓ | - | ✓ | - | 1st try |
| 2 | small_02 | ✓ | ✓ | - | ✓ | - | |
| 3 | small_03 | ✓ | ✗ | ✓ | ✓ | 반사 | 각도 조정 후 성공 |
| 4 | small_04 | ✗ | - | ✗ | ✗ | 화질 저하 | 이미지 손상 의심 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 25 | small_25 | ✓ | ✓ | - | ✓ | - | 소계: 24/25 |
```

**열 설명**:
- **QR ID**: 테스트 파일명
- **카메라 피드 인식**: 카메라 프리뷰에서 QR 신호 감지
- **자동 스캔**: 카메라 앱이 자동으로 스캔
- **수동 스캔**: 사용자가 명시적으로 스캔 (자동 실패 시 재시도)
- **Layer A 정확**: 읽은 데이터가 예상값과 일치
- **실패 사유**: 타임아웃, 미스캔, 체크섬 실패, 화질 등
- **비고**: 환경 변화, 기기 재시작 등

### 4.7 Pass/Fail 기준 (MET-1)

- **PASS**: 전체 시도 중 성공률 >= 95% (예: 200회 중 190회 이상)
- **FAIL**: 성공률 < 95%
- **조건부 PASS**: 특정 크기에서만 실패 → 제한사항 문서화

---

## 5. 독립 판독 경로 확인 (O-2 검증)

### 5.1 목적

오버래핑 QR이 두 가지 경로에서 올바르게 작동하는지 확인:
1. **일반 경로**: 기본 카메라 앱 → Layer A만 노출
2. **확장 경로**: PoC 디코더 → A/B/C 복원 가능

### 5.2 절차

#### 5.2.1 기본 경로 (일반 카메라 앱)

A-ENV1 및 MET-1에서 이미 검증됨. 추가 확인 사항:

| 항목 | 확인 |
|------|------|
| iOS 기본 카메라 (또는 Stocks 앱의 QR 스캔) | ✓ Layer A만 읽힘 |
| Android 기본 카메라 (또는 Google 렌즈) | ✓ Layer A만 읽힘 |
| B/C 데이터 절대 노출 | ✓ |

#### 5.2.2 확장 경로 (PoC 디코더)

QR 생성기와 같은 구현체로 **라운드트립 검증**:

```python
# 생성
payload, a_text, b_data, c_data = _make_three_layer_payload()
img = _make_qr(payload)

# 기본 경로 검증 (위에서)
# ...

# 확장 경로 검증
from PIL import Image
bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
decoded_raw = pyzbar_decode(bgr)[0].data.decode('utf-8')
got_a, got_b, got_c = decode_layers(decoded_raw)

assert got_a == a_text, f"A 불일치: {got_a!r} != {a_text!r}"
assert got_b == b_data, f"B 불일치: {len(got_b)} != {len(b_data)}"
assert got_c == c_data, f"C 불일치: {len(got_c)} != {len(c_data)}"
```

**기록 템플릿**:

```markdown
## 독립 판독 경로 (O-2)

### 기본 경로
| QR 샘플 | iOS | Android | B/C 노출 | 결과 |
|--------|-----|---------|---------|------|
| small_01 | ✓ | ✓ | ✗ | PASS |
| medium_01 | ✓ | ✓ | ✗ | PASS |
| large_01 | ✓ | ✓ | ✗ | PASS |
| overlapping_01 | ✓ | ✓ | ✗ | PASS |

### 확장 경로 (PoC 디코더)
| QR 샘플 | decode_layers 성공 | A 정확 | B 정확 | C 정확 | 결과 |
|--------|-------|--------|--------|--------|------|
| small_01 | ✓ | ✓ | N/A | N/A | PASS |
| medium_01 | ✓ | ✓ | ✓ | ✓ | PASS |
| large_01 | ✓ | ✓ | ✓ | ✓ | PASS |
| overlapping_01 | ✓ | ✓ | ✓ | ✓ | PASS |
```

---

## 6. 전체 기록 체크리스트

테스트 세션마다 다음을 확인한다:

- [ ] 디바이스 및 기기명 기록 완료
- [ ] 조명 조건 및 조도(lux) 측정 기록
- [ ] QR 생성 스크립트 실행 성공
- [ ] A-ENV1: 각 조건별 4개 페이로드 × 2 디바이스 테스트 완료
- [ ] MET-1: 최소 200회 시도 기록 (권장 400회)
- [ ] MET-1 성공률 >= 95% 달성 여부 확인
- [ ] 독립 판독 경로: 기본 경로 PASS 확인
- [ ] 독립 판독 경로: 확장 경로 라운드트립 PASS 확인
- [ ] 실패 사례 분석: 원인 및 제한사항 문서화
- [ ] 최종 보고서 작성 시작

---

## 7. 보고서 작성

### 7.1 구조

Phase B 입력 아티팩트: `experiment-report.md` 또는 `experiment-report.json`

```markdown
# A-ENV1 & MET-1 물리 디바이스 테스트 결과

## 환경 메타데이터
- 테스트 일시: YYYY-MM-DD HH:MM
- Python 버전: 3.X
- qrcode 라이브러리 버전: X.Y.Z
- pyzbar 버전: X.Y.Z
- QR ECC 레벨: M
- 테스트자: ____________

## A-ENV1 결과
[위의 3.4 템플릿 포함]

### 요약
- 화면 표시 환경: PASS/FAIL
- 저조도 환경: PASS/FAIL
- 역광 환경: PASS/FAIL
- 전체: PASS/FAIL

## MET-1 결과
[위의 4.6 템플릿 포함]

### 요약
- 총 시도: 200회 (또는 ____회)
- 성공: ____회
- 실패: ____회
- 성공률: ____%
- Pass/Fail: PASS (>= 95%) / FAIL (< 95%)

## 독립 판독 경로 (O-2)
[위의 5.2 템플릿 포함]

### 요약
- 기본 경로 (기본 카메라): PASS/FAIL
- 확장 경로 (PoC 디코더): PASS/FAIL
- Layer A/B/C 분리: PASS/FAIL

## 제한사항 및 향후 작업
- [실패 사례 분석]
- [페이로드 크기 제한]
- [디바이스/OS별 편차]
```

### 7.2 Pass/Fail 최종 판정

| 검증 항목 | 결과 |
|----------|------|
| A-ENV1 (화면 표시/조도) | PASS / FAIL |
| MET-1 (스캔 성공률 >= 95%) | PASS / FAIL |
| 독립 판독 경로 (O-2) | PASS / FAIL |
| **Phase A 종료 가능** | YES / NO |

**Phase A 종료 조건**: 위 3개 항목 모두 PASS이고, `metrics-protocol.md`가 문서 승인 수준일 때.

---

## 부록: 스크립트 사용 예시

### QR 생성

```bash
cd /home/rae/projects/workspace/QoverwRap

# 기본 사용
python scripts/generate_test_qrs.py \
  --output docs/test-plan/qr-samples \
  --payload-sizes small,medium,large,overlapping \
  --ecc M \
  --count 25

# 출력 확인
ls docs/test-plan/qr-samples/
# small_01.png, small_02.png, ..., overlapping_25.png
```

### 간편 측정 (향후)

```bash
# 자동화 테스트 (개발 중)
python -m pytest tests/feasibility/test_device_minio.py \
  --device-count 2 \
  --trials 200 \
  --record-csv test-results.csv
```

### 라운드트립 검증 (확장 경로)

```bash
# tests/feasibility/conftest.py의 helper 사용
from tests.feasibility.conftest import encode_layers, decode_layers

a = "https://qoverwrap.example.com/v1/card?id=test"
b = b'{"issuer":"QoverwRap"}'
c = b'signature...'

payload = encode_layers(a, b, c)
got_a, got_b, got_c = decode_layers(payload)
assert got_a == a and got_b == b and got_c == c
```

---

## Quick Reference: 밀도 한계 테스트 명령어

### 1. QR 이미지 생성 (최초 1회)
```bash
cd ~/projects/workspace/QoverwRap
.venv/bin/python scripts/generate_density_qrs.py
# → test-qr-density/ 에 48개 이미지 + manifest.json 생성
# 옵션: --versions 5,10,15,20,25,30,35,40 --sizes 200,400,600 --ecc M,H
```

### 2. 디스플레이 서버 실행 (터미널 1)
```bash
.venv/bin/python scripts/qr-display-server.py --image-dir test-qr-density --interval 0 --port 8765
# 브라우저에서 http://localhost:8765 열기
```

### 3. 스캔 테스트 실행 (터미널 2)
```bash
# 기기별로 --output 파일을 다르게 지정할 것!
.venv/bin/python scripts/density_scan_test.py --device "Xiaoxin Pad" --output test-results/density-xiaoxin-pad.json
.venv/bin/python scripts/density_scan_test.py --device "Galaxy Tab S9 Ultra" --output test-results/density-galaxy-tab.json
.venv/bin/python scripts/density_scan_test.py --device "LG V20" --output test-results/density-lg-v20.json
.venv/bin/python scripts/density_scan_test.py --device "Galaxy S7" --output test-results/density-galaxy-s7.json
```

### 4. 개별 QR 재확인 (의심 결과)
```bash
# 디스플레이 서버가 실행 중인 상태에서:
curl -s -X POST "http://localhost:8765/api/set?index=$(curl -s http://localhost:8765/api/list | python3 -c "import sys,json; imgs=json.load(sys.stdin)['images']; print(imgs.index('v10_600px_M.png'))")"
```

### 참고
- `--interval 0` = 수동 모드 (자동 전환 안 함)
- 스캔 기록기가 디스플레이 서버를 자동 제어함 (→ 키 안 눌러도 됨)
- Ctrl+C로 중단해도 결과 저장됨, 같은 명령 재실행 시 이어서 가능
- 같은 --output 파일을 다른 기기로 실행하면 resume 기능이 오작동함 — 반드시 기기별 별도 파일 사용

---

## 참고 문서

- [phase-a-feasibility.md](phase-a-feasibility.md) — A-ENV1 정의
- [metrics-protocol.md](metrics-protocol.md) — MET-1 고정값
- [overlap-and-independent-readpath.md](overlap-and-independent-readpath.md) — 독립 경로 요구사항
- [test_a_env.py](../../tests/feasibility/test_a_env.py) — 자동화된 이미지 변환 테스트 (참고용)

