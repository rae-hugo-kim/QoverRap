# QoverwRap 시연용 웹 앱 구현 계획

**목적**: 특허 심사관 제출용 3-layer QR 기술 시연 앱
**스택**: React (Vite + TypeScript) + FastAPI (Python)
**기간**: 1-2주

---

## 1. 요구사항 요약

### 핵심 시연 플로우 (심사관이 따라갈 스토리)
```
키 생성 → 레이어 입력 → 서명 → QR 생성 → 카메라 스캔 → 접근레벨별 결과 비교
```

### 기능 요구사항
| ID | 기능 | 설명 |
|----|------|------|
| F-1 | 키 생성 | Ed25519 키쌍 생성, 공개키/비밀키 표시 |
| F-2 | 레이어 입력 | Layer A (텍스트), Layer B (바이너리/텍스트), 자동 서명(Layer C) |
| F-3 | QR 생성 | 3-layer 인코딩 → QR 이미지 생성 + 화면 표시 |
| F-4 | 카메라 스캔 | 모바일/데스크탑 브라우저에서 카메라로 QR 스캔 |
| F-5 | 디코딩 결과 | Layer A/B/C 각각 분리 표시 |
| F-6 | 접근레벨 시연 | 동일 QR을 public/authenticated/verified로 해석, 차이 시각화 |
| F-7 | 서명 검증 | Layer C 서명 검증 결과 표시 (valid/invalid + 위변조 감지) |

### 비기능 요구사항
| ID | 항목 | 기준 |
|----|------|------|
| NF-1 | HTTPS | 카메라 접근을 위해 필수 (self-signed 또는 Let's Encrypt) |
| NF-2 | 반응형 | 모바일 브라우저에서 PWA 전체화면 모드 지원 |
| NF-3 | 스크린샷 품질 | 특허 제출용 — 깔끔한 UI, 각 단계가 명확히 구분 |
| NF-4 | 코드 동일성 | Python 코어 포팅 없이 API 래핑으로 재사용 |

---

## 2. 아키텍처

```
┌─────────────────────────────────────┐
│  Frontend (Vite + React + TS)       │
│  - html5-qrcode (카메라 스캔)        │
│  - Tailwind CSS (스타일링)           │
│  - PWA manifest (전체화면 모드)       │
│                                     │
│  Port: 5173 (dev) / 3000 (prod)     │
└──────────────┬──────────────────────┘
               │ REST API (JSON)
               │
┌──────────────▼──────────────────────┐
│  Backend (FastAPI + Uvicorn)        │
│  - src/qoverwrap/ 직접 import       │
│  - QR 이미지 생성 (qrcode + Pillow) │
│  - CORS 허용                        │
│                                     │
│  Port: 8000                         │
└─────────────────────────────────────┘
```

### 디렉토리 구조
```
demo/
├── backend/
│   ├── main.py                 # FastAPI app + CORS + lifespan
│   ├── routers/
│   │   ├── encode.py           # POST /api/encode, POST /api/qr-image
│   │   ├── decode.py           # POST /api/decode
│   │   ├── resolve.py          # POST /api/resolve
│   │   └── crypto.py           # POST /api/generate-key, /api/sign, /api/verify
│   ├── schemas.py              # Pydantic request/response 모델
│   └── requirements.txt        # fastapi, uvicorn, python-multipart
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # 메인 레이아웃 + 스텝 네비게이션
│   │   ├── components/
│   │   │   ├── StepNav.tsx         # 스텝 진행 표시기
│   │   │   ├── KeyGenerator.tsx    # F-1: 키 생성 UI
│   │   │   ├── LayerInput.tsx      # F-2: 레이어 입력 폼
│   │   │   ├── QRDisplay.tsx       # F-3: QR 이미지 표시
│   │   │   ├── QRScanner.tsx       # F-4: 카메라 스캔
│   │   │   ├── DecodeResult.tsx    # F-5: 디코딩 결과
│   │   │   ├── AccessLevelDemo.tsx # F-6: 접근레벨 비교
│   │   │   └── VerifyBadge.tsx     # F-7: 서명 검증 배지
│   │   ├── api/
│   │   │   └── client.ts          # fetch 래퍼
│   │   ├── types.ts               # 공유 타입 정의
│   │   └── main.tsx
│   ├── public/
│   │   ├── manifest.json          # PWA 매니페스트
│   │   └── icons/                 # 앱 아이콘
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts             # proxy: /api → localhost:8000
│
└── README.md                       # 실행 방법
```

---

## 3. API 설계

### 엔드포인트

| Method | Path | Request | Response | 래핑 대상 |
|--------|------|---------|----------|-----------|
| POST | `/api/generate-key` | `{}` | `{private_key: hex, public_key: hex}` | `crypto.generate_keypair()` |
| POST | `/api/sign` | `{private_key, layer_a, layer_b}` | `{signature: hex}` | `crypto.sign_layers()` |
| POST | `/api/encode` | `{layer_a, layer_b?, layer_c?}` | `{encoded: str}` | `encoder.encode_layers()` |
| POST | `/api/qr-image` | `{encoded: str, size?: int}` | `{image: base64_png}` | `qrcode.make()` |
| POST | `/api/decode` | `{payload: str}` | `{layer_a, layer_b: hex, layer_c: hex}` | `decoder.decode_layers()` |
| POST | `/api/resolve` | `{payload, access_level, public_key?}` | `{layer_a, layer_b?, layer_c?, verified}` | `resolver.resolve()` |
| POST | `/api/verify` | `{public_key, layer_a, layer_b, signature}` | `{valid: bool}` | `crypto.verify_signature()` |
| GET | `/api/health` | — | `{status: "ok"}` | — |

### 설계 원칙
- 모든 바이너리 데이터는 **hex 문자열**로 직렬화 (base64보다 직관적, 심사관이 읽기 쉬움)
- 에러는 HTTP 422 + `{detail: str}` 형태로 반환
- CORS: 프론트엔드 origin 허용

---

## 4. 프론트엔드 화면 설계

### 스텝 기반 위저드 플로우 (6단계)

**Step 1 — 키 생성**
- [생성] 버튼 → Ed25519 키쌍 생성
- 공개키/비밀키를 hex로 표시 (복사 가능)
- 키가 세션에 저장됨을 안내

**Step 2 — 레이어 입력**
- Layer A: 텍스트 입력 (예: "QoverwRap Demo - Public Message")
- Layer B: 텍스트 입력 → UTF-8 인코딩 (예: `{"context":"authenticated","timestamp":"..."}`)
- Layer C: 자동 서명 (Step 1의 비밀키로 sign_layers 호출)
- 각 레이어에 색상 구분 (A=파랑, B=주황, C=초록)

**Step 3 — QR 코드 생성**
- encode_layers() → QR 이미지 표시
- 인코딩된 원문 텍스트도 접을 수 있는 패널로 표시
- [다운로드] 버튼 (PNG)

**Step 4 — QR 스캔**
- 카메라 활성화 (html5-qrcode)
- 스캔 성공 시 raw payload 표시
- 또는 [직접 입력] 탭 (카메라 없는 환경 대응)

**Step 5 — 접근레벨별 결과 비교**
- 3-column 레이아웃: Public | Authenticated | Verified
- 각 컬럼에서 보이는 레이어가 다름을 시각적으로 강조
- 가려진 레이어는 잠금 아이콘 + 흐릿한 표시
- Verified 컬럼에 서명 검증 배지 (✓ Valid / ✗ Invalid)

**Step 6 — 위변조 감지 시연**
- Layer A 또는 B를 의도적으로 변조하는 버튼
- 변조 후 재검증 → Invalid 결과 표시
- 원본과 변조본의 차이를 diff 형태로 시각화

### UI 스타일
- Tailwind CSS: 미니멀, 깔끔한 디자인
- 색상 팔레트: 흰 배경 + 강조색 (레이어별 구분)
- 폰트: 시스템 폰트 스택 (모노스페이스는 코드/키 표시에만)
- PWA 전체화면: 주소창 없이 앱 느낌

---

## 5. 수용 기준 (Acceptance Criteria)

| ID | 기준 | 검증 방법 |
|----|------|-----------|
| AC-1 | 키 생성 후 공개키/비밀키가 각각 32바이트(64 hex chars)로 표시된다 | UI에서 길이 확인 |
| AC-2 | Layer A/B 입력 후 서명이 자동 생성되어 64바이트(128 hex chars)로 표시된다 | UI에서 길이 확인 |
| AC-3 | 인코딩된 QR 코드가 화면에 표시되고 PNG로 다운로드 가능하다 | QR 이미지 렌더링 + 다운로드 테스트 |
| AC-4 | 모바일 브라우저에서 카메라로 QR 코드를 스캔할 수 있다 | Android Chrome + iOS Safari 테스트 |
| AC-5 | 스캔 결과가 decode_layers()로 정확히 3-layer 분리된다 | 원본 입력값과 디코딩 결과 비교 |
| AC-6 | public 레벨에서 Layer A만 표시, B/C는 숨겨진다 | UI에서 잠금 아이콘 확인 |
| AC-7 | authenticated 레벨에서 Layer A+B 표시, C는 숨겨진다 | UI에서 레이어 표시 확인 |
| AC-8 | verified 레벨에서 Layer A+B+C 표시 + 서명 검증 "Valid" 표시 | 녹색 배지 확인 |
| AC-9 | 레이어 위변조 후 서명 검증이 "Invalid"로 변경된다 | 빨간 배지 확인 |
| AC-10 | PWA 전체화면 모드에서 주소창 없이 앱 형태로 표시된다 | 모바일 홈 화면 추가 후 확인 |

---

## 6. 구현 단계 (스프린트)

### Sprint 1: 백엔드 API (2-3일)

| 순서 | 작업 | 파일 | 의존성 |
|------|------|------|--------|
| 1-1 | FastAPI 프로젝트 세팅 + health 엔드포인트 | `demo/backend/main.py` | — |
| 1-2 | Pydantic 스키마 정의 | `demo/backend/schemas.py` | — |
| 1-3 | `/api/generate-key` 라우터 | `demo/backend/routers/crypto.py` | `src/qoverwrap/crypto.py` |
| 1-4 | `/api/sign`, `/api/verify` 라우터 | `demo/backend/routers/crypto.py` | `src/qoverwrap/crypto.py` |
| 1-5 | `/api/encode`, `/api/qr-image` 라우터 | `demo/backend/routers/encode.py` | `src/qoverwrap/encoder.py` |
| 1-6 | `/api/decode` 라우터 | `demo/backend/routers/decode.py` | `src/qoverwrap/decoder.py` |
| 1-7 | `/api/resolve` 라우터 | `demo/backend/routers/resolve.py` | `src/qoverwrap/resolver.py` |
| 1-8 | API 통합 테스트 (pytest + httpx) | `tests/demo/test_api.py` | 1-1~1-7 |

### Sprint 2: 프론트엔드 기본 구조 (2-3일)

| 순서 | 작업 | 파일 | 의존성 |
|------|------|------|--------|
| 2-1 | Vite + React + TS + Tailwind 프로젝트 세팅 | `demo/frontend/` | — |
| 2-2 | API 클라이언트 + 타입 정의 | `demo/frontend/src/api/client.ts`, `types.ts` | — |
| 2-3 | 스텝 네비게이션 레이아웃 | `App.tsx`, `StepNav.tsx` | — |
| 2-4 | Step 1: KeyGenerator 컴포넌트 | `KeyGenerator.tsx` | 2-2 |
| 2-5 | Step 2: LayerInput 컴포넌트 | `LayerInput.tsx` | 2-2 |
| 2-6 | Step 3: QRDisplay 컴포넌트 | `QRDisplay.tsx` | 2-2 |

### Sprint 3: 스캔 + 검증 (2-3일)

| 순서 | 작업 | 파일 | 의존성 |
|------|------|------|--------|
| 3-1 | Step 4: QRScanner (html5-qrcode 통합) | `QRScanner.tsx` | html5-qrcode |
| 3-2 | Step 5: AccessLevelDemo (3-column 비교) | `AccessLevelDemo.tsx` | 2-2 |
| 3-3 | Step 6: 위변조 감지 시연 | `AccessLevelDemo.tsx` 확장 | 3-2 |
| 3-4 | VerifyBadge 컴포넌트 | `VerifyBadge.tsx` | — |
| 3-5 | DecodeResult 컴포넌트 | `DecodeResult.tsx` | — |

### Sprint 4: 마감 + 배포 (2-3일)

| 순서 | 작업 | 파일 | 의존성 |
|------|------|------|--------|
| 4-1 | PWA 매니페스트 + 아이콘 | `manifest.json`, `icons/` | — |
| 4-2 | 반응형 레이아웃 점검 (모바일) | 전체 컴포넌트 | — |
| 4-3 | HTTPS 설정 (홈서버 배포) | nginx/caddy 설정 | — |
| 4-4 | 모바일 실기기 카메라 스캔 테스트 | — | 4-3 |
| 4-5 | 특허 제출용 스크린샷 촬영 | — | 4-4 |
| 4-6 | README 작성 (실행 방법) | `demo/README.md` | — |

---

## 7. 기술 선택 근거

| 선택 | 대안 | 근거 |
|------|------|------|
| **Vite + React** | Next.js, SvelteKit | SPA로 충분, SSR 불필요. Vite가 DX 최고 |
| **FastAPI** | Flask, Django | 자동 OpenAPI 문서, async 지원, Pydantic 통합. 코어 래핑에 최적 |
| **html5-qrcode** | jsQR, zxing-wasm | 카메라 권한/UI 처리 내장, 가장 성숙한 라이브러리 |
| **Tailwind CSS** | CSS Modules, styled-components | 빠른 프로토타이핑, 일관된 디자인, 번들 최적화 |
| **hex 직렬화** | base64 | 심사관이 바이너리 데이터 길이/형태를 직관적으로 확인 가능 |
| **DB 없음** | SQLite | 세션 내 상태만 필요, 영구 저장 불필요 |

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 확률 | 대응 |
|--------|------|------|------|
| 웹 카메라 QR 인식률 낮음 | AC-4 실패 | 낮음 | html5-qrcode 대신 네이티브 `BarcodeDetector` API 시도 (Chrome 지원). 최악의 경우 이미지 업로드 폴백 |
| iOS Safari 카메라 권한 문제 | AC-4 부분 실패 | 중간 | HTTPS 필수 + `playsinline` 속성. iOS 15+ 에서는 안정적 |
| self-signed HTTPS에서 카메라 차단 | AC-4 실패 | 중간 | Let's Encrypt 무료 인증서 사용 (홈서버 도메인 필요) 또는 ngrok 터널 |
| QR 페이로드가 너무 커서 스캔 실패 | AC-3, AC-4 실패 | 낮음 | Layer B 크기 제한 (256바이트 이하 권장). 이미 encoder에서 65535바이트 제한 있음 |
| Python 코어 import 경로 문제 | 백엔드 시작 실패 | 낮음 | pyproject.toml에서 `packages` 설정 또는 PYTHONPATH 지정 |

---

## 9. 검증 계획

### 자동화 테스트
- **백엔드 API 테스트**: `pytest` + `httpx.AsyncClient` — 각 엔드포인트 roundtrip 검증
- **프론트엔드**: TypeScript 타입 체크 (`tsc --noEmit`)

### 수동 검증
- **데스크탑 브라우저**: Chrome에서 전체 플로우 (Step 1→6) 수행
- **모바일 (Android)**: Chrome에서 카메라 스캔 + PWA 전체화면
- **모바일 (iOS)**: Safari에서 카메라 스캔 + 홈 화면 추가
- **스크린샷**: 각 Step별 모바일 스크린샷 촬영 → 특허 도면 후보

### 검증 체크리스트
- [ ] `pytest tests/demo/` 전체 통과
- [ ] 데스크탑 Chrome에서 Step 1→6 완주
- [ ] Android Chrome에서 카메라 스캔 성공
- [ ] iOS Safari에서 카메라 스캔 성공
- [ ] PWA 전체화면 모드에서 앱 형태 확인
- [ ] 위변조 시연에서 Invalid 배지 정상 표시
- [ ] 3-column 접근레벨 비교가 시각적으로 명확
