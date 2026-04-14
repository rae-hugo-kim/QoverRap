# 테스트 디렉터리

2단계 구조:

- `feasibility/` — Phase A 스파이크·측정 고정 스크립트
- `unit/` — encoder, decoder, resolver, crypto, models
- `integration/` — 라운드트립·독립 판독 경로
- `experiment/` — AC 게이트·리포트 생성

문서 원본: [../docs/test-plan/README.md](../docs/test-plan/README.md)

PoC 코드가 생기면 `pytest`로 실행한다. 현재는 문서 존재 sanity와 선택적 placeholder만 둔다.
