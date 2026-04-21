# EPO OPS 검색 쿼리 설계

**작성일**: 2026-04-17
**작성자**: AI (rae-hugo-kim 지시)
**용도**: 선행기술 조사 §6-2 (CNIPA) · §6-3 (INPI/EP) · §6-4 (J-PlatPat) 보완
**대상 API**: EPO OPS v3.2 `/rest-services/published-data/search`
**상태**: EPO 계정 활성화 대기 중 (설계 사전 작업)

---

## 1. API 제약 및 쿼터 (Non-paying 티어)

| 제약 | 값 |
|------|-----|
| 주당 트래픽 상한 | **3.5~4 GB/week** (보수적으로 3.5 GB 가정) |
| 검색 쿼리당 총 결과 상한 | 2,000건 (하드캡) |
| 1회 호출당 최대 결과 | 100건 (`Range: 1-100` 헤더) |
| Throttling | 1분 롤링 윈도우 |
| 상태 색상 | Green <50% · Yellow 50~75% · Red >75% · Black 차단 |
| 시간당 쿼터 | 존재 (`IndividualQuotaPerHour` 예외) — 초과 후 10분 후 리셋 |

## 2. 전체 조사 예산 추정

| 단계 | 호출 | 예상 크기 | 주 쿼터 대비 |
|------|------|----------|------------|
| 1. 광역 검색 (15 쿼리 × 100건 biblio 요약) | 15 | ~5~7 MB | 0.2% |
| 2. 관련 후보 biblio 전체 (상위 ~150건) | ~150 | ~2~4 MB | 0.1% |
| 3. 최종 후보 abstract+claims (~30건) | 30 | ~3~15 MB | 0.4% |
| **합계** | ~195 | **~10~26 MB** | **~0.7%** |

→ 주 쿼터의 1% 미만. 재실행 여유 100회+.

## 3. 쿼리 목록

### 우선순위 체계

**KR 특허 심사에서 실질 인용 가능성 + QoverwRap 청구항 구성에 미치는 영향** 기준.

| 태그 | 의미 | 실행 지침 |
|------|------|----------|
| **P1 ★★★** | KIPO 심사관 인용 가능성 높음 + 청구항 차별화에 직접 영향 | **필수 실행**, 결과 전수 검토 |
| **P2 ★★** | 인용 가능성 중간 또는 제한적 영향 | **실행 권장**, 결과 제목·초록 스캔 |
| **P3 ★** | 인용 가능성 낮음 또는 기존 조사로 이미 차별화됨 | **선택 실행**, 쿼터 여유 있을 때만 |

### 3-1. §6-2 CNIPA — Liu et al. (2019) 관련 CN 특허

| ID | 우선순위 | CQL 쿼리 | Range | 근거 |
|----|---------|---------|-------|------|
| Q1 | **P1 ★★★** | `in=(liu AND (fu OR yu)) AND cpc=G06K19/06` | `1-100` | 저자명 교차 + QR CPC. Liu 논문이 가장 가까운 선행기술, CN 병행 출원 가능성 |
| Q2 | **P2 ★★** | `ti,ab=("rich QR" OR "three-layer QR") AND pn=CN*` | `1-25` | 제목 키워드 + CN 공개번호. Q1 보완 |
| Q3 | **P1 ★★★** | `ti,ab=(QR AND hamming) AND pn=CN*` | `1-100` | Hamming 기반 QR (Liu 논문 핵심 기법). 다른 CN 출원인도 포함 |
| Q4 | **P2 ★★** | `ti,ab=(QR AND (steganograph* OR hidden)) AND pn=CN*` | `1-100` | 일반 스테가노그래피 QR (CN 범위) |

### 3-2. §6-3 INPI/EP — 2LQR (Tkachenko/Puech) 관련

| ID | 우선순위 | CQL 쿼리 | Range | 근거 |
|----|---------|---------|-------|------|
| Q5 | **P3 ★** | `in=(tkachenko OR puech)` | `1-100` | 발명자명 직접. 2LQR은 물리 인쇄 기반으로 기술 방식 근본적으로 다름 — 특허 번호만 확보용 |
| Q6 | **P3 ★** | `pa=(CNRS OR "universite de montpellier" OR LIRMM) AND ti,ab=QR` | `1-100` | 기관 검색은 노이즈 많음 |
| Q7 | **P3 ★** | `ti,ab=("two-level QR" OR "2LQR" OR "two level QR")` | `1-25` | 제목 직접. 보조 확인용 |
| Q8 | **P3 ★** | `ti,ab=(QR AND (texture OR "print-and-scan" OR "P&S"))` | `1-100` | 2LQR 기법 키워드. 물리 방식이라 우리와 차이 명확 |

### 3-3. §6-4 J-PlatPat — DENSO WAVE 및 JP 다층 QR

| ID | 우선순위 | CQL 쿼리 | Range | 근거 |
|----|---------|---------|-------|------|
| Q9 | **P3 ★** | `pa=("denso wave" OR "denso corporation")` | `1-100` | QR 원천 특허 대부분 만료 + 우리 청구항과 기술 거리 멂 |
| Q10 | **P3 ★** | `in=("masahiro hara")` | `1-100` | 원천 발명자, Q9과 동일 이유 |
| Q11 | **P2 ★★** | `ti,ab=(QR AND (multi-layer OR multilayer OR "multiple layer")) AND pn=JP*` | `1-100` | 다층 QR JP 중형 출원인. KIPO가 JP 특허 인용 사례 존재 |
| Q12 | **P2 ★★** | `ti,ab=(QR AND (steganograph* OR "hidden data" OR payload)) AND pn=JP*` | `1-100` | 스테가노그래피/페이로드 JP |

### 3-4. 관할 무관 보강

| ID | 우선순위 | CQL 쿼리 | Range | 근거 |
|----|---------|---------|-------|------|
| Q13 | **P2 ★★** | `cpc=G06K19/06 AND ti,ab=(signature AND QR)` | `1-100` | QR 분류 + 서명 조합. 우리 Layer C와 직결 |
| Q14 | **P2 ★★** | `ti,ab=(QR AND ed25519)` | `1-100` | QoverwRap 정확 방식. 히트 시 가장 위험, 확률은 낮음 |
| Q15 | **P3 ★** | `ti,ab=(QR AND (delimiter OR "payload structur*"))` | `1-100` | 페이로드 구조화 키워드. 노이즈 비율 높음 |

### 우선순위 요약

| 등급 | 쿼리 수 | 쿼리 ID |
|------|--------|---------|
| P1 ★★★ (필수) | 2 | Q1, Q3 |
| P2 ★★ (권장) | 6 | Q2, Q4, Q11, Q12, Q13, Q14 |
| P3 ★ (선택) | 7 | Q5, Q6, Q7, Q8, Q9, Q10, Q15 |

**실무 권장**: P1+P2만 실행해도 §6-2/6-4의 주요 리스크 커버. P3은 쿼터 여유 있을 때 보강.

## 4. 운영 규칙 (쿼터·안정성 보호)

| 규칙 | 값 |
|------|-----|
| 호출 간 최소 간격 | 1.5초 (분당 ~40호출) |
| 페이지네이션 임계 | 결과 == 100 AND 도메인 관련성 높을 때만 `101-200` 추가 호출 |
| 캐싱 | 모든 응답 JSON으로 `docs/research/epo-results-*.json` 저장. 중복 호출 회피 |
| 중단 조건 | HTTP 403 + `CLIENT.RobotDetected` OR 쿼터 상태 Black 시 즉시 중단 |
| 이미지/full-text 호출 | **이 조사에서는 제외** — abstract+claims로 충분 |
| 응답 크기 모니터링 | 응답 헤더 `X-Throttling-Control`·`X-IndividualQuotaPerHour-Used`·`X-RegisteredQuotaPerWeek-Used` 로깅 |

## 5. 산출물 구조

```
docs/research/
├── epo-queries.md            ← 본 문서 (쿼리 사양)
├── epo-results-cn.json       ← Q1~Q4 응답
├── epo-results-ep-fr.json    ← Q5~Q8 응답
├── epo-results-jp.json       ← Q9~Q12 응답
├── epo-results-common.json   ← Q13~Q15 응답
└── epo-quota-log.json        ← 호출별 쿼터 소비 기록 (재실행 시 참고)
```

## 6. 실행 순서 (활성화 이후)

1. `.env`에 `EPO_OPS_KEY`, `EPO_OPS_SECRET` 설정
2. `scripts/epo_ops_search.py` 작성 (KIPRIS 스크립트 패턴 재사용 + OAuth2 추가)
3. Q1~Q15 순차 실행 (`--query QN` 단위로 개별 실행 가능하게)
4. 결과 triage → `prior-art-survey.md` §3 후보 확장 + §6 미완료 해소

## 7. 참고

- [EPO OPS Developer Portal](https://ops.epo.org)
- [python-epo-ops-client README](https://github.com/ip-tools/python-epo-ops-client/blob/main/README.md)
- CQL 문법: [EPO OPS Documentation](https://link.epo.org/web/21901_ops_v_3.2_documentation_-_version_1.3.20_en.pdf)
- 선행 기반 문서: `docs/research/prior-art-survey.md` §6
