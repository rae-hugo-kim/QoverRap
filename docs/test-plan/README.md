# QR 오버래핑 테스트 계획 (2단계)

Phase A는 **실현 가능성 스파이크**, Phase B는 **PoC 구현 및 AC 게이트**다. 상세 ID와 통과 조건은 각 문서를 본다.

| 문서 | 내용 |
|------|------|
| [phase-a-feasibility.md](phase-a-feasibility.md) | Phase A: 스택, 가설, 환경, 측정 고정 |
| [overlap-and-independent-readpath.md](overlap-and-independent-readpath.md) | 오버래핑 고유 가설·독립 판독 경로 검증 |
| [metrics-protocol.md](metrics-protocol.md) | AC 4지표 측정 방식 고정 (Phase B 게이트 입력) |
| [phase-b-poc.md](phase-b-poc.md) | Phase B: unit / integration / experiment |
| [legacy-test-mapping.md](legacy-test-mapping.md) | 기존 T-* ID와 A-/B-* 대응 |

## 실행 순서

1. Phase A 종료 조건을 만족할 때까지 스파이크만 수행한다.
2. `metrics-protocol.md`가 승인되면 Phase B 구현 테스트를 본격화한다.
3. Phase B 마지막에 `B-EXP5` 단일 리포트로 AC pass/fail을 판정한다.

## 관련 하네스

- [../harness/seed.yaml](../harness/seed.yaml)
- [../harness/kickoff-summary.md](../harness/kickoff-summary.md)
- [../../brainstorming/05_qr-layering-feasibility-protocol.md](../../brainstorming/05_qr-layering-feasibility-protocol.md)
