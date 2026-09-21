import Link from "next/link";

export default function Home() {
  return (
    <main className="grid min-h-screen place-items-center px-6 py-16">
      <section className="w-full max-w-3xl rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60 sm:p-12">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">ClassMind AI</p>
        <h1 className="max-w-xl text-4xl font-bold tracking-tight text-slate-950 sm:text-6xl">A clearer view of classroom engagement.</h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">Join a classroom as a student, preview your camera, and share engagement updates with your teacher in real time.</p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link className="rounded-xl bg-indigo-600 px-5 py-3 text-center font-semibold text-white transition hover:bg-indigo-700" href="/join">Join a classroom</Link>
          <Link className="rounded-xl border border-slate-300 px-5 py-3 text-center font-semibold text-slate-700 transition hover:bg-slate-50" href="/teacher">Teacher dashboard</Link>
        </div>
      </section>
    </main>
  );
}
