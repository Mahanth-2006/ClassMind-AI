"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Student = { name: string; engagement: number; status: string };
const mockStudents: Student[] = [{ name: "Aarav Patel", engagement: 91, status: "Focused" }, { name: "Meera Shah", engagement: 76, status: "Participating" }, { name: "Kabir Singh", engagement: 54, status: "Needs check-in" }, { name: "Anaya Rao", engagement: 88, status: "Focused" }];
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function TeacherDashboard() {
  const [students, setStudents] = useState(mockStudents);
  useEffect(() => { if (!API_URL) return; fetch(`${API_URL.replace(/\/$/, "")}/classrooms/DEMO-101/engagement`).then((r) => r.ok ? r.json() : Promise.reject()).then((data: Student[]) => Array.isArray(data) && setStudents(data)).catch(() => undefined); }, []);
  const average = Math.round(students.reduce((sum, student) => sum + student.engagement, 0) / students.length);
  return <main className="min-h-screen px-6 py-8 sm:px-10"><header className="mx-auto flex max-w-6xl items-center justify-between"><Link href="/" className="text-lg font-bold">ClassMind AI</Link><span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">Class live</span></header><section className="mx-auto mt-10 max-w-6xl"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Teacher dashboard</p><div className="mt-2 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-4xl font-bold tracking-tight">Mathematics 101</h1><p className="mt-2 text-slate-600">Live engagement overview · Room DEMO-101</p></div><Link href="/join" className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700">Share join link</Link></div><div className="mt-8 grid gap-4 sm:grid-cols-3"><Metric title="Average engagement" value={`${average}%`} detail="Across active students" /><Metric title="Students online" value={`${students.length}`} detail="All checked in" /><Metric title="Needs attention" value={`${students.filter((s) => s.engagement < 60).length}`} detail="Below 60% engagement" /></div><div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="border-b border-slate-200 px-6 py-5"><h2 className="font-bold">Student engagement</h2></div><div className="divide-y divide-slate-100">{students.map((student) => <div key={student.name} className="grid grid-cols-[1fr_auto] items-center gap-4 px-6 py-5 sm:grid-cols-[1fr_180px_140px]"><div><p className="font-semibold">{student.name}</p><p className="text-sm text-slate-500">{student.status}</p></div><div className="hidden h-2 overflow-hidden rounded-full bg-slate-100 sm:block"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${student.engagement}%` }} /></div><span className="font-bold text-indigo-700">{student.engagement}%</span></div>)}</div></div></section></main>;
}

function Metric({ title, value, detail }: { title: string; value: string; detail: string }) { return <article className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-sm font-semibold text-slate-500">{title}</p><p className="mt-2 text-3xl font-bold">{value}</p><p className="mt-1 text-sm text-slate-500">{detail}</p></article>; }
