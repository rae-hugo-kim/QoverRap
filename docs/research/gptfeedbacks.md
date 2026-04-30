1. 결론: A안으로 가되, “암호화 없음”을 청구항의 본질로 쓰지는 마세요

제가 보기에는 이렇게 정리하는 게 가장 좋습니다.

A안 채택. 다만 청구항에서 ‘암호화 없음’을 적극적으로 한정하지 말고, ‘암호학적 접근 제어를 필수 구성으로 하지 않는, 서명 기반 계층형 출력/렌더링 정책’으로 포지셔닝한다.

즉, 핵심은 “우리는 암호화를 안 한다”가 아닙니다. 핵심은 다음입니다.

표준 QR 리더가 판독 가능한 단일 payload 문자열에서 Layer A를 선두 평문으로 유지하고, delimiter 이후의 trailer에 versioned binary frame을 text-safe encoding으로 결합하며, 검증 실패 시 공개 계층으로 강등하는 resolver 정책을 제공한다.

이렇게 써야 합니다. “암호화 없음”을 청구항에 너무 세게 넣으면 나중에 실시예 확장이나 후속 출원에서 스스로 발목을 잡을 수 있습니다.

2. 왜 A안이 더 안전한지는 이렇게 써야 합니다

첨부 메모는 “B안은 SQRC가 직격이고, A안은 SQRC가 다른 문제영역으로 빠진다”고 정리하고 있습니다. 방향은 맞지만 표현은 조금 더 정교해야 합니다.

DENSO WAVE의 SQRC는 단일 QR 코드에 public data와 private data를 함께 담고, cryptographic key를 가진 dedicated reader만 private data를 읽을 수 있다고 설명합니다. 따라서 QoverwRap이 “암호화된 비공개 데이터 접근 제어”를 핵심으로 주장하면 SQRC와 가까워집니다.

반면 QoverwRap을 A안으로 재포지셔닝하면 가장 가까운 비교대상은 SQRC보다는 signed credential QR, visible digital seal, QR authenticity verification 계열이 됩니다. SMART Health Cards는 issuer가 Health Card VC에 서명하고 verifier가 issuer public key로 검증하는 구조이며, 공개키는 issuer의 JWK set으로 게시됩니다. QR 코드 진본성 검증 관련 KR20180122843A도 QR 생성 정보에 서명문과 기관코드를 포함하고, 공개키검증서버 및 기관 공개키를 통해 서명을 검증하는 구성을 설명합니다.

따라서 A안의 장점은 “SQRC를 완전히 피한다”가 아니라, 더 정확히는 이것입니다.

SQRC가 점유한 ‘키 기반 비공개 영역 판독 제한’ 영역에서 벗어나, ‘표준 QR payload 문자열의 부분 호환성, signed trailer framing, fallback disclosure policy’라는 다른 과제로 심사 초점을 이동시킨다.

이 표현이 더 방어적이고 설득력 있습니다.

3. 가장 중요한 수정: “접근 제어”를 “출력/렌더링 정책”으로 바꾸세요

기존 명세서 초안은 제목부터 “내장 서명 기반 접근 제어 시스템”이고, 기술 분야와 과제 해결 수단에서도 접근 권한에 따라 노출 계층을 동적으로 결정한다고 설명합니다. 이 표현이 현재 가장 큰 공격면입니다.

암호화가 없다면 Layer B는 payload 내부에 존재하고, 표준 리더 또는 커스텀 파서가 원하면 읽을 수 있습니다. 따라서 이것은 cryptographic access control이 아닙니다. 대신 아래 용어로 바꿔야 합니다.

추천 용어:

검증 결과 기반 출력 정책
역할 기반 렌더링 정책
계층형 표시 제어
safe-fallback disclosure policy
tamper-evident layered QR payload
offline verifiable layered QR payload

단, “표시 정책”만 쓰면 UI에 너무 좁게 묶입니다. 청구항에서는 “출력 정책” 또는 **“응용 프로그램에 반환되는 계층 데이터 선택 정책”**이 더 좋습니다.

추천 문구:

본 발명에서 접근 수준은 페이로드 자체의 암호학적 판독 제한을 의미하는 것이 아니라,
디코더 또는 응용 프로그램이 사용자 또는 후속 처리 모듈에 반환하는 계층 데이터의
범위를 결정하기 위한 출력 정책 매개변수를 의미한다.

첨부 메모의 self-disclaim 문구도 방향은 좋습니다. 다만 “페이로드 내용 자체에 대한 암호학적 접근 제어를 의미하지 않는다”는 문장은 명세서 정의부에는 넣을 수 있지만, 청구항에는 넣지 않는 편이 낫습니다. 청구항에 너무 강하게 들어가면 보호범위를 불필요하게 줄일 수 있습니다.

4. 발명 명칭은 반드시 바꾸세요

현재 초안 제목:

단일 QR 페이로드 내 다층 데이터 구조화 및 내장 서명 기반 접근 제어 시스템과 그 방법

이건 A안과 맞지 않습니다.

추천 제목:

단일 QR 페이로드 내 다층 데이터 직렬화 및 내장 서명 기반 오프라인 검증 시스템과 그 방법

조금 더 공격적으로 가면:

표준 QR 리더 호환 공개 계층과 내장 서명 트레일러를 포함하는 단일 QR 페이로드 검증 시스템과 그 방법

영문은 아래가 좋습니다.

System and Method for Offline Verification of a Layered Single QR Payload with a Plaintext Public Prefix and Embedded Signature Trailer

이 영문 제목은 발명의 실제 차별점, 즉 plaintext public prefix와 embedded signature trailer를 바로 드러냅니다.

5. 선행기술조사보고서도 같이 고쳐야 합니다

현재 선행기술조사보고서는 QoverwRap의 핵심을 “페이로드-레벨 구조화 + 내장 Ed25519 서명 + 역할 기반 Resolver”로 잡고, EPO OPS 0-hit를 신규성 근거로 사용합니다. 하지만 “QR + signature” 자체는 더 이상 0-hit처럼 쓰면 안 됩니다.

예를 들어 US20120308003A1은 “barcodes using digital signatures”를 다루고, Google Patents 요약 기준으로 barcode의 생성·인증을 digital signature로 수행하는 방법과 시스템을 설명합니다. SAP Mobile Services 문서도 signed QR code 기능에서 private key로 QR을 서명하고, public key로 검증하며, 스캔 결과가 JWS string이라고 설명합니다.

따라서 조사보고서 §6-5의 결론은 이렇게 바꾸세요.

기존 취지:

QR + signature + G06K19/06 = 0 hit
→ Layer C 내장 서명 독창성 강력 지지

수정 권고:

특정 EPO OPS 쿼리에서는 QR + signature 조합의 직접 문헌이 확인되지 않았으나,
barcode 또는 QR payload에 digital signature를 포함하여 인증하는 선행기술은 존재한다.
따라서 신규성·진보성 주장은 QR 내 서명 일반 개념이 아니라,
Layer A 평문 선두 유지, delimiter-framed trailer, versioned binary header,
Layer B/C 분리, 검증 실패 시 공개 계층으로 강등하는 resolver 정책의 구체적 결합에 둔다.

그리고 §3.2 선행기술 분류에 5번째 군을 추가하세요.

(마) 서명-내장 자격증명/인증 QR
대표: SMART Health Cards, ICAO VDS/VDS-NC, US20120308003A1, KR20180122843A, SAP signed QR
방식: signed credential, digital seal, QR authenticity verification
한계: 전체 credential 또는 barcode message를 서명 객체로 취급하며,
Layer A 평문 prefix와 delimiter-framed trailer를 통한 부분 호환 payload 구조 및
safe-fallback resolver 정책을 명시하지 않음

이렇게 해야 심사관이 “QR에 서명 넣는 건 이미 있다”고 지적해도 방어선이 유지됩니다.

6. 청구항 1은 이렇게 재작성하는 게 좋습니다

현재 청구항 1은 “Layer B와 Layer C가 모두 비어있지 않은 경우”라고 되어 있는데, 구현 설명은 B 또는 C 중 하나라도 있으면 복합 모드입니다. 이건 반드시 고쳐야 합니다.

추천 청구항 1 골격:

QR 코드의 표준 심벌 체계에 의해 인코딩 가능한 단일 페이로드 문자열을 생성하는 방법으로서,

(a) 표준 QR 리더에 의해 평문으로 판독 가능한 공개 텍스트 계층인 Layer A를 입력받는 단계;

(b) Layer A와 구별되는 적어도 하나의 후속 계층 데이터를 입력받는 단계;

(c) 상기 후속 계층 데이터가 존재하는 경우,
    버전 정보 및 각 후속 계층의 길이 정보를 포함하는 이진 헤더를 생성하는 단계;

(d) 상기 이진 헤더 및 상기 후속 계층 데이터를 순차적으로 결합한 프레임을
    텍스트 안전 인코딩 방식으로 인코딩하여 트레일러를 생성하는 단계;

(e) Layer A, 미리 정해진 구획자 및 상기 트레일러를 순차적으로 결합하여
    단일 페이로드 문자열을 출력하는 단계;

를 포함하며,

상기 단일 페이로드 문자열은 표준 QR 코드 데이터로 인코딩 가능하고,
상기 Layer A는 상기 구획자보다 앞에 위치하여 표준 QR 리더의 판독 결과에서
선두 평문으로 표시되는 것을 특징으로 하는 방법.

여기서 중요한 점은 독립항에서 Layer B, Layer C, Ed25519, base64를 너무 일찍 고정하지 않는 것입니다. 독립항은 “후속 계층 데이터”, “텍스트 안전 인코딩”, “길이 정보”로 넓게 두고, 종속항에서 구체화하는 게 좋습니다.

7. 청구항 2의 “자기완결” 표현은 반드시 고치세요

기존 초안은 “동일 페이로드 내부의 정보만으로 자기완결적으로 수행”된다고 쓰면서, 청구항 6에서는 공개키가 페이로드 외부에서 제공된다고 합니다. 이건 명백한 내부 충돌입니다.

추천 문구:

상기 검증 대상 데이터 및 서명값은 동일 페이로드 문자열 내부에 포함되고,
검증기는 사전에 저장되거나 외부 입력으로 제공된 공개키를 사용하여,
온라인 검증 서버 또는 블록체인 조회 없이 서명 검증을 수행하는 것을 특징으로 하는 방법.

“PKI 인프라 없이”도 빼는 게 좋습니다. SMART Health Cards는 issuer public key를 JWK set으로 게시하고 verifier가 이를 사용해 issuer signature를 검증합니다. 또한 X.509 certificate 기반 trust framework도 언급합니다. 그러므로 “PKI 없이”라고 쓰면 불필요한 공격면이 생깁니다.

더 안전한 표현은:

온라인 검증 서버 호출 없이

입니다.

8. 청구항 7·8은 A안의 핵심입니다

A안에서 가장 살려야 할 청구항은 사실 청구항 7·8입니다. 특히 safe-fallback은 단순 signed QR과의 차별점으로 쓸 수 있습니다.

현재 청구항 7은 “접근 수준에 따라 노출되는 계층을 달리하는 리졸버”라고 되어 있습니다. 이걸 아래처럼 바꾸세요.

청구항 2에 있어서,
디코더 또는 응용 프로그램에 반환되는 계층 데이터를 출력 정책에 따라 선택하는 리졸버를 더 포함하며,
상기 리졸버는
(i) 공개 수준에서 Layer A를 반환하고,
(ii) 인증 수준에서 Layer A 및 Layer B를 반환하며,
(iii) 검증 수준에서 서명 검증이 성공한 경우에 한하여 Layer A 및 Layer B를 검증된 데이터로 반환하는 것을 특징으로 하는 방법.

Layer C 자체를 사용자에게 “출력”한다고 쓰는 건 조심해야 합니다. Layer C는 서명값이지 사용자에게 노출할 실질 데이터가 아닙니다. 따라서 “Layer A·B·C를 출력”보다는 “Layer A 및 Layer B를 검증된 데이터로 반환하고, 검증 결과를 함께 출력”이 더 자연스럽습니다.

청구항 8은 아래처럼 정리하면 좋습니다.

청구항 7에 있어서,
상기 리졸버는 페이로드 파싱 실패, 헤더 검증 실패, 트레일러 디코딩 실패,
공개키 부재 또는 서명 검증 실패 중 어느 하나가 발생하는 경우,
Layer B를 반환하지 않고 Layer A만을 반환하는 공개 수준으로 강등하는 것을 특징으로 하는 방법.

이게 A안의 핵심 방어 포인트입니다.

9. §8.4 issuer routing은 살리되, “청구범위 외” 문구는 삭제하세요

첨부 메모의 지적처럼, §8.4에서 “청구의 범위 외의 응용 예시”라고 해놓고 청구항 9에서 issuer ID + trust registry routing을 청구하면 내부 모순이 됩니다. 현재 초안도 실제로 그렇게 되어 있습니다.

수정:

본 절은 본 발명의 선택적 실시예로서,
Layer A의 선두 영역에 포함된 발급자 식별자를 이용하여
검증용 공개키를 선택하는 응용 레이어의 라우팅 구성을 설명한다.

다만 “시각 테마가 곧 검증 키의 단서”라는 문장은 청구항에서는 빼세요. 기술적 효과라기보다 UX/브랜딩 효과처럼 보일 수 있습니다. 명세서 실시예에는 남겨도 되지만, 청구항 9는 더 건조하게 가야 합니다.

추천 청구항 9:

청구항 1 또는 청구항 2에 있어서,
Layer A의 선두 영역은 발급자 식별자를 포함하고,
디코더는 상기 발급자 식별자를 추출하여 복수의 검증 공개키 중 하나를 선택하는 것을 특징으로 하는 방법.

“신뢰 레지스트리”는 종속항에서 더 좁혀도 됩니다.

10. 산술·정합성 P0 수정은 바로 반영하세요

아래는 반드시 고쳐야 합니다.

delimiter 길이

현재 초안은 "\n---QWR---\n"를 고정 9바이트라고 적고 있습니다. 실제로는 11바이트입니다.

\n      = 1
---     = 3
QWR     = 3
---     = 3
\n      = 1
합계    = 11

수정:

DELIMITER = "\n---QWR---\n" (UTF-8/ASCII 기준 고정 11바이트)
“공개 계층 이상” 표현

현재 초안의 안전 기본값 설명은 “공개 계층 이상을 노출하지 않는다”라고 되어 있습니다. 한국어에서는 “이상”이 더 높은 수준을 포함하는 느낌을 줍니다.

수정:

어떠한 실패 경로에서도 공개 계층을 초과하는 정보를 반환하지 않는다.

또는:

실패 시 출력 결과를 공개 수준으로 강등한다.
ECC 100% 보존

기존 명세서와 조사보고서는 “ECC 용량 100% 보존”을 장점으로 반복합니다. 취지는 맞지만 표현은 과합니다. payload가 길어지면 더 큰 QR version이나 더 낮은 오류정정 레벨이 필요할 수 있습니다.

수정:

QR 모듈 또는 오류정정 코드워드를 은닉 채널로 변조하지 않으므로,
선택된 QR 버전 및 오류정정 레벨의 표준 오류정정 메커니즘을 그대로 사용한다.
11. A안 기준으로 Abstract도 다시 쓰면 좋습니다

기존 abstract는 “접근 권한 수준에 따라 노출 계층을 결정”한다고 되어 있어 A안과 완전히 정렬되지는 않습니다.

추천 요약서:

본 발명은 표준 QR 코드의 데이터 필드에 인코딩 가능한 단일 페이로드 문자열 내에서,
표준 QR 리더에 의해 선두 평문으로 판독 가능한 공개 계층과,
구획자 이후에 배치되는 텍스트 안전 인코딩된 트레일러를 결합하는
계층형 QR 페이로드 직렬화 및 검증 시스템을 제공한다.

상기 트레일러는 버전 정보 및 계층 길이 정보를 포함하는 이진 헤더와,
컨텍스트 메타데이터 계층 및 디지털 서명 계층을 포함할 수 있다.
디코더는 페이로드에 포함된 검증 대상 데이터 및 서명값과,
사전에 보유하거나 외부에서 제공된 공개키를 사용하여
온라인 검증 서버 호출 없이 서명 검증을 수행한다.

또한 리졸버는 파싱 실패, 헤더 검증 실패, 공개키 부재 또는 서명 검증 실패 시
공개 계층만 반환하는 안전 강등 정책을 수행함으로써,
표준 QR 리더와의 부분 호환성과 검증 결과 기반 계층형 출력 정책을 동시에 제공한다.

이 버전은 “접근 제어”를 빼면서도 발명의 효과를 충분히 살립니다.

12. 최종 판단

지금 재포지셔닝은 맞는 방향입니다. 단, 다음 세 가지를 동시에 해야 합니다.

명세서에서 “접근 제어”를 제거하거나 “출력/렌더링 정책”으로 재정의.
선행기술조사보고서에서 “QR + signature 전무” 식의 결론을 폐기하고, signed credential QR / VDS / signed barcode 계열을 별도 비교군으로 추가.
청구항 중심을 Ed25519나 서명 일반이 아니라, Layer A 선두 평문 + delimiter-framed trailer + versioned binary header + safe-fallback resolver 조합으로 이동.

제일 중요한 한 문장으로 줄이면 이겁니다.

QoverwRap은 ‘비밀 데이터를 숨기는 QR’이 아니라, ‘표준 QR 리더와 부분 호환되는 공개 평문 prefix 위에 signed structured trailer를 덧붙이고, 검증 실패 시 공개 계층으로 강등하는 계층형 QR payload wire format’으로 포지셔닝해야 합니다.

이 프레이밍이면 SQRC와 정면충돌을 줄이고, SMART Health Cards·VDS·signed barcode 계열과도 차별점을 만들 수 있습니다.

반론 가능성

반대로, 암호화를 완전히 배제하면 “역할 기반”이나 “authenticated” 수준이 기술적 효과가 아니라 단순 응용 정책으로 보일 수 있습니다. 또한 safe-fallback resolver도 심사관이 “통상적인 오류 처리”라고 볼 가능성이 있습니다. 그래서 청구항에서는 fallback을 단순 에러 처리로 쓰지 말고, 계층형 payload 구조와 결합된 반환 데이터 제한 정책으로 써야 합니다. 즉, fallback 자체보다 “구조화된 trailer 파싱/검증 실패 시 Layer A prefix만 반환한다”는 결합을 강조해야 합니다.

추가로 보면 좋은 개념

다음 단계에서는 problem-solution approach, closest prior art, negative limitation, self-disclaimer, claim differentiation, wire format claim, safe-fallback security property, JWS compact serialization, Visible Digital Seal, SMART Health Cards를 같이 보면 청구항 정리가 훨씬 좋아질 겁니다.

---

네. 방향은 맞습니다. 다만 현재 첨부된 specdraft 자체는 아직 “최종안”이 아닙니다.
첨부된 “최종안”은 실제 개정 명세서라기보다, 기존 specdraft에 반영해야 할 최종 패치 계획입니다. 이 계획은 대체로 타당하지만, specdraft 본문에는 아직 이전 위험 문구가 그대로 남아 있습니다.

1. 결론

A안, 즉 “암호화 없는 재포지셔닝”으로 가는 판단은 맞습니다.
QoverwRap을 “비공개 데이터를 암호학적으로 숨기는 QR”로 주장하면 DENSO SQRC와 정면 충돌합니다. SQRC는 단일 QR에 public/private data를 담고, private data는 cryptographic key를 가진 dedicated reader만 읽는다고 설명됩니다.

따라서 QoverwRap의 중심은 아래 문장으로 고정하는 게 좋습니다.

QoverwRap은 표준 QR 리더가 판독 가능한 Layer A 평문 prefix를 유지하면서, delimiter 이후에 signed structured trailer를 배치하고, 파싱·검증 실패 시 Layer A만 반환하는 계층형 QR payload wire format이다.

이 프레이밍이면 SQRC의 “키 기반 비공개 영역 판독 제한”과 과제를 분리할 수 있고, SMART Health Cards, ICAO VDS, signed barcode 계열과도 차별점을 만들 수 있습니다. 다만 SMART Health Cards는 issuer가 Health Card VC에 서명하고, verifier가 issuer public key로 서명을 검증하는 구조를 이미 갖고 있습니다. 또 US20120308003A1도 QR Code 같은 barcode에 digital signature 기반 verification mechanism을 직접 incorporated하는 방법을 설명합니다. 따라서 “QR + 서명” 자체가 아니라 Layer A prefix + delimiter trailer + versioned header + safe-fallback resolver의 결합이 핵심이어야 합니다.

2. “최종안”에서 잘 잡은 부분

첨부된 최종 패치 계획은 이전 피드백을 잘 흡수했습니다. 특히 아래 세 가지는 그대로 채택해도 됩니다.

첫째, self-disclaim을 청구항이 아니라 명세서 정의부에만 두는 판단이 맞습니다. 청구항에 “암호학적 접근 제어가 아님”을 직접 넣으면 negative limitation이 되어 보호범위가 불필요하게 줄어듭니다.

둘째, 청구항 1을 Layer B/C, base64, Ed25519에 고정하지 않고 “후속 계층 데이터 / 텍스트 안전 인코딩 / 길이 정보”로 추상화하는 방향이 맞습니다. 독립항은 넓게, 구체 wire format은 종속항에서 받는 구조가 낫습니다.

셋째, 청구항 7에서 Layer C를 사용자 출력 대상으로 보지 않고, A/B를 검증된 데이터로 반환하며 검증 결과를 함께 출력하는 방식이 맞습니다. Layer C는 서명값이므로 “사용자에게 노출되는 계층 데이터”라기보다 검증 재료입니다.

3. 하지만 specdraft는 아직 구버전입니다

specdraft에는 여전히 수정 전 위험 요소가 많이 남아 있습니다. 이 상태로는 변리사에게 “최종안”으로 넘기기 어렵습니다.

가장 큰 잔존 이슈는 다음입니다.

위치	현재 문제	수정 방향
제목	“접근 제어 시스템”	“오프라인 검증 시스템” 또는 “내장 서명 트레일러를 포함하는 단일 QR 페이로드 검증 시스템”
기술 분야	“접근 권한에 따라 노출”	“검증 결과 및 출력 정책에 따라 반환 계층 결정”
§3.3	QR+signature 0-hit를 핵심 근거로 사용	signed QR 선행기술 존재를 인정하고, 구체 조합 차별성으로 이동
§4	“PKI 인프라 없이 자기완결”	“온라인 검증 서버 호출 없이”
§5(c)	“역할 기반 리졸버 / 접근 권한”	“출력 정책 / 렌더링 정책 / 반환 데이터 제한 정책”
§6	“ECC 용량 100% 보존”	“QR 모듈 또는 ECC 코드워드를 은닉 채널로 변조하지 않음”
§8.1	delimiter 9바이트	"\n---QWR---\n"는 11바이트
§8.3	“공개 계층 이상”	“공개 계층을 초과하는 정보를 반환하지 않음”
§8.4	“청구의 범위 외”	“본 발명의 선택적 실시예”
청구항 2	동일 페이로드 내부 정보만으로 자기완결	공개키는 사전 보유/외부 입력, 온라인 서버 호출 없이 검증
청구항 7	Layer A·B·C 출력	A/B 및 검증 결과 반환
§10	QR+signature 0-hit, Ed25519+QR 0-hit 중심	signed QR 선행기술과 비교 후 narrow combination 중심

즉, 첨부된 최종 패치 계획은 맞지만, specdraft에는 아직 반영되지 않았습니다.

4. prior-art-survey 보강은 P1이 아니라 최소 P0입니다

최종 패치 계획에서는 prior-art-survey 보강을 P1로 둔 것 같은데, 저는 이 부분은 P0에 가깝다고 봅니다. 이유는 specdraft 상단의 “검증 정책”이 여전히 prior-art-survey.md의 0-hit 항목을 핵심 차별점으로 사용한다고 되어 있기 때문입니다.

현재 prior-art-survey도 “QR + signature + G06K19/06 = 0 hit → 핵심 차별 요소 선행기술 전무”라는 결론을 유지하고 있습니다. 그런데 QR 또는 barcode에 digital signature를 포함하는 선행기술은 확인됩니다. US20120308003A1은 barcode, including QR Codes, 를 digital signatures로 생성·인증하는 methods and systems를 설명합니다. KR20180122843A도 QR 생성 정보에 서명문과 기관코드를 포함하고, 기관 공개키 및 공개키검증서버를 통해 QR 진본 여부를 검증하는 구조를 설명합니다.

따라서 prior-art-survey를 나중에 고치면, specdraft와 조사보고서가 서로 충돌합니다. 최소한 아래 문장은 바로 바꿔야 합니다.

기존 취지:

QR + signature 선행기술 전무. 내장 서명 독창성 강력 지지.

수정 권고:

특정 EPO OPS 쿼리에서는 직접 hit가 없었으나, QR 또는 barcode에 digital signature를 포함하여 인증하는 선행기술은 존재한다. 따라서 QoverwRap의 차별점은 QR 내 서명 일반 개념이 아니라, Layer A 평문 선두 유지, delimiter-framed trailer, versioned binary header, Layer B/C 분리, 검증 실패 시 Layer A만 반환하는 safe-fallback resolver의 구체적 결합에 있다.

이 수정은 specdraft 패치와 같은 커밋 또는 같은 수정 라운드에 들어가야 합니다.

5. 최종안에 하나 더 추가해야 할 P0: 서명 대상의 canonicalization

현재 specdraft는 “Layer A와 Layer B의 결합 메시지에 대한 디지털 서명”이라고만 설명합니다. 이 표현은 특허 명세서와 구현 명세 관점에서 아직 불안합니다.

문제는 “결합 메시지”가 불명확하다는 점입니다. 예를 들어 문자열 정규화, UTF-8 바이트화, 길이 경계, 버전, 알고리즘 식별자, header 포함 여부가 명확하지 않으면 같은 데이터라도 검증 결과가 구현마다 달라질 수 있습니다. 또한 header가 서명 대상에서 빠지면 version 또는 length field tampering에 대한 설명이 약해집니다.

명세서 §8.1 또는 §8.3에 아래 같은 문구를 넣는 것이 좋습니다.

일 실시예에서 서명 대상 메시지는 다음과 같은 정규화된 바이트열로 구성된다.

signing_message =
  magic("QWR1") ||
  uint8(version) ||
  uint16(len(layer_a_utf8)) ||
  layer_a_utf8 ||
  uint16(len(layer_b)) ||
  layer_b

또는 다른 실시예에서 signing_message는 header 및 Layer A, Layer B를 포함하는
정규화된 바이트열로 구성될 수 있다.

독립항에는 너무 세게 넣지 말고, 종속항 또는 실시예로 두면 됩니다. 하지만 명세서 본문에는 반드시 있어야 합니다. 이게 없으면 “Layer A + Layer B 결합”이 구현상 애매하고, 심사관이나 제3자가 “통상적인 signed message”로 축소 해석할 여지가 있습니다.

6. “authenticated” 레벨 명칭도 조심해야 합니다

현재 resolver는 public / authenticated / verified 3단계입니다. 문제는 authenticated 레벨에서 Layer B를 반환하지만 서명 검증은 하지 않는 구조라는 점입니다.

이 자체가 불가능한 것은 아닙니다. 다만 “authenticated”라는 이름은 사용자가 데이터가 인증되었다고 오해할 수 있습니다. 특허 문구에서는 아래처럼 정의를 분명히 해야 합니다.

여기서 authenticated 수준은 사용자 또는 응용 프로그램의 출력 권한 수준을 의미하며,
Layer B의 암호학적 무결성이 검증되었음을 의미하지 않는다.
Layer B가 검증된 데이터로 반환되는 것은 verified 수준에서 서명 검증이 성공한 경우에 한한다.

또는 명칭을 structured, privileged, expanded 같은 중립적 표현으로 바꾸는 것도 고려할 만합니다.

청구항에서는 이렇게 쓰는 게 안전합니다.

제2 출력 수준에서 Layer A 및 Layer B를 반환하되 검증 상태를 미검증으로 표시하고,
제3 출력 수준에서 서명 검증이 성공한 경우에 한하여 Layer A 및 Layer B를 검증된 데이터로 반환한다.

이렇게 하면 “접근 제어” 문제도 줄고, verified 레벨의 기술적 의미도 살아납니다.

7. §3.2 선행기술 분류는 5군 체계로 바꾸는 게 맞습니다

현재 specdraft는 선행기술을 4개 군으로 분류합니다. 이제는 5번째 군을 추가해야 합니다.

(마) 서명-내장 자격증명/인증 QR
대표: SMART Health Cards, ICAO VDS/VDS-NC, US20120308003A1, KR20180122843A, SAP signed QR
방식: signed credential, visible digital seal, signed barcode, QR authenticity verification
한계: 전체 credential 또는 barcode message를 서명 객체로 취급하며,
Layer A 평문 prefix와 delimiter-framed trailer를 통한 부분 호환 payload 구조 및
safe-fallback resolver 정책을 명시하지 않음

ICAO VDS 계열도 반드시 넣어야 합니다. VDS는 cryptographically signed digital seal이 2D barcode로 표현되는 구조이고, 비자 등 문서의 authenticity 확인 목적으로 쓰입니다. 이 계열을 누락하면 “서명 내장 2D barcode” 비교가 비어 보입니다.

8. 작업 순서는 이렇게 바꾸는 게 좋습니다

첨부된 최종 패치 계획은 “1번 specdraft 패치 → 2번 prior-art-survey 보강” 순서를 제안합니다. 저는 약간 수정해서 아래 순서를 권합니다.

1단계: specdraft 핵심 패치 + prior-art 헤드라인 패치를 같은 라운드에 처리

동시에 바꿔야 하는 항목입니다.

specdraft:
- 제목
- 기술 분야
- 과제
- 해결 수단
- 효과표
- §8.1 delimiter 11바이트
- §8.3 safe-fallback 문구
- §8.4 선택적 실시예
- 청구항 1/2/7/8/9
- §10 신규성·진보성 매핑
- Abstract

prior-art-survey:
- §2 QoverwRap 기술 요약의 “자기완결”, “접근 제어”, “ECC 능력 100%” 표현 수정
- §3.2 또는 §5에 signed credential / signed QR 비교군 추가
- §6-5의 QR+signature 0-hit 결론 약화
- §8 최종 결론에서 “핵심 차별 요소 선행기술 전무” 삭제
2단계: 원문 citation 보강

이건 그 다음에 해도 됩니다.

- SQRC
- SMART Health Cards
- ICAO VDS/VDS-NC
- US20120308003A1
- KR20180122843A
- SAP signed QR

즉, 문구 정정은 P0, 원문 인용 1~2문장 보강은 P1로 나눌 수 있습니다. 지금처럼 prior-art 전체를 P1로 밀면 위험합니다.

9. 변리사에게 넘기기 전 체크리스트

이 체크리스트를 통과하면 “최종안”이라고 불러도 됩니다.

제목에 “접근 제어”가 남아 있지 않을 것.
“PKI 인프라 없이”가 “온라인 검증 서버 호출 없이”로 바뀌어 있을 것.
“자기완결”은 “검증 대상 데이터와 서명값이 동일 페이로드에 포함”이라는 제한적 의미로 정의되어 있을 것.
“QR + signature 0-hit”가 신규성의 핵심 근거로 남아 있지 않을 것.
"\n---QWR---\n"가 11바이트로 수정되어 있을 것.
Claim 1(c)가 “Layer B와 C가 모두 비어있지 않은 경우”가 아니라 “후속 계층 데이터가 존재하는 경우” 또는 “B 또는 C 중 적어도 하나”로 바뀌어 있을 것.
Claim 2가 외부 공개키 사용과 모순되지 않을 것.
Claim 7이 Layer C를 사용자 출력 데이터처럼 쓰지 않을 것.
Claim 8이 단순 오류 처리가 아니라 “계층형 payload 구조와 결합된 반환 데이터 제한 정책”으로 쓰여 있을 것.
Claim 9에서 시각 테마/브랜딩 표현이 빠져 있을 것.
서명 대상 canonical byte sequence가 실시예에 정의되어 있을 것.
prior-art-survey에 signed QR / VDS / SHC 비교군이 추가되어 있을 것.
최종 판단

최종 패치 계획은 통과입니다.
다만 첨부된 specdraft는 아직 통과가 아닙니다. 지금 파일 상태는 “A안 재포지셔닝을 하기로 합의한 단계”이지, “A안이 실제 명세서에 반영된 단계”는 아닙니다.

가장 안전한 다음 액션은 이겁니다.

specdraft 본문과 청구항을 먼저 패치하되, prior-art-survey의 0-hit 결론 문구도 같은 라운드에서 최소 수정한다. 그 다음 SQRC/SHC/VDS/US20120308003A1/KR20180122843A 원문 인용을 보강한다.

이렇게 정리하면 변리사에게 넘길 때 “QR + 서명은 이미 있지 않나?”라는 질문을 받아도, 곧바로 **“그렇다. 그래서 본 발명의 차별점은 서명 일반이 아니라 plaintext prefix + framed trailer + resolver fallback의 wire-format 결합이다”**라고 방어할 수 있습니다.