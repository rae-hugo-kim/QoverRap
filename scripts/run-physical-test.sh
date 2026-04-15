#!/usr/bin/env bash
# run-physical-test.sh — 물리 기기 QR 스캔 테스트 오케스트레이터
#                         Physical device QR scan test orchestrator
#
# 사용법 (Usage):
#   ./scripts/run-physical-test.sh [samsung|generic] [qr-count]
#
# 예시 (Examples):
#   ./scripts/run-physical-test.sh samsung 20
#   ./scripts/run-physical-test.sh generic 10
#   ./scripts/run-physical-test.sh samsung      # 기본값: 5개 / default: 5 QRs
#
# 사전 조건 (Prerequisites):
#   1. 기기 USB 연결 및 adb 인식 확인
#      Device connected via USB, recognized by adb
#   2. QR 이미지 생성 완료
#      QR images generated: python scripts/generate_test_qrs.py
#   3. Maestro 설치 확인 (maestro --version)
#      Maestro installed: maestro --version
#   4. 디스플레이 서버는 이 스크립트가 자동으로 백그라운드 실행
#      Display server is auto-started by this script in background
#
# 결과물 (Output):
#   - test-results/{device}/scan_NNN.png — 각 스캔 스크린샷
#   - test-results/{device}/maestro-output.log — Maestro 실행 로그
#   - test-results/summary.txt — 실행 요약

set -euo pipefail

# ---------------------------------------------------------------------------
# 설정 (Configuration)
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEVICE="${1:-samsung}"           # samsung 또는 generic / samsung or generic
QR_COUNT="${2:-5}"               # 스캔할 QR 수 / Number of QRs to scan
DISPLAY_PORT="${DISPLAY_PORT:-8080}"
DISPLAY_INTERVAL="${DISPLAY_INTERVAL:-8}"  # 초 / seconds
IMAGE_DIR="${PROJECT_ROOT}/test-qr-images"
RESULTS_BASE="${PROJECT_ROOT}/test-results"
RESULTS_DIR="${RESULTS_BASE}/${DEVICE}"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

# ---------------------------------------------------------------------------
# 색상 출력 (Color output)
# ---------------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()    { echo -e "${RED}[FAIL]${NC}  $*"; }
die()     { fail "$*"; exit 1; }

# ---------------------------------------------------------------------------
# 사전 조건 확인 (Prerequisite checks)
# ---------------------------------------------------------------------------

check_prerequisites() {
    info "사전 조건 확인 중... / Checking prerequisites..."
    local errors=0

    # 1. adb 존재 확인
    if ! command -v adb &>/dev/null; then
        fail "adb가 설치되지 않았습니다. Android SDK Platform Tools를 설치하세요."
        fail "adb not found. Install Android SDK Platform Tools."
        (( errors++ ))
    else
        ok "adb 발견 / adb found: $(adb version | head -1)"
    fi

    # 2. 연결된 기기 확인
    if command -v adb &>/dev/null; then
        local devices
        devices=$(adb devices | grep -v "^List" | grep -v "^$" | wc -l)
        if [[ "${devices}" -eq 0 ]]; then
            fail "연결된 Android 기기 없음. USB 케이블과 USB 디버깅을 확인하세요."
            fail "No Android device connected. Check USB cable and USB Debugging."
            (( errors++ ))
        else
            ok "기기 연결됨 / Device(s) connected: ${devices}개"
            adb devices | grep -v "^List" | grep -v "^$" | while read -r line; do
                info "  -> ${line}"
            done
        fi
    fi

    # 3. maestro 존재 확인
    if ! command -v maestro &>/dev/null; then
        fail "maestro가 설치되지 않았습니다."
        fail "maestro not found. Install: https://maestro.mobile.dev"
        (( errors++ ))
    else
        ok "maestro 발견 / maestro found: $(maestro --version 2>/dev/null || echo 'version unknown')"
    fi

    # 4. QR 이미지 존재 확인
    if [[ ! -d "${IMAGE_DIR}" ]]; then
        fail "QR 이미지 디렉터리 없음: ${IMAGE_DIR}"
        fail "QR image directory not found: ${IMAGE_DIR}"
        fail "먼저 실행: python scripts/generate_test_qrs.py"
        fail "Run first: python scripts/generate_test_qrs.py"
        (( errors++ ))
    else
        local img_count
        img_count=$(find "${IMAGE_DIR}" -name "qr_*.png" ! -name "*grid*" | wc -l)
        if [[ "${img_count}" -eq 0 ]]; then
            fail "QR 이미지가 없습니다. python scripts/generate_test_qrs.py를 실행하세요."
            fail "No QR images found. Run: python scripts/generate_test_qrs.py"
            (( errors++ ))
        else
            ok "QR 이미지 발견 / QR images found: ${img_count}개"
        fi
    fi

    # 5. Python 및 venv 확인
    local python_cmd="${VENV_PYTHON}"
    if [[ ! -f "${python_cmd}" ]]; then
        python_cmd="python3"
        warn "가상환경 없음. 시스템 Python 사용: ${python_cmd}"
        warn "No venv found, using system Python: ${python_cmd}"
    fi
    if ! "${python_cmd}" -c "import http.server" &>/dev/null; then
        fail "Python http.server 모듈을 불러올 수 없습니다."
        (( errors++ ))
    else
        ok "Python 확인 / Python OK: ${python_cmd}"
    fi

    # 6. 플로우 파일 확인
    local flow_file
    case "${DEVICE}" in
        samsung) flow_file="${PROJECT_ROOT}/.maestro/qr-scan-samsung.yaml" ;;
        generic) flow_file="${PROJECT_ROOT}/.maestro/qr-scan-generic.yaml" ;;
        *)
            fail "알 수 없는 기기 유형: ${DEVICE} (samsung 또는 generic 사용)"
            fail "Unknown device type: ${DEVICE} (use samsung or generic)"
            (( errors++ ))
            flow_file=""
            ;;
    esac
    if [[ -n "${flow_file}" && ! -f "${flow_file}" ]]; then
        fail "Maestro 플로우 파일 없음: ${flow_file}"
        fail "Maestro flow file not found: ${flow_file}"
        (( errors++ ))
    elif [[ -n "${flow_file}" ]]; then
        ok "플로우 파일 확인 / Flow file OK: ${flow_file}"
    fi

    if [[ "${errors}" -gt 0 ]]; then
        die "${errors}개 사전 조건 실패. 위 오류를 수정하세요. / ${errors} prerequisite(s) failed."
    fi

    ok "모든 사전 조건 통과 / All prerequisites passed."
}

# ---------------------------------------------------------------------------
# 디스플레이 서버 시작 (Start display server)
# ---------------------------------------------------------------------------

DISPLAY_SERVER_PID=""

start_display_server() {
    info "디스플레이 서버 시작 중... / Starting display server..."

    local python_cmd="${VENV_PYTHON}"
    if [[ ! -f "${python_cmd}" ]]; then
        python_cmd="python3"
    fi

    "${python_cmd}" "${SCRIPT_DIR}/qr-display-server.py" \
        --image-dir "${IMAGE_DIR}" \
        --port "${DISPLAY_PORT}" \
        --interval "${DISPLAY_INTERVAL}" \
        > "${RESULTS_BASE}/display-server.log" 2>&1 &

    DISPLAY_SERVER_PID=$!
    echo "${DISPLAY_SERVER_PID}" > "${RESULTS_BASE}/display-server.pid"

    # 서버 시작 확인 대기
    local retries=10
    local started=false
    while [[ ${retries} -gt 0 ]]; do
        if curl -sf "http://localhost:${DISPLAY_PORT}/health" &>/dev/null; then
            started=true
            break
        fi
        sleep 0.5
        (( retries-- ))
    done

    if [[ "${started}" == "true" ]]; then
        ok "디스플레이 서버 시작됨 / Display server started: http://localhost:${DISPLAY_PORT} (PID: ${DISPLAY_SERVER_PID})"
    else
        warn "디스플레이 서버 시작 확인 불가 (계속 진행)"
        warn "Could not verify display server start (continuing anyway)"
        warn "로그 확인: ${RESULTS_BASE}/display-server.log"
    fi
}

stop_display_server() {
    if [[ -n "${DISPLAY_SERVER_PID}" ]]; then
        info "디스플레이 서버 종료 중... / Stopping display server (PID: ${DISPLAY_SERVER_PID})..."
        kill "${DISPLAY_SERVER_PID}" 2>/dev/null || true
        DISPLAY_SERVER_PID=""
    fi
    # PID 파일에서 읽어서 종료 시도
    local pid_file="${RESULTS_BASE}/display-server.pid"
    if [[ -f "${pid_file}" ]]; then
        local pid
        pid=$(cat "${pid_file}")
        kill "${pid}" 2>/dev/null || true
        rm -f "${pid_file}"
    fi
}

# 스크립트 종료 시 서버 정리 / Cleanup server on script exit
trap stop_display_server EXIT INT TERM

# ---------------------------------------------------------------------------
# 기기 위치 확인 대기 (Wait for user to position device)
# ---------------------------------------------------------------------------

wait_for_device_positioning() {
    echo ""
    echo "======================================================================="
    info "다음 단계를 완료하세요 / Complete the following steps:"
    echo ""
    echo "  1. 브라우저에서 열기 / Open in browser:"
    echo "     http://localhost:${DISPLAY_PORT}"
    echo ""
    echo "  2. ${DEVICE} 기기를 화면 앞에 위치시키세요 (30~50cm 거리 권장)"
    echo "     Position ${DEVICE} device in front of the screen (30-50cm recommended)"
    echo ""
    echo "  3. QR 코드가 카메라 뷰파인더에 잘 보이는지 확인하세요"
    echo "     Confirm QR code is visible in the camera viewfinder"
    echo ""
    echo "준비되면 Enter를 누르세요 / Press Enter when ready..."
    echo "======================================================================="
    read -r
}

# ---------------------------------------------------------------------------
# Maestro 실행 (Run Maestro flow)
# ---------------------------------------------------------------------------

run_maestro() {
    local flow_file
    case "${DEVICE}" in
        samsung) flow_file="${PROJECT_ROOT}/.maestro/qr-scan-samsung.yaml" ;;
        generic) flow_file="${PROJECT_ROOT}/.maestro/qr-scan-generic.yaml" ;;
    esac

    local log_file="${RESULTS_DIR}/maestro-output.log"

    info "Maestro 플로우 실행 중... / Running Maestro flow..."
    info "  플로우 / Flow: ${flow_file}"
    info "  QR 수 / QR count: ${QR_COUNT}"
    info "  결과 / Results: ${RESULTS_DIR}"
    info "  로그 / Log: ${log_file}"

    # 환경 변수로 QR_COUNT와 SCREENSHOT_DIR 전달
    # Pass QR_COUNT and SCREENSHOT_DIR as environment variables
    QR_COUNT="${QR_COUNT}" \
    SCREENSHOT_DIR="${RESULTS_DIR}" \
    maestro test "${flow_file}" 2>&1 | tee "${log_file}"

    local exit_code=${PIPESTATUS[0]}
    return ${exit_code}
}

# ---------------------------------------------------------------------------
# 스크린샷 수집 (Collect screenshots)
# ---------------------------------------------------------------------------

collect_results() {
    info "결과 수집 중... / Collecting results..."

    local screenshot_count
    screenshot_count=$(find "${RESULTS_DIR}" -name "*.png" | wc -l)
    ok "스크린샷 수집됨 / Screenshots collected: ${screenshot_count}개"

    # 요약 파일 작성 / Write summary file
    local summary_file="${RESULTS_BASE}/summary.txt"
    {
        echo "================================================"
        echo "QoverwRap 물리 기기 테스트 요약 / Physical Device Test Summary"
        echo "================================================"
        echo "실행 시각 / Run time   : $(date '+%Y-%m-%d %H:%M:%S')"
        echo "기기 유형 / Device     : ${DEVICE}"
        echo "QR 스캔 수 / QR count  : ${QR_COUNT}"
        echo "스크린샷 수 / Screenshots: ${screenshot_count}"
        echo "결과 디렉터리 / Results dir: ${RESULTS_DIR}"
        echo "Maestro 로그 / Log     : ${RESULTS_DIR}/maestro-output.log"
        echo "================================================"
        echo ""
        echo "다음 단계 / Next steps:"
        echo "  python scripts/collect-results.py --results-dir ${RESULTS_DIR}"
        echo ""
    } | tee "${summary_file}"

    ok "요약 저장됨 / Summary saved: ${summary_file}"
}

# ---------------------------------------------------------------------------
# 메인 (Main)
# ---------------------------------------------------------------------------

main() {
    echo ""
    echo "============================================="
    echo " QoverwRap 물리 기기 테스트 오케스트레이터"
    echo " Physical Device Test Orchestrator"
    echo "============================================="
    echo " 기기 / Device   : ${DEVICE}"
    echo " QR 수 / Count   : ${QR_COUNT}"
    echo " 디스플레이 포트 / Display port: ${DISPLAY_PORT}"
    echo " 전환 간격 / Interval: ${DISPLAY_INTERVAL}s"
    echo "============================================="
    echo ""

    # 결과 디렉터리 준비 / Prepare results directory
    mkdir -p "${RESULTS_DIR}" "${RESULTS_BASE}"

    # 1. 사전 조건 확인
    check_prerequisites

    # 2. 디스플레이 서버 시작
    start_display_server

    # 3. 기기 위치 확인 대기
    wait_for_device_positioning

    # 4. Maestro 실행
    if run_maestro; then
        ok "Maestro 플로우 완료 / Maestro flow completed successfully."
    else
        warn "Maestro 플로우가 오류와 함께 완료됨 (결과는 저장됨)"
        warn "Maestro flow completed with errors (results still saved)"
    fi

    # 5. 결과 수집
    collect_results

    echo ""
    ok "완료! / Done!"
    echo ""
    echo "결과 분석 / Analyze results:"
    echo "  python scripts/collect-results.py --results-dir ${RESULTS_DIR}"
    echo ""
}

main "$@"
