# 09. Metrics and Feedback Loop

## Measurement Goals
- 콘텐츠 품질, 전환 성과, 리스크 준수 상태를 매주 확인한다.

## KPI Set
### Content Quality
- 발행 준수율: 주 1편 달성 여부
- 구조 준수율: Hook/근거/리스크/CTA 포함률
- FAQ 충족률: 글당 3개 이상

### Conversion
- 훅 글 -> 장문 아카이브 클릭률
- CTA 위치별 클릭 비중 (도입/중간/결말)
- 장문 글 평균 체류 지표

### Safety and Patent Process
- 특허 글 검수 게이트 통과율
- `human_legal_checked` 누락 건수
- 선행기술 후보 3건 미달 건수

## Weekly Review Loop
1. 월요일: 전주 지표 집계
2. 화요일: 실패 지표 원인 분류
3. 수요일: 캘린더/템플릿 수정
4. 목요일: 다음 글 초안 생성
5. 금요일: 게이트 검수 + 발행

## Alert Thresholds
- 발행 누락: 1주라도 발생 시 즉시 캘린더 재조정
- CTA 클릭률 급락: 직전 2주 평균 대비 30% 하락 시 훅/CTA 문구 교체
- safety 위반: 1건이라도 발견되면 발행 파이프라인 중단 후 원인 분석

## Improvement Backlog Template
| Date | Signal | Suspected Cause | Action | Owner | Status |
|---|---|---|---|---|---|
| YYYY-MM-DD | | | | | |

## Done Criteria
- 매주 1회 지표 리포트 작성
- 임계치 위반 시 대응 로그 기록
