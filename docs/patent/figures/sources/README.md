# Patent Figure Sources (KIPO 출원용)

본 디렉토리는 명세서 도면 (Fig. 1 ~ Fig. 6) 의 PlantUML 소스 파일을 보관한다. 출원용 흑백 도면은 `../rendered/` 에 자동 생성된다. 종전 명명 Fig. 8 / Fig. 9 는 16차 라운드 (2026-05-15) 에서 Fig. 5 / Fig. 6 으로 재번호화되었다. 종전 데모 화면 캡처 (`fig{5,6a,6b,6c,7a,7b}_clean.png`) 는 PNG 원본이 `../rendered/` 에 마케팅/내부 검토용으로 보관되며 본 출원에는 미첨부.

## 도면 목록

| 파일 | 도면 | 내용 |
|------|------|------|
| `fig1_payload.puml` | Fig. 1 | 단일 페이로드 문자열 (10) 의 비트 레이아웃 — Layer A (11) / 구획자 (12) / 트레일러 (13) [헤더 (14) + Layer B (15) + Layer C (16)] |
| `fig2_encoder.puml` | Fig. 2 | 인코더 (130) 의 동작 흐름 — S100 ~ S106 |
| `fig3_decoder_resolver.puml` | Fig. 3 | 디코더 (220) 및 리졸버 (250) 의 동작 흐름 — S200 ~ S208 + safe-fallback |
| `fig4_issuer_routing.puml` | Fig. 4 | 발급자 식별자 기반 공개키 선택 라우팅 (선택적 실시예) — S300 ~ S305 |
| `fig5_system_block.puml` | Fig. 5 | 시스템 (1) 의 모듈 구성 블록도 — 발급 측 (100) + 검증 측 (200), 청구항 11 시스템항 매핑 |
| `fig6_mobile_terminal_flow.puml` | Fig. 6 | 휴대용 단말 응용 및 출력 수준별 반환 데이터 흐름 — S401~S406, 청구항 14·15 매핑 |

`_kipo_style.iuml` 은 모든 도면에 공통 적용되는 KIPO 스타일 (흑백, 300dpi, sans-serif) 정의 파일이다.

## 렌더링

```bash
# PlantUML 설치 (택1)
sudo apt install plantuml             # Debian/Ubuntu/WSL
# 또는
wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar

# (선택) SVG → PDF 변환 도구
sudo apt install librsvg2-bin         # rsvg-convert
# 또는
pip install cairosvg

# 전체 도면 렌더링 (PNG + SVG + 선택적 PDF)
bash scripts/render_patent_figures.sh

# 특정 도면만 렌더링
bash scripts/render_patent_figures.sh fig1
bash scripts/render_patent_figures.sh fig5
```

## 출력 형식

| 형식 | 용도 |
|------|------|
| `*.png` | 300dpi 흑백 PNG — KEAPS 첨부용 ("도면" 항목) |
| `*.svg` | 벡터 — 인쇄용 또는 PDF 변환 소스 |
| `*.pdf` | 벡터 PDF — `rsvg-convert` 또는 `cairosvg` 설치 시 자동 생성 |

## KIPO 도면 형식 준수 사항

본 소스는 다음 KIPO 도면 작성 기준을 자동으로 충족한다 (`_kipo_style.iuml` 참조).

- **흑백 원칙**: 색상 미사용, 흰색 배경 + 검은색 실선
- **300dpi**: PlantUML `skinparam dpi 300` 으로 설정
- **참조부호 일치**: 명세서 §7.1 참조부호 일람표와 1:1 대응
- **글자 단위 배제**: 단위(mm, kg 등) 미사용
- **분할 표현**: 한 도면에 복잡한 요소를 담지 않고 5개로 분할

## 출원 전 수동 점검 항목

- [ ] 렌더링된 PNG 가 300dpi 인지 확인 (`identify -format "%x x %y dpi" rendered/fig1_payload.png`)
- [ ] 모든 텍스트가 ASCII / 한글로 정상 표시되는지 확인 (한글 폰트 fallback 이슈 시 시스템에 Noto Sans KR 등 설치)
- [ ] 명세서 §7 도면 설명 및 §7.1 참조부호 일람표와 도면 내용이 일치하는지 교차 확인
- [ ] 종전 데모 PNG (`fig{5,6a,6b,6c,7a,7b}_clean.png`) 는 본 출원에 미첨부 (마케팅/내부 검토용); KEAPS 첨부 도면은 Fig. 1 ~ Fig. 6 의 PlantUML 산출물에 한정
