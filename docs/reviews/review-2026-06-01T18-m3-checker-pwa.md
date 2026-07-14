# Code Review — M3 검표원(게이트) 스캔 모드 + PWA 강화

- **Date**: 2026-06-01
- **Scope**: `demo/frontend/` 만 (백엔드 `redeem` 기존·코어 `src/qoverwrap/` 무수정 — diff 빈 출력 확인)
- **Reviewer**: oh-my-claudecode:code-reviewer (opus) ×2 패스, 별도 레인 — 작성(executor + 후속 델타)과 분리
- **diff-hash: 5059de45c42787d207ef1d6ba82b147b8d1f02d9ff4ce785fca1b49915db6ecb**

## Verdict: PASS

CRITICAL/HIGH/MEDIUM 0건. 2개 패스(코어 + 후속 델타) 모두 APPROVE. 라이브 E2E 3-way + build/lint로 검증. 로컬 커밋 적합.

## 변경 (10파일)
- 신규 `components/CheckerView.tsx`: 검표원 풀스크린. 스캔→`Promise.allSettled([redeem(MAX_USES), resolve(verified)])`→배너(ok/already_used/invalid)+ThemedCard(issuer null 가드)+다음스캔.
- `App.tsx`: `appMode` builder|checker 토글(헤더 mode-checker/mode-builder), checker 분기 렌더. builder 흐름 무변경.
- `api/client.ts`+`types.ts`: `redeem(payload,max_uses=1)`+`RedeemResponse`.
- `vite.config.ts`: VitePWA(autoUpdate, manifest+`lang:ko`, app-shell precache, **/api NetworkOnly**, navigateFallbackDenylist) + `preview.proxy`.
- `package.json`(+lock): `vite-plugin-pwa@^1.3.0`. `index.html` 수동 manifest link 제거. `public/manifest.webmanifest` 삭제(플러그인 생성).
- `components/QRScanner.tsx`: 수동 입력 `<input>`→`<textarea>`(후술).

## 1차 패스 — 코어 (APPROVE, CRITICAL/HIGH 0)
- **verdict 로직**: allSettled reject→`{status:invalid}` 매핑 정확. redeem/resolve가 동일 서명을 검증해 배너·카드 모순 불가.
- **null-issuer crash 가드**: invalid+issuer=null → ThemedCard 미호출, 텍스트 폴백. 안전.
- **SW /api NetworkOnly**: 생성된 `dist/sw.js` 직접 확인 — `registerRoute(/\/api\//, NetworkOnly)` + denylist, precache에 /api 없음. redeem 카운터·resolve가 캐시 오염 안 됨(소비형 검표원의 핵심 불변식).
- **builder 무변경**·스캐너 lifecycle(key 리마운트, stop on decode/unmount) 안전.

## 2차 패스 — 후속 델타 (APPROVE, CRITICAL/HIGH/MEDIUM 0)
- **QRScanner `<input>`→`<textarea>`**: 와이어 페이로드가 `\n---QWR---\n` 줄바꿈 포함 → 단일행 input은 값 정규화로 줄바꿈 제거 → 페이로드 손상(decode 422→오탐 invalid). textarea가 보존. 공유 컴포넌트 2개 콜사이트(checker `onResult`, builder `onScanned`) 모두 `(text)→JSON 전송`이라 회귀 없음, builder의 잠재 paste 버그도 동시 해소. **정답 수정(워크어라운드 아님)**.
- **MAX_USES 상수 + `if(busy)return` 재진입 가드**: busy가 같은 async에서 무조건 false 복귀(allSettled는 reject 안 함)→ 데드락 없음. 카메라 더블파이어 방어. denominator 커플링 정확.
- **manifest `lang:ko`**: 유효, 타입 안전. vite-plugin-pwa devDep package.json+lock 양쪽 선언 확인.

## 비차단 LOW (이월)
- CheckerView `err` state는 allSettled 설계상 도달 불가(실패는 invalid verdict로 라우팅) → dead UI. 무해, 추후 제거 가능.
- QRScanner 수동입력 레이아웃 flex→stacked(의도적·코스메틱).

## 라이브 검증 (Claude, 별도 레인)
- build(tsc+vite, `dist/sw.js`·`dist/manifest.webmanifest` 생성)·lint clean.
- agent-browser E2E(dev :5173, SW 무간섭; 수동 paste, 멀티라인 nl=2 보존): scan→**✅ 진본 입장(ok)** + festival_pass 카드 / 동일 재scan→**⛔ 복제·차단 already_used "이미 사용됨 (1/1)"**(use_count 1 유지) / 쓰레기→**❌ 위조/미등록(invalid)** 텍스트 폴백. 스크린샷 3종(`/tmp/m3_{ok,dup,invalid}.png`).
- PWA: preview :4173에서 SW `controller=true`, `dist/sw.js` `/api` NetworkOnly.
- `git diff --stat -- demo/backend/ src/qoverwrap/` → 빈 출력.
