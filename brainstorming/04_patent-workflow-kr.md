# 04. Patent Workflow (KR First)

## Scope and Safety
- 관할: KR 우선
- 기준: KIPRIS 중심 선행기술 조사
- 고지: 본 문서는 법률 자문이 아니라 실무 학습/기획 문서다.

## End-to-End Steps
1. Invention framing
- 발명 명칭, 해결 문제, 핵심 차별점을 1페이지로 고정

2. Prior-art search (KIPRIS)
- 키워드 세트 작성: 기능/구성요소/효과 기준 3축
- IPC/CPC 분류 확인
- 후보 문헌 최소 3건 수집

3. Similarity mapping
- 후보 문헌별 유사점/차이점 표 작성
- 신규성 가설을 "주장"이 아닌 "검증 가설"로 기록

4. Claim draft v0
- 독립항 1~2개, 종속항 5~10개 초안
- 모호 표현 제거

5. Embodiment draft
- 구현 예시, 변형 예시, 적용 범위 정리

6. Image planning
- 도면 목적/도면 번호/캡션 설계

7. Gate review
- gate_1~4 체크 후 상태 전환

## Required Artifact Schema (`patent_dossier`)
```yaml
invention_name: ""
jurisdiction: "KR"
problem_definition: ""
novelty_hypotheses:
  - ""
prior_art_candidates:
  - source: "KIPRIS"
    id: ""
    note: ""
embodiments:
  - ""
claim_draft:
  - ""
experiment_protocol:
  - metric: ""
    method: ""
    fail_condition: ""
image_plan:
  - figure_id: "Fig-1"
    purpose: ""
    caption: ""
gate_status: "ai_generated"
```

## Quality Gates
- `gate_1_fact_check`: 기술 주장에 근거/실험 계획 존재
- `gate_2_prior_art_check`: KR 선행기술 후보 3건 이상
- `gate_3_claim_safety`: 단정/과장 표현 제거
- `gate_4_publish_safety`: 법률 자문 아님 고지 삽입

## Status Transition
- `ai_generated` -> `human_reviewed` -> `attorney_ready`
- `human_reviewed` 없이 `attorney_ready` 전환 금지

## Done Criteria
- QR 레이어링 dossier 초안 1건 완성
- 후보 선행기술 3건 이상 연결
- 게이트 4단계 체크 로그 확보
