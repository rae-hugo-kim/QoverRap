# 데모 응용 레이어 4개 메커니즘 — 신규성·진보성 선행기술 대조 (출원 전 의사결정용)

> **성격**: 출원 여부 결정을 위한 **엔지니어링/선행기술 수준 분석**. 명세서·청구항·도면이 **아님**(출원 동결분과 무관, 신규 분석 문서). **변리사 자문 아님**(QoverwRap = AI작성→KEAPS 본인출원 직행, 변리사 검토 단계 없음).
> **작성**: 2026-06-02 · deep-research 하네스(6각도 fan-out, 25소스 fetch, 111주장 추출, 25주장 3표 적대검증→21확정/4기각, 108 에이전트)
> **대상**: 이미 출원·심사청구된 코어(청구항 1~15: 단일 QR 평문 Layer A+구획자+base64 트레일러[헤더+Layer B+Ed25519 Layer C], 오프라인 자기완결 검증, 발급자 라우팅, 3레벨 리졸버+안전강등)의 **청구항 밖** 응용 메커니즘 4개.

## 종합 등급 + 별도 출원 우선순위

**M1 ≫ M2 ≫ (M2.5 · Liveness — 단독 출원가치 낮음)**

| 메커니즘 | 등급 | 신뢰도 | 한 줄 판정 |
|---|---|---|---|
| **M1** 결정론적 서명값=일회성 복제감지 키 | 🟢 강함 | high | 최근접 선행기술 어느 것도 "공개키 서명값 자체를 positive 소비원장 유일성 키로 verify-then-consume"를 개시 안 함. 관례(별도 nonce)가 teaching-away |
| **M2** sha256(서명)=가명 묶기 + 운영자 방문마커 | 🟡 보통 | high | PLUME nullifier가 개념 강선취하나 M2는 ZKP 없는 단순 서명-해시라 정면 선취 아님. 차별점("더 단순")의 진보성 입증 필요 |
| **M2.5** 자기기술 schema_id + 정수키 CBOR | 🔴 약함/거의 선취 | medium | RFC8392·CDDL·W3C VC 표준조합. 코어 종속항 흡수 검토 |
| **Liveness** 동적 시계+shimmer anti-스크린샷 | 🔴 거의 완전 선취 | high | US9489614·US10460221이 원리·위협모델 정면 개시. genus 선취 |

## 메커니즘별 상세 (확정 주장 + 인용)

### M1 — 강함
- **US10033732** (Symantec/Gen Digital): 공유비밀 OTP(HOTP/TOTP) **두 로그 사후비교**로 클론 추론. 공개키 서명값을 dedup 키로 안 씀. 인용: `...derived...from a shared secret` / `...one-time-use security code...not included in the...codes logged at the authentic security token`.
- **US20110016054 / US8412640** (Visa): 서명값(암호코드)을 식별자로 쓰되 **오프라인 네거티브(블랙)리스트 조회**. positive 일회성 소비원장 아님. 인용: `Without decrypting...a checking is made off line...of a list of other encryption codes` / `...a list of card numbers thought to be counterfeit`.
- **NDN 패킷 스펙 / arXiv:1602.02148**: 리플레이 방지를 **별도 필드**(SignatureNonce/Time/SeqNum, 또는 랜덤 message identifier)로. 서명값 비소비. 단 `retain only after authenticating`로 **verify-then-consume 순서는 공통**. → 관례가 "별도 필드"라는 점이 M1의 "서명값 재사용·무추가필드"를 **teaching-away로 뒷받침**.
- 소스: uspto 10033732, patents.google US20110016054, named-data.net spec, arXiv:1602.02148.

### M2 — 보통
- **PLUME nullifier**: 비밀키+앱별 메시지→결정론적 공개 식별자, 재사용으로 **동일 익명 보유자의 다중 행위를 신원 비노출 연결**(= visitor_token 크로스연결과 직접 유비). 인용: `you could post under the same nullifier three times...all your posts came from the same person...but no one will know that the author is you`. **단 PLUME은 비밀키 위 ZKP 증명, M2는 이미 공개된 서명값의 sha256 — 더 단순/약함**(정면 선취 아님).
- **Blanco-Justicia & Domingo-Ferrer 2014** (arXiv:1411.3961): 익명 충성 프로그램이나 **부분 블라인드서명+일반화** 접근 → M2와 상이(teaching-away).
- 소스: blog.aayushg.com/nullifier (+ePrint 2022/1255·ERC-7524 교차), arXiv:1411.3961.

### M2.5 — 약함/거의 선취
- **RFC8392(CWT)**: `To keep CWTs as small as possible, the Claim Keys are represented using integers` (정수키 CBOR 컴팩트 인코딩 표준).
- **CDDL/RFC8610**: 타입-choice(`t1/t2`) + 정수/문자열 키 맵 = 표준 구문.
- **W3C VC**: payload 내 스키마 참조(credentialSchema) — *단일발급자 다중스키마*·*in-body 판별자* 관련 보조주장은 **검증에서 기각(0-3 포함)** → M2.5 차별성을 오히려 약화.
- 좁은 미선취: base CWT는 타입 판별을 외부(content-type/CBOR tag)에 위임 — 그러나 후속(SD-CWT vct, EAT, RFC9596)이 메웠을 가능성(미해결).
- 소스: RFC8392, arXiv:2505.17335, W3C vc-json-schema.

### Liveness — 거의 완전 선취
- **US9489614** (Comenity/Bread Financial): 모바일 결제카드 **애니메이션 디지털 워터마크**로 정적 스크린샷 위조 방지. claim1 `displaying a user-interactive animated digital watermark...to ensure authenticity...visually perceptible to a human`.
- **US10460221** (Tucker): **연속 갱신 QR**로 사진-후-재스캔 리플레이/스크린샷 방지. `a changing QR prevents this`.
- genus(움직임이 정적캡처 무력화+인간 시각판별) 정면 선취. "초단위 실시간 시계+shimmer" 특정 species만 미명시.
- 소스: uspto 9489614, uspto 10460221.

## 캐비엇 (리포트 원문)
1. 엔지니어링/선행기술 수준 대조, 변리사 자문 아님. 최종 출원성은 청구항 문언·심사관 거절이유에 좌우.
2. 일부 USPTO PDF(10033732·10460221) 스캔본 → Google Patents 렌더 + 독립 웹검색 교차로 verbatim 검증.
3. M2의 PLUME 근거는 1차저자 블로그 중심(ePrint·ERC-7524·MIT thesis로 보강), 단일 개념 도메인.
4. M2.5는 단일 표준 도메인(IETF/W3C), in-body discriminator 선취 여부 보조주장 split/기각 → 차별성 경계 불확실(기각 방향 = 선취 강화).
5. 모든 선행기술이 우리 고유 계층형 QR 전체 조합을 개시하는 건 아님. **코어 청구항과의 결합(combination) 신규성은 별도 사안**.
6. 검색은 일반 기법 용어로만 — 우리 비공개 조합 미게재.

## 미해결 질문 (출원 전 닫을 것)
- **M1**: "verify-then-consume **순서**" 자체가 청구가능 한정인가 vs `retain only after authenticating`으로 자명한가 — M1 청구범위 설계 핵심.
- **M2**: ZKP 없는 단순 sha256이 PLUME 대비 진보성인가(비자명 차별 vs 단순 설계선택). **POAP/proof-of-attendance 특허군 직접 대조(이번 라운드 미수집)**.
- **M2.5**: SD-CWT(vct=11)/EAT(eat_profile)/RFC9596(COSE typ)이 잔여 미선취 갭을 메웠는지.
- **Liveness**: TOTP 동적 QR + Apple/Google Wallet 동적바코드 특허 직접 대조(미수집).

## 공개 의사결정 메모 (§30 연계)
- 보호가치 있는 건 **M1(강함)·M2(보통)**뿐. M2.5·Liveness는 거의 선취 → 공개 부담 낮음.
- 미공개 커밋 스택(M1.2·M1·M2·M2.5·M3)은 **M3 검표원이 M1(`/api/redeem`)을 surface**하므로 묶여 있음 → M1/M2 결정이 스택 전체 push를 게이트.
- §30: KR/US는 공개 후 12개월 내 출원으로 구제 가능(증명서류 30일). **단 EP·CN은 grace 거의 없어 공개 즉시 해당국 신규성 상실**; §30은 제3자 독립공개·선출원은 못 막음(first-to-file 충돌 위험).

## 핵심 소스
- 특허: US10033732, US20110016054/US8412640, US9489614, US10460221, US9047715B2
- 표준/논문: RFC8392, RFC8610(CDDL), W3C vc-json-schema, arXiv:1602.02148, arXiv:1411.3961, arXiv:2505.17335, blog.aayushg.com/nullifier(PLUME)
- 제품/대조: Ticketmaster SafeTix, MOSIP QR spec, POAP
