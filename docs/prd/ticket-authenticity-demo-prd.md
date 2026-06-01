# PRD — 티켓 진위확인 데모 앱 (QoverwRap 기반)

**작성일**: 2026-05-27 (v2 — 기존 `demo/` 자산 반영)
**상태**: Draft (남은 미결정 사항 — §11)
**접근 방식**: **기존 `demo/` (FastAPI+React) 기반 리팩터링** (2026-05-27 결정). P0 코어는 이미 구현돼 재사용. 첫 착수 = **일회성 카운터**.
**기반 문서**: [브레인스토밍 캡처](../brainstorming/qoverwrap-app-ideas_2026-05-26_1644.md), [세션 정리](../sum/session_2026-05-26_qoverwrap-app-ideas.md)
**관련**: [QoverwRap 명세 초안](../patent/spec-draft.md), `src/qoverwrap/`, `demo/`

> ⚠️ 이 문서는 데모 앱 PRD다. 합의되지 않은 영역(디자인 시스템 등)은 **섹션만 만들고 비워뒀다**. 임의로 채운 항목 없음. 결정이 필요한 지점은 모두 §11에 모았다.

---

## 1. 배경 / 컨텍스트

QoverwRap은 표준 QR 데이터 문자열 안에 **평문(Layer A) + 구획자 + base64(헤더 + Layer B + Ed25519 서명 Layer C)** 를 결합한 페이로드 레벨 wire format이다. 두 차례 브레인스토밍을 거쳐, 가장 강한 활용처로 **"티켓 진위확인 시스템(방문 성취 컬렉션 흡수)"** 이 도출되었다.

**시장 근거 (리서치 확인)**:
- 국내 4사 지류 티켓은 아트지 + 1D 바코드 + 일련번호 수준. 보안 사양 부재. **오프라인 즉시 진본 입증 수단 없음**.
- 2025-06 블랙핑크 위조 500여 장 사건, 적발 단서가 "오탈자" = 검표가 사람 눈에 의존.
- 경쟁(부스터랩 NFC 칩)은 인터넷 의존 + 고비용 + 본인확인 불가. **QoverwRap은 오프라인 검증 + 인쇄비 0 + 통신두절 백업**으로 차별.

**최대 잔여 리스크**: "위기의식 격차" — 고객(예매처/공연장)이 위조를 자기 문제로 느끼는지 미검증. 이 데모는 그 격차를 좁히는 영업·검증 도구이기도 하다.

## 2. 목적 (Goals)

이 데모는 하나의 코어 위에 **청중별 시연 시나리오 3개**를 얹어 세 목적을 동시에 충족한다.

| 청중 | 시연 강조점 | 성공 기준(데모가 보여줘야 할 것) |
|------|------|------|
| **기술 시연** (특허 PoC) | wire format·Ed25519 서명·오프라인 검증이 실제 작동 | 위조 QR은 검증 실패, 진짜 QR만 통과. 서버 없이도 서명 검증됨 |
| **예매처 영업** (B2B) | 검표 속도·위조 식별·기존 인쇄 그대로 도입 | 일반 프린터로 찍은 티켓을 스마트폰으로 즉시 판별. 특수 인쇄 0 |
| **투자/피칭** | 시장 페인 → 솔루션 → 확장(방문 컬렉션) 스토리 | 위조 사건 맥락 + 진위확인 + 팬덤 컬렉션 부가가치 흐름 |

### Non-Goals (이번 데모에서 증명하지 않는 것)
- 암표(부정 양도) 차단 — QoverwRap은 위조 차단이지 본인확인이 아님 (별도 논의)
- 실제 예매처 시스템 통합 / 상용 수준 보안 운영
- 종이 티켓의 법적 효력 대체

## 3. 범위 (Scope)

사용자 결정(2026-05-27): **발급 + 검증 + 방문 컬렉션** 풀 시나리오 / **웹 + 모바일 양 플랫폼** / **서버 포함**.

> 데모치고 범위가 크므로 §10에서 P0/P1/P2로 우선순위를 제안한다. (우선순위 자체는 미확정 — §11)

| 영역 | 포함 | 비고 |
|------|------|------|
| 발급 (티켓 QR 생성·서명) | ✅ | Layer A/B 구성 + Ed25519 서명 |
| 검증 (검표 스캔·판별) | ✅ | 오프라인 서명 검증 + 서버 일회성 카운터 |
| 방문 성취 컬렉션 | ✅ | 현장 QR 스캔 → 뱃지 누적 |
| 서버 (중복/복제 차단) | ✅ | 일회성 카운터 |
| 웹 플랫폼 | ✅ | 기존 `demo/` FastAPI+React 자산 활용 가능 |
| 모바일 플랫폼 | ✅ | 검표원 스캔 시연 |

### 3.1 기존 자산 매핑 (`demo/` — 재사용 기반)

특허 스크린샷용으로 구현된 `demo/`가 **P0 코어를 이미 충족**한다. 이 PRD는 그 위에 리팩터링/확장한다.

**이미 구현됨 (재사용)**:
| 기능 | 위치 |
|------|------|
| 발급자 키 서명 | `demo/backend/routers/crypto.py`, `trust.py` (`/api/trust/{id}/sign`) |
| 인코딩 + QR PNG | `routers/encode.py` (`/api/encode`, `/api/qr-image` — ECC L/M/Q/H) |
| 오프라인 서명 검증 + 3레벨 출력 | `routers/resolve.py` (public/authenticated/verified + 안전 강등) |
| 발급자 트러스트 라우팅 | `trust_registry.py` (`qwr:<issuer-id>\|<msg>` 컨벤션, in-memory) |
| **위조 시연** | `frontend/src/App.tsx` `attemptTamper()` + `TAMPER_PRESETS` (서명 후 Layer B 교체 → Verified INVALID 강등) |
| 티켓 Layer B 스키마 예시 | `App.tsx` `LAYER_B_PRESETS` (`section/seat/gate/date/time/opponent/holder`) |
| QR 스캐너 (카메라) + 직접 입력 | `frontend/src/components/QRScanner.tsx` |
| 가상 발급자 IP (상표 회피) | Tigers Baseball / Violet Fandom / Comic Con 2026 |
| 스크린샷 모드 | `App.tsx` `screenshot` 토글 |

**기존 자산에 없는 것 (이 PRD가 새로 추가)**:
1. **서버 일회성 카운터** — 중복/복제 사용 차단 (현재 데모는 서명만 검증, 재사용 미차단) ← **첫 착수**
2. **방문 성취 컬렉션** — 뱃지 누적 (현재는 단일 발급-검증만)
3. **모바일 최적화** — 현재 웹 카메라(PWA manifest 존재), 네이티브/PWA 강화 필요

**기존 데모의 데모 한정 제약 (운영 전 교체 대상)**:
- `trust_registry.py`가 프로세스 시작 시 발급자 비밀키를 메모리 생성·보관 (재시작마다 새 키) → 실제는 발급자만 비밀키 보유
- `/api/trust/{id}/sign`은 `QWR_ENABLE_DEMO_SIGNING=1`일 때만 동작하는 데모 편의 엔드포인트
- CORS `*` 개방

## 4. 페르소나 / 액터

| 액터 | 역할 | 데모에서의 행동 |
|------|------|------|
| **발급자** (공연주최/예매처) | 서명된 티켓 발행 | 공연·좌석 정보로 QR 티켓 생성 |
| **관객** (사용자) | 티켓 보유·현장 방문 | 티켓 제시, 현장 부스 QR 스캔으로 컬렉션 |
| **검표원** | 입장 게이트 검증 | 스마트폰으로 티켓 QR 스캔 → 진위 판별 |
| (선택) **운영자** | 서버 관리 | 일회성 카운터·사용 로그 — *데모 노출 여부 미정* |

## 5. 핵심 사용자 플로우 (User Flows)

> 아래는 Session 1–2에서 합의된 메커니즘 기반. 구체 화면·UX는 디자인 시스템(§9) 확정 후.

### 5.1 발급 플로우
1. 발급자가 공연/좌석/일련번호/발급시각 입력
2. 시스템이 Layer A(공식 URL+식별자) + Layer B(티켓 메타데이터) 구성
3. 발급자 개인키로 canonical 메시지 서명 → Layer C(64B)
4. wire format 인코딩 → QR 생성 → (인쇄 또는 사용자 단말 전달)

### 5.2 검증 플로우 (게이트)
1. 검표원이 QR 스캔
2. **오프라인**: 발급자 공개키로 서명 검증 → `verified`/`authenticated`/`public` 레벨 판정
3. **온라인(서버)**: 일회성 카운터 조회 → 중복 사용/복제 차단
4. 결과 표시 (진짜/위조/이미 사용됨)

### 5.3 방문 컬렉션 플로우
1. 관객이 현장 부스/포스터의 QR 스캔
2. 자격(티켓 보유/회원) 확인 + 방문 기록 서명 검증
3. 뱃지/마커 누적 → 컬렉션에 표시 (양자적 감정: 신원 노출 없이 "다녀왔음"만 증명)

## 6. 기능 요구사항 (Functional Requirements)

### 6.1 발급 (Issuance)
- FR-I1: 발급자는 공연 메타데이터를 입력해 서명된 티켓 QR을 생성할 수 있다
- FR-I2: 키 관리 — 발급자 키페어 생성/보관 *(데모 수준 범위 미정 — §11)*
- FR-I3: 생성된 QR을 화면 표시 / 다운로드 / 인쇄 가능

### 6.2 검증 (Verification)
- FR-V1: QR 스캔 시 Ed25519 서명을 **오프라인**으로 검증한다
- FR-V2: 검증 실패(위조/변조) 시 명확히 거부 표시한다
- FR-V3: resolver 출력 레벨(public/authenticated/verified)을 구분 표시한다
- FR-V4: 서버 연동 시 일회성 카운터로 중복/복제 사용을 차단한다
- FR-V5: 위조 시연용 — 의도적으로 위조/변조된 QR을 거부하는 시나리오 제공

### 6.3 방문 컬렉션 (Collection)
- FR-C1: 현장 QR 스캔 시 방문 기록을 신뢰 가능한 형태로 누적
- FR-C2: 컬렉션(뱃지/마커)을 사용자에게 표시
- FR-C3: 신원 비노출 — 컬렉션이 개인정보를 드러내지 않음 *(정책 세부 미정)*

### 6.4 서버 (Backend)
- FR-S1: 일회성 카운터 — QR별 사용 횟수 기록·조회
- FR-S2: 사용 로그 (사후 증거용) *(보존 정책 미정)*

## 7. 기술 요구사항 (Technical Requirements)

### 7.1 Wire Format (코드 확인됨 — `src/qoverwrap/encoder.py`, `crypto.py`)
```
[Layer A 평문 UTF-8] + "\n---QWR---\n"(11B) + base64( [5B 헤더] + [Layer B] + [64B Ed25519 서명] )
헤더 = version(1B) + b_len(2B BE) + c_len(2B BE)
canonical 서명 메시지 = "QWR1" + version(1B) + len(A)(2B) + A + len(B)(2B) + B
```
- 단순 모드: Layer B·C 모두 비면 구획자·트레일러 없이 Layer A만
- 서명: Ed25519 (서명 64B 고정), base64 +33% 팽창, byte 모드

### 7.2 QR 스펙 (실측 — 커밋 `e771f30` Layer B 코덱 도입 후)

이전 sum 인쇄비교의 "현실값 ~241B → v10" 추정은 4-필드 단순 가정 기준이었다. 실제 9-필드 + 한국어 + ISO 타임스탬프 + Ed25519 64B 서명을 결합하면 페이로드는 훨씬 크다. Layer B 직렬화 포맷에 따라 QR 버전이 크게 달라진다.

**측정 환경**: Layer A "qwr:tigers-2026|game-042-seat-12B" (33B), 9-필드 풀 티켓, ECC M, byte mode.

| 포맷 (태그) | Layer B | 전체 페이로드 | QR 버전 | 모듈 수 | 권장 물리 크기 |
|-------------|---------|-------------|---------|---------|--------------|
| **JSON (0x01)** | 246B | 464B | **v17** | 85×85 | ~42mm @ 0.5mm/모듈 |
| **CBOR str-key (0x02)** | 208B | 416B | **v16** | 81×81 | ~40mm |
| **CBOR-aggressive (0x03)** | 92B | 260B | **v12** | 65×65 | ~32mm @ 0.5mm / ~26mm @ 0.4mm |

**최소 케이스** (필수 3필드만 + 짧은 Layer A "qwr:t26|T123" = 12B): Layer B 24B, 전체 147B, **QR v8 (49×49)**, ~24mm @ 0.5mm/모듈 → **팔찌 가능**.

**플로어** (Layer B 비움): 136B, QR v8. 더 작게는 불가 — Ed25519 64B 서명 + base64 팽창이 하한.

**시사**:
- 콘서트/공연 종이 티켓 (3×4cm 이상): JSON OK, 디버그 가독성 우선
- 명함·영수증·전시 입장권 (2.5×2.5cm 내외): CBOR-aggressive 권장
- 팔찌 (2.5cm 폭): CBOR-aggressive + 필수 필드 + 짧은 Layer A 조합
- 특수 보안잉크(UV/홀로그램/미세문자) 모두 불필요 → 추가 인쇄 단가 0

**권장**: 발급자가 매체 선택과 함께 포맷 선택(`format: "json" | "cbor" | "cbor_aggr"` API 파라미터, M2에서 노출 예정). 검증기는 첫 바이트 태그로 자동 디스패치.

**스키마 discriminator (M2.5)**: `[tag:1B][body]` 프레이밍은 불변. 스키마 식별자는 body 내부에 둔다 — JSON/CBOR(str-key)는 기존 `kind` 필드로, aggressive(0x03)는 **정수키 `0 = schema_id`** 를 전 스키마 공통으로 신규 예약(필드 맵은 1부터 시작). **key 0 부재 시 schema_id=1(baseball_ticket) 폴백** → 카탈로그 도입 전 발급된 aggressive ticket 바이트와 backward-compatible. `kind`가 `"ticket"`→`"baseball_ticket"`로 길어져 string-keyed 포맷은 +10B(예산 JSON ≤260B / CBOR ≤225B로 상향), aggressive·프레이밍 바이트는 불변.

### 7.3 검증 (Resolver — `src/qoverwrap/resolver.py`)
- 출력 레벨: `public`(Layer A만) / `authenticated`(파싱된 메타, 미검증) / `verified`(서명 검증)
- 실패 시 Layer A만 노출하는 강등(safe-fallback) 정책

### 7.4 서버 (일회성 카운터 = 복제 "감지")
- **SQLite** 저장소 (확정 §11). 키 = **Layer C 서명(hex)** — 복제본은 동일 서명 → 자연 감지
- API: `POST /api/redeem {payload, max_uses}` → 서명 검증 → 카운터 증가 → `{status: ok|already_used|invalid, use_count}`
- ⚠️ 역할 = 복제 **"감지"** (중복 사용 = 복제 존재 신호). **진짜/가짜 자동 판별이 아님** — 서명만으론 재인증 vs 복제 구분 불가 (§7.5)

### 7.5 복제(완전 복사) 대책 — 매체별

> ⚠️ **전제**: 정적 서명은 **출처·무결성**을 보장하나 **유일성**은 보장 못 함. 비트 단위 완전 복제(스크린샷·재인쇄)는 코어 밖에서 매체별로 다룬다. (지폐 일련번호 ↔ 홀로그램 관계와 동일)

| 매체 | 대책 | 효과 / 한계 |
|------|------|------|
| **모바일 화면 제시** | **동적 liveness 요소** (현재시각·흐르는 안내 텍스트·애니메이션 — 코레일/SRT 방식) | 정지 스크린샷 복제가 그 자리에서 드러남. **검표원 육안 의존**(자동 X), 화면 녹화 실시간 재생엔 약하나 캐주얼 캡처엔 실용적 충분 |
| **지류(인쇄) 티켓** | **신분증 등 운영적 본인확인** | 동적 불가 → 기술이 아닌 운영 영역. **데모/기술 범위 밖** |
| **공통(온라인)** | 서버 일회성 카운터 (§7.4) | 복제 "감지" (사용 시점) |

- **데모 반영**: 소지자 앱 화면에 [서명 QR] + [동적 liveness 요소] 동시 표시. 지류 복제·신분증 검증은 범위 밖(§12).
- 암호학적 동적 회전 QR(TOTP식)·챌린지-리스폰스는 **로드맵**(데모 범위 밖) — 소지자 개인키 보유/시간 동기화가 필요해 발급자-서명 모델이 바뀜.

**복제 대책 3층 요약**:
1. **진위**(위조 차단) = QoverwRap Ed25519 서명 — *코어(동결)*
2. **감지**(복제 존재) = 서버 일회성 카운터 — *M1*
3. **liveness**(스크린샷 무력화) = 모바일 동적 요소 / 지류는 신분증(운영)

## 8. 비기능 요구사항 (Non-Functional)
- **오프라인 우선**: 서명 검증은 네트워크 없이 동작 (핵심 강점)
- **검표 속도**: 스캔→판정 *(목표 수치 미정 — §11)*
- 보안: 개인키 비노출, 데모 키와 운영 키 분리
- 호환: 일반 QR 리더로 Layer A는 읽힘 (폴백)

## 9. 디자인 시스템 / UI
> **[비워둠 — 미논의]** 색상·타이포·컴포넌트·뱃지 비주얼·화면 레이아웃 등 일체 미정.

## 10. 우선순위 / 마일스톤 (2026-05-27 확정)

기존 `demo/`가 P0 코어를 충족하므로, 마일스톤은 **리팩터링 + 신규 갭** 중심으로 재편.

- **M0 — 완료 (기존 `demo/`)**: 발급(서명) + 오프라인 서명 검증 + 3레벨 출력 + 위조 거부 시연 — 웹
- **✅ M1 — 완료 (커밋 da41352, 2026-05-28)**: **서버 일회성 카운터 = 복제 감지**. `POST /api/redeem` (SQLite, 키=서명 hex, max_uses 설정 가능). 응용 레이어(특허 청구 외, 코어 무수정). 테스트 6종 통과(`tests/demo/test_redeem.py`). 파일: `demo/backend/{redemption_store.py, routers/redeem.py, schemas.py, main.py}`
  - **✅ Follow-up (M1.1, code-reviewer 권고) — 전부 완료 (2026-05-28)**:
    - [HIGH] `SELECT → UPDATE` race window → `BEGIN IMMEDIATE` + `threading.Lock` 이중 방어. 16-스레드 barrier 동시성 테스트 추가. 커밋 `fa2d2a7`
    - [MEDIUM] `RedemptionStore()` 모듈 import 즉시 인스턴스화 → `Depends(get_store)` lazy init + `app.dependency_overrides` 테스트 패턴. 커밋 `14ab63b`
    - [LOW] tampered 카운터 테스트 진단력 부족 → 3회 재시도 black-box `invalid+use_count=0` 강제. 커밋 `6ff4a52`
- **✅ M1.2 — 완료 (커밋 e771f30, 2026-05-28)**: **Layer B 티켓 스키마 + 3-포맷 코덱** (JSON / CBOR str-key / CBOR-aggressive). `demo/backend/layer_b_codec.py`, 테스트 18종 (`tests/demo/test_layer_b_codec.py`). 발급자별 매핑 분기는 M2.5로 분리. §7.2에 실측 QR 버전 + 매체별 권장 명시.
- **✅ M2 — 완료 (2026-06-01)**: 3개 항목 전부 완료.
  - **✅ format 파라미터 노출 + 검증 경로 Layer B decode + 모바일 동적 liveness** (커밋 `9aff7e5`, 2026-05-29).
  - **✅ 방문 성취 컬렉션 + 뱃지 (양자적 감정 UX)** (2026-06-01): **신뢰모델 B** — 관객이 부스에서 티켓 제시 → 발급자 일치 검증(`verify_signature` + issuer 매칭) → 운영자 키로 "방문 마커" 서명 발급 → 신원 비노출 뱃지 누적. **양자적 감정** = `visitor_token = sha256(티켓 Layer C)[:32]`(PII 없음, 같은 티켓 결정적 묶기). **부스당 1뱃지**(`RedemptionStore` 키 `visit:{booth_id}:{visitor_token}` 재사용), `booth_id`를 마커 Layer B에 내장·서명 → **서울≠부산 별도 뱃지**. **발급자 일치 강제**(아이유 티켓→아이유 부스만, 타행사=`wrong_issuer`; 위조=`ticket_invalid`). 마커 자체가 wire format이라 **오프라인 재검증**(`POST /api/visit/verify`). 파일: `demo/backend/{booth_registry.py, routers/visit.py, schemas.py, main.py}`, `demo/frontend/src/{components/CollectionPanel.tsx, App.tsx, types.ts, api/client.ts}`, 테스트 11종(`tests/demo/test_visit.py`). **코어 무수정**, layer_b_codec 신규 태그 없음.
- **✅ M2.5 — 완료 (2026-06-01, 백엔드+테스트+문서)**: **self-describing Layer B 스키마 카탈로그**(B안). 발급자→스키마 1:1 라우팅 대신 schema_id를 body에 임베드(JSON/CBOR는 `kind`, aggressive는 정수키 0). 스키마 3종 `baseball_ticket`/`festival_pass`/`wristband` + `LayerBSchema` 디스크립터·`SCHEMA_CATALOG`. **멀티매체**: Comic Con이 한 키로 festival_pass+wristband 둘 다 발매·검증. **스키마 공유**: festival_pass를 Violet+Comic Con 공유. trust registry에 `allowed_schemas` 노출(발급 시 강제는 후속). 신규 `GET /api/schemas`, `/api/encode-layer-b`에 `schema` 파라미터·응답 `schema`/`schema_id`, `/api/resolve`에 `layer_b_schema`. 파일: `demo/backend/{layer_b_codec.py, trust_registry.py, schemas.py, routers/{encode,resolve,trust,catalog}.py, main.py}`, 테스트(`tests/demo/test_schema_catalog.py` 신규 + 4종 개정). **코어 무수정**, 프레이밍 바이트·aggressive 1~9 맵 불변(key 0 폴백으로 구 ticket 바이트 backward-compatible). 프론트 2단계 선택·동적 폼은 후속.
- **M3**: 모바일 최적화 (PWA 강화 / 검표원 스캔 흐름)

> 접근 방식 = 기존 기반 리팩터링이므로, M1 시작 전 기존 `demo/` 구조를 "티켓 진위확인 제품" 관점으로 재정리하는 작업이 선행된다 (범위·명명 정리).

## 11. 미결정 사항 / 오픈 퀘스천

기존 `demo/` 자산 확인으로 다수 해소됨. **남은 것만 결정하면 M1 착수 가능.**

### 해소됨 (기존 구현/결정 반영)
- ~~1. 우선순위~~ → 확정 (§10: M0 완료, M1 일회성 카운터 우선)
- ~~3. 키 관리 (데모 수준)~~ → in-memory 트러스트 레지스트리 (운영용 KMS는 별도)
- ~~4. 서버 스택~~ → FastAPI 재활용 (저장소는 11-A 참고)
- ~~6. 위조 시연 방법~~ → 구현됨 (서명 후 Layer B 교체 → INVALID)
- ~~8. 데모 콘텐츠~~ → 가상 IP (Tigers/Violet Fandom/Comic Con)

### M1(일회성 카운터) 착수 전 결정

**D. 오프라인 vs 온라인 — 해소 (2026-05-27): 도메인별 2층 검증**
- **콘서트/공연 (데모 주 타깃)**: 게이트 상시 온라인 가정 → **일회성 카운터 실시간 조회**. 오프라인 서명 검증은 *통신두절 백업* 시나리오.
- **약품/물류 등 (확장 도메인, 데모 범위 외)**: 장기 오프라인 → 서명 검증은 현장 즉시, **일회성은 서버 동기화 시점에 사후 검수**.
- 데모는 콘서트(온라인) 기준으로 구현하되, "통신두절 시 서명 검증만으로 위조 1차 차단" 토글을 백업 시연으로 둘 수 있음.

**A/B/C — 확정 (2026-05-27)**:
- **A. 카운터 저장소 = SQLite** — 재시작 후에도 카운터 유지, 사후 검수·로그 시연에 유리.
- **B. 일회성 정책 = 설정 가능** — 1회 / N회 / 재입장 허용을 티켓별 플래그로. 데모에서 여러 정책 시연.
- **C. 특허 경계 = 응용 레이어 (확정·불변)** — 일회성 카운터는 **특허 청구 외 응용 레이어**. ⚠️ **특허(명세·청구항·도면)는 이미 심사청구 완료 → 일절 수정 금지.** 코어(`src/qoverwrap/` wire format + Ed25519 서명 + resolver)도 청구 범위라 건드리지 않음. 모든 데모 작업은 `demo/`(응용 레이어)에만 한정.

### 나중 마일스톤 결정 (M2/M3)
- ~~**방문 컬렉션 정책** (M2)~~ → **해소 (2026-06-01)**: 신뢰모델 B(티켓 제시→발급자 일치 검증→운영자 키로 마커 발급), **부스당 1뱃지**(재방문="이미 수집됨"), 신원 비노출=`visitor_token` 해시 묶기, **발급자 일치 강제**(자기 행사 부스만). 한 사람의 여러 티켓을 한 컬렉션으로 묶는 **회원 단위 통합**은 자격 ID 레이어로 후속(M2.5 이후).
- ~~**Layer B 티켓 스키마 확정**~~ → **해소** (커밋 `e771f30`, 2026-05-28). `demo/backend/layer_b_codec.py`에 `TicketLayerB` + 3-포맷 코덱(JSON/CBOR/CBOR-aggressive). 매체별 포맷 선택 권장은 §7.2 참고. 발급자별 매핑표 분기는 **M2.5**에 trust registry 확장으로 계획.
- **모바일 구현 방식** (M3) — PWA 강화 vs 네이티브 (메모리: `agent-browser`가 UI 검증 기본 경로)
- **검표 속도 KPI** — 영업 데모 목표 수치
- **포맷 선택 API 노출** (M2) — `/api/encode` 또는 신규 엔드포인트가 `format: "json"|"cbor"|"cbor_aggr"` 파라미터 받아 발급 시 선택 가능하도록 노출
- ~~**발급자별 Layer B 스키마** (M2.5)~~ → **해소 (2026-06-01)**: 발급자→스키마 1:1 라우팅(A안) 대신 **self-describing schema_id를 Layer B body에 임베드한 공유 카탈로그**(B안) 채택. 스키마 3종 `baseball_ticket`/`festival_pass`/`wristband`. **멀티매체**=한 운영자 키로 여러 스키마 발매(Comic Con이 festival_pass+wristband 둘 다), **스키마 공유**=한 스키마를 여러 발급자가(festival_pass를 Violet+Comic Con). trust registry `allowed_schemas`는 노출만, 발급 시 강제는 후속.

## 12. 범위 외 (Out of Scope)
- 암표/부정 양도 차단 (본인확인)
- 실제 예매처 4사 시스템 연동
- 종이 티켓 법적 효력 대체
- 상용 수준 키 관리·보안 운영

---

## 부록: 검증 영역 (PRD 외부 — 별도 추적)
> "발산 ≠ 공상" 원칙: 아래는 데모로 답할 수 없고 **고객 대화로만** 확인되는 항목. (sum 문서 Open Items와 연동)
- 비용 장벽 vs 인식 장벽 중 진짜 병목
- 예매처/공연장의 도입 의향·위기의식
- 세그먼트별 페인 강도
