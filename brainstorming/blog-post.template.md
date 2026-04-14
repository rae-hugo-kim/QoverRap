---
title: "제목을 입력하세요"
slug: "url-slug"
date: "YYYY-MM-DD"
post_type: "deep_dive" # hook | deep_dive | patent_log | milestone
target_audience: "tech_practitioner_founder"
primary_keyword: "핵심 키워드"
seo_support_keywords:
  - "보조 키워드 1"
  - "보조 키워드 2"
geo_questions:
  - "생성형 검색이 물을 질문 1"
  - "생성형 검색이 물을 질문 2"
aeo_answer_snippets:
  - "질문에 바로 답하는 1~2문장 스니펫 1"
  - "질문에 바로 답하는 1~2문장 스니펫 2"
cta_target: "longform_archive"
legal_disclaimer_level: "conservative"
review_status: "draft" # draft | ai_checked | human_legal_checked | publish_ready | published
tags:
  - "tech"
  - "patent"
---

# {{ 제목 }}

## TL;DR
- 핵심 문제:
- 이번 글의 결론:
- 독자가 바로 가져갈 것:

## Hook (도입)
<!-- 3~5문장: 실제 문제 장면 + 왜 지금 중요한지 -->

## Why It Matters
<!-- 기술 실무자/창업자 관점에서 비용, 리스크, 기회 관점 설명 -->

## Technical Core
### 1) 현재 상태
<!-- 지금 무엇이 막히는지 -->

### 2) 접근 방법
<!-- 단계형 설명 -->

### 3) 적용 예시
<!-- 짧은 예시/표/체크리스트 -->

## Evidence or Protocol
<!-- 근거 출처, 실험 계획, 실패 조건 중 최소 1개 -->
- 근거/출처:
- 검증 방법:
- 실패 조건:

## Limits and Risks
<!-- 과장 금지. 한계와 전제 명시 -->
- 한계 1:
- 한계 2:
- 오해 방지 포인트:

## FAQ (AEO)
### Q1. 질문 1
A1. 2~4문장으로 직접 답변.

### Q2. 질문 2
A2. 2~4문장으로 직접 답변.

### Q3. 질문 3
A3. 2~4문장으로 직접 답변.

## English Summary
<!-- 5~8문장. 한국어 본문과 논지 일치 -->
1.
2.
3.
4.
5.

## CTA (장문 아카이브 유도)
<!-- 도입/중간/결론 3지점 중 결론용 문구 -->
핵심 실험 설계, 체크리스트 원문, 후속 업데이트는 장문 아카이브에서 확인할 수 있습니다: [링크]

## Legal Notice
이 글은 학습/기획 목적의 기술 문서이며 법률 자문이 아닙니다. 특허 출원/해석은 전문 자격자의 검토가 필요합니다.

---

## Optional: Patent Dossier Block (for `patent_log`)
```yaml
patent_dossier:
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
  gate_status: "ai_generated" # ai_generated | human_reviewed | attorney_ready
```

## Pre-Publish Checklist
- [ ] `post_frontmatter` 필수 필드 작성 완료
- [ ] Hook/Why/Technical/Evidence/Limits 구조 포함
- [ ] FAQ 3개 포함
- [ ] 한국어 본문 + 영어 요약 포함
- [ ] CTA 포함 (최소 결론 1회, 권장 3지점)
- [ ] 법률 고지문 포함
- [ ] `patent_log`인 경우 KR 선행기술 후보 3건 이상 연결
- [ ] `human_legal_checked` 없이 `publish_ready` 전환하지 않음
