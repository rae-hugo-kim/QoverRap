# 05. QR Layering Feasibility Protocol

## Objective
QR 레이어링 아이디어의 기술적 구현 가능성을 코드 구현 이전 단계에서 설계/검증 프로토콜로 고정한다.

## Problem Definition
단일 QR 코드가 제공하는 정보량, 위변조 저항성, 맥락 분기 능력의 한계를 다층 레이어 설계로 개선할 수 있는가.

## Novelty Hypotheses
1. 시각적 동일성을 유지하면서 다층 데이터 해석 경로를 분리할 수 있다.
2. 레이어별 접근 권한/복호 정책을 적용해 보안성과 유연성을 높일 수 있다.
3. 사용 환경(카메라/조도/왜곡)에서 허용 가능한 인식 성능을 유지할 수 있다.

## Proposed Architecture (Concept)
- Layer A: Public payload (기본 안내)
- Layer B: Context payload (사용자/환경 조건 기반)
- Layer C: Verification payload (서명/검증 데이터)
- Resolver: 입력 조건에 따라 레이어 해석 정책을 적용

## Experiment Protocol
| Metric | Method | Pass Condition | Fail Condition |
|---|---|---|---|
| Scan Success Rate | 다양한 기기/조도에서 200회 스캔 | 95% 이상 성공 | 90% 미만 |
| Decode Latency | 평균 해석 시간(ms) 측정 | 300ms 이하 | 500ms 초과 |
| Layer Integrity | 변조 샘플 주입 테스트 | 검증 실패 탐지율 99% | 95% 미만 |
| Context Routing Accuracy | 조건 분기 100케이스 평가 | 98% 이상 정확도 | 93% 미만 |

## Data to Collect
- 디바이스/OS/카메라 스펙
- 조도 조건
- 코드 손상/왜곡 수준
- 레이어별 payload 크기
- 판독 시간과 실패 로그

## Image Plan
| Figure ID | Purpose | Caption |
|---|---|---|
| Fig-1 | 레이어 구조 개요 | Public/Context/Verification 3계층 구조 |
| Fig-2 | Resolver 흐름 | 입력 조건에 따른 레이어 해석 분기 |
| Fig-3 | 실험 셋업 | 기기/조도/각도 테스트 환경 |
| Fig-4 | 결과 대시보드 | 성공률/지연/무결성 지표 요약 |

## Risk Notes
- 실제 특허성은 선행기술 범위에 따라 크게 달라질 수 있다.
- 보안성 주장은 실험/검증 로그 없이 확정하지 않는다.

## Done Criteria
- 위 실험표 기준으로 테스트 설계 문서가 완성됨
- 실패 조건이 각 지표마다 1개 이상 정의됨
- 이미지 계획 4개 도면이 목적/캡션과 함께 확정됨
