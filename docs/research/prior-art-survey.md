# 선행기술 조사 보고서: QR 다중 레이어 인코딩

**조사일**: 2026-04-16 (초안), 2026-04-17 (KIPRIS API 조사 반영)
**조사자**: AI (Exa, Google Patents, WebSearch, KIPRIS Plus OpenAPI)
**상태**: KIPRIS 직접 검색 **완료** (KR 특허 4건 추가 식별). CNIPA·J-PlatPat·INPI 미완

---

## 1. 조사 범위 및 방법

### 검색 엔진
- **Exa**: 학술 논문, 특허 문서 시맨틱 검색
- **Google Patents**: US/CN/JP 특허
- **WebSearch**: KIPRIS 접근 시도, 일반 웹

### 검색 키워드
- QR code multi-layer data encoding hidden payload
- QR code steganography digital signature verification layer
- QR코드 다중 레이어 인코딩 오버래핑 특허
- QR code dual layer hidden data encoding patent
- Two-level QR code private message sharing
- QR code payload delimiter structured data access control signature

---

## 2. QoverwRap 기술 요약 (비교 기준)

| 특성 | QoverwRap |
|------|-----------|
| 임베딩 방식 | **페이로드 구조화** — QR 표준 데이터 필드 내에서 delimiter + base64(binary header + layers) |
| 레이어 구조 | 3-layer: A(공개 텍스트) + B(컨텍스트 메타데이터) + C(Ed25519 서명) |
| 표준 스캐너 호환 | Layer A가 평문으로 먼저 표시, 뒤의 trailer는 무의미한 문자열로 보임 |
| 오류 정정 영향 | **없음** — ECC 능력을 소모하지 않음 |
| 서명/검증 | **자기 완결적** — Ed25519 서명이 Layer C로 QR 안에 내장, 외부 시스템 불필요 |
| 접근 제어 | **역할 기반 Resolver** — public / authenticated / verified 3단계 |
| Wire format | `[Layer A 평문]\n---QWR---\n[base64([1B ver][2B b_len][2B c_len][B][C])]` |

---

## 3. 후보 선행기술 6건

### 3-1. Liu, Fu, Yu (2019) — Rich QR Codes with Three-Layer Information Using Hamming Code

| 항목 | 내용 |
|------|------|
| **출처** | IEEE Access, vol.7, pp.78640-78651, DOI: 10.1109/ACCESS.2019.2922259 |
| **유사도** | **높음** |
| **핵심** | Hamming 코드 특성과 QR 오류 정정 메커니즘을 이용하여 단일 QR에 3개 레이어 정보 임베딩. 첫 번째 레이어(공개)는 표준 QR 리더로 판독 가능. |
| **기술 방식** | **스테가노그래피** — QR 코드워드 내 비트를 조작하여 Hamming 코드 기반으로 2번째/3번째 레이어 은닉 |
| **서명/검증** | 없음 |
| **접근 제어** | 없음 (Hamming 디코딩 알고리즘 보유자만 추출 가능) |

**차이점 상세**:

| 비교 항목 | Liu et al. | QoverwRap |
|-----------|-----------|-----------|
| 임베딩 위치 | QR 모듈(코드워드) 비트 조작 | QR 데이터 필드의 문자열 내용 |
| ECC 영향 | **소모** (ECC 영역을 은닉에 사용) | **무영향** |
| 디코딩 | Hamming 디코딩 알고리즘 필요 | base64 + struct.unpack (범용) |
| 무결성 보장 | 없음 | Ed25519 서명 |
| 확장성 | Hamming 파라미터에 제한 | QR 용량 범위 내 자유 |
| 복잡도 | 높음 (비트 레벨 조작) | 낮음 (문자열 직렬화) |

---

### 3-2. Tkachenko, Puech et al. (2016) — Two-Level QR Code (2LQR)

| 항목 | 내용 |
|------|------|
| **출처** | IEEE Trans. Information Forensics and Security, vol.11(3), pp.571-583, DOI: 10.1109/TIFS.2015.2506546 |
| **유사도** | **중간** |
| **핵심** | QR 검은 모듈을 텍스처 패턴으로 대체하여 2번째 레벨(비공개) 저장. 인쇄-스캔(P&S) 프로세스 민감성으로 위변조 탐지. |
| **기술 방식** | **물리적 패턴 대체** — 흑색 모듈 → 텍스처 패턴 (디지털 환경에서는 미작동) |
| **특허** | 보유 확인 (CNRS 페이지에 [P1]로 언급, 정확한 번호 미확인) |
| **용도** | 문서 인증 + 비공개 메시지 공유 |

**차이점 상세**:

| 비교 항목 | 2LQR | QoverwRap |
|-----------|------|-----------|
| 레이어 수 | 2 (public + private) | 3 (public + context + signature) |
| 작동 환경 | 물리 인쇄 전용 | 디지털 + 인쇄 모두 |
| 비공개 채널 | 텍스처 패턴 인식 (고해상도 카메라 필요) | base64 디코딩 (소프트웨어만으로 가능) |
| 인증 방식 | P&S 열화 통계 분석 | 암호학적 서명 (Ed25519) |
| 복제 방지 | 가능 (물리 인쇄 의존) | 해당 없음 (디지털 서명 방식) |

---

### 3-3. Suresh, Sadhya, Rajput (2023) — Multi-Layered QR Codes with Efficient Compression

| 항목 | 내용 |
|------|------|
| **출처** | PReMI 2023, LNCS vol.14301, pp.301-311, DOI: 10.1007/978-3-031-45170-6_31 |
| **유사도** | **중간** |
| **핵심** | 최대 9개 숨김 레이어, 각 레이어별 압축+암호화, 스테가노그래피 기반. 최상위 레이어는 표준 QR로 기능. |
| **기술 방식** | **스테가노그래피** — QR 모듈 조작 + 압축(LZW/Huffman) + AES 암호화 |

**차이점 상세**:

| 비교 항목 | Suresh et al. | QoverwRap |
|-----------|--------------|-----------|
| 레이어 역할 | 동종 (모두 임의 데이터) | 이종 (A=공개, B=컨텍스트, C=서명) |
| 레이어 접근 | 키 기반 복호화 | 역할 기반 Resolver |
| 무결성 | 없음 | 내장 서명 |
| ECC 영향 | 소모 | 무영향 |
| 복잡도 | 높음 (압축+암호화+스테가노그래피) | 낮음 (직렬화+서명) |

---

### 3-4. Arce et al. (US10152663B2 / US20170076127A1) — Colored Secure QR Code

| 항목 | 내용 |
|------|------|
| **출처** | Google Patents, University of Delaware, 출원: 2016-09-08, 등록: 2018 |
| **유사도** | **낮음-중간** |
| **핵심** | 컬러 채널(RGB)을 이용해 비밀 QR 코드를 공개 QR 코드에 시각적으로 임베딩. 표준 리더는 공개 QR만 읽음. |
| **기술 방식** | **컬러 기반 시각적 임베딩** |

**차이점**: QoverwRap는 흑백 단일 QR, 데이터 레벨 구조화. 컬러 채널 미사용.

---

### 3-5. Koptyra, Ogiela (2024) — Multi-secret Steganography in QR Codes

| 항목 | 내용 |
|------|------|
| **출처** | WSEAS Trans. Information Science and Applications, vol.21, Art.#49, pp.533-537 |
| **유사도** | **낮음-중간** |
| **핵심** | 2개 독립 비밀을 단일 QR에 숨김. 1번째: 빈 세그먼트 유형으로 인코딩, 2번째: ECC 메커니즘 악용 |
| **기술 방식** | **듀얼 도메인 스테가노그래피** (세그먼트 조작 + ECC 조작) |

**차이점**: 스테가노그래피 기반, 서명/접근 제어 없음, 2-secret 한정.

---

### 3-6. Subramanian (US12200151B2) — QR Code Security via Blockchain

| 항목 | 내용 |
|------|------|
| **출처** | Google Patents, 등록: 2025, 출원: 2022 |
| **유사도** | **낮음** |
| **핵심** | 블록체인(Ethereum 등)에 QR 코드 URL 해시를 기록하여 변조 감지. 스캔 시 블록체인 조회로 검증. |
| **기술 방식** | **외부 검증 시스템** (블록체인) |

**차이점**: QoverwRap는 자기 완결적 (서명이 QR 안에 내장, 외부 시스템 불필요).

---

## 4. 추가 참고 문헌 (간접 관련)

| 저자 | 연도 | 제목 | 관련도 |
|------|------|------|--------|
| Lin, Chen | 2017 | High payload secret hiding technology for QR codes | ECC 기반 스테가노그래피, 낮음 |
| Huang et al. | 2019 | High-payload secret hiding mechanism for QR codes | Reed-Solomon + Turtle Shell, 낮음 |
| Koptyra, Ogiela | 2024 | Steganography in QR Codes — Suboptimal Segmentation | 세그먼트 모드 선택 기반, 낮음 |
| Alajmi et al. | 2020 | Steganography of Encrypted Messages Inside Valid QR Codes | AES + ECC 스테가노그래피, 낮음 |
| Chow et al. | 2016 | Exploiting Error Correction in QR Codes for Secret Sharing | 비밀 분산 공유, 낮음 |

---

## 5. 종합 분석

### QoverwRap 차별점 (novelty 후보)

1. **페이로드-레벨 구조화 (Payload-Level Structuring)**
   - 모든 선행기술 6건은 스테가노그래피(QR 모듈 비트 조작), 물리적 방식(컬러/텍스처), 또는 외부 시스템(블록체인)을 사용
   - QoverwRap는 QR 표준 데이터 필드의 **문자열 내용 안에서** delimiter + binary header로 레이어를 구분
   - 이 접근의 선례를 **발견하지 못함**

2. **ECC 무손실**
   - 스테가노그래피 방식(Liu, Suresh, Koptyra 등)은 ECC 용량을 소비하여 오류 정정 능력 감소
   - QoverwRap는 표준 인코딩 그대로 사용하므로 ECC 능력 100% 유지

3. **자기 완결적 암호학적 서명**
   - 서명이 Layer C로 QR 페이로드 안에 내장
   - 외부 서버, 블록체인, PKI 인프라 없이 오프라인 검증 가능
   - 이 조합(QR 내 내장 서명 + 다층 구조)의 선례를 **발견하지 못함**

4. **역할 기반 Resolver 정책**
   - public / authenticated / verified 3단계 접근 수준
   - 검증 실패 시 안전 기본값(public) 강등
   - 정책 레이어가 구조적으로 분리된 선례를 **발견하지 못함**

### 리스크 평가

| 항목 | 위험도 | 근거 |
|------|--------|------|
| "다층 QR" 개념 일반 | **중간** | Liu(2019), Suresh(2023) 등 다수 선례. 단 기술 방식이 완전히 다름 |
| "공개+비공개 이중 구조" | **중간** | 2LQR(2016) 등 다수. 단 QoverwRap는 "숨김"이 아닌 "구조화" |
| delimiter + base64 wire format | **낮음** | 이 구체적 방식의 선례 미발견 |
| 내장 서명 + Resolver 조합 | **낮음** | 이 조합의 선례 미발견 |
| 전체 기술 조합의 신규성 | **낮음** | 개별 요소(다층/서명/접근제어)는 공지, 조합 방식이 신규 |

---

## 6. 미완료 사항 및 추가 조사 필요

### 6-1. KIPRIS 직접 검색 (한국 특허) — **완료 2026-04-17**
- **방법**: KIPRIS Plus OpenAPI `getAdvancedSearch` — 자유검색 6건 + 제목검색 11건 (총 17개 쿼리)
- **스크립트**: `scripts/kipris_search.py`
- **원본 결과**: `docs/research/kipris-results.json`, `docs/research/kipris-results-title.json`
- **제목 기준 고유 후보**: 64건 → 도메인 관련성 필터 후 **4건** (아래 3-7~3-10 참조)
- **선형대수 "QR 분해" 노이즈 다수 제거** (한국전자통신연구원/삼성 MIMO 관련)

### 6-2. 중국 특허 (CNIPA)
- **상태**: Liu et al. (2019)가 중국 연구진 — CN 특허 존재 가능성
- **필요 작업**: CNIPA 또는 Google Patents에서 저자명/키워드로 CN 특허 확인

### 6-3. 2LQR 특허 상세
- **상태**: Tkachenko et al. 특허 보유 확인되나 번호 미확인
- **필요 작업**: INPI(프랑스) 또는 Espacenet에서 발명자명으로 검색

### 6-4. 일본 특허 (J-PlatPat)
- **상태**: 미조사
- **필요 작업**: QR 코드 원천 기술이 일본(DENSO WAVE)이므로 관련 특허 존재 가능성

---

## 7. KR 특허 (KIPRIS) 추가 후보 4건

### 3-7. 넥스팟솔루션 (KR10-2875492, 2024) — 다중 레이어 QR 코드 기반 인증 라벨

| 항목 | 내용 |
|------|------|
| **출처** | KIPRIS, 출원 2024-11-22, 등록 2024 (출원번호 1020240168104) |
| **유사도** | **높음** |
| **핵심** | 디자인 레이어 + QR 데이터 레이어 + 이미지 넘버 레이어 + 검증 레이어의 물리적 **누적(stack) 구조**. URL과 보안코드를 분리된 레이어로 저장 후 진위 판별. |
| **기술 방식** | **물리 라벨 누적** — 프린트 출력에서 여러 레이어를 겹쳐 인쇄 |

**차이점 상세**:

| 비교 항목 | 넥스팟솔루션 | QoverwRap |
|-----------|-------------|-----------|
| 임베딩 위치 | 물리 라벨의 층별 인쇄 | QR 단일 데이터 필드 문자열 내부 |
| 작동 환경 | 인쇄된 라벨 전용 (물리 스캐너) | 디지털+인쇄 모두 (표준 QR 스캐너) |
| 서명 방식 | URL+보안코드 대조 (서버 필요) | Ed25519 자기완결 서명 (오프라인 검증) |
| 다층의 의미 | 물리적 stack | 논리적 payload 구조 |

---

### 3-8. 한국전자통신연구원·POSTECH (KR10-2765780, 2022) — 다층 구조의 QR코드

| 항목 | 내용 |
|------|------|
| **출처** | KIPRIS, 출원 2022-10-05, 등록 2024 (출원번호 1020220127348) |
| **유사도** | **중간** |
| **핵심** | 금속층 + 유전 패턴 + 고분자 패턴의 **재료 공학적 다층 구조**로 보안 코드 구현. 패턴 두께/재질 차이로 정품 판별. |
| **기술 방식** | **재료 물리 기반 물리 보안** (두께/굴절률 차이 검출) |

**차이점**: QoverwRap는 순수 디지털·논리 구조. 재료 공학/물리적 제작 무관.

---

### 3-9. 에이엠홀로 (KR 10-2022-0046292, 2022, **거절**) — 홀로그램을 이용한 다중 QR 코드

| 항목 | 내용 |
|------|------|
| **출처** | KIPRIS, 출원 2022-04-14, **등록거절** (출원번호 1020220046292) |
| **유사도** | **중간** |
| **핵심** | 홀로그램 표면의 색상발현/비발현 셀로 QR 구성. 제1 QR 코드부 내부에 제2 QR 코드부 배치(중첩형). |
| **기술 방식** | **시각-광학적 다중 QR** (홀로그램 회절) |

**차이점**: QoverwRap는 단일 QR + 페이로드 레벨 분리. 광학/시각 중첩과 완전 다름. **거절 사유** 확인 시 신규성 판단에 참고 가능.

---

### 3-10. 김동현 (KR10-2576380, 2023) — rMQR 코드에 날짜가 중첩되어 표기된 상품 관리

| 항목 | 내용 |
|------|------|
| **출처** | KIPRIS, 출원 2023-06-07, 등록 2023 (출원번호 1020230072683) |
| **유사도** | **낮음** |
| **핵심** | rMQR(rectangular micro QR) 위에 날짜 문자를 시각적으로 overlay 인쇄. 뉴럴 네트워크로 읽기. |
| **기술 방식** | **시각 overlay + NN 복원** |

**차이점**: overlay가 시각 레벨이며 별도 NN 필요. QoverwRap는 표준 스캐너 판독 가능한 페이로드 구조.

---

### KR 검색 관찰

1. **"다층/다중 QR"** 관련 KR 특허는 대부분 **물리적/시각적 다층**(재료·홀로그램·라벨 stack)
2. **"페이로드 내 논리 레이어"** 방식의 KR 특허 **미발견**
3. **"QR 스테가노그래피"** KR 특허 제목 기준 **0건** (학술 논문은 해외 중심)
4. **"QR 서명"** 제목 기준 **0건** — QR 내장 서명 개념이 KR 특허 DB에서 드묾

---

## 8. 최종 결론

QoverwRap의 핵심 기술(페이로드-레벨 구조화 + 내장 Ed25519 서명 + 역할 기반 Resolver)은 학술 6건(국제) + KR 특허 4건을 통합 조사한 결과 동일한 접근을 **발견하지 못했다**.

- 국제 학술(Liu/Tkachenko/Suresh/Arce/Koptyra/Subramanian): 스테가노그래피·물리·블록체인 접근만 존재
- 한국 특허(넥스팟솔루션/ETRI·POSTECH/에이엠홀로/김동현): 물리 라벨 stack, 재료 공학, 홀로그램, 시각 overlay — **논리 레이어링 없음**

**신규성 후보 (재확인):**
1. QR 표준 데이터 필드 내 delimiter+binary header 기반 **논리적 다층 페이로드**
2. Ed25519 서명의 QR 내장 + 오프라인 자기완결 검증
3. public/authenticated/verified **역할 기반 Resolver** (안전 기본값 강등)

**특허 명세서 전략:**
- 청구항은 "문자열 수준 구조화 (character-level structuring) / 논리 레이어 (logical layering)"를 핵심 구별 용어로 사용
- 비교표에서 "물리 stack" / "모듈 비트 스테가노그래피" / "재료 다층" / "시각 overlay" 를 명시적 차별군으로 제시

**추가 조사 남은 항목 (6-2~6-4)**: CNIPA, J-PlatPat, INPI — 출원 전 보강 권장.
