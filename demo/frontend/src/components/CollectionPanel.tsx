import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { BoothInfo, TrustEntry, VisitCollectResponse } from "../types";

// Identity-blind display: marker timestamps shown in a fixed TZ (ThemedCard's
// fmtDateTime is private, so format inline — same ko-KR / Asia/Seoul contract).
const _VISITED_FMT = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  dateStyle: "medium",
  timeStyle: "short",
});
function fmtVisited(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : _VISITED_FMT.format(d);
}

interface CollectedBadge {
  booth_id: string;
  booth_name: string;
  emoji: string;
  visitor_token: string;
  visited_at: string;
}

interface Props {
  /** The attendee's ticket — the QR built in the issue step. */
  ticketPayload: string | null;
  /** Trust entries, reused only for the operator's theme color. */
  trust: TrustEntry[];
  screenshot?: boolean;
}

export default function CollectionPanel({ ticketPayload, trust, screenshot }: Props) {
  const [booths, setBooths] = useState<BoothInfo[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [useManual, setUseManual] = useState(false);
  const [manualTicket, setManualTicket] = useState("");
  const [collected, setCollected] = useState<Record<string, CollectedBadge>>({});
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .booths()
      .then((r) => setBooths(r.booths))
      .catch((e) => setStatus(String(e)));
  }, []);

  const activeTicket = useManual ? manualTicket.trim() : (ticketPayload ?? "");
  const themeFor = (issuerId: string) =>
    trust.find((t) => t.issuer_id === issuerId)?.theme_color ?? "#0f172a";

  async function collectVisit() {
    if (!selected || !activeTicket) return;
    setBusy(true);
    setStatus(null);
    try {
      const res: VisitCollectResponse = await api.visitCollect(activeTicket, selected);
      if (res.status === "collected") {
        setCollected((prev) => ({
          ...prev,
          [res.booth_id]: {
            booth_id: res.booth_id,
            booth_name: res.booth_name ?? res.booth_id,
            emoji: res.emoji ?? "🎖️",
            visitor_token: res.visitor_token ?? "",
            visited_at: res.visited_at ?? "",
          },
        }));
        setStatus(`✓ 뱃지 획득 — ${res.booth_name ?? res.booth_id}`);
        setSelected(null);
      } else if (res.status === "already_collected") {
        setStatus(`이미 수집한 부스입니다 — ${res.booth_name ?? selected}`);
      } else if (res.status === "wrong_issuer") {
        setStatus("이 부스(행사)의 티켓이 아닙니다 — 해당 행사 티켓으로만 수집됩니다");
      } else {
        setStatus("유효한 티켓이 아닙니다 (서명 검증 실패 — 진짜 회원만 수집 가능)");
      }
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const hasTicket = activeTicket.length > 0;

  return (
    <div className="space-y-4">
      {/* Ticket source */}
      {!screenshot && (
        <div className="rounded-lg border border-slate-200 p-3 space-y-2">
          <div className="text-sm font-medium">내 티켓 (자격 증명)</div>
          <label className="flex items-center gap-1.5 text-xs text-slate-600">
            <input
              data-testid="collect-from-last-ticket"
              type="checkbox"
              checked={!useManual}
              onChange={() => setUseManual(false)}
              className="rounded border-slate-300"
            />
            방금 만든 티켓 사용
            {ticketPayload ? (
              <span className="text-emerald-600">✓ 준비됨</span>
            ) : (
              <span className="text-amber-600">— 먼저 1~3단계에서 티켓을 발급하세요</span>
            )}
          </label>
          <label className="flex items-start gap-1.5 text-xs text-slate-600">
            <input
              type="checkbox"
              checked={useManual}
              onChange={(e) => setUseManual(e.target.checked)}
              className="mt-1 rounded border-slate-300"
            />
            <span className="flex-1">
              다른 티켓 직접 입력
              {useManual && (
                <textarea
                  value={manualTicket}
                  onChange={(e) => setManualTicket(e.target.value)}
                  rows={3}
                  placeholder="티켓 QR payload 문자열 붙여넣기"
                  className="mt-1 w-full px-2 py-1.5 border border-slate-300 rounded text-xs font-mono"
                />
              )}
            </span>
          </label>
        </div>
      )}

      {/* Collect action */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          data-testid="collect-visit"
          onClick={collectVisit}
          disabled={!selected || !hasTicket || busy}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
        >
          {selected ? "이 부스 방문 (마커 받기)" : "아래에서 부스를 먼저 선택하세요"}
        </button>
        {status && (
          <span
            data-testid="collect-status"
            className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700"
          >
            {status}
          </span>
        )}
      </div>

      {/* Badge grid: each booth is a slot — locked until collected. Selecting a
          locked booth arms the collect button. Distinct booth_id ⇒ distinct badge. */}
      <div
        data-testid="collection-grid"
        className="grid grid-cols-2 sm:grid-cols-3 gap-3"
      >
        {booths.map((b) => {
          const got = collected[b.booth_id];
          const isSel = selected === b.booth_id;
          return (
            <div
              key={b.booth_id}
              data-testid={`badge-${b.booth_id}`}
              data-collected={got ? "true" : "false"}
              className={`rounded-xl p-4 text-white border-2 transition ${
                got
                  ? "border-emerald-400"
                  : isSel
                    ? "border-slate-100"
                    : "border-transparent"
              }`}
              style={{ background: got ? themeFor(b.issuer_id) : "#1e293b" }}
            >
              <div className="text-3xl mb-1">{got ? b.emoji : "🔒"}</div>
              <div className="font-semibold text-sm leading-tight">{b.booth_name}</div>
              {got ? (
                <>
                  <div className="text-[11px] text-emerald-300 mt-1">✓ 방문 인증</div>
                  {got.visited_at && (
                    <div className="text-[10px] opacity-80 mt-0.5">
                      {fmtVisited(got.visited_at)}
                    </div>
                  )}
                  <div
                    data-testid="badge-visitor-token"
                    className="text-[10px] font-mono opacity-70 mt-1"
                  >
                    방문자 #{got.visitor_token.slice(0, 8)}
                  </div>
                </>
              ) : (
                <button
                  data-testid={`booth-${b.booth_id}`}
                  onClick={() => setSelected(b.booth_id)}
                  className="mt-2 text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20"
                >
                  {isSel ? "선택됨" : "이 부스 선택"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {!screenshot && (
        <p className="text-[11px] text-slate-400">
          신원 비노출: 뱃지에는 실명·좌석이 없고 방문자 토큰(같은 티켓끼리만 묶임)만
          남습니다. "내 얼굴은 숨기되, 내가 거기 갔음은 증명".
        </p>
      )}
    </div>
  );
}
