# QoverwRap 특허 명세서 초안

> **상태**: `ai_generated` — 변리사 검토 전. 청구항 표현·법률 용어는 변리사 단계에서 정제.
> **검증 정책**: 청구항 후보의 신규성/진보성은 `docs/research/prior-art-survey.md` (KIPRIS + EPO OPS) 결과에 근거하며, 인용 0-hit 항목을 핵심 차별점으로 사용한다.
> **관련 문서**: 코어 구현 `src/qoverwrap/`, 통합 테스트 `tests/test_*.py`, 데모 앱 `demo/`, 선행기술 조사 `docs/research/prior-art-survey.md`.
> **작성일 기준**: 2026-04-29 / 도면은 `docs/patent/figures/` 의 PNG 캡처 + 본 문서의 텍스트 다이어그램 결합.

---

## 1. 발명의 명칭

**단일 QR 페이로드 내 다층 데이터 구조화 및 내장 서명 기반 접근 제어 시스템과 그 방법** (가제)

영문: *System and Method for Multi-Layer Data Structuring within a Single QR Payload with Embedded Signature-Based Access Control*

---

## 2. 기술 분야

본 발명은 QR 코드(Quick Response Code, ISO/IEC 18004) 기반 데이터 인코딩 및 검증 분야에 관한 것으로, 보다 상세하게는 **단일 QR 코드 내에 복수의 논리 계층(layer)을 구조화하여 저장하고**, 디지털 서명을 동일 페이로드 내에 내장하며, 접근 권한에 따라 노출되는 계층을 동적으로 결정하는 시스템 및 그 방법에 관한 것이다.

---

## 3. 발명의 배경이 되는 기술

### 3.1 표준 QR 코드의 한계

표준 QR 코드는 하나의 데이터 필드만을 지원하며, 모든 정보가 동일하게 노출된다. 권한별 차등 노출, 위변조 탐지, 발급자 진위 확인이 단일 QR 단독으로 불가능하다.

### 3.2 종래 기술의 분류 및 한계 (선행기술 조사 결과)

선행기술 11건은 다음 4개 군으로 분류되며, 본 발명의 접근 방식은 어느 군에도 속하지 않는다 (`docs/research/prior-art-survey.md` §3, §7 참조).

| 군 | 대표 문헌 | 방식 | 한계 |
|----|-----------|------|------|
| (가) 모듈 비트 스테가노그래피 | Liu et al. 2019; Suresh et al. 2023; Koptyra & Ogiela 2024 | QR 코드워드 비트 조작 (Hamming/ECC 활용) | **ECC 용량 소비** → 오류 정정 능력 감소; 디코딩 시 알고리즘 의존 |
| (나) 물리/시각 다층 | Tkachenko (2LQR, FR3027430A1); 넥스팟솔루션 KR10-2875492; 에이엠홀로 KR10-2022-0046292 | 텍스처 패턴, 라벨 스택, 홀로그램 | **물리 인쇄 의존** → 디지털 환경 미작동; 고해상도 입력 필요 |
| (다) 컬러/재료 채널 | Arce US10152663B2; ETRI/POSTECH KR10-2765780; CN111224771A | RGB 채널, 재료층, 이미지 도메인 카오스 암호 | 표준 흑백 QR 비호환; 전용 디코더 필요 |
| (라) 외부 검증 시스템 | Subramanian US12200151B2 (블록체인); Apple IOL US 9,022,291 (시간축 chrominance) | 블록체인·시간축 신호 등 외부 채널 | **외부 인프라/네트워크 의존** → 오프라인 검증 불가 |

### 3.3 EPO OPS 보강 검색 (관할 무관)

다음 핵심 키워드 조합은 전세계에서 0건이었다 (`prior-art-survey.md` §6-5).

- `cpc=G06K19/06 AND ti,ab=(signature AND QR)` → 0
- `ti,ab=(QR AND ed25519)` → 0
- `ti,ab=(QR AND (delimiter OR "payload structur*"))` → 0

---

## 4. 발명이 해결하려는 과제

1. 단일 표준 QR 코드 내에 **복수의 논리 계층**을 ECC 용량을 소모하지 않으면서 구조화 저장한다.
2. 외부 시스템(서버·블록체인·PKI 인프라) 없이 **오프라인 자기완결적**으로 위변조 검증이 가능하게 한다.
3. 디코더 측에서 **접근 권한별 차등 노출**(role-based exposure)이 가능하게 하며, 검증 실패 시 안전 기본값으로 강등(safe-fallback)을 보장한다.
4. **표준 QR 리더와 호환**되어, 본 발명을 모르는 디코더도 최소한의 평문 정보(공개 계층)는 정상적으로 판독한다.

---

## 5. 과제 해결 수단 (요약)

본 발명은 다음 구성을 결합한다.

(a) **페이로드-레벨 구조화**: QR 코드의 표준 데이터 필드 *문자열 내용 안에서* 구획자(delimiter) 와 이진 헤더(binary header) 를 사용하여 3개 논리 계층 — Layer A(공개 텍스트), Layer B(컨텍스트 메타데이터), Layer C(서명) — 을 직렬화한다.

(b) **내장 서명**: Layer A 와 Layer B 의 결합 메시지에 대한 디지털 서명(예: Ed25519)을 Layer C 로 동일 QR 페이로드 안에 내장한다. 이로써 QR 자체가 위변조 탐지의 자기완결적 단위가 된다.

(c) **역할 기반 리졸버**: 접근 권한 수준(public / authenticated / verified)에 따라 노출되는 계층이 정책으로 분기되며, 검증 실패 시 public 으로 강등된다.

(d) **표준 호환**: Layer A 가 평문으로 페이로드 선두에 위치하므로 표준 QR 리더는 이를 그대로 판독하며, 후속 base64 트레일러는 무의미한 문자열로 보일 뿐 디코더의 동작을 방해하지 않는다.

---

## 6. 발명의 효과

| 효과 | 비교 대상 | 효과의 근거 |
|------|-----------|-------------|
| ECC 용량 100% 보존 | (가) 군 | 모듈 비트 조작 없이 표준 QR 인코딩 그대로 사용 |
| 오프라인 자기완결 검증 | (라) 군 | 서명을 페이로드 내부에 내장 |
| 디지털·인쇄 양 환경 지원 | (나) 군 | 페이로드 문자열 기반 → 매체 비의존 |
| 표준 흑백 QR 호환 | (다) 군 | 색상·재료 채널 미사용 |
| 표준 리더와 부분 호환 | 전체 | Layer A 평문 노출 |
| 안전 기본값 보장 | — | Verified 실패 시 public 강등 |

---

## 7. 도면의 간단한 설명

- **Fig. 1**: 단일 QR 페이로드의 비트 레이아웃 구조도. (텍스트 다이어그램 — 본 명세서 §8.1)
- **Fig. 2**: 인코더(encode_layers)의 동작 흐름도. (텍스트 다이어그램 — §8.2)
- **Fig. 3**: 디코더 및 리졸버의 접근 수준 분기 흐름도. (텍스트 다이어그램 — §8.3)
- **Fig. 4**: 응용 레이어의 발급자 라우팅 개념도. (텍스트 다이어그램 — §8.4)
- **Fig. 5**: Bare 모드 — 동일 QR 의 3-수준 해석 결과 (raw 텍스트). (`figures/fig5-bare-3col.png`)
- **Fig. 6a-c**: Themed 모드 — 발급자별 응용 카드 렌더링 (Tigers/Violet/Comic Con). (`figures/fig6a-tigers.png`, `fig6b-violet.png`, `fig6c-comiccon.png`)
- **Fig. 7a/7b**: 위변조 검출 — Verified 카드의 INVALID 강등 (`figures/fig7a-tampered-invalid.png`) 및 원본 복원 시 VALID 회복 (`figures/fig7b-restored-valid.png`).

---

## 8. 발명을 실시하기 위한 구체적인 내용

### 8.1 페이로드 비트 레이아웃 (Fig. 1)

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer A (UTF-8 평문 문자열)                                       │
│   예: "qwr:tigers-2026|VIP seat A1"                              │
├─────────────────────────────────────────────────────────────────┤
│ DELIMITER  =  "\n---QWR---\n"  (고정 9 바이트)                    │
├─────────────────────────────────────────────────────────────────┤
│ base64(  HEADER  ‖  LAYER_B  ‖  LAYER_C  )                      │
│                                                                 │
│ HEADER (5 바이트, big-endian):                                   │
│   ├─ version    : uint8   (현재 0x01)                            │
│   ├─ b_len      : uint16  (Layer B 바이트 길이)                   │
│   └─ c_len      : uint16  (Layer C 바이트 길이)                   │
│                                                                 │
│ LAYER_B : 임의 바이너리 (≤ 65535 바이트)                          │
│ LAYER_C : 디지털 서명 바이트열 (예: Ed25519 = 64 바이트)           │
└─────────────────────────────────────────────────────────────────┘
```

[규칙]
- Layer A 가 비어있지 않더라도, Layer B 와 Layer C 가 모두 비어있는 경우 DELIMITER 와 트레일러를 생략하고 Layer A 만으로 페이로드를 구성한다.
- Layer A 는 DELIMITER 문자열을 포함할 수 없다 (인코더가 거부).
- 표준 QR 리더는 Layer A + DELIMITER + (base64 문자열) 전체를 단일 평문으로 인식한다 → 본 발명을 모르는 디코더에서는 Layer A 가 의미 있는 정보로, 트레일러는 무관한 문자열로 보인다.

### 8.2 인코더 동작 (Fig. 2)

```
입력: layer_a (str), layer_b (bytes), layer_c (bytes)
 │
 ├─ 검증: layer_a 에 DELIMITER 미포함, b/c 길이 ≤ 65535
 │
 ├─ b/c 둘 다 비어있나? ───── Yes ──→ return layer_a            (단순 모드)
 │     No
 │
 ├─ header = pack(">BHH", 0x01, len(b), len(c))
 ├─ frame  = header || layer_b || layer_c
 ├─ trailer = base64.b64encode(frame).decode()
 │
 └─ return layer_a + DELIMITER + trailer                       (복합 모드)
```

### 8.3 디코더 + 리졸버 (Fig. 3)

```
입력: payload (str), access_level ∈ {public, authenticated, verified}, public_key?

decode_layers(payload):
 │
 ├─ DELIMITER 미포함? ──── Yes ──→ return (payload, b"", b"")
 │     No
 ├─ split(DELIMITER, max=1) → layer_a, trailer
 ├─ frame = base64.b64decode(trailer)
 ├─ version, b_len, c_len = unpack(">BHH", frame[:5])
 ├─ version 검증, frame 길이 검증
 └─ return (layer_a, frame[5:5+b_len], frame[5+b_len:5+b_len+c_len])

resolve(payload, access_level, public_key):
 │
 ├─ access_level 정상화 (미지의 값 → "public")
 ├─ decode_layers 시도 → 실패 시 layer_a 만 추출하여 public 강등
 │
 ├─ public          → return (layer_a, None, None, verified=False)
 ├─ authenticated   → return (layer_a, layer_b, None, verified=False)
 └─ verified
       │
       ├─ public_key 없음 → public 강등
       ├─ verify_signature(public_key, layer_a, layer_b, layer_c)
       │      ├─ valid   → return (layer_a, layer_b, layer_c, verified=True)
       │      └─ invalid → public 강등
```

[안전 기본값] 인증 자료 결손, 페이로드 손상, 서명 위변조 — 어떠한 실패 경로에서도 결과는 *공개 계층 이상*을 노출하지 않는다.

### 8.4 응용 레이어 — 발급자 라우팅 (Fig. 4)

본 절은 **청구의 범위 외의 응용 예시** 이며, 발명의 실시를 보조하는 운영사 측 정책 레이어를 설명한다.

[Layer A 발급자 ID 컨벤션]
```
qwr:<issuer-id>|<human-readable message>
```

[신뢰 레지스트리 (운영사 측)]
```python
TRUST_REGISTRY = {
    "tigers-2026":      ed25519_pub_A,
    "violet-fandom":    ed25519_pub_B,
    "comic-con-2026":   ed25519_pub_C,
    ...
}
```

[검증 시 라우팅 흐름]
```
QR 스캔 → Layer A 추출 → "qwr:" 프리픽스 파싱 → issuer-id 분리
        → TRUST_REGISTRY[issuer-id] → public_key 조회
        → 본 발명의 verify_signature() 호출
        → 결과를 응용 UI(시각 테마/카드 렌더링)에 반영
```

이 구성에서 시각 테마(색·로고)는 issuer-id 와 1:1 대응되어, **사용자가 보는 시각적 표식이 곧 내부적으로 사용되는 검증 키의 단서**가 된다. 즉, 응용 측에서 마케팅 요소와 기술적 검증 루트가 분리되지 않는다.

### 8.5 데모 앱 실시예 (Fig. 5, 6, 7)

본 발명의 실시를 위한 일례로서, `demo/` 디렉토리에 React + FastAPI 기반 시연 앱이 구현되어 있다. 본 명세서에 첨부되는 도면은 해당 앱의 화면을 캡처한 것이다.

#### Fig. 5 — Bare 모드 (청구항 본체 시각화)

3-column 비교 화면에서 동일 QR 페이로드가 access_level 별로 다음과 같이 노출된다.

- Public 컬럼: Layer A 평문만 표시. Layer B/C 는 잠금.
- Authenticated 컬럼: Layer A + Layer B 노출. Layer C 잠금.
- Verified 컬럼: Layer A + Layer B + Layer C(서명) 노출 + 검증 결과 배지.

#### Fig. 6 — Themed 모드 (응용 예시)

같은 페이로드를 발급자 테마로 렌더링했을 때의 사용자 화면.

- Fig. 6a (Tigers): 야구 입장권 카드 — 좌석/구역/게이트/날짜/상대팀
- Fig. 6b (Violet): 팬덤 멤버십 카드 — Tier/Member ID/독점 콘텐츠
- Fig. 6c (Comic Con): 출입 배지 — 패스 등급/Hall/Panel

세 카드 모두 페이로드 데이터는 동일하며, 운영사 측 응용 레이어만 다르다.

#### Fig. 7 — 위변조 검출

서명 후 Layer B 가 변경된 경우, Verified 컬럼 카드가 잠금 상태로 강등되고 INVALID 도장이 표시된다. 동일 페이로드를 원본 데이터로 복원하면 즉시 VALID 로 회복된다.

---

## 9. 청구의 범위 (변리사 검토 전 후보)

> **법률 자문 아님**. 아래는 명세서 작성 단계의 청구항 후보이며, 최종 표현은 변리사 검토에서 확정된다.

### 9.1 독립항 후보

**[청구항 1] 단일 QR 페이로드 내 다층 데이터 구조화 방법**

QR 코드의 표준 데이터 필드에 저장되는 단일 페이로드 문자열을 생성하는 방법으로서,
(a) 공개 텍스트 계층(Layer A) 을 UTF-8 문자열로 입력받는 단계;
(b) 컨텍스트 메타데이터 계층(Layer B) 및 검증 계층(Layer C) 을 각각 바이너리 데이터로 입력받는 단계;
(c) Layer B 와 Layer C 가 모두 비어있지 않은 경우, 미리 정해진 구획자(DELIMITER) 와, 버전·Layer B 길이·Layer C 길이를 포함하는 고정 길이 이진 헤더를 생성하는 단계;
(d) 상기 헤더, Layer B, Layer C 를 순차적으로 결합한 프레임을 base64 인코딩하여 트레일러를 생성하는 단계;
(e) Layer A, 상기 구획자, 상기 트레일러를 순차적으로 결합하여 단일 페이로드 문자열을 출력하는 단계;
를 포함하며,
상기 단일 페이로드 문자열은 표준 QR 리더에 의하여 평문으로 판독 가능한 것을 특징으로 하는 방법.

**[청구항 2] 내장 서명을 이용한 자기완결적 검증 방법**

청구항 1 의 페이로드 문자열을 입력받아 다층 데이터를 분리하고 검증 계층의 디지털 서명을 검증하는 방법으로서,
(a) 입력 페이로드에서 구획자를 기준으로 Layer A 와 트레일러를 분리하는 단계;
(b) 트레일러를 base64 디코딩하여 헤더를 파싱하고, Layer B 및 Layer C 를 추출하는 단계;
(c) Layer A 와 Layer B 의 결합 메시지에 대하여, Layer C 를 디지털 서명으로 사용하여 외부 시스템 호출 없이 검증 결과를 출력하는 단계;
를 포함하며,
상기 검증은 동일 페이로드 내부의 정보만으로 자기완결적으로 수행되는 것을 특징으로 하는 방법.

### 9.2 종속항 후보

**[청구항 3]** 청구항 1 에 있어서, 상기 이진 헤더는 1 바이트 버전, 2 바이트 Layer B 길이, 2 바이트 Layer C 길이를 big-endian 으로 직렬화한 5 바이트로 구성되는 것을 특징으로 하는 방법.

**[청구항 4]** 청구항 1 에 있어서, 상기 구획자는 줄바꿈 문자로 둘러싸인 고유 문자열로서 Layer A 가 해당 문자열을 포함하는 입력은 거부되는 것을 특징으로 하는 방법.

**[청구항 5]** 청구항 1 에 있어서, Layer B 와 Layer C 가 모두 비어있는 경우 구획자 및 트레일러를 생략하고 Layer A 만으로 페이로드를 구성하는 단순 모드를 더 포함하는 것을 특징으로 하는 방법.

**[청구항 6]** 청구항 2 에 있어서, 상기 디지털 서명은 Ed25519 서명 알고리즘을 사용하며, 검증을 위한 공개키는 동일 페이로드 외부에서 제공되는 것을 특징으로 하는 방법.

**[청구항 7]** 청구항 2 에 있어서, 접근 수준에 따라 노출되는 계층을 달리하는 리졸버를 더 포함하며, 상기 리졸버는 (i) 공개 수준에서 Layer A 만, (ii) 인증 수준에서 Layer A 와 Layer B 를, (iii) 검증 수준에서 서명 검증 성공 시에 한하여 Layer A·B·C 를 출력하는 것을 특징으로 하는 방법.

**[청구항 8]** 청구항 7 에 있어서, 상기 리졸버는 페이로드 손상, 헤더 검증 실패, 공개키 미제공, 서명 검증 실패 중 어느 하나의 사유 발생 시 출력 결과를 공개 수준 이하로 강등하는 안전 기본값(safe-fallback) 을 적용하는 것을 특징으로 하는 방법.

**[청구항 9]** 청구항 1 또는 청구항 2 에 있어서, Layer A 의 선두 영역에 발급자 식별자가 미리 약속된 컨벤션(예: `qwr:<issuer-id>|<message>`) 으로 표기되며, 디코더 측이 해당 식별자를 추출하여 신뢰 레지스트리로부터 검증용 공개키를 조회하는 단계를 더 포함하는 것을 특징으로 하는 방법.

**[청구항 10]** 청구항 1 의 방법을 컴퓨터에 실행시키기 위한 명령어가 기록된 컴퓨터 판독 가능 저장 매체.

**[청구항 11]** 청구항 1 의 방법을 수행하는 인코더, 청구항 2 의 방법을 수행하는 디코더 및 검증부, 청구항 7 의 리졸버를 포함하는 단일 QR 페이로드 다층 데이터 시스템.

---

## 10. 신규성·진보성 근거 매핑

| 청구 요소 | 종래 기술 위치 | 차이점 |
|-----------|----------------|--------|
| 페이로드-레벨 구조화 (delimiter + base64 header) | 0 hits (EPO Q15) | 모든 선행기술이 (가)~(라) 군에 속함 |
| ECC 무손실 다층 인코딩 | (가) 군과 대비 | 코드워드 비트 미조작 |
| 자기완결 내장 서명 | 0 hits (EPO Q13: `signature AND QR + G06K19/06`) | (라) 군은 외부 시스템 의존 |
| Ed25519 + QR 조합 | 0 hits (EPO Q14) | 직접 선행기술 부재 |
| 안전 기본값 강등 정책 | 미발견 | 종래 정책층 분리 사례 부재 |
| 발급자 ID 컨벤션 + 라우팅 | 응용 영역 | 청구 핵심은 아니나 종속항 9 로 보호 |

---

## 11. 요약서 (Abstract)

본 발명은 단일 QR 코드의 표준 데이터 필드 내에 구획자와 이진 헤더를 사용하여 공개 텍스트(Layer A), 컨텍스트 메타데이터(Layer B), 검증 계층(Layer C) 의 3개 논리 계층을 직렬화하고, Layer C 에 Layer A 와 Layer B 에 대한 디지털 서명을 내장함으로써 외부 시스템 없이 오프라인으로 위변조 검증이 가능한 자기완결적 다층 QR 페이로드 시스템을 제공한다. 디코더는 접근 권한 수준에 따라 노출 계층을 결정하며, 검증 실패 시 공개 수준으로 안전 강등하는 정책을 포함한다. 본 발명은 QR 표준에 호환되어 본 발명을 모르는 표준 리더에서도 Layer A 평문 판독이 가능하고, 종래 기술과 달리 ECC 용량을 소모하지 않으며 인쇄·디지털 양 환경에서 동작한다.

---

## 12. 작업 상태 및 후속 작업

| 항목 | 상태 |
|------|------|
| 청구항 골격 (독립 2 + 종속 9) | ✅ 초안 |
| 실시예 본문 (§8) | ✅ 초안 |
| 도면 텍스트 (Fig. 1~4) | ✅ 본 문서에 포함 |
| 도면 캡처 (Fig. 5~7) | ⏳ `scripts/capture_figures.sh` 로 자동 생성 예정 |
| 변리사 검토 | ⏳ |
| KIPO 출원서 양식화 | ⏳ 변리사 단계 |

[다음 작업]
1. `scripts/capture_figures.sh` 실행하여 Fig. 5~7 PNG 생성
2. 본 문서 §8.5 의 도면 참조 경로 검증
3. 변리사 검토 (`status: ai_generated → human_reviewed → attorney_ready`)
