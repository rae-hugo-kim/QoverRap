# QoverwRap 시연 앱

3-layer QR 페이로드 + 내장 Ed25519 서명 + 발급자 라우팅을 화면으로 보여주기 위한 데모 웹 앱입니다.

> **특허 청구 대상은 코어** (`src/qoverwrap/`) 입니다. 이 데모 앱의 트러스트 레지스트리·발급자 라우팅·UI 테마는 *응용 레이어*이며 청구항 외부입니다.

## 구조

```
demo/
├── backend/                FastAPI 래퍼 (코어를 직접 import)
│   ├── main.py
│   ├── schemas.py
│   ├── trust_registry.py   응용 레이어: 발급자 → 공개키 + 테마
│   ├── routers/
│   │   ├── crypto.py       /api/generate-key, /api/sign, /api/verify
│   │   ├── encode.py       /api/encode, /api/qr-image
│   │   ├── decode.py       /api/decode
│   │   ├── resolve.py      /api/resolve  (자동 발급자 키 라우팅 포함)
│   │   └── trust.py        /api/trust, /api/trust/{id}/sign
│   └── requirements.txt
└── frontend/               Vite + React + TS + Tailwind
    └── src/
        ├── App.tsx
        ├── api/client.ts
        ├── types.ts
        └── components/{StepNav,IssuerPicker,QRPanel,QRScanner,ResolveColumn}.tsx
```

## 실행 (개발 모드)

### 1. 백엔드

루트에서 (가상환경 활성 상태):

```bash
.venv/bin/pip install -r demo/backend/requirements.txt
.venv/bin/uvicorn demo.backend.main:app --reload --port 8000
```

확인:

```bash
curl http://127.0.0.1:8000/api/health     # {"status":"ok"}
curl http://127.0.0.1:8000/api/trust       # 발급자 3종
```

### 2. 프론트엔드

```bash
cd demo/frontend
npm install        # 최초 1회
npm run dev        # http://localhost:5173
```

`vite.config.ts`에 `/api` → `http://localhost:8000` 프록시가 설정되어 있어
프론트엔드는 그냥 `/api/...`로 요청합니다.

## 시연 흐름

1. **발급자 선택** — Tigers / Violet Fandom / Comic Con 중 1개 선택. 색·로고는 응용 레이어, 동시에 검증에 쓰일 공개키를 결정함.
2. **레이어 입력** — Layer A 메시지 + Layer B JSON. (Layer C는 백엔드에서 발급자 키로 자동 서명)
3. **QR 생성** — 하나의 QR. 상단 토글로 **Bare ↔ Themed** 표시 전환. *데이터는 두 모드에서 100% 동일.*
4. **스캔** — 카메라 (HTTPS 환경 권장) 또는 직접 페이로드 붙여넣기. 같은 페이지의 "지금 만든 QR 바로 해석" 버튼으로 카메라 없이도 확인 가능.
5. **3-레벨 해석** — 같은 페이로드를 Public / Authenticated / Verified로 해석. 각 레벨에서 보이는 레이어가 다름. 위변조 시연 토글로 Verified→INVALID 강등 확인.

## 테스트

백엔드 통합 테스트 (FastAPI TestClient):

```bash
.venv/bin/python -m pytest tests/demo/test_api.py -v
```

12개 엔드포인트 시나리오:

- 헬스, 키 생성 모양 (Ed25519 32B/32B)
- sign/verify roundtrip + 변조 검출
- encode/decode roundtrip
- QR PNG 생성 (PNG 매직바이트)
- public/authenticated/verified 노출 정책
- **트러스트 라우팅** (공개키 미입력 + Verified 통과)
- **변조 후 안전 강등** (서명 실패 → public)
- 미등록 발급자 처리
- hex 입력 검증 (422)

## 청구항 vs 응용 분리 (UI에서도 명시)

| 영역 | 청구항 안 | 응용 레이어 |
|------|-----------|-------------|
| 페이로드 구조 (delimiter + base64 header) | ✅ | |
| Ed25519 내장 서명 | ✅ | |
| 역할 기반 Resolver (안전 강등) | ✅ | |
| 발급자 ID 컨벤션 (`qwr:<id>\|<msg>`) | | ✅ |
| 트러스트 레지스트리 | | ✅ |
| Themed QR 카드, 색·로고 | | ✅ |

App 푸터에 동일 라벨링이 노출됩니다.

## 보안 / 데모 한정 주의

- `trust_registry.py`는 프로세스 시작 시 발급자 비밀키를 메모리에 생성해 보관합니다. 데모 편의용이며, 실제 서비스는 *발급자만* 비밀키를 보유해야 합니다.
- `/api/trust/{id}/sign`은 데모 편의 엔드포인트입니다. 운영 환경에서는 노출하지 마십시오.
- CORS는 `*`로 열려 있습니다. 운영 환경에서는 origin을 좁히십시오.
