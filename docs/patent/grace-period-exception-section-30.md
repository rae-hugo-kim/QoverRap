# 특허법 §30 공지예외 적용 자료 (KIPO 본인 출원용)

> **목적**: 본 출원에 앞서 공개된 GitHub 저장소 (`github.com/rae-hugo-kim/QoverRap`) 의 공지에 대하여 특허법 §30(1)1호에 따른 공지예외 적용을 주장하기 위한 자료. KEAPS 출원서 작성 시 본 문서의 §3 ~ §5 를 근거로 "공지예외 적용 주장" 체크 + 증명서류 첨부.
>
> **법적 근거**: 특허법 §30(1)1호 — "특허를 받을 수 있는 권리를 가진 자에 의하여 그 발명이 ... 공지되거나 공연히 실시되는 등의 사유에 해당하게 된 경우, 그 사유에 해당하는 날부터 12개월 이내에 그 자가 출원한 특허출원에 대하여는 ... 신규성·진보성을 부인하지 아니한다."

---

## 1. 공지 사실 요약

| 항목 | 내용 |
|---|---|
| 공지 매체 | GitHub.com 공개 저장소 |
| 저장소 URL | https://github.com/rae-hugo-kim/QoverRap |
| 저장소 명 | `rae-hugo-kim/QoverRap` (calling 명 "QoverwRap" 의 GitHub 명) |
| 저장소 공개 상태 | **PUBLIC** (gh CLI 메타데이터 확인, `isPrivate: false`) |
| 최초 공지일 (저장소 PUBLIC 생성·첫 push) | 2026-04-14 05:21:23 UTC = **2026-04-14 14:21 KST** |
| 첫 commit 시각 | 2026-04-14 14:21:29 KST (`601eb6c Initial commit`) |
| 최종 push 시각 (GitHub 기준, gh CLI `pushedAt`) | **2026-05-04 10:58:11 UTC = 2026-05-04 19:58 KST** |
| 로컬 최신 commit (출원 직전 push 예정) | 2026-05-15 이후 (출원 직전 push 시점) |
| 공지자 (GitHub 계정) | `rae-hugo-kim` (이메일 `rae.kim@aipq.kr`) |
| 공지 내용 | 본 발명의 명세서·청구항·도면·구현 코드. 단, **공개 범위는 GitHub 에 push 된 commit 까지** — 로컬 commit 만 있는 부분은 공지 대상 아님 |

**공지 기간 (현재 시점)**:
- **1차 공개**: 2026-04-14 (저장소 PUBLIC 생성 + 첫 push, 원본 11항 청구항 + 명세서 골격 + 구현 + Fig. 1~4)
- **연속 보완 공개**: 2026-04-14 ~ 2026-05-04 (마지막 push 시점, 청12~15 의 기초 구현 + 원 Fig. 8/9 도면 + 다수 보정 라운드)
- **로컬 보완 (push 미완료)**: 2026-05-04 이후의 commits (16~19차 라운드 청구항·본문 보정, 도면 재번호화 Fig. 5/6 재렌더) 는 현 시점 GitHub 에 미반영. 출원 직전 push 시 공지 범위 확장됨.

**§30 12개월 기한**: 최초 공지일 2026-04-14 기준 → **2027-04-14 이전 출원 필수**.

---

## 1.A 공지 일자별 commit / 청구항 매핑

| 일자 | 주요 commit (대표) | GitHub 반영 (push 시점 ≤ 2026-05-04 = ✓) | 공지된 청구항·도면 |
|---|---|---|---|
| 2026-04-14 | `601eb6c` Initial commit, `7704e0e` initialize | ✓ | 저장소 골격, 초기 README·LICENSE |
| 2026-04-14 ~ 04-29 | 다수 feasibility/spec/figure commits | ✓ | 본 발명의 wire format 본문 + 청구항 1·2·3·4·5·6·7·8·9·10·11 의 기술적 기재 (원본 11항) + Fig. 1~4 (PlantUML 첫 산출) |
| 2026-04-30 | `90d8552 docs(patent): add §8.6 system block diagram for claim 11 mapping` | ✓ | 청11 (시스템 독립항) 본문 + 원 Fig. 8 (현 Fig. 5) 시스템 블록도 |
| 2026-05-04 (마지막 push) | `c027c8a chore(harness): sync harness 2026.5 → 2026.14`, `bee8aae docs(patent): reposition spec to plaintext-prefix + signed-trailer wire format` | ✓ | 명세서 본문 재포지셔닝 (선두 평문 prefix + signed trailer wire format), 5차~7차 라운드 보정. 이 시점까지의 청1~11 본문이 GitHub 에 공개됨 |
| 2026-05-05 ~ 05-15 (로컬 only) | `eefaddc feat: patent spec draft + figure capture`, `a223ea2 docs(patent): 14-round clarity/support hardening` 등 16~19차 보정 commits | ✗ (push 미완료) | 청12 (canonical signing), 청13 (verified-empty 보존), 청14 (휴대용 단말), 청15 (시스템 종속) 의 청구항 본문, Fig. 6 (mobile flow) 신설, 응용 명세서 보정, Fig. 5/6 재번호화 — **현 시점 미공개**. 출원 직전 push 시 공지 범위 확장 |

**해석**:
- 2026-05-04 까지 push 된 부분에 대해서만 §30 적용이 필요. 그 이후 (로컬) 변경은 공지된 적이 없으므로 §29(1) 우려 자체가 없음.
- 출원 직전에 final push 를 수행하면, 그 시점이 청12~15 의 최초 공지일이 되며, 모두 §30 12개월 윈도우 내에 위치.
- **권장**: 출원 직전 (a) 모든 로컬 commits push → (b) Web Archive 캡처 → (c) KEAPS 출원. 이 순서로 진행하면 §30 적용 범위가 명확히 출원 전체 청구항을 포섭.

---

## 2. 공지자와 출원인 동일성

| 식별자 | GitHub 계정 (공지자) | 출원인 |
|---|---|---|
| 영문명 | rae-hugo-kim | Sangrae Kim |
| 한글명 | (계정 표시 — Sangrae Kim 동일) | 김상래 |
| 이메일 | rae.kim@aipq.kr (모든 commit 의 author email) | rae.kim@aipq.kr |
| 저작권 표시 | LICENSE 파일 "© 2026 Sangrae Kim (김상래)" | 동일 |
| pyproject.toml `authors` | `Sangrae Kim (김상래)` | 동일 |

**동일성 결론**: GitHub 계정 `rae-hugo-kim` (이메일 `rae.kim@aipq.kr`) 의 모든 공지 commit 의 author 가 본 출원인 Sangrae Kim (김상래) 임이 LICENSE / pyproject.toml / commit author email 의 일관성으로 입증됨. 공지자 = 출원인 (특허법 §30(1)1호 "특허를 받을 수 있는 권리를 가진 자" 요건 충족).

---

## 3. 공지 시점 증명

**1차 증명**: GitHub 저장소 메타데이터 (gh CLI 추출, `docs/patent/evidence/github-repo-metadata.json`)

```json
{
  "createdAt": "2026-04-14T05:21:23Z",
  "isPrivate": false,
  "nameWithOwner": "rae-hugo-kim/QoverRap",
  "url": "https://github.com/rae-hugo-kim/QoverRap",
  "visibility": "PUBLIC"
}
```

**2차 증명**: git commit log 전체 (`docs/patent/evidence/git-commit-log.txt`, 39 commits, 2026-04-14 ~ 2026-05-15)

첫 commit:
```
601eb6c | 2026-04-14 14:21:29 +0900 | rae.kim <rae.kim@aipq.kr> | Initial commit
```

**3차 증명 (출원 직전 추가 권장)**: Web Archive 캡처
- 출원 직전 https://web.archive.org/ 에서 저장소 페이지를 명시적으로 크롤링 요청하여 출원 시점의 공개 상태와 commit 이력을 영구 보존.
- 캡처 URL: `https://web.archive.org/web/<timestamp>/https://github.com/rae-hugo-kim/QoverRap`
- 저장 후 본 §3 에 URL 추가.

---

## 4. 공지 내용 (본 출원과의 대응)

본 출원 (`docs/patent/qoverwrap-kipo-application-draft.md`) 의 청구범위 청1 ~ 청15 에 대응하는 공지 내용 및 GitHub 공개 여부:

| 본 출원 청구항 | 공지 위치 (GitHub 저장소 내 경로) | 현 시점 GitHub 공개? |
|---|---|---|
| 청1 (생성 방법), 청2 (검증 방법) | `src/qoverwrap/encoder.py`, `src/qoverwrap/decoder.py` | ✓ (≤2026-05-04 push) |
| 청3 (5바이트 헤더), 청4 (구획자) | `src/qoverwrap/encoder.py` | ✓ |
| 청5 (단순 모드), 청7 (3단 출력 수준), 청8 (안전 강등) | `src/qoverwrap/decoder.py`, `src/qoverwrap/resolver.py` | ✓ |
| 청6 (Ed25519) | `src/qoverwrap/crypto.py` | ✓ (구현 코드) / Layer C 길이 64바이트 명시 한정의 청구항 본문은 로컬 only |
| 청9 (발급자 라우팅) | `src/qoverwrap/registry.py` | ✓ |
| 청10 (CRM) | 저장소 전체 (Python source) | ✓ |
| 청11 (시스템 독립항) | `src/qoverwrap/` + `demo/` 통합 구성 + 명세서 §8.6 (원 Fig. 8 → 현 Fig. 5) | ✓ (~2026-04-30 시스템 블록도 추가 이후) |
| 청12 (canonical signing message 정규화) | `src/qoverwrap/crypto.py` (canonical signing 함수 구현) | ✓ (구현 코드) / 청구항 본문 명시화는 로컬 only |
| 청13 (verified-empty Layer B 보존) | `src/qoverwrap/resolver.py` (verified-empty 처리 로직) | ✓ (구현) / positive limitation 청구항 본문은 로컬 only |
| 청14 (휴대용 단말 응용) | `demo/frontend/`, `demo/backend/` | ✓ (데모 앱) / 휴대용 단말 청구항 본문은 로컬 only |
| 청15 (시스템 종속, canonical+verified-empty 결합) | 결합 실시예 (`demo/` + spec §8.7.3) | ✗ (로컬 only) |
| 명세서 §발명을 실시하기 위한 구체적인 내용 | `docs/patent/spec-draft.md`, `docs/patent/qoverwrap-kipo-application-draft.md` | 부분 ✓ (2026-04-14 ~ 05-04 push 분), 이후 보정은 로컬 only |
| 도면 Fig. 1 ~ Fig. 4 | `docs/patent/figures/rendered/fig{1..4}_*.png` | ✓ |
| 도면 Fig. 5 (system block, 원 Fig. 8) | `docs/patent/figures/rendered/fig5_system_block.png` (원본은 `fig8_system_block.png` 로 push 됨) | ✓ (원 명명으로 공개) / 재번호화·재렌더는 로컬 only |
| 도면 Fig. 6 (mobile flow, 원 Fig. 9) | `docs/patent/figures/rendered/fig6_mobile_terminal_flow.png` (원본은 `fig9_mobile_terminal_flow.png` 로 push 됨) | ✓ (원 명명으로 공개) / 재번호화·재렌더는 로컬 only |

**공지 범위 해석**:
- **2026-05-04 이전 push 분**: 청1~11 본문 (원본 11항) + Fig. 1~4 + 원 Fig. 8/9 + 구현 코드 전체. 본 부분에 대해 §30 적용 주장.
- **2026-05-04 이후 로컬 commits**: 청12~15 본문, 청1·6·14 의 정밀화 표현, Fig. 5/6 재번호화 및 재렌더. **공지된 적 없음 → §29(1) 우려 없음 → §30 적용 대상도 아님**. 단, 출원 직전 push 시점에서 공지 범위 확장됨.
- 본 §30 신청은 **2026-04-14 의 1차 공개**를 기점으로 일괄 주장하되, 청구항별 최초 공지 시점은 위 표의 commit 매핑으로 추적 가능. 모든 공지가 12개월 윈도우 내에 위치하므로 §30 적용 영향 균질.

---

## 5. 출원 시 §30 적용 절차 (KEAPS)

### 5.1 출원서 작성 단계

KEAPS 출원서 양식의 "공지예외 적용 주장" 섹션에서 다음 항목 입력:

| 항목 | 입력값 |
|---|---|
| 공지예외 적용 주장 | **✓ 신청함** |
| 적용 조항 | 특허법 §30(1)1호 (출원인 자신의 공지) |
| 공지 일자 | 2026-04-14 (최초 공지일 = 저장소 생성·첫 push) |
| 공지 매체 | 인터넷 (GitHub 공개 저장소) |
| 공지 장소 | https://github.com/rae-hugo-kim/QoverRap |
| 공지 형태 | 저장소 전체 공개 (소스코드, 문서, 도면 일체) |
| 공지자 | Sangrae Kim (김상래) — 출원인과 동일 |

### 5.2 증명서류 제출 (출원과 동시 또는 출원 후 30일 이내)

KEAPS "공지예외 증명서류" 첨부 항목에 다음 자료 제출:

1. **공지예외 적용 신청서** (KIPO 별지 양식 — KEAPS 자동 생성 가능)

2. **저장소 공개 사실 증명**: GitHub 저장소 메타데이터 캡처 (PDF 또는 HTML)
   - 본 자료: `docs/patent/evidence/github-repo-metadata.json` 을 PDF로 변환하거나 GitHub 저장소 페이지의 브라우저 캡처 (PDF 인쇄)
   - 필수 표시: 저장소 URL, "Public" 표시, 첫 commit 일자, 소유자 계정명

3. **공지 시점 증명**: git commit log 전체 (`docs/patent/evidence/git-commit-log.txt`)
   - PDF로 변환하여 첨부
   - 또는 Web Archive 캡처 URL 첨부

4. **공지자-출원인 동일성 증명**:
   - LICENSE 파일 사본 (저작권 표시)
   - GitHub 계정 소유 증명 — 이상 자료로 부족 시 다음 중 택1:
     - (a) GitHub 계정 설정 페이지 캡처 (이메일 = 출원인 이메일)
     - (b) GitHub 저장소에 출원인 명의의 자필 서명 commit (출원 직전 1회) — 이메일 일치
     - (c) 공증인의 확인 (실명·계정 확인서)

5. **선택적 추가 증명**: Web Archive 영구 보존 URL
   - 출원 직전 https://web.archive.org/save/https://github.com/rae-hugo-kim/QoverRap 요청
   - 캡처 완료 후 URL 을 본 문서 §3 에 기록 + 증명서류 첨부

### 5.3 주의사항

- **30일 기한**: §30 적용 주장은 출원과 동시에 하되, 증명서류는 출원일로부터 30일 이내 제출 (특허법 시행규칙 §22 참조). KEAPS 출원과 함께 제출하는 것이 가장 안전.
- **모든 공지 일자**: 동일 발명에 대한 복수의 공지가 있는 경우 가장 빠른 공지일 (2026-04-14) 을 기준으로 12개월 계산. 출원일이 2027-04-14 이전이면 §30 적용 가능.
- **공지자 외 제3자 인용**: 본 저장소에 출원인 외 제3자가 commit 한 사실이 있으면 그 부분에 대해서는 §30 적용 추가 입증 필요. **본 저장소는 모든 39 commit 의 author email 이 `rae.kim@aipq.kr` 로 일관됨 → 단독 공지 → 추가 입증 불요.**

---

## 6. 위험 분석

| 위험 | 발생 가능성 | 영향 | 완화 |
|---|---|---|---|
| §30 적용 주장 미제출 | (현재 미제출) | 본 출원이 GitHub 공지에 의해 §29(1) 신규성 상실 → 거절 | 본 문서 §5 절차로 출원과 동시 신청 |
| 증명서류 30일 기한 도과 | 중 | §30 신청은 유효하나 증명서류 부재로 인정 안 됨 | 출원 직전 §5.2 자료 모두 준비, KEAPS 첨부 |
| GitHub 계정 ↔ 출원인 동일성 불충분 | 중 | 동일인 인정 안 되면 §30 적용 불가 | LICENSE + pyproject.toml + commit author email 일관성 + 필요시 공증 |
| 출원일이 2027-04-14 이후 | 저 (현재 1개월) | 12개월 도과로 §30 적용 불가 | 본 출원이 2026-05-15 이후 1개월 내 출원 권장 |
| 공지 후 12개월 내 제3자가 동일 발명 출원 | 중 | 본 출원이 §29(1)·§29(3) 모두 적용되어 거절 가능 | §30 은 출원인 본인의 공지에만 적용. 제3자 출원의 신규성 부인 효과는 별개. **본 출원의 출원 시기를 최대한 앞당기는 것이 최선의 완화책.** |
| Web Archive 캡처 누락 | 저 | GitHub 저장소가 삭제·비공개 전환되면 공지 사실 증명 곤란 | 출원 직전 Web Archive 캡처 + 저장소를 출원 후 일정 기간 PUBLIC 유지 |

---

## 7. 출원 직전 체크리스트

- [ ] **모든 로컬 commits 를 GitHub 에 push** (`git push origin main`) — 청12~15·재번호화 등 로컬-only 항목을 공지 범위에 편입할지 결정. push 후 본 §1.A 표의 "GitHub 반영" 컬럼 일괄 ✓ 처리 가능
- [ ] **Web Archive 캡처**: `https://web.archive.org/save/https://github.com/rae-hugo-kim/QoverRap` 요청 → 캡처 URL 기록 (예: `https://web.archive.org/web/2026MMDDhhmmss/...`)
- [ ] GitHub 저장소 페이지 브라우저 캡처 (Code 탭 + History 탭) → PDF 저장
- [ ] `docs/patent/evidence/git-commit-log.txt` 출원 직전 시점으로 재생성 — `git log --reverse --format="%h | %ai | %an <%ae> | %s" > docs/patent/evidence/git-commit-log.txt`
- [ ] `docs/patent/evidence/github-repo-metadata.json` 출원 직전 재추출 — `gh repo view rae-hugo-kim/QoverRap --json visibility,createdAt,pushedAt,isPrivate,nameWithOwner,url,licenseInfo,updatedAt > docs/patent/evidence/github-repo-metadata.json`. push 직후 pushedAt 갱신 확인
- [ ] LICENSE 파일 PDF 변환 (출원인 명의 명시)
- [ ] pyproject.toml authors 필드 캡처 (출원인 = `Sangrae Kim (김상래)`)
- [ ] (필요 시) GitHub 계정 설정 페이지 캡처 (이메일 일치 확인용)
- [ ] KEAPS 출원서에서 "공지예외 적용 주장" ✓ 체크
- [ ] 위 증명서류 모두 KEAPS 첨부 (PDF / 이미지)
- [ ] 출원 후 30일 이내 증명서류 누락분 추가 제출 (KEAPS 보정 절차)

---

## 8. 참조

- 특허법 §30(1)1호: https://www.law.go.kr/법령/특허법/제30조
- 특허법 시행규칙 §22 (증명서류 제출 기한): https://www.law.go.kr/법령/특허법시행규칙/제22조
- KIPO 심사기준 제2부 제3장 §3 (공지예외 적용): KIPO 사이트
- KEAPS 매뉴얼 §6.4 (공지예외 적용 주장 입력): KEAPS 다운로드 동봉 매뉴얼

증명서류 원본 (디지털 사본):
- `docs/patent/evidence/git-commit-log.txt` — 39 commits, 2026-04-14 ~ 2026-05-15
- `docs/patent/evidence/github-repo-metadata.json` — 저장소 메타데이터 (gh CLI 추출)
- `LICENSE` (저장소 루트) — 저작권 표시
- `pyproject.toml` (저장소 루트) — authors 필드
