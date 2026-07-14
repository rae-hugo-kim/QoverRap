# Code Review — M2.5 프론트: 발급자→매체 선택 + 스키마별 동적 폼/카드

- **Date**: 2026-06-01
- **Scope**: `demo/frontend/` 만 (백엔드·코어 `src/qoverwrap/` 무수정 — diff 빈 출력 확인)
- **Reviewer**: oh-my-claudecode:code-reviewer (opus), 별도 레인 적대 리뷰 — 작성(executor)과 분리
- **diff-hash: 341ea105015cf497f200df7d172894780f062d4764eb8bac85fda69395ba1342**

## Verdict: PASS

CRITICAL/HIGH 0건. tsc·eslint clean, lsp_diagnostics 7파일 0. 멀티매체 목표·verified-empty(claim 7(iii)) 경로·위조 거부 보존을 코드 + 라이브 시각 QA로 확인. 로컬 커밋 적합.

## 변경 (7파일)
- `types.ts`: `kind` 드리프트 해소 + 판별 유니온 `LayerBTicket`(baseball_ticket/festival_pass/wristband), `ResolveResult.layer_b_schema`, `SchemaInfo`/`SchemaFieldInfo`, `TrustEntry.allowed_schemas`. 필드명 백엔드 모델과 정확히 일치.
- `api/client.ts`: `encodeLayerB(ticket,format,schema)`, `EncodeLayerBResponse.schema/schema_id`, `schemas()` GET.
- `components/SchemaForm.tsx`(신규): `/api/schemas` 필드로 제너릭 폼(kind 제외, is_timestamp→date, required 표시).
- `components/MediaPicker.tsx`(신규): allowed_schemas 제한 칩(1개 자동선택).
- `App.tsx`: 카탈로그 로드, schemaKind state, (issuer×kind) 프리셋, MediaPicker+SchemaForm, buildQR schema 전달, rawMode 보존. **+ 리뷰 반영**: buildQR 구조화 분기에 `if(!schemaKind)` 가드 + 죽은 `"baseball_ticket"` 폴백 제거.
- `components/ThemedCard.tsx`: `switch(data.kind)`로 재배선. BaseballTicketCard/FestivalPassCard/신규 WristbandCard/EmptyPayloadCard(no-kind 폴백).
- `components/ResolveColumn.tsx`: layer_b_schema 뱃지.

## code-reviewer 지적 처리
- **[MEDIUM] buildQR `"baseball_ticket"` 하드코딩 폴백(latent 불일치)** → **수정 완료**: `if(!schemaKind){setErr;return}` 가드 + 폴백 제거(빌드·lint 재통과).
- **[MEDIUM] `type=date` 시각 손실** → **의도적 유지**: `datetime-local`은 포맷 간 tz 불일치(JSON vs aggressive)를 유발해 "표현 무관 동일 데이터" 메시지를 해침. date-only는 포맷 간 일관(검증: 동일 날짜 09:00 KST 일관 표시). 데모-폴리시, 비차단.
- **[MEDIUM] EmptyPayloadCard 라벨** → 무해(실 도달은 verified-empty/raw만; tamper는 locked로 감). 유지.
- LOW(키스트로크 spread/단일칩 self-contain/a11y aria-pressed): 비차단, 데모 규모서 무시.

## 라이브 시각 QA (agent-browser, eval `.click()` IIFE)
- `GET /api/schemas` 3종 로드 → MediaPicker: Tigers 1(자동), Comic Con 2(festival_pass/wristband).
- **Comic Con festival_pass**: SchemaForm festival 필드 자동 생성·프리셋 → build → resolve verified VALID → **FestivalPassCard**(DAY/ZONE/TIER/GATE 실필드). 스크린샷.
- **Comic Con wristband(aggressive 76B)**: 같은 키, 폼이 band_id/tier/valid_until로 전환 → **WristbandCard**(별도 카드) = **멀티매체 2카드 시각 입증**. 스크린샷.
- **Violet festival_pass**(보라 테마, 자동선택): VALID + festival_pass 뱃지 = **스키마 공유** 입증.
- **위조 시도**: tamper → Verified **INVALID** + 잠금 강등(claim 7(iii) safe-fallback 보존).
- build/lint clean, `git diff --stat -- demo/backend/ src/qoverwrap/` 빈 출력.

## 후속(범위 밖)
- Violet 기존 멤버십 전용 비주얼은 festival_pass 카드로 통합됨(승인된 스키마-키 결정). 발급 시 allowed_schemas 강제·M3 모바일은 후속.
