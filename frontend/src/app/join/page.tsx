"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function JoinPage() {
  const router = useRouter(); const [name, setName] = useState(""); const [roomCode, setRoomCode] = useState("");
  function join(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (name.trim() && roomCode.trim()) router.push(`/classroom?name=${encodeURIComponent(name.trim())}&room=${encodeURIComponent(roomCode.trim())}`); }
  return <main className="grid min-h-screen place-items-center px-6 py-12"><form onSubmit={join} className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">Student access</p><h1 className="mt-3 text-3xl font-bold tracking-tight">Join your classroom</h1><p className="mt-2 text-slate-600">Enter the details given by your teacher.</p><label className="mt-7 block text-sm font-semibold text-slate-700">Your name<input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Aarav Patel" className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none ring-indigo-500 focus:ring-2" /></label><label className="mt-5 block text-sm font-semibold text-slate-700">Classroom code<input value={roomCode} onChange={(e) => setRoomCode(e.target.value.toUpperCase())} required placeholder="MATH-101" className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 uppercase outline-none ring-indigo-500 focus:ring-2" /></label><button className="mt-7 w-full rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white transition hover:bg-indigo-700">Continue to camera check</button></form></main>;
}
