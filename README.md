# QoverwRap

표준 QR 코드 **데이터 문자열** 안에서, 선두 평문(Layer A)과 **구획자 + base64(이진 헤더 + Layer B + 서명 Layer C)** 를 결합한 **페이로드 레벨** wire format 과, 출력 정책에 따른 **safe-fallback resolver** 를 제공하는 PoC 저장소입니다.

Python 패키지 디렉터리명은 `qoverwrap` 입니다.

## 핵심 아이디어

```
[Layer A — UTF-8 평문]
\n---QWR---\n
base64( [1B version][2B b_len BE][2B c_len BE][Layer B][Layer C 서명] )
```

- **단순 모드**: Layer B·C가 모두 비면 구획자와 트레일러 없이 Layer A만 사용합니다.
- **서명**: §8.1.1에 맞는 canonical 메시지(`QWR1`||version||len(A)||A||len(B)||B)에 대해 Ed25519로 서명합니다.
- **Resolver**: `public` / `authenticated`(파싱된 메타데이터, 미검증) / `verified`(서명 검증) 출력 수준과, 실패 시 Layer A만 노출하는 강등 정책을 구현합니다.

## What this is not

- QR **모듈·ECC 코드워드**를 은닉 채널로 쓰는 스테가노그래피가 아닙니다.
- 페이로드 자체에 대한 **암호학적 access control** 이 아니라, 앱이 사용자에게 **무엇을 보여줄지**에 대한 출력 정책입니다.
- “QR에 서명을 넣었다”는 **일반 아이디어**만의 구현이 아니라, 위 wire format·canonical 서명·strict v1 디코드·resolver 결합을 다룹니다.

## 디렉터리

| 경로 | 설명 |
|------|------|
| [src/qoverwrap/](src/qoverwrap/) | 코어 라이브러리 (인코더·디코더·crypto·resolver) |
| [demo/](demo/) | FastAPI + React 시연 앱 |
| [tests/](tests/) | 단위·통합·데모 API 테스트 |
| [docs/patent/spec-draft.md](docs/patent/spec-draft.md) | 특허 명세 초안 |
| [docs/research/prior-art-survey.md](docs/research/prior-art-survey.md) | 선행기술 조사 |

## 빠른 시작 (개발)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -r demo/backend/requirements.txt
export QWR_ENABLE_DEMO_SIGNING=1
PYTHONPATH=src .venv/bin/pytest -q
```

데모 앱 실행은 [demo/README.md](demo/README.md) 를 참고하세요.

## 라이선스

저장소 루트의 `LICENSE` 또는 `pyproject.toml` 메타데이터를 따릅니다.
