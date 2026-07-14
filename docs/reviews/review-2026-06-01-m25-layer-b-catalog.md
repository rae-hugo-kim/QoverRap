# Code Review — M2.5 Self-describing Layer B 스키마 카탈로그

- **Date**: 2026-06-01
- **Scope**: demo 응용 레이어 (코어 `src/qoverwrap/` 무수정)
- **Reviewer**: oh-my-claudecode:code-reviewer (opus), 별도 레인 적대 리뷰 — 작성(executor)과 분리
- **diff-hash: 59d842de1afae8af88828b16ed2755ca7347fbc8186bf6de5af4b5faa08d0568**

## Verdict: PASS

CRITICAL/HIGH 0건. 포저리 내성·backward-compat·key-0 폴백·resolve 파생을 라이브 적대 검증 + 전체 테스트로 확인. 로컬 커밋 적합.

## 검증 축 (모두 통과)

1. **포저리 내성 (security-critical)** — 스키마 라우팅은 항상 권위 있는 discriminator(aggressive=정수키 0, JSON/CBOR=`kind`)로만 수행, 필드 모양 스니핑 없음. `kind`↔필드 불일치/미지 schema_id/스푸핑 → `ValueError`/`ValidationError` → resolve `except Exception` 안전 폴백 `(None,None)`. 서명은 Layer B 전체 바이트열을 덮으므로 schema_id 재태깅은 verified 단계에서 서명 실패 → Layer B None.
2. **Backward-compat** — baseball aggressive 맵 1~9 바이트 동일(HEAD 대비 diff), key 0 전역 예약, 부재→baseball 폴백은 "진짜 부재"에만 한정(존재하나 무효는 거부). 프레이밍 바이트 불변. M1.2 안정성 계약 준수.
3. **resolve 파생** — `_decode_layer_b` 시그니처 불변 유지하며 디코드 dict의 `kind`로 `layer_b_schema` 파생, 레벨/안전폴백 시맨틱 상속(claim 7(iii) 보존).

## 지적 사항 및 처리

- **[MEDIUM] 죽은 코드 `_TICKET_AGGRESSIVE_V1_REV` + 매-호출 rev_map 재구성** → **수정 완료**: `LayerBSchema`에 `rev_map` 필드(`__post_init__`에서 1회 구성) 흡수, 모듈 전역 REV 제거, decode는 `schema.rev_map` 사용.
- **[MEDIUM] 프론트 `types.ts` `kind:"ticket"` 드리프트** → **후속 이월**(스펙상 프론트 범위 제외; 백엔드 `kind` 옵셔널·데모 키 재생성으로 비차단). 후속 프론트 스텝에서 `GET /api/schemas` 기반으로 갱신.
- **[LOW] `schema` 필드가 BaseModel `.schema()`(deprecated) 섀도 → UserWarning** → **무해 확인 + 의도 주석 추가**(와이어 계약이라 개명 금지 명시). openapi/model_json_schema 정상.
- **[LOW] aggressive ts `int(value)` 진단 메시지** → 안전 폴백이 흡수, 선택적 개선 보류.
- **[권고] 서명 후 schema_id relabel → verified=False 명시 테스트** → **추가 완료**: `test_signed_token_relabeled_to_another_schema_fails_verification`(festival 서명 후 schema_id 2→1, verified=False + layer_b_* None).

## 독립 검증 (Claude, 별도 레인)

- `pytest tests/demo/` → **94 passed** (기존 68 → +26; 신규 relabel 포함).
- API 엔드투엔드 스모크(`QWR_ENABLE_DEMO_SIGNING=1`, TestClient): `GET /api/schemas` 3종, Comic Con festival_pass(189B)+wristband(53B aggressive) 한 키로 verified, Violet+Comic Con festival_pass 공유 verified — 멀티매체·스키마공유 실증.
- `git diff --stat -- src/qoverwrap/` → 빈 출력(코어 무수정).
