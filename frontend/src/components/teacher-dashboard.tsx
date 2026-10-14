"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";

type Student = { name: string; engagement: number; status: string };
type RequestState = "loading" | "ready" | "empty" | "error" | "not-configured";
type IconName = "alert" | "calendar" | "chart" | "grid" | "pulse" | "refresh" | "spark" | "users";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const navigation: { label: string; href: string; icon: IconName }[] = [
  { label: "Overview", href: "#overview", icon: "grid" },
  { label: "Recent sessions", href: "#sessions", icon: "calendar" },
  { label: "System health", href: "#health", icon: "pulse" },
];

export default function TeacherDashboard() {
  const [students, setStudents] = useState<Student[]>([]);
  const [state, setState] = useState<RequestState>(API_URL ? "loading" : "not-configured");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadEngagement = useCallback(async () => {
    if (!API_URL) return;
    setState("loading");
    try {
      const response = await fetch(`${API_URL.replace(/\/$/, "")}/classrooms/DEMO-101/engagement`);
      if (!response.ok) throw new Error("Engagement request failed");
      const payload: unknown = await response.json();
      if (!Array.isArray(payload)) throw new Error("Unexpected engagement response");
      const records = payload.filter(isStudent);
      setStudents(records);
      setState(records.length ? "ready" : "empty");
      setLastUpdated(new Date());
    } catch {
      setStudents([]);
      setState("error");
    }
  }, []);

  useEffect(() => { void loadEngagement(); }, [loadEngagement]);

  const hasData = state === "ready";
  const average = students.length ? Math.round(students.reduce((total, student) => total + student.engagement, 0) / students.length) : null;
  const needsAttention = students.filter((student) => student.engagement < 60).length;

  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto flex min-h-screen max-w-[1440px]">
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-5 py-7 lg:flex">
      <Link href="/" className="flex items-center gap-3 px-3 text-lg font-bold tracking-tight"><span className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white"><Icon name="spark" /></span>ClassMind</Link>
      <p className="mt-10 px-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
      <nav className="mt-3 space-y-1" aria-label="Dashboard sections">{navigation.map((item) => <a key={item.label} href={item.href} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 first:bg-indigo-50 first:text-indigo-700"><Icon name={item.icon} />{item.label}</a>)}</nav>
      <div className="mt-auto rounded-2xl border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-900"><p className="font-bold">Mathematics 101</p><p className="mt-1 leading-5 text-indigo-700">Room DEMO-101</p></div>
    </aside>

    <div className="min-w-0 flex-1 px-5 py-6 sm:px-8 lg:px-10">
      <header className="flex items-center justify-between border-b border-slate-200 pb-5"><div className="flex items-center gap-3 lg:hidden"><span className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white"><Icon name="spark" /></span><span className="font-bold">ClassMind</span></div><p className="hidden text-sm text-slate-500 lg:block">Administrator workspace</p><Link href="/join" className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700">Open student join</Link></header>

      <section id="overview" className="pt-9"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold text-indigo-600">Dashboard overview</p><h1 className="mt-1 text-3xl font-bold tracking-tight sm:text-4xl">Classroom activity</h1><p className="mt-2 text-sm text-slate-500">A concise view of the current Mathematics 101 room.</p></div><button onClick={() => void loadEngagement()} disabled={state === "loading" || state === "not-configured"} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"><Icon name="refresh" />{state === "loading" ? "Refreshing" : "Refresh data"}</button></div>
        <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><MetricCard title="Active students" value={hasData ? students.length.toLocaleString() : "—"} detail={metricDetail(state, "students checked in")} icon="users" /><MetricCard title="Average engagement" value={hasData && average !== null ? `${average}%` : "—"} detail={metricDetail(state, "from current check-ins")} icon="chart" /><MetricCard title="Needs attention" value={hasData ? needsAttention.toLocaleString() : "—"} detail={metricDetail(state, "below 60% engagement")} icon="alert" /></div>
        <div className="mt-6 grid gap-6 xl:grid-cols-[1.6fr_0.9fr]"><section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-bold">Engagement trend</p><p className="mt-1 text-sm text-slate-500">Session history over time</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">No history source</span></div><UnavailableChart /></section><section id="health" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div><p className="text-sm font-bold">System health</p><p className="mt-1 text-sm text-slate-500">Service signals exposed to this dashboard</p></div><div className="mt-5 space-y-1"><HealthRow name="Backend API" status={API_URL ? state === "ready" || state === "empty" ? "Available" : state === "error" ? "Unavailable" : "Checking" : "Not configured"} tone={API_URL ? state === "error" ? "red" : state === "ready" || state === "empty" ? "green" : "amber" : "slate"} /><HealthRow name="AI engine" status="Unknown" tone="slate" /><HealthRow name="WebSocket service" status={process.env.NEXT_PUBLIC_WS_URL ? "Unknown" : "Not configured"} tone="slate" /><HealthRow name="Database" status="Unknown" tone="slate" /></div><p className="mt-5 text-xs leading-5 text-slate-500">Only the existing engagement endpoint is checked. No dedicated health endpoint is available.</p></section></div>
      </section>

      <section id="sessions" className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-6 py-5"><div><h2 className="font-bold">Recent classroom sessions</h2><p className="mt-1 text-sm text-slate-500">Latest completed and active classroom sessions</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">No sessions endpoint</span></div><div className="grid min-h-48 place-items-center px-6 py-10 text-center"><div className="max-w-sm"><span className="mx-auto grid size-11 place-items-center rounded-xl bg-slate-100 text-slate-500"><Icon name="calendar" /></span><p className="mt-4 font-semibold">Session history is not available yet</p><p className="mt-2 text-sm leading-6 text-slate-500">Connect a session-history endpoint to show classroom name, teacher, duration, participants, and session status here.</p></div></div></section>

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-6 py-5"><div><h2 className="font-bold">Current student engagement</h2><p className="mt-1 text-sm text-slate-500">{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Awaiting a data refresh"}</p></div><StateBadge state={state} /></div>{state === "loading" ? <LoadingRows /> : state === "ready" ? <StudentTable students={students} /> : <EngagementState state={state} onRetry={loadEngagement} />}</section>
    </div>
  </div></main>;
}

function isStudent(value: unknown): value is Student { return typeof value === "object" && value !== null && typeof (value as Student).name === "string" && typeof (value as Student).engagement === "number" && typeof (value as Student).status === "string"; }
function metricDetail(state: RequestState, readyText: string) { if (state === "not-configured") return "API not configured"; if (state === "error") return "Data currently unavailable"; if (state === "empty") return "No active check-ins"; if (state === "loading") return "Loading current data"; return readyText; }
function MetricCard({ title, value, detail, icon }: { title: string; value: string | number; detail: string; icon: IconName }) { return <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-start justify-between"><div><p className="text-sm font-semibold text-slate-500">{title}</p><p className="mt-3 text-3xl font-bold tracking-tight">{value}</p></div><span className="grid size-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Icon name={icon} /></span></div><p className="mt-3 text-sm text-slate-500">{detail}</p></article>; }
function UnavailableChart() { return <div className="mt-6 grid min-h-56 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50 px-6 text-center"><div><span className="mx-auto grid size-11 place-items-center rounded-xl bg-white text-slate-400 shadow-sm"><Icon name="chart" /></span><p className="mt-4 font-semibold text-slate-700">No engagement history to plot</p><p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">The current API returns live student check-ins only. A time-series endpoint is needed before this chart can show verified trends.</p></div></div>; }
function HealthRow({ name, status, tone }: { name: string; status: string; tone: "green" | "amber" | "red" | "slate" }) { const colors = { green: "bg-emerald-500", amber: "bg-amber-500", red: "bg-rose-500", slate: "bg-slate-400" }; return <div className="flex items-center justify-between py-2.5"><span className="text-sm font-medium text-slate-700">{name}</span><span className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500"><span className={`size-2 rounded-full ${colors[tone]}`} />{status}</span></div>; }
function StateBadge({ state }: { state: RequestState }) { const text = state === "ready" ? "Live data" : state === "loading" ? "Loading" : state === "empty" ? "No check-ins" : state === "error" ? "Unavailable" : "Not configured"; const style = state === "ready" ? "bg-emerald-50 text-emerald-700" : state === "error" ? "bg-rose-50 text-rose-700" : "bg-slate-100 text-slate-600"; return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${style}`}>{text}</span>; }
function LoadingRows() { return <div className="space-y-4 p-6">{[0, 1, 2].map((row) => <div key={row} className="h-12 animate-pulse rounded-lg bg-slate-100" />)}</div>; }
function EngagementState({ state, onRetry }: { state: RequestState; onRetry: () => Promise<void> }) { const content = state === "not-configured" ? ["Connect the API to see engagement", "Set NEXT_PUBLIC_API_URL in .env.local, then restart the development server."] : state === "error" ? ["Engagement data could not be loaded", "The existing engagement endpoint did not return a usable response."] : ["No students have checked in", "This classroom has not received any engagement records yet."]; return <div className="grid min-h-56 place-items-center px-6 py-10 text-center"><div className="max-w-sm"><span className="mx-auto grid size-11 place-items-center rounded-xl bg-slate-100 text-slate-500"><Icon name="users" /></span><p className="mt-4 font-semibold">{content[0]}</p><p className="mt-2 text-sm leading-6 text-slate-500">{content[1]}</p>{state === "error" && <button onClick={() => void onRetry()} className="mt-5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Try again</button>}</div></div>; }
function StudentTable({ students }: { students: Student[] }) { return <div className="divide-y divide-slate-100">{students.map((student) => <div key={student.name} className="grid grid-cols-[1fr_auto] items-center gap-4 px-6 py-4 sm:grid-cols-[1fr_180px_120px]"><div><p className="font-semibold text-slate-800">{student.name}</p><p className="mt-0.5 text-sm text-slate-500">{student.status}</p></div><div className="hidden h-2 overflow-hidden rounded-full bg-slate-100 sm:block"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.min(100, Math.max(0, student.engagement))}%` }} /></div><span className="text-right font-bold text-indigo-700">{Math.round(student.engagement)}%</span></div>)}</div>; }
function Icon({ name }: { name: IconName }) { const paths: Record<IconName, ReactNode> = { grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>, calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4M17 3v4M3 10h18" /></>, pulse: <path d="M3 12h4l2.2-5 4 10 2.1-5H21" />, users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></>, chart: <><path d="M3 3v18h18" /><path d="m7 16 4-5 3 3 5-7" /></>, alert: <><path d="M10.3 3.3 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.3a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4M12 17h.01" /></>, refresh: <><path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 5v4h4" /><path d="M4 13a8.1 8.1 0 0 0 15.5 2M20 19v-4h-4" /></>, spark: <path d="m12 2 1.7 6.3L20 10l-6.3 1.7L12 18l-1.7-6.3L4 10l6.3-1.7L12 2Z" /> }; return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-5">{paths[name]}</svg>; }
