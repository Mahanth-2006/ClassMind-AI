"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

type Connection = "connecting" | "live" | "offline";
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

export default function ClassroomClient() {
  const search = useSearchParams();
  const name = search.get("name") || "Student";
  const room = search.get("room") || "DEMO-101";
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [cameraState, setCameraState] = useState<"idle" | "ready" | "blocked">("idle");
  const [connection, setConnection] = useState<Connection>(WS_URL ? "connecting" : "offline");
  const [engagement, setEngagement] = useState(82);

  useEffect(() => {
    if (!WS_URL) return;
    const url = new URL(WS_URL);
    url.searchParams.set("room", room);
    url.searchParams.set("student", name);
    const socket = new WebSocket(url);
    socketRef.current = socket;
    socket.onopen = () => setConnection("live");
    socket.onerror = () => setConnection("offline");
    socket.onclose = () => setConnection("offline");
    socket.onmessage = (event) => {
      try { const data = JSON.parse(event.data) as { engagement?: number }; if (typeof data.engagement === "number") setEngagement(Math.round(data.engagement)); } catch { /* Ignore non-JSON server messages. */ }
    };
    return () => socket.close();
  }, [name, room]);

  useEffect(() => () => streamRef.current?.getTracks().forEach((track) => track.stop()), []);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setCameraState("ready");
    } catch { setCameraState("blocked"); }
  }

  async function sendCheckIn() {
    const payload = { type: "engagement", room, student: name, engagement, timestamp: new Date().toISOString() };
    if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(JSON.stringify(payload));
    if (API_URL) await fetch(`${API_URL.replace(/\/$/, "")}/engagement`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }).catch(() => undefined);
  }

  const connectionStyle = connection === "live" ? "bg-emerald-100 text-emerald-700" : connection === "connecting" ? "bg-amber-100 text-amber-700" : "bg-slate-200 text-slate-600";
  const connectionLabel = connection === "live" ? "Live connection" : connection === "connecting" ? "Connecting…" : "Offline demo";

  return <main className="min-h-screen px-6 py-8 sm:px-10"><header className="mx-auto flex max-w-6xl items-center justify-between"><Link href="/" className="text-lg font-bold">ClassMind AI</Link><span className={`rounded-full px-3 py-1 text-sm font-semibold ${connectionStyle}`}>{connectionLabel}</span></header><section className="mx-auto mt-10 grid max-w-6xl gap-8 lg:grid-cols-[1.5fr_0.8fr]"><div className="overflow-hidden rounded-3xl bg-slate-950 shadow-2xl"><div className="aspect-video bg-slate-900"><video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />{cameraState !== "ready" && <div className="grid h-full place-items-center p-8 text-center text-slate-300"><div><p className="text-lg font-semibold">Camera preview is off</p><p className="mt-2 text-sm text-slate-400">Your video stays on this device; only engagement metrics are shared.</p><button onClick={startCamera} className="mt-5 rounded-xl bg-indigo-500 px-5 py-3 font-semibold text-white hover:bg-indigo-400">Enable camera</button>{cameraState === "blocked" && <p className="mt-3 text-sm text-rose-300">Camera access was blocked. Update browser permissions and try again.</p>}</div></div>}</div><div className="flex items-center justify-between p-5 text-white"><div><p className="font-semibold">{name}</p><p className="text-sm text-slate-400">Room: {room}</p></div><span className="text-sm text-slate-400">Preview only</span></div></div><aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Your check-in</p><h1 className="mt-2 text-3xl font-bold">Ready to learn?</h1><p className="mt-3 text-slate-600">Adjust the demo score, then send a check-in to the teacher dashboard.</p><div className="mt-8 rounded-2xl bg-indigo-50 p-5"><div className="flex items-end justify-between"><span className="text-sm font-semibold text-indigo-900">Engagement</span><span className="text-4xl font-bold text-indigo-700">{engagement}%</span></div><input aria-label="Engagement score" type="range" min="0" max="100" value={engagement} onChange={(e) => setEngagement(Number(e.target.value))} className="mt-5 w-full accent-indigo-600" /></div><button onClick={sendCheckIn} className="mt-6 w-full rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700">Send check-in</button><p className="mt-4 text-center text-xs text-slate-500">API and WebSocket URLs are configurable in .env.local.</p></aside></section></main>;
}
