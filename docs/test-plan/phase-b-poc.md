# Phase B: PoC 구현 테스트

**전제**: Phase A 종료 및 [metrics-protocol.md](metrics-protocol.md) 승인.

**코드 레이아웃(권장)**:

- `src/encoder.py`, `decoder.py`, `resolver.py`, `crypto.py`, `models.py`
- `tests/unit/`, `tests/integration/`, `tests/experiment/`

## B-1. 모델·인코딩 단위

| ID | 설명 |
|----|------|
| B-E1 | Layer A 단일 인코딩 |
| B-E2 | Layer A+B 인코딩 |
| B-E3 | Layer A+B+C 인코딩 |
| B-E4 | 빈 payload, 초과 payload, 잘못된 스키마 → 명확한 에러 |
| B-E5 | 직렬화 결정성(동일 입력 → 동일 바이트) |

## B-2. 디코딩 단위

| ID | 설명 |
|----|------|
| B-D1 | Layer A 디코딩 |
| B-D2 | Layer B 디코딩 |
| B-D3 | Layer C 디코딩 |
| B-D4 | 손상 입력 → 실패 또는 감지 플래그 |
| B-D5 | 미지원 버전·포맷·메타데이터 처리 |

## B-3. Resolver 정책

| ID | 설명 |
|----|------|
| B-R1 | public → A만 |
| B-R2 | authenticated → A+B |
| B-R3 | verified → A+B+C |
| B-R4 | unknown → 안전 기본값(A만) |
| B-R5 | 위조·부분 유효·만료 컨텍스트 → B/C 비노출 |

## B-4. Crypto

| ID | 설명 |
|----|------|
| B-C1 | Layer C 서명 생성 |
| B-C2 | 올바른 키 검증 성공 |
| B-C3 | 잘못된 키 검증 실패 |
| B-C4 | 변조 payload 검증 실패 |
| B-C5 | 직렬화 순서·필드 누락·재사용 시나리오 방어 |

## B-5. 통합

| ID | 설명 |
|----|------|
| B-INT1 | encode → decode 3-layer 무손실 |
| B-INT2 | encode → resolve(public) → A만 |
| B-INT3 | encode → resolve(verified) → A+B+C 및 C 검증 |
| B-INT4 | 파일 저장·로드 roundtrip |
| B-INT5 | 독립 판독 경로와의 호환 ([overlap-and-independent-readpath.md](overlap-and-independent-readpath.md)) |

## B-6. 실험·AC 게이트

[metrics-protocol.md](metrics-protocol.md)와 1:1 대응.

| ID | 설명 |
|----|------|
| B-EXP1 | MET-1 스캔 성공률 |
| B-EXP2 | MET-2 레이턴시 (p95 <= 300ms) |
| B-EXP3 | MET-3 무결성 탐지율 |
| B-EXP4 | MET-4 라우팅 100케이스 |
| B-EXP5 | 단일 리포트로 AC 전체 pass/fail |

## TDD 권장 순서

1. models + encoder/decoder (B-E1~E5, B-D1~D5)
2. crypto (B-C1~C5)
3. resolver (B-R1~R5)
4. integration (B-INT1~INT5)
5. experiment 게이트 (B-EXP1~EXP5)
