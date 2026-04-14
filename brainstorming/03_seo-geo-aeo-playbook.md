# 03. SEO/GEO/AEO Playbook

## Objective
- SEO: 검색 노출
- GEO: 생성형 검색/요약 환경에서 인용 가능성 확보
- AEO: 질문형 쿼리에 직접 답을 제공

## Keyword Strategy
1. Primary keyword 1개 선정
2. Support keywords 4~8개 구성
3. 문제-해결-검증 구조의 쿼리 묶음 생성

예시 (QR 레이어링):
- Primary: `QR 레이어링 특허 가능성`
- Support:
  - `QR 다층 인코딩 구현`
  - `KR 특허 선행기술 검색`
  - `특허 출원 AI 초안`
  - `QR 보안 레이어 설계`

## GEO Rule Set
- 문서 첫 300자 안에 문제/접근/결론 요약
- 정의 문장은 짧고 단정 대신 조건부 표현 사용
- 표/체크리스트로 구조화된 정보 제공
- 출처 또는 검증 계획 링크를 명시

## AEO Rule Set
각 포스트에 최소 3개 FAQ를 넣는다.

FAQ 템플릿:
- Q1: "QR 레이어링은 무엇을 해결하나?"
- A1: 2~4문장, 정의 + 적용 맥락
- Q2: "특허 가능성은 어떻게 검토하나?"
- A2: KR 선행기술 탐색 절차 요약
- Q3: "AI 자동화는 어디까지 가능한가?"
- A3: E2E 자동화 + 검수 게이트 원칙 설명

## Metadata Template
```yaml
title: ""
slug: ""
description: "120~155자 요약"
primary_keyword: ""
seo_support_keywords: []
geo_questions: []
aeo_answer_snippets: []
cta_target: "longform_archive"
```

## Internal Linking Rules
- 모든 훅 글은 최소 1개의 장문 글로 링크
- 장문 글은 관련 `patent_log`와 상호 링크
- 최신 글 -> 아카이브 허브 링크 고정

## Done Criteria
- 각 글에 키워드 묶음 + FAQ 3개 + 메타데이터 적용
- 상호 링크 구조(훅/장문/로그) 확인 완료
