# 06. Post Pipeline and Checklists

## Pipeline Overview
1. Idea intake
2. Question triage (`10_question-registry.md`)
3. Brief generation (`post_frontmatter`)
4. AI draft generation (KR 본문 + EN 요약 + FAQ + 이미지 캡션)
5. Review gate 1~4
6. Publish
7. Metrics capture

## Interface 1: `post_frontmatter`
```yaml
title: ""
slug: ""
post_type: "deep_dive" # hook|deep_dive|patent_log|milestone
target_audience: "tech_practitioner_founder"
primary_keyword: ""
seo_support_keywords: []
geo_questions: []
aeo_answer_snippets: []
cta_target: "longform_archive"
legal_disclaimer_level: "conservative"
review_status: "draft" # draft|ai_checked|human_legal_checked|publish_ready|published
```

## Interface 2: `patent_dossier`
```yaml
invention_name: ""
jurisdiction: "KR"
problem_definition: ""
novelty_hypotheses: []
prior_art_candidates:
  - source: "KIPRIS"
    id: ""
    note: ""
embodiments: []
claim_draft: []
experiment_protocol:
  - metric: ""
    method: ""
    fail_condition: ""
image_plan:
  - figure_id: ""
    purpose: ""
    caption: ""
gate_status: "ai_generated" # ai_generated|human_reviewed|attorney_ready
```

## Interface 3: `review_gate`
- `gate_1_fact_check`: 주장-근거 연결 확인
- `gate_2_prior_art_check`: KR 선행기술 후보 3건 이상 확인
- `gate_3_claim_safety`: 단정/과장/오해 문구 제거
- `gate_4_publish_safety`: 고지문, 검수기록, CTA 확인

## Hard Constraints
- `human_legal_checked` 없는 특허 글은 `publish_ready` 전환 금지
- `publish_ready` 없는 문서는 발행 금지
- CTA 누락 문서는 발행 금지

## Operational Checklist
### Draft Stage
- post_type/keyword/독자/CTA 입력
- 한국어 본문 초안 생성
- 영어 요약 5~8문장 생성

### AI Checked Stage
- FAQ 3개 포함
- 이미지 캡션 포함
- 금지 표현 자동 탐지 통과

### Human Legal Checked Stage
- 특허/법률 표현 점검
- 선행기술 링크 점검
- 고지문 삽입 확인

### Publish Ready Stage
- review_gate 4개 전부 통과
- 내부 링크 2개 이상
- CTA 3지점 확인

## State Machine
- `draft` -> `ai_checked` -> `human_legal_checked` -> `publish_ready` -> `published`
- 역전환 허용: 발견된 이슈가 있으면 이전 단계로 되돌린다.

## Done Criteria
- 파이프라인 템플릿으로 샘플 포스트 1건 생성
- 상태 전환 규칙 위반 사례 0건
