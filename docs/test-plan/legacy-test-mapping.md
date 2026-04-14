# 기존 테스트 ID → 2단계 재구성 매핑

초기 플랜의 `T-*` 항목을 Phase A / Phase B로 재배치한 참조표다.

## Phase A로 이동·분할

| 기존 ID | Phase A 대상 | 비고 |
|---------|----------------|------|
| T-ASM1 | A-ASM1 | 스택 스모크 |
| T-ASM2 | A-ASM2 | 용량·ECC·버전 |
| T-EDGE1 | A-ENV4, B-E4 | 용량 한계는 스파이크 + 구현 에러 둘 다 |
| T-EDGE2 | A-ASM2 | 최소 QR 버전 탐색 |
| T-EDGE3 | A-ENV3 | 리사이즈 |
| T-EDGE4 | A-ENV3 | JPEG |
| T-EXP1 일부 | A-MET1, A-ENV1~2 | 200회는 AC 게이트이나, 디바이스·조명 매트릭스 정의는 Phase A |
| T-EXP2 일부 | A-MET2 | p95 정의 고정 후 B-EXP2 |
| T-EXP3 일부 | A-MET3 | 변조 분포 정의 후 B-EXP3 |
| T-EXP4 일부 | A-MET4 | 100케이스 생성 규칙 고정 후 B-EXP4 |

## Phase B (구현·회귀)

| 기존 ID | Phase B 대상 |
|---------|----------------|
| T-E1~E4 | B-E1~E4 |
| T-D1~D4 | B-D1~D4 |
| T-R1~R4 | B-R1~B-R4 |
| T-C1~C4 | B-C1~B-C4 |
| T-INT1~INT4 | B-INT1~B-INT4 |

## 신규 (기존 플랜에 명시 없음)

| ID | 이유 |
|----|------|
| A-ASM3 | 독립 판독 경로 |
| A-HYP1~A-HYP4 | 오버래핑 가설 |
| A-ENV2 | 회전·기울기·거리 |
| B-E5, B-D5, B-R5, B-C5, B-INT5, B-EXP5 | 결정성·버전·권한 경계·외부 호환·단일 리포트 |

## 실험 게이트

| 기존 ID | Phase B 대상 |
|---------|----------------|
| T-EXP1 | B-EXP1 (MET-1) |
| T-EXP2 | B-EXP2 (MET-2) |
| T-EXP3 | B-EXP3 (MET-3) |
| T-EXP4 | B-EXP4 (MET-4) |
| (없음) | B-EXP5 리포트 |
