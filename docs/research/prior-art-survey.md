# 선행기술 조사 보고서: QR 다중 레이어 인코딩

**조사일**: 2026-04-16 (초안), 2026-04-17 (KIPRIS API 조사 반영), 2026-04-22 (EPO OPS CNIPA/JP/EP 조사 반영)
**조사자**: AI (Exa, Google Patents, WebSearch, KIPRIS Plus OpenAPI, EPO OPS v3.2)
**상태**: KIPRIS **완료** (KR 4건) + EPO OPS **완료** (CN/JP/EP 보강, 15 쿼리). 2LQR 관련 FR3027430A1 은 EPO OPS 에서 확인 완료. INPI 원문 및 청구항 직접 확인은 출원 전 선택적 보강 항목.

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
| 임베딩 방식 | **페이로드 문자열-레벨 구조화** — QR 표준 데이터 필드 안에서 delimiter + base64(binary header + 후속 계층 데이터) 결합 |
| 레이어 구조 | Layer A(공개 텍스트 prefix) + Layer B(컨텍스트 메타데이터) + Layer C(디지털 서명, 예: Ed25519) |
| 표준 스캐너 호환 | Layer A가 표준 QR 리더의 판독 결과 선두에 평문으로 표시, 뒤의 trailer는 표준 리더 동작을 방해하지 않음 |
| 오류 정정 영향 | QR 모듈 또는 ECC 코드워드를 은닉 채널로 변조하지 않음 (선택된 QR 버전·오류 정정 레벨의 표준 ECC 메커니즘 그대로 사용) |
| 서명/검증 | 검증 대상 데이터 및 서명값이 동일 페이로드에 포함되고, 공개키는 사전 보유 또는 외부 입력으로 제공되며, **온라인 검증 서버 또는 블록체인 조회 호출 없이** 검증 |
| 출력 정책 | 검증 결과 기반 출력 정책 — 제1/제2/제3 출력 수준 (구 명칭: public / authenticated / verified). 페이로드 자체의 암호학적 판독 제한이 아닌 응용 프로그램 반환 데이터의 범위를 결정하는 매개변수 |
| 안전 강등 | 페이로드 파싱·헤더 검증·트레일러 디코딩·공개키 부재·서명 검증 실패 중 어느 하나라도 발생 시 Layer A 만 반환 |
| Wire format | `[Layer A 평문]\n---QWR---\n[base64([1B ver][2B b_len][2B c_len][B][C])]` (DELIMITER = UTF-8 11바이트) |

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
| **특허** | **FR3027430A1** — CNRS + Univ. Montpellier 2 + Authentication Industries 공동출원. 제목(FR): "Code visuel graphique à deux niveaux d'information et sensible à la copie". EPO OPS 2026-04-22 확인 (triage: `epo-triage-FR-3027430-A1.json`) |
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
| 레이어 접근 | 키 기반 복호화 | 검증 결과 기반 출력 정책 (Resolver) |
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

**차이점**: QoverwRap는 검증 대상 데이터 및 서명값이 동일 페이로드 내부에 포함되며, 사전 보유 또는 외부 입력 공개키만으로 온라인 검증 서버 호출 없이 검증 가능.

---

## 4. 추가 참고 문헌 (간접 관련)

| 저자 | 연도 | 제목 | 관련도 |
|------|------|------|--------|
| Lin, Chen | 2017 | High payload secret hiding technology for QR codes | ECC 기반 스테가노그래피, 낮음 |
| Huang et al. | 2019 | High-payload secret hiding mechanism for QR codes | Reed-Solomon + Turtle Shell, 낮음 |
| Koptyra, Ogiela | 2024 | Steganography in QR Codes — Suboptimal Segmentation | 세그먼트 모드 선택 기반, 낮음 |
| Alajmi et al. | 2020 | Steganography of Encrypted Messages Inside Valid QR Codes | AES + ECC 스테가노그래피, 낮음 |
| Chow et al. | 2016 | Exploiting Error Correction in QR Codes for Secret Sharing | 비밀 분산 공유, 낮음 |
| van der Merwe, Noble (Apple) | 2015 | Invisible Optical Label for Transmitting Information Between Computing Devices (US 9,022,291 B1 / US 9,022,292 B1) | 시간축 chrominance 인코딩 — 아래 §4-1 참조 |

### 4-1. Apple "Invisible Optical Label" (IOL) — US 9,022,291 / US 9,022,292

| 항목 | 내용 |
|------|------|
| **출처** | US 9,022,291 B1 / US 9,022,292 B1, Apple Inc., 발급 2015-05-05 |
| **유사도** | **낮음** (QR 도메인 외) |
| **핵심** | 디스플레이에서 프레임 A(파랑+자홍) / 프레임 B(주황+초록)를 60~120fps로 교대 표시하여 인간 눈에는 회색 애니메이션으로만 보이지만, 카메라 센서는 프레임 간 색차(chrominance)에서 2D 매트릭스 코드를 추출. Apple Watch 초기 페어링 파티클 클라우드 애니메이션이 이 기술의 상용 구현. |
| **기술 방식** | **시간축 chrominance 은닉** — 디스플레이→카메라 채널의 시간 도메인 레이어링 |
| **용도** | 디바이스 페어링 (Apple Watch ↔ iPhone) |

**QoverwRap와 차이**:

| 비교 항목 | Apple IOL | QoverwRap |
|-----------|-----------|-----------|
| 인코딩 도메인 | **시간축** (프레임 간 색상 교대, 디스플레이→카메라) | **페이로드** (QR 데이터 필드 문자열 내부) |
| 가시성 | 인간 눈에 비가시 (카메라만 감지) | 표준 QR 스캐너로 판독 가능 (Layer A 평문) |
| 복제 방지 | 시간축 정보 소실로 스크린샷 복제 불가 | Ed25519 서명으로 위변조 감지 |
| 레이어 구조 | 단일 은닉 채널 (페어링 데이터) | 3-layer 논리 구조 (A=공개 + B=메타 + C=서명) |
| 표준 호환 | Apple 독자 프로토콜 | QR 표준 (ISO/IEC 18004) 완전 호환 |
| 인증 대상 | 디바이스 (이 Watch가 나의 것인가) | 데이터 무결성 (이 QR 내용이 진짜인가) |

**시사점**: IOL은 "시각 코드에 정보를 은닉하여 전송"이라는 상위 개념을 공유하지만, 인코딩 도메인(시간 vs 페이로드), 채널(디스플레이→카메라 vs QR 데이터 필드), 목적(디바이스 페어링 vs 데이터 인증)이 모두 다름. 특허 청구항 충돌 리스크 **없음**. 다만, 특허 명세서의 "관련 기술" 섹션에서 시간축 은닉(IOL) 대비 페이로드-레벨 구조화의 차별성을 언급하면 심사관에게 기술 스펙트럼의 위치를 명확히 전달할 수 있음.

---

## 5. 종합 분석

### QoverwRap 차별점 (novelty 후보)

본 발명의 신규성·진보성은 "QR + 서명" 또는 "다층 QR" 일반 개념이 아니라, 아래 요소의 **구체적 결합** 에 둔다. QR 또는 barcode 페이로드에 디지털 서명을 포함하여 인증을 수행하는 선행기술군((마) 서명-내장 자격증명/인증 QR — SMART Health Cards, ICAO VDS/VDS-NC, US20120308003A1, KR20180122843A, SAP signed QR 등)은 별도로 존재하므로, "QR + 서명 자체의 선례 부재"는 신규성 근거로 사용하지 않는다.

1. **페이로드 문자열-레벨 구조화 (Payload-Level Structuring)**
   - 선행기술 (가)~(다) 군은 스테가노그래피(QR 모듈 비트 조작), 물리적 방식(컬러/텍스처), 또는 이미지 도메인 변형을 사용
   - QoverwRap는 QR 표준 데이터 필드의 **문자열 내용 안에서** delimiter + versioned binary header로 계층을 구분하고 텍스트 안전 인코딩 트레일러로 결합
   - (마) 군은 전체 credential 또는 barcode message를 단일 서명 객체로 취급하며, Layer A 평문 prefix 와 delimiter-framed trailer 의 결합 wire format 을 명시하지 않음

2. **QR 모듈 / ECC 코드워드 무변조**
   - 스테가노그래피 방식((가) 군)은 모듈 비트·코드워드를 은닉 채널로 변조
   - QoverwRap는 모듈 또는 ECC 코드워드를 은닉 채널로 변조하지 않으므로, 선택된 QR 버전 및 오류정정 레벨의 표준 오류정정 메커니즘을 그대로 사용

3. **온라인 서버 호출 없는 내장 서명 검증**
   - 검증 대상 데이터 및 서명값이 동일 페이로드에 포함됨
   - 공개키는 사전 보유 또는 외부 입력으로 제공되며, 온라인 검증 서버 또는 블록체인 조회 호출 없이 검증
   - (라) 군은 외부 인프라/온라인 호출 의존, (마) 군은 issuer 키 분배가 일반적으로 가정되나 본 발명은 키 분배 채널을 청구하지 않음

4. **검증 결과 기반 출력 정책 + 안전 강등의 결합**
   - 출력 수준은 페이로드 자체의 암호학적 판독 제한이 아닌, 응용 프로그램 반환 데이터의 범위를 결정하는 매개변수
   - 페이로드 파싱·헤더 검증·트레일러 디코딩·공개키 부재·서명 검증 실패 중 어느 하나라도 발생 시 Layer A 만 반환
   - 본 강등 정책은 통상적인 오류 처리가 아니라 본 발명의 계층형 페이로드 구조 및 트레일러 검증 절차와 결합된 반환 데이터 제한 정책으로서, (마) 군 선행기술에서는 이 결합을 명시하지 않음

### 리스크 평가

| 항목 | 위험도 | 근거 |
|------|--------|------|
| QR + 디지털 서명 일반 | **높음** | (마)군 — SHC, ICAO VDS, US20120308003A1, KR20180122843A, SAP signed QR 등 별도 선행기술군 존재. 본 발명의 신규성은 "QR + 서명" 일반 개념에 두지 않음 |
| 다층 QR 일반 | **중간** | Liu(2019), Suresh(2023), 2LQR 등 다수 선례. 단 기술 방식(스테가노/물리/논리)이 다름 |
| public/private QR 구조 | **중간~높음** | DENSO SQRC 가 가장 가까운 직접 비교 대상 — dedicated reader + cryptographic key 의존 구조. 본 발명은 표준 리더 부분 호환 + 출력 정책 분리로 차별화 |
| Layer A prefix + delimiter trailer + versioned binary header 결합 wire format | **낮음~중간** | 본 결합의 직접 선례 미발견. 다만 search 범위(KIPRIS + EPO OPS biblio)의 커버리지 한계 고려 시 절대적 단정은 어려움 |
| safe-fallback resolver 결합 | **중간** | "검증 실패 시 데이터를 숨긴다"는 일반 개념은 통상적 보안 처리로 평가될 여지가 있어, 반드시 wire format 결합과 묶어 청구해야 방어 가능 |
| 전체 narrow combination (5요소 결합) | **중간** | 개별 요소는 공지이나, Layer A prefix + delimiter-framed trailer + versioned binary header + 공개키 사전 보유/외부 입력 + safe-fallback resolver 의 결합은 (마)군 어느 문헌에도 명시되지 않음 |

---

## 6. 미완료 사항 및 추가 조사 필요

### 6-1. KIPRIS 직접 검색 (한국 특허) — **완료 2026-04-17**
- **방법**: KIPRIS Plus OpenAPI `getAdvancedSearch` — 자유검색 6건 + 제목검색 11건 (총 17개 쿼리)
- **스크립트**: `scripts/kipris_search.py`
- **원본 결과**: `docs/research/kipris-results.json`, `docs/research/kipris-results-title.json`
- **제목 기준 고유 후보**: 64건 → 도메인 관련성 필터 후 **4건** (아래 3-7~3-10 참조)
- **선형대수 "QR 분해" 노이즈 다수 제거** (한국전자통신연구원/삼성 MIMO 관련)

### 6-2. 중국 특허 (CNIPA) — **완료 2026-04-22 via EPO OPS**

- **방법**: EPO OPS v3.2 `published-data/search` — 4 쿼리 (Q1~Q4, 쿼리 설계는 `epo-queries.md` §3-1)
- **스크립트**: `scripts/epo_search.py`
- **원본 결과**: `docs/research/epo-results-cn.json`
- **상세 triage**: `docs/research/epo-triage-CN111224771A.json`, `docs/research/epo-triage-CN115828975A.json`

**쿼리별 결과 요약**:

| ID | CQL | 결과 | 해석 |
|----|-----|------|------|
| Q1 | `in=(liu AND (fu OR yu)) AND cpc=G06K19/06` | **0** | Liu et al. 저자군의 CN 병행 출원 **EPO biblio 미발견** |
| Q2 | `ti,ab=("rich QR" OR "three-layer QR")` | **0** | Liu 논문 제목 키워드 직접 매치 없음 |
| Q3 | `ti,ab=(QR AND hamming)` | **0** | Hamming 기반 QR 전세계 직접 hit 없음 |
| Q4 | `ti,ab=(QR AND (steganograph* OR hidden))` → CN 필터 | **1건** | CN111224771A (아래 참조) |

**후속 broader 확인 쿼리 (EPO OPS, 추가)**:

| CQL | 총 결과 | CN 건 |
|-----|--------|------|
| `ti=QR AND cpc=G06K19/06` | 60 (전세계) | 저커버리지 신호 |
| `ti,ab=(QR AND (hierarchical OR tiered OR nested))` | 1 | **CN115828975A** |
| `ti,ab=("multi-layer QR" OR "multilayer QR")` | 1 | 0 (CN 아님) |
| `ti,ab=(QR AND (authenticity OR authentication OR tamper))` | 3 | 0 |

**발견된 CN 관련 2건의 기술 분석**:

#### (a) CN111224771A — Management code encryption/decryption based on PCA and Henon mapping
- **출원인/발명자**: 세부 확인 가능 (triage JSON 참조)
- **핵심**: 민감정보 QR을 무의미한 QR 이미지 내부에 **PCA로 은닉**한 뒤 **Henon 카오스 매핑**으로 이미지 암호화
- **기술 방식**: 이미지 도메인 스테가노그래피 + 카오스 암호
- **QoverwRap와 차이**:
  | 비교 | CN111224771A | QoverwRap |
  |------|-------------|-----------|
  | 은닉 도메인 | **이미지 픽셀 레벨** (PCA+Henon) | **문자열 페이로드 레벨** |
  | 암호 | 카오스(Henon) 기반 | 표준 대칭/비대칭 (Ed25519 서명) |
  | 표준 스캐너 판독 | 불가 (이미지 암호화됨) | 가능 (Layer A 평문) |
  | ECC 영향 | 원본 QR 자체 복호 필요 | 무영향 |
- **결론**: 기술 경로가 근본적으로 다름. 인용 리스크 **낮음**.

#### (b) CN115828975A — Visual art-oriented 2D code via hierarchical enhanced identification rate
- **핵심**: 입력 이미지와 QR을 겹쳐 **모듈 중심 밝기를 조정**해 시각적 예술성 유지 + 디코딩 가능성 확보
- **기술 방식**: 이미지-시각 레벨의 hierarchical mask 조작 (아트 QR)
- **QoverwRap와 차이**:
  | 비교 | CN115828975A | QoverwRap |
  |------|-------------|-----------|
  | "hierarchical"의 의미 | 임계 마스크의 **인식률 계층** | **페이로드 논리 레이어** (A/B/C) |
  | 목적 | 시각 예술성 보존 | 계층형 페이로드 직렬화 + 내장 서명 검증 |
  | 변경 대상 | 모듈 중심 밝기 | 없음 (표준 인코딩 유지) |
- **결론**: "hierarchical" 용어만 공유, 기술 의미 완전 상이. 인용 리스크 **낮음**.

**커버리지 caveat**: EPO OPS biblio DB의 CN 특허 커버리지는 CNIPA 원본 대비 제한적 (`ti=QR AND cpc=G06K19/06`가 전세계 60건만 반환 → 저커버리지 시그널). CNIPA 직접 검색으로 교차 확인이 이상적이나, 핵심 위험 쿼리(Q1/Q3)가 모두 0 hit이므로 잔여 리스크 제한적.

### 6-3. 2LQR 특허 상세 (EP/FR) — **완료 2026-04-22 via EPO OPS**

- **방법**: EPO OPS v3.2 — 4 쿼리 (Q5~Q8)
- **원본 결과**: `docs/research/epo-results-ep-fr.json`

| ID | CQL | 결과 | 해석 |
|----|-----|------|------|
| Q5 | `in=(tkachenko OR puech)` | 6586 | 발명자명 노이즈 대량 (동명이인/유사명) |
| Q5-정제 | `in=(tkachenko AND puech)` (AND 조합) | **1** | **FR3027430A1 = 2LQR 특허 확정** |
| Q6 | `pa=(CNRS OR "universite de montpellier" OR LIRMM) AND ti,ab=QR` | **0** | 2LQR 기관 출원인 + QR 직접 매치 없음 (2LQR 특허는 "QR" 대신 "code visuel graphique" 용어 사용) |
| Q7 | `ti,ab=("two-level QR" OR "2LQR" OR "two level QR")` | **0** | 2LQR 제목 키워드 직접 hit 없음 (동일 이유) |
| Q8 | `ti,ab=(QR AND (texture OR "print-and-scan" OR "P&S"))` | **1** | WO2023086506A2 (2LQR 기법 키워드, 별건) |

**결론**: Q5 정제로 **2LQR 특허 FR3027430A1 확정**. 공동출원인 CNRS + Univ. Montpellier 2 + Authentication Industries. QoverwRap 청구항은 **물리 인쇄 기반 2LQR과 기술 경로가 근본적으로 다르므로** 인용 가능성 제한적 (§3-2 비교표 참조).

### 6-4. 일본 특허 (J-PlatPat) — **완료 2026-04-22 via EPO OPS**

- **방법**: EPO OPS v3.2 — 4 쿼리 (Q9~Q12)
- **원본 결과**: `docs/research/epo-results-jp.json`

| ID | CQL | 결과 | 해석 |
|----|-----|------|------|
| Q9 | `pa=("denso wave" OR "denso corporation")` | 36770 | DENSO 전체 출원. 원천 QR 특허 대부분 만료 |
| Q9-정제 | `pa=("denso wave" OR "denso corporation") AND ti,ab=QR` | 3 | DE102016221500A1 (자동차 조향, "Qs" 변수명 오매칭) 등 — **DENSO WAVE 출원인은 pa 필드에 "denso wave" 문자열이 다르게 기록**됨. QR 특허는 EPO biblio 제한적 노출 |
| Q10 | `in=("masahiro hara")` | 26 | QR 원천 발명자 (Masahiro Hara) 26건 — 만료 특허군. 우리 청구항과 직접 경합 없음 |
| Q11 | `ti,ab=(QR AND (multi-layer OR multilayer OR "multiple layer"))` → JP 필터 | **0** | 다층 QR JP 타깃 직접 hit 없음 (전세계 1건도 JP 아님) |
| Q12 | `ti,ab=(QR AND (steganograph* OR "hidden data" OR payload))` → JP 필터 | **0** | JP 스테가노/페이로드 QR 직접 hit 없음 |

**결론**: 일본 쪽 핵심 리스크(다층/스테가노) **제로 hit**. DENSO/Masahiro Hara 원천 특허군은 만료되었고 청구항 방식이 다름. JP 쪽 잔여 리스크 **낮음**.

### 6-5. 관할 무관 보강 쿼리 — **완료 2026-04-22 via EPO OPS**

- **원본 결과**: `docs/research/epo-results-common.json`

| ID | CQL | 결과 | 해석 |
|----|-----|------|------|
| Q13 | `cpc=G06K19/06 AND ti,ab=(signature AND QR)` | **0** | 본 CQL의 정확 조합 직접 hit 없음. 다만 (마) 군 — SMART Health Cards, ICAO VDS, US20120308003A1, KR20180122843A 등 — 은 별도 검색에서 확인되므로 "QR + 서명 일반"의 선행기술은 존재 |
| Q14 | `ti,ab=(QR AND ed25519)` | **0** | ed25519 + QR 정확 조합 직접 hit 없음 (다만 알고리즘명 단일 hit는 신규성 근거로 약함) |
| Q15 | `ti,ab=(QR AND (delimiter OR "payload structur*"))` | **0** | 페이로드 구조화 키워드 직접 hit 없음 |

**결론 (재정의)**: 위 EPO OPS CQL의 직접 hit 부재 자체는 신규성의 핵심 근거가 아니다. (마) 군에 해당하는 선행기술 — barcode 또는 QR payload 에 digital signature 를 포함하여 인증하는 시스템 (예: US20120308003A1, KR20180122843A, SMART Health Cards, ICAO VDS) — 은 존재한다. 따라서 QoverwRap의 신규성·진보성 주장은 "QR + 서명 일반 개념"이 아니라, **Layer A 평문 prefix + delimiter-framed trailer + versioned binary header + Layer B/C 분리 + 검증 실패 시 Layer A 만 반환하는 safe-fallback resolver의 구체적 결합**에 둔다.

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
| 서명 방식 | URL+보안코드 대조 (서버 필요) | 페이로드 내부에 Ed25519 서명 내장 (온라인 서버 호출 없는 검증) |
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

QoverwRap의 핵심 기술 결합 — (i) 표준 QR 리더가 평문으로 표시하는 Layer A prefix + (ii) delimiter-framed trailer + (iii) versioned binary header + (iv) Layer B/C 분리 + (v) 검증 실패 시 Layer A 만 반환하는 safe-fallback resolver — 은 **학술 6건(국제) + KR 특허 4건 + EPO OPS 15 쿼리(CN/JP/EP/공통)** 통합 조사 결과 동일한 결합 형태를 **발견하지 못했다**. 다만 결합을 구성하는 개별 개념(QR + 서명, signed credential, multi-layer QR 등)은 별도 선행기술군에 존재한다.

- **국제 학술** (Liu/Tkachenko/Suresh/Arce/Koptyra/Subramanian): 스테가노그래피·물리·블록체인 접근만 존재
- **한국 특허** (넥스팟솔루션/ETRI·POSTECH/에이엠홀로/김동현): 물리 라벨 stack, 재료 공학, 홀로그램, 시각 overlay — **논리 레이어링 없음**
- **중국 특허** (EPO OPS 경유): CN111224771A(PCA+Henon 이미지 카오스 암호), CN115828975A(아트 QR hierarchical mask) 2건 — 모두 이미지 도메인
- **일본 특허** (EPO OPS 경유): DENSO/Masahiro Hara 원천 특허군(만료) 외 다층/스테가노 QR 직접 hit 없음
- **EP/FR 특허** (EPO OPS 경유): 2LQR 특허 FR3027430A1 확정 (물리 인쇄 기반)
- **(마) 서명-내장 자격증명/인증 QR** (별도 식별): SMART Health Cards (signed JWS + JWK set), ICAO VDS / VDS-NC (cryptographically signed digital seal), US20120308003A1 (signed barcode), KR20180122843A (QR 진본성 + 서명문 + 기관코드), SAP Mobile Services signed QR — 본 군은 전체 credential 또는 barcode message 를 단일 서명 객체로 취급하며, 본 발명의 wire-format 결합 및 safe-fallback resolver 정책을 명시하지 않음
- **관할 무관 보강 쿼리**: `QR + signature + G06K19/06` 등 일부 CQL은 0 hit이나, 위 (마) 군은 별도 경로로 식별됨. 따라서 0 hit 자체를 신규성의 핵심 근거로 사용하지 않음

**신규성 후보 (재정의):**

본 발명의 신규성·진보성은 다음 요소의 **구체적 결합** 에 둔다.

1. 표준 QR 리더의 판독 결과에서 선두 평문으로 표시되는 Layer A prefix
2. 미리 정해진 구획자 이후의 트레일러에 배치되는 versioned binary header (버전·길이 정보 포함)
3. 후속 계층 데이터 (예: 컨텍스트 메타데이터 Layer B + 디지털 서명 Layer C) 의 텍스트 안전 인코딩 결합
4. 동일 페이로드 내부의 정규화된 서명 대상에 대해 온라인 검증 서버 호출 없이 수행되는 디지털 서명 검증
5. 페이로드 파싱·헤더 검증·트레일러 디코딩·공개키 부재·서명 검증 실패 중 어느 하나라도 발생 시 Layer A 만 반환하는, 계층 구조와 결합된 반환 데이터 제한 정책 (단순 오류 처리와 구별)

**특허 명세서 전략:**
- 청구항은 "Layer A prefix + delimiter-framed trailer + versioned binary header + safe-fallback resolver" 의 결합을 핵심 구별 요소로 사용
- 독립항은 base64/Ed25519/구체 출력 수준 명칭에 고정하지 않고, 종속항에서 구체화 (claim differentiation)
- 비교군은 (가) 모듈 비트 스테가노그래피 / (나) 물리·시각 다층 / (다) 컬러·재료 채널 / (라) 외부 검증 시스템(블록체인·dedicated reader 포함) / (마) 서명-내장 자격증명/인증 QR 의 5군 체계로 제시

**조사 완료 상태 (2026-04-22)**: §6-1~§6-5 전 항목 완료. 2LQR 특허 FR3027430A1 확정. 추가 보완 검토 항목:
- CNIPA 직접 DB 교차 확인 (EPO biblio CN 커버리지 제한 리스크 헤지 — 출원 전 권장)
- J-PlatPat DENSO WAVE 출원인명 정확 표기 확인 (EPO biblio에서 QR 특허 노출 제한)

**(마)군 원문 인용 보강 (2026-04-30)**: §9 (3-11 ~ 3-16) 항목으로 SQRC, SHC, ICAO VDS, US20120308003A1, KR20180122843A, SAP signed QR 의 1차 출처·인용·QoverwRap 차별점 정리 완료.

---

## 9. (마)군 — 서명-내장 자격증명/인증 QR 원문 인용 보강

본 절은 §8 최종 결론에서 언급한 (마) 서명-내장 자격증명/인증 QR 군에 대한 1차 출처·인용·QoverwRap 차별점 정리이다. 본 군은 spec-draft.md §3.2의 (마)군 행 및 §10 신규성·진보성 매핑 표와 cross-reference된다. 모든 항목은 "QoverwRap이 본 선행기술과 어떻게 구별되는가"의 wire-format·정책 차별점에 초점을 맞춘다.

### 3-11. DENSO WAVE SQRC® (Secret-function-equipped QR Code)

| 항목 | 내용 |
|------|------|
| **출처 1** | DENSO WAVE 공식 제품 페이지 — https://www.denso-wave.com/en/system/qr/product/sqrc.html |
| **출처 2** | QRcode.com (DENSO WAVE 운영) — https://www.qrcode.com/en/codes/sqrc.html |
| **출처 3 (표준)** | ISO/IEC 18004:2024 — https://www.iso.org/standard/83389.html (SQRC 미등재 확인) |
| **유사도** | **매우 높음** — 가장 가까운 선행기술 |
| **핵심** | 단일 QR 코드에 public data + private data를 공존시키고, cryptographic key를 보유한 전용 리더만 private data를 판독할 수 있는 DENSO WAVE 독점 기술 |
| **기술 방식** | 표준 QR과 외형상 유사한 단일 코드 내에 public data 와 private data 를 공존시키고, cryptographic key 를 가진 dedicated reader 만 private data 를 판독하도록 하는 DENSO WAVE 독점 확장 기술로 설명됨 (구체적 데이터 배치 방식의 기술 가설은 footnote 참조) |
| **표준화 여부** | **ISO/IEC 18004 미등재** — DENSO WAVE 독점 확장 (SQRC® 등록상표). DENSO WAVE 의 표준 QR Code 특허 포기 선언은 표준화된 QR Code 에 한함 |

> **footnote (기술 가설)**: 일부 리버스 엔지니어링 분석 자료는 SQRC private data 가 QR terminator 이후 표준 패딩 바이트(`EC 11`) 영역에 암호화된 형태로 삽입되며, 표준 스캐너가 terminator 에서 판독을 종료함으로써 public 영역만 노출된다고 설명한다. 본 분석은 1차 출처 미확인 가설이므로 본 보고서의 결정적 차별 근거로 사용하지 않으며, 1차 차별 근거는 위 표의 "dedicated reader + cryptographic key 요건" 및 "ISO/IEC 18004 미등재" 사실에 둔다.

**직접 인용** (DENSO WAVE 공식 제품 페이지):

> "A single QR Code can carry public data and private data. The private data can be read only with a dedicated reader having the cryptographic key, which provides data protection."

**QoverwRap과의 차별점**:

| 비교 항목 | SQRC | QoverwRap |
|-----------|------|-----------|
| private 영역 위치 | QR terminator **이후** 패딩 자리 (표준 데이터 영역 외부) | QR 표준 데이터 필드 **내부** delimiter 이후 base64 트레일러 |
| ISO/IEC 18004 적합성 | 표준 외 독점 확장 | 표준 데이터 필드 안에서 동작 |
| private 접근 조건 | 키 보유 전용 하드웨어/SDK 필수 (암호학적 판독 제한) | 표준 리더로 raw payload 전체 취득 가능; 출력 정책은 검증 결과 기반 |
| 무결성 보장 | 없음 (복호화 성공이 진위 판단의 전부) | 디지털 서명 + safe-fallback 강등 |
| 레이어 수 | 2 (public / private) | 3 (Layer A / B / C) |

### 3-12. SMART Health Cards (SHC) — VCI / HL7 FHIR Implementation Guide

| 항목 | 내용 |
|------|------|
| **출처** | https://spec.smarthealth.cards/ — Vaccine Credential Initiative / HL7 FHIR IG |
| **인용 섹션** | `#health-cards-as-qr-codes`, `#signing-health-cards`, `#determining-keys-associated-with-an-issuer` |
| **유사도** | **중간** — "QR로 표현되는 signed credential" 범주에서 직접 비교 대상 |
| **QR 인코딩** | `shc:/` IANA 스킴 prefix + JWS 문자열 각 문자를 `ord(c)−45` 2자리로 변환한 numeric-mode 시퀀스 |
| **서명 알고리즘** | ECDSA P-256 / **ES256**, JWS compact serialization. payload는 DEFLATE 압축 후 서명. JWS header: `alg:"ES256"`, `zip:"DEF"`, `kid`=base64url(SHA-256 JWK Thumbprint) |
| **공개키 배포** | issuer JWK Set을 `<<iss>>/.well-known/jwks.json` 에서 배포 (CORS + TLS 1.2+ 필수). verifier는 사전 다운로드·캐싱으로 오프라인 검증 가능 |

**직접 인용** (spec.smarthealth.cards, §"Health Cards as QR Codes"):

> "Each character of the JWS is converted to a number by subtracting 45 from the character's ordinal value."

**직접 인용** (§"Signing Health Cards"):

> "payload is minified ... and compressed with the DEFLATE ... algorithm before being signed."

**직접 인용** (§"Determining Keys"):

> "anyone can issue Health Cards, and every verifier can make its own decision about which issuers to trust."

**QoverwRap과의 차별점**:

| 비교 항목 | SMART Health Cards | QoverwRap |
|-----------|--------------------|-----------|
| Wire format | `shc:/` prefix + numeric-mode JWS compact serialization (단일 서명 객체) | Layer A 평문 prefix + delimiter + base64(binary header + B + C) — public prefix + delimiter-framed trailer 결합 |
| 공개 텍스트 접근 | 없음 — 표준 QR 리더 출력은 numeric-encoded JWS (사람이 읽을 수 없는 숫자열) | Layer A가 표준 QR 리더 출력 선두에 평문으로 즉시 표시 |
| 공개키 요구사항 | issuer 별 `/.well-known/jwks.json` fetch 또는 사전 registry 필요 | 사전 보유 또는 외부 입력 공개키 — issuer registry 불필요 |
| 미지 issuer 처리 | verifier 정책에 따라 거부 | safe-fallback: 키 부재 / 검증 실패 시 Layer A만 반환 |
| 레이어 구조 | 단일 서명 객체 (multi-layer 없음) | Layer A / B / C 독립 분리 |

### 3-13. ICAO Visible Digital Seal (VDS / VDS-NC) — Doc 9303 Part 13 / ISO 22376:2023

| 항목 | 내용 |
|------|------|
| **출처 1** | ICAO Doc 9303 Part 13 *Visible Digital Seals* (2021, 8th ed., 무료 공개) — https://www.icao.int/sites/default/files/publications/DocSeries/9303_p13_cons_en.pdf |
| **출처 2** | ISO 22376:2023 *Security and resilience — Specification and usage of visible digital seal (VDS) data format* — https://www.iso.org/standard/50278.html |
| **출처 3** | BSI TR-03137 Part 1 (encoding reference) — VDS C40/TLV 인코딩 기반 |
| **VDS-NC 가이드** | https://www.icao.int/secretariat/TechnicalCooperation/Pages/VDS-NC-iPACK.aspx |
| **유사도** | **중간** — 단일 2D 바코드 내 서명 내장 목표는 동일하나 wire format / 레이어 분리 방식 근본 차이 |
| **데이터 구조** | **Header Zone** (발급 국가코드, Signer Identifier, Certificate Reference, 발급일·서명일) + **Message Zone** (C40/MRZ/UTF-8/BYTE TLV 인코딩) + **Signature Zone** (raw r‖s ECDSA 서명값) |
| **서명 알고리즘** | ECDSA over Brainpool curves (brainpoolP224r1 / brainpoolP256r1); 서명값은 raw r‖s 바이트열 (ASN.1/DER 아님) |
| **신뢰 체인** | CSCA(Country Signing CA) → DSC(Document Signer Certificate). 검증 키는 ICAO PKD 등 외부 디렉터리에서 사전 취득. 바코드 내부에 공개키 자체는 미포함, Certificate Reference만 포함 |
| **바코드 심볼** | 기본 DataMatrix (ISO/IEC 16022); 비-제약(non-constrained, VDS-NC) 환경에서는 QR도 허용 |

**QoverwRap과의 차별점**:

| 비교 항목 | ICAO VDS / VDS-NC | QoverwRap |
|-----------|-------------------|-----------|
| Wire format | 전체 payload를 단일 바이너리 객체(Header+Message+Signature)로 취급; 평문 텍스트 prefix 없음 | Layer A 평문 prefix + delimiter + base64(B+C); Layer A는 표준 QR 리더 출력에 사람이 읽을 수 있는 텍스트로 표시 |
| 표준 QR 리더 출력 | 불투명한 바이너리 blob | Layer A가 URL·제목 등 인간 가독 텍스트로 즉시 표시 |
| 공개키 배포 | CSCA→DSC 인증서 체인 + ICAO PKD 등 외부 디렉터리; verifier 앱의 사전 trust store 필요 | 공개키 사전 보유 또는 외부 입력; 온라인 검증 서버·블록체인 조회 불필요 |
| 검증 실패 처리 | 검증 실패 시 문서 거부 (단일 계층) | 서명 검증 실패 시 Layer A만 반환하는 안전 강등 |
| 바코드 심볼 결정 | DataMatrix 우선; QR는 VDS-NC에서만 허용 | QR code 전용 (ISO/IEC 18004 준수) |

### 3-14. Mukherjee / VeriSign (2012) — Barcodes Using Digital Signatures (US20120308003A1)

| 항목 | 내용 |
|------|------|
| **출처** | Google Patents — https://patents.google.com/patent/US20120308003A1 |
| **출원인/양수인** | VeriSign, Inc. |
| **발명자** | Anirban Mukherjee |
| **출원일 / 공개일** | 2011-05-31 / 2012-12-06 (출원 단계 공개, A1) |
| **유사도** | **중간** — barcode + 디지털 서명의 결합을 명시한 미국 출원 (등록 여부 무관, 35 USC §102 prior art 적격) |

**Abstract (원문)**:

> "Methods and systems for generating and authenticating barcodes using digital signatures comprise: inputting graphical data representing a barcode pattern into memory; translating the graphical data into barcode information according to a standard for translating a particular type of barcode pattern into barcode information; extracting a message and a digital signature from the barcode information; and determining whether the message is authentic by determining whether the digital signature matches the message."

**Claim 1 (원문)**:

> "A computer-implemented method of verifying the authenticity of a barcode, comprising: inputting graphical data representing a barcode pattern into memory; translating the graphical data into barcode information according to a standard for translating a particular type of barcode pattern into barcode information; extracting a message and a digital signature from the barcode information; and determining whether the message is authentic by determining whether the digital signature matches the message."

**QoverwRap과의 차별점**:

| 비교 항목 | US20120308003A1 | QoverwRap |
|-----------|-----------------|-----------|
| 서명 결합 방식 | barcode 페이로드 전체를 단일 message로 취급, message + signature 추출 (wire-format 결합 구조 미명시) | Layer A prefix + delimiter-framed trailer + versioned binary header로 구획; 서명 대상(Layer B+C)과 공개 텍스트(Layer A) 구조적 분리 |
| 공개/비공개 레이어 분리 | 없음 — message/signature를 동일 평면 두 필드로 취급 | Layer A(표준 리더 표시) / Layer B·C(delimiter 이후 trailer) 명시적 2-계층 |
| delimiter-framed trailer | 명시 없음 | 핵심 구성 요소 (`---QWR---` 구획자 + base64 인코딩 trailer) |
| safe-fallback resolver | 명시 없음 | 파싱·헤더·트레일러·공개키·서명 검증 실패 시 Layer A 만 반환하는 정책 |
| 표준 스캐너 호환 | 처리 결과에 대한 명시 없음 | Layer A가 표준 QR 리더 출력 선두 평문으로 표시됨 보장 |

### 3-15. 라온시큐어 (KR20180122843A, 2018 공개, **거절**) — QR 진본성 + 서명문 + 기관코드

| 항목 | 내용 |
|------|------|
| **출처** | Google Patents — https://patents.google.com/patent/KR20180122843A |
| **출원인** | 라온시큐어(주) (Raon Secure Co., Ltd.) |
| **발명자** | 김태윤, 용상운 |
| **출원일 / 공개일** | 2017-05-04 / 2018-11-14 |
| **등록 상태** | **거절 (Ceased)** — 단, 공개공보(KR-A)는 prior art로 유효 |
| **유사도** | **높음 (한국 출원인 입장 (마)군 최근접)** |
| **핵심** | 기관 개인키로 서명한 서명문과 기관코드를 QR 페이로드에 포함. 검증 시 외부 **공개키검증서버**에 조회하여 공개키 무결성 확인 후 서명 검증 |

**청구항 1 요지** (Google Patents, 단락 [0031]–[0037]):

> 기관서버가 기관코드와 공개키를 해시하고 기관 개인키로 서명한 서명문을 QR 데이터에 삽입 → QR 클라이언트가 서명문·기관코드를 파싱 → **공개키검증서버**가 수신 공개키와 등록 공개키를 비교하여 확인 → QR 클라이언트가 검증된 공개키로 서명 검증.

**QoverwRap과의 차별점**:

| 비교 항목 | KR20180122843A | QoverwRap |
|-----------|----------------|-----------|
| 서명 포함 위치 | QR 데이터 필드 내 서명문 포함 (직렬화 방식 미명시) | payload-level wire format: delimiter + base64 binary trailer 명시 |
| 검증 아키텍처 | **외부 공개키검증서버 네트워크 호출 필수** (청구항 1(d)단계) | **온라인 서버 호출 없이 검증** — 공개키 사전 보유 또는 외부 입력만 필요 |
| Wire format | 규정 없음 (서명문·기관코드 포함 방식 미명시) | `[Layer A]\n---QWR---\n[base64 binary header+B+C]` 명시적 규정 |
| 표준 스캐너 호환 | 언급 없음 | Layer A가 표준 QR 리더에 평문 표시; trailer는 non-breaking |
| 안전 강등 정책 | 없음 | 파싱·서명 실패 시 Layer A만 반환 |
| 다계층 출력 정책 | 없음 | 제1/제2/제3 출력 수준 매개변수 |

**포지셔닝 메모**: 본 KR 출원은 **(마)군 + (라)군 경계**에 위치한다. QR 페이로드에 서명문을 포함한다는 점((마)군 방향)은 본 발명에 가장 근접하나, 검증을 위해 외부 공개키검증서버 호출을 필수로 한다는 점에서 (라)군(외부 검증 시스템 의존형) 특성도 공유한다. QoverwRap의 핵심 청구 포인트인 (i) delimiter-framed wire format, (ii) 온라인 서버 호출 없는 서명 검증, (iii) safe-fallback resolver 정책은 본 KR 출원에 개시되지 않는다.

### 3-16. SAP Mobile Services — Digitally Signed QR Codes (산업 구현체)

| 항목 | 내용 |
|------|------|
| **출처 1 (iOS 가이드)** | https://help.sap.com/doc/f53c64b93e5140918d676b927a3cd65b/Cloud/en-US/docs-en/guides/features/security/ios/digitally-signed-qr-code.html (2022-09-27) |
| **출처 2 (MDK 가이드)** | https://help.sap.com/doc/f53c64b93e5140918d676b927a3cd65b/Cloud/en-US/docs-en/guides/features/security/mdk/signed-qr.html (2024-04-12) |
| **출처 3 (Help Portal)** | https://help.sap.com/docs/mobile-services/mobile-services-cloud-foundry/configuring-digitally-signed-qr-codes (canonical short URL) |
| **유사도** | (마)군 산업 구현체 — 학술/특허 대비 prior art 무게는 약하나 결합 차별성 비교에 포함 |
| **서명 알고리즘** | RSA(RS256/RS384/RS512, 2048/3072/4096-bit) 또는 EC(ES256/ES384/ES512, 256/384/521-bit). 키 형식: PKCS#8 PEM unencrypted |
| **페이로드 형태** | 스캔 결과 = JWS 문자열 (compact serialization 추정; 직렬화 세부 구조 문서 미공개) |
| **공개키 배포** | 앱 번들에 `SignedQRCodePublicKey.pem` 파일로 사전 내장 (iOS: `AppParameters.plist`; Android: `App_Resources/Android/.../assets`). 런타임 온라인 조회 없음 |

**직접 인용** (SAP Mobile Services iOS Guide, §"Digitally Signed QR Codes"):

> "When the SDK scans a signed QR code, the result is a JWS string, and the digital signature on the JWS string is verified first."

**QoverwRap과의 차별점**:

| 비교 항목 | SAP Signed QR | QoverwRap |
|-----------|--------------|-----------|
| 페이로드 wire format | QR 전체를 단일 JWS 객체로 취급. Layer A 평문 prefix + delimiter-framed trailer 결합 구조 미명시 | `[Layer A 평문]\n---QWR---\n[base64(header+B+C)]` 명시적 결합 |
| 표준 스캐너 safe-fallback | 문서 미언급 (QR 전체가 JWS string → 표준 리더에 불투명) | 파싱·서명 실패 시 Layer A만 반환하는 안전 강등 정책 |
| Resolver 출력 정책 | 없음 (인증 성공/실패 이진) | 검증 결과 기반 3단계 출력 수준 (제1/제2/제3) |
| 온라인 서버 의존 | 없음 (앱 내 공개키) | 없음 (동일) |

---

### §9 통합 메모

위 6개 항목 (3-11 ~ 3-16) 은 spec-draft.md §3.2 (마)군 행 및 §10 신규성·진보성 매핑 표에서 cross-reference된다. 6개 항목 모두 "단일 객체로 전체 message에 서명" 또는 "외부 키/서버 의존" 패턴이며, **Layer A 평문 prefix + delimiter-framed trailer + versioned binary header + safe-fallback resolver의 결합** 을 명시한 선행기술은 §9 범위 내에서 발견되지 않는다.
