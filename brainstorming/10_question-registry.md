# 10. Question Registry

## Purpose
아이디어/작성/특허 실무 중 발생하는 질문을 `Resolvable / Decidable / Blocked`로 분류해 의사결정 지연을 줄인다.

## Usage Rules
- Resolvable: 문서/데이터에서 확인 가능한 질문
- Decidable: 트레이드오프를 선택하면 되는 질문
- Blocked: 외부 입력(전문가, 사용자, 법률 확인)이 필요한 질문

## Open Questions
### Resolvable
| ID | Question | Source to Check | Owner | Due | Status |
|---|---|---|---|---|---|
| R-001 | QR 레이어링 관련 기존 내부 문서가 있는가 | 본 폴더 + 기존 repo | operator | W1 | open |
| R-002 | CTA 클릭 저하 구간은 어디인가 | 주간 지표 리포트 | operator | W3 | open |

### Decidable
| ID | Question | Option A | Option B | Current Default | Owner | Status |
|---|---|---|---|---|---|---|
| D-001 | 영어 요약 길이 | 5문장 | 8문장 | 5~8문장 | operator | fixed |
| D-002 | milestone 글의 감정 강도 | 절제형 | 강한 선언형 | 절제형 | operator | fixed |

### Blocked
| ID | Question | Why Blocked | Needed Input | Impact | Owner | Status |
|---|---|---|---|---|---|---|
| B-001 | KR 출원 문구의 법적 리스크 최종 검토 기준은? | 법률 전문성 필요 | 변리사 피드백 | high | operator | open |
| B-002 | QR 레이어링 청구범위의 상업화 범위는? | 사업 전략 확정 필요 | 사업 우선순위 결정 | medium | operator | open |

## Resolution Log
| Date | ID | Resolution | Category | Confidence | Reversal Trigger |
|---|---|---|---|---|---|
| YYYY-MM-DD | | | | | |

## Done Criteria
- 매주 최소 1회 질문 상태 업데이트
- Blocked 질문은 영향도와 필요 입력이 항상 명시됨
