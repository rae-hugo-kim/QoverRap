# Kickoff Summary

## Goal
QR 다중 레이어 오버래핑 기술의 실현 가능성을 검증(PoC)하고, KR 특허 출원을 완료한다.

## Constraints
- 법률 자문 언어 사용 금지 (모든 특허 주장에 검증 계획 필요)
- 검증 없이 특허성 확정 주장 금지
- review gate 우회 금지 (4-stage: fact → prior-art → claim safety → publish safety)
- human_legal_checked 없이 특허 관련 문서 게시 불가
- 보안 주장은 검증 로그 없이 확정 불가

## Acceptance Criteria
- QR 오버래핑 PoC: 스캔 성공률 95%+, 디코드 레이턴시 ≤300ms, 레이어 무결성 99%, 컨텍스트 라우팅 98%+ (200회 스캔, 다양한 디바이스/조명)
- 선행기술 조사: KIPRIS에서 3건+ 후보 특허 발견 + 각각 유사점/차이점 테이블 작성
- 특허 명세서 초안: 독립항 1-2개 + 종속항 5-10개, 실시예, 도면 계획 포함
- 실험 프로토콜: 4개 메트릭(스캔/레이턴시/무결성/라우팅) 실행 + pass/fail 결과 기록 완료

## Out of Scope
- 상용 서비스 배포 (SaaS/앱)
- 해외 특허 출원 (PCT, US 등)
- 블로그 플랫폼 개발
- 법률 자문 제공

## Assumptions
- KIPRIS에서 QR 관련 선행기술 검색이 가능함
- QR 코드 표준 내에서 다중 레이어 인코딩이 기술적으로 가능함
- 3-layer 아키텍처(A: 공개 / B: 컨텍스트 / C: 검증)가 단일 QR 코드에 구현 가능함
- 실험에 필요한 디바이스/환경 접근이 가능함

## Risks
- QR 코드 크기/해상도 제한으로 3-layer 인코딩이 불가능할 수 있음
- 선행기술 조사에서 높은 유사도의 기존 특허 발견 시 novelty 위협
- 실험 환경(조명/카메라/왜곡) 차이로 인한 결과 변동
- 실제 특허성은 선행기술 범위에 크게 의존하여 예측 불가
- Layer C 보안 레이어의 실제 암호화 검증 범위 불명확

## References
- `docs/harness/seed.yaml` - 구조화된 명세 (하네스 1급 입력)
- `brainstorming/05_qr-layering-feasibility-protocol.md` - QR 레이어링 실험 프로토콜
- `brainstorming/04_patent-workflow-kr.md` - KR 특허 워크플로우
- `brainstorming/00_problem-framing.md` - 전략적 문제 프레이밍
- `brainstorming/03_seo-geo-aeo-playbook.md` - 키워드/검색 최적화 전략

## Notes
- 검증 방법: PoC 자동 테스트는 Agent Browser(기본) + Maestro(모바일), 코드 리뷰는 OMC + Superpowers + Codex 3중 적대적 검증
- 특허 문서 상태 전환: ai_generated → human_reviewed → attorney_ready (human_review 건너뛰기 불가)
- brainstorming 문서 13개가 이미 체계적으로 정리되어 있어 구현 기반이 확보됨
