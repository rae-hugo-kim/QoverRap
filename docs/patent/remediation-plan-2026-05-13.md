# 거절이유 보완계획 (2026-05-13)

> **목적**: 자체 심사관 시점 비평(8건)에 대한 보완 작업의 범위·우선순위·구체적 텍스트 변경·위험을 정리하고, Codex 적대적 비평 후 확정한다.
> **대상 문서**: `docs/patent/qoverwrap-kipo-application-draft.md` (출원 예정 KIPO 양식 초안), `docs/patent/spec-draft.md` (upstream 설계 문서).
> **제약**: 신규사항 추가 금지(§47(2)), 구현(src/qoverwrap/)·테스트(tests/)와의 정합 유지, 출원 직전 12개월 prior-art 재조사 결과(`prior-art-survey.md` §10) 반영.

---

## 0. 진단 — 가장 중요한 발견

**`spec-draft.md §9` 의 청구항 골격이 `qoverwrap-kipo-application-draft.md §청구범위` 보다 훨씬 진화한 상태**이며, 자체 비평에서 지적된 결함 중 ⑦(청구항 12 카테고리 혼재), 일부의 ①(청구항 1 보강), 일부의 ③(청구항 7 전제부)은 이미 spec-draft 에서 해소되어 있다. **출원 예정 문서가 upstream design doc 보다 뒤처져 있는 것이 가장 큰 단일 원인.**

증거:
- `spec-draft.md:540-590` (청1·2 독립 + 청3~10·12·13·14 종속 + 청11 시스템 독립 + 청15 시스템 종속 = 15항 5층 그루핑 구조).
- `qoverwrap-kipo-application-draft.md:259-395` (청1·7 독립 + 청2~6·8~11·12·14 종속 + 청13 시스템 + 청15 CRM = 15항이나 청1 에 서명·safe-fallback 누락, 청12 카테고리 혼재).
- `spec-draft.md:646` (작업 이력 "A안 청구항 골격 확장, 2026-05-11"): 별건 출원 의통서 분석을 반영하여 청1 에 safe-fallback 결합 functional language 를 부착하고 청13~15 를 신설.

따라서 보완 작업의 **첫 단계는 spec-draft 청구항 골격을 KIPO 양식 문서로 이식**하는 것이다. 그 후 spec-draft 도 보유하지 못한 잔여 결함(④⑤⑥⑧)을 양쪽에 일괄 적용한다.

---

## 1. 결함별 현황 분류

| 결함 | spec-draft 상태 | application-draft 상태 | 보완 필요 작업 |
|---|---|---|---|
| ① 청1 진보성 (서명·safe-fallback 누락) | **부분 보강됨** (claim 1 마지막 문장에 functional language) | **미보강** | spec-draft 형식으로 동기화 + functional language 명시도 강화 |
| ② SQRC+signed barcode 결합 부정 | spec §3.2 표에 차별점 기술 | application §0006 단순 열거 | application 의 §배경기술/§선행기술문헌 보강 |
| ③ 청7 조건부 검증 | spec-draft 청2 가 독립항으로 분리됨, 전제부 "복합 모드 페이로드" 한정 | **미보강** (청7 본문에 "디지털 서명 계층이 포함된 경우" 조건절 잔존) | application 청7 을 spec-draft 청2 로 교체 |
| ④ "fail-safe = 통상 UI 정책" 공격 | spec §8.3 "안전 기본값" 단락에서 구조적 근거 기술 | application §0024 단순 진술 | spec/application 양쪽 §6 효과 보강 (단순 fail-safe 와의 구별 명시) |
| ⑤ "표준 QR 리더 호환" 표현 | spec 청1 (a) 동일 표현 | application 청1 (a) 동일 표현 | 양쪽 동기 보정 |
| ⑥ 청1 후속 계층 길이 범위 | spec 청1 (c) "각 후속 계층의 길이" 표현 | application 청1 동일 | 양쪽 동기 보정 |
| ⑦ 청12 카테고리 혼재 | spec-draft 청12 는 청2 만 의존 (해소됨) | application 청12 "청구항 5 또는 청구항 7" + "방법 또는 검증 방법" (혼재) | application 청12 를 spec-draft 청12 로 교체 |
| ⑧ 선행기술문헌 누락 | spec §3.2/§9 (3-11~3-16) 에 6건 보강 | application 특허문헌 5건만, 비특허문헌은 (가)군 학술 2건만 | application §선행기술문헌에 (마)군 비특허문헌 4건 추가 |

---

## 2. 작업 항목 (실행 순서)

### P0. 청구범위 동기화 (application ← spec-draft)

**근거**: 위 표 ①·③·⑦ 중 application 미보강 부분 일괄 해소.

**변경 내용**: `qoverwrap-kipo-application-draft.md` §청구범위(`:261-395`)를 다음 구조로 교체.

| 신구 | 청1 | 청2 | 청3 | 청4 | 청5 | 청6 | 청7 | 청8 | 청9 | 청10 | 청11 | 청12 | 청13 | 청14 | 청15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **현행 (application)** | 생성 (서명 없음) | 종속: 후속 계층 | 종속: 헤더 형식 | 종속: 구획자 | 종속: 서명 (청2 의존) | 종속: 정규화 | **독립: 검증 (조건부)** | 종속: 외부 호출 금지 | 종속: 리졸버 3수준 | 종속: safe-fallback | 종속: 발급자 ID | **종속: 카테고리 혼재** | 시스템 독립 | 시스템 종속 (신뢰 레지스트리) | CRM |
| **신규 (spec-draft 골격)** | 생성 (functional language) | **독립: 검증 (복합 모드 전제)** | 종속: 헤더 형식 | 종속: 구획자 | 종속: 디코더 자동 판별 | 종속: Ed25519 + 키 출처 | 종속: 리졸버 3수준 | 종속: safe-fallback | 종속: 발급자 ID | **CRM** | **시스템 독립** | 종속: canonical signing msg | 종속: verified-empty Layer B 보존 | 종속: 휴대용 단말 응용 | 시스템 종속 (canonical+verified-empty 결합) |

**제거 항목**: 현행 application 청12("청구항 5 또는 청구항 7" + "방법 또는 검증 방법") — 카테고리 혼재이며 spec-draft 에서는 청12 가 청2 만 의존하는 종속항으로 재정의됨.

**추가 항목**: spec-draft 청13(verified-empty Layer B 보존), 청14(휴대용 단말 응용), 청15(canonical+verified-empty 시스템 결합) — 별건 출원 의통서 학습에서 살아남은 차별 종속항으로 도입됨.

### P0.5. 청1 강화 (보완 ①·⑤·⑥ 동시 적용)

spec-draft 청1 의 functional language("이진 헤더의 버전·길이 정보는 후속하는 디코딩·검증 절차의 어느 단계에서 실패가 발생하더라도 응용 프로그램에 반환되는 데이터를 Layer A 만으로 강등할 수 있는 형태로 결합") 는 보존하되, 다음 세 부분을 보강:

(a) ⑤ "표준 QR 리더에 의해 평문으로 판독 가능한 공개 텍스트 계층" → "표준 QR 코드 데이터로 인코딩되었을 때 표준 QR 리더의 판독 결과 문자열의 선두에 평문으로 위치하는 공개 텍스트 계층". 표준 리더가 Layer A 만 분리해 보여준다는 오해 차단.

(b) ⑥ "각 후속 계층의 길이 정보를 포함하는 이진 헤더" → "Layer B 의 바이트 길이를 나타내는 길이 필드 및 Layer C 의 바이트 길이를 나타내는 길이 필드를 포함하는 이진 헤더". 후속 계층 수를 2 로 고정하여 명세서(b_len/c_len 두 필드) 와 일치.

(c) ① "단계 (a)~(e) 중 어느 하나라도 실패하는 경우, 또는 검증 단계에서 실패하는 경우, 응용 프로그램에 반환되는 계층 데이터를 Layer A 만으로 강등할 수 있는 형태로 상기 단일 페이로드 문자열을 구성" 의 명시도를 강화. 단, 청1 자체가 "생성 방법" 이므로 검증·강등은 wire format 의 결합 가능성으로만 표현 (방법 청구항 카테고리 위반 회피).

### P1. 선행기술문헌 보강 (⑧)

`qoverwrap-kipo-application-draft.md:64-80` 의 특허문헌·비특허문헌 목록을 다음과 같이 확장. 신규사항 추가 금지 원칙 위반 아님 — 선행기술 인용은 발명의 신규 기재가 아니라 출원인 공지의무 이행.

**추가할 비특허문헌**:
- (비특허문헌 0003) Vaccine Credential Initiative / HL7 FHIR, "SMART Health Cards Framework Implementation Guide", 2021– (https://spec.smarthealth.cards/).
- (비특허문헌 0004) ICAO Doc 9303 Part 13, *Machine Readable Travel Documents — Visible Digital Seals*, 8th ed., 2021.
- (비특허문헌 0005) ISO 22376:2023, *Security and resilience — Specification and usage of visible digital seal (VDS) data format*.
- (비특허문헌 0006) SAP SE, "Digitally Signed QR Codes — SAP Mobile Services Documentation" (iOS / MDK), 2022-09-27 / 2024-04-12.

배경기술 본문 (`:54-60`) 의 마지막 단락도 "전체 credential 또는 전체 메시지를 하나의 서명 객체로 취급" 구문 다음에 "예를 들어 비특허문헌 0003 내지 0006 은 각각 단일 QR 또는 2D 바코드 내에 서명된 자격증명을 포함하는 방식을 개시한다" 를 1문장 삽입하여 (마)군 인지 명시.

### P2. 발명의 효과 §6 보강 (④)

application `:112-122` (효과 §0025~§0029) 에 다음 단락 추가:

> 【0030】 본 발명에 따른 안전 강등은 단일 검증 실패 경로에 대한 통상의 오류 처리와는 구별된다. 본 발명에서 안전 강등은 (i) 페이로드 문자열 내부에 Layer A 가 표준 QR 리더 판독 결과의 선두 평문으로 노출되도록 사전 배치되어 있는 wire format 결합과, (ii) 후속 계층 데이터의 검증 결과에 따라 반환 계층의 범위를 출력 정책 매개변수에 종속시키는 리졸버 동작이 결합된 정책으로서, 미검증 또는 위변조된 후속 계층 데이터가 검증된 데이터로 응용 프로그램 또는 사용자에게 노출되는 것을 페이로드 구조 차원에서 차단한다.

spec-draft §6 효과 표의 마지막 행 "부분 호환 + 출력 정책 + 안전 강등의 결합" 의 근거 컬럼도 동일 취지로 1문장 보강.

### P3. 정합성 검증

- `pytest -q` 통과 (현재 107/107). 청구항 본문 변경은 코드와 무관하지만 회귀 점검.
- application §0030~§0036 도면 설명, §대표도(현재 도8), 부호의 설명, §10 진보성 매핑 표(spec-draft 만 존재), §11 요약서(spec-draft `:614`) 가 신규 청구항 13·14·15 와 일치하는지 확인. application §요약서 (`:403`) 는 SQRC/SHC 등 (마)군 차별 표현이 약하므로 spec-draft §11 어구 일부 차용해 보강.
- `keaps-submission-guide.md` 청구항 인용 형식 표 (`:67-78`) 가 청1~15 모두 커버하는지 확인.

---

## 3. 위험 분석

| 위험 | 발생 가능성 | 영향 | 완화 |
|---|---|---|---|
| 청구항 골격 동기화 시 신규사항 추가(§47(2)) | 중 | 보정 거절 → 출원 직후 단계에서 회복 가능 | 청13·14·15 가 모두 spec-draft 본문(§8.7)·테스트(B-R7)·구현(`resolver.py`) 에 명시되어 있음을 인용 증거로 확보 |
| 청1 functional language 가 "방법" 청구항으로 부적격 | 중 | 명확성 거절 가능 | spec-draft 청1 "이진 헤더의 버전·길이 정보는 ... 강등할 수 있는 형태로 결합" 은 "결합 단계"의 *결과 한정* 으로 작성됨. 추가로 "단, 강등 동작 자체는 청구항 2·7·8 에 기재됨" 의 변리사 검토 메모 권고 |
| 후속 계층 길이 필드 2개 고정으로 권리범위 축소 | 중 | 향후 N-layer 확장 시 청구항 재출원 필요 | 종속항(spec 청3: 5바이트 헤더)이 이미 2개 고정. 본 변경은 청1 의 범위를 종속항 수준으로 정렬할 뿐 |
| spec-draft 청구항이 KIPO 형식과 미세 차이 (Markdown vs KEAPS) | 저 | 출원 시 형식 변환 필요 | keaps-submission-guide.md §3.1 의 sed 일괄 변환으로 해결 |
| 효과 §6 보강 단락이 명세서 본문에 없는 내용을 청구할 우려 | 저 | §42(3) 기재불비 | spec-draft §8.3 "안전 기본값" 단락이 본문 근거이며 동일 어구 재활용 |
| Codex 비평이 본 계획의 전제(spec-draft가 더 진화함) 자체를 부정 | 저 | 계획 재수립 | Codex 비평 결과를 본 §4 에 부록 정리 후 반영 결정 |

---

## 4. Codex 비평 의뢰 항목 (초안)

Codex 에게 다음 4개 질문을 의뢰:

1. (전제 점검) "spec-draft.md §9 청구항이 application-draft 청구항보다 진화되어 있으므로 동기화가 우선" 이라는 진단이 타당한가, 또는 application-draft 가 의도적으로 좁게 작성된 별개 전략인 가능성이 있는가?
2. (청1 함수형 한정) spec-draft 청1 마지막 문장의 "응용 프로그램에 반환되는 데이터를 Layer A 만으로 강등할 수 있는 형태로 결합되는 것을 특징으로" functional language 가 한국 특허법 §42(4)·§42(2) 의 명확성/뒷받침 요건을 충족하는가? 더 안전한 표현이 있는가?
3. (청구항 1 ↔ 청7 관계) 청1 을 broad 생성 방법으로 두고 청2 를 독립 검증 방법으로 분리한 spec-draft 전략이, "SQRC + signed barcode 단순 결합" 공격에 대한 청1 의 자기 방어력을 손상시키지 않는가?
4. (verified-empty 보존 청구항 13) "trustness-falsy 변환을 적용하지 아니하는" 표현이 한국 특허 실무에서 받아들여지는 형태인가? 부정적 한정(`A 를 적용하지 않는`) 의 모호성 위험이 있는가?
5. (선행기술 인용 시점) 출원 예정 문서에 SHC/ICAO VDS/SAP 를 자발 인용하는 것이 IDS 효과를 가져오는가, 아니면 오히려 심사관에게 거절이유 근거를 제공하는 단점이 있는가?

---

## 5. Codex 적대적 비평 반영 (2026-05-13)

Codex 1차 비평 (agentId a9510d85605fd2b2b) 의 결정 8건 추가 적용. 법조문은 §42(4)1호(뒷받침)·2호(명확성), §47(2)(보정 범위) 로 정정 (Codex 지적).

| 결정 | Severity | 반영 위치 |
|---|---|---|
| (C1) 청1 functional language("강등할 수 있는 형태로 결합") → **구조적 한정**: "Layer A 가 구획자 이전에 배치되어 트레일러 디코딩 없이 분리 가능", "헤더의 B·C 길이 필드가 바이트 경계를 결정 가능", "그로 인해 검증 실패 시 후속 계층이 검증된 데이터로 반환되지 않도록 처리 가능한 구조" | CRITICAL | spec/application 청1 |
| (C2) 청1 후속 계층 정의를 "**Layer B 와 Layer C 중 적어도 하나, 또는 양자 부재**" 로 명시. ⑥ B/C 고정. N-layer 확장은 §8.1.1 alg_id/encoding_id 확장 실시예로 spec 본문에서 보존 | HIGH | spec/application 청1 (b) |
| (C3) 청13 negative limitation → **positive limitation**: 출력 데이터 구조에 Layer B 필드를 존재 상태로 포함시키고 영 바이트 빈 바이트열로 설정 + 검증 성공 상태 정보 동반 → 영 바이트 검증 상태와 부재 상태가 구별되도록 반환 | HIGH | spec/application 청13 |
| (C4) 청14 약점 → "구획자 이전의 Layer A 보존" + "Layer B·C 표시 객체 미생성" 의 구조적 한정 추가 | HIGH | spec/application 청14 |
| (C5) 청15 방법항 참조식 → 청12 정규화 바이트열 정의·청13 verified-empty 보존 동작을 시스템항 본문에 **직접** 기술 | HIGH | spec/application 청15 |
| (C6) 청구범위만 동기화 금지 → **§8.7 본문·Fig.9·부호 설명 동시 이식** 필수 | HIGH | application §발명을 실시하기 위한 구체적 내용 |
| (C7) **SQRC 누락 보완** → 비특허문헌에 SQRC(DENSO WAVE) 도 포함 (총 5건: SQRC, SHC, ICAO VDS, ISO 22376, SAP) | MEDIUM | application §비특허문헌 |
| (C8) §6 효과 §0030 "구조 차원에서 차단" 표현 → "Layer A 선두 배치 + 구획자 분리 + 헤더 길이 검증 + 리졸버 반환 제한 의 결합" 으로 정정. 단락 번호 충돌 회피 위해 마지막 효과 단락 다음에 배치 | MEDIUM | application 효과 신설 단락 |

**전략적 결정**: 청1 broad 폭 유지(spec-draft `:649` "Codex 1차 검토 불채택") 를 이 라운드에서 **반전**. SQRC + signed barcode 단순 결합 공격 위험이 broad 청1 의 폭 효과보다 큼. 청1 은 종전보다 좁아지나 등록 가능성·진보성 방어력 강화.

---

## 6. 실행 순서 (Codex 비평 통과 후)

1. [P0] application §청구범위를 spec-draft §9 + Codex (C1)~(C5) 반영 골격으로 일괄 교체.
2. [P0.5] spec-draft §9 의 청1·13·14·15 본문도 Codex (C1)~(C5) 로 재작성.
3. [P0.7] application 에 spec §8.7 본문 (휴대용 단말 응용 + verified-empty 보존) 이식. §부호의 설명에 S401~S406 추가. §도면의 간단한 설명에 Fig. 9 추가.
4. [P1] application §선행기술문헌에 비특허 0003~0007 (SQRC 포함) 추가, 배경기술 본문 1문장 삽입.
5. [P2] application 발명의 효과 신설 단락 (Codex (C8) 표현 정정).
6. [P3] application §요약서를 spec §11 어구로 보강.
7. [검증] `pytest -q` 회귀. application 본문 ↔ 청구범위 cross-reference 점검.
8. spec-draft `## 12. 작업 상태` 에 "P0+++ 보완계획 + Codex 적대적 비평 반영 2026-05-13" 이력 추가.
