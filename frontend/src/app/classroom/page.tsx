import ClassroomClient from "@/components/classroom-client";
import { Suspense } from "react";

export default function ClassroomPage() {
  return <Suspense fallback={<main className="grid min-h-screen place-items-center">Loading classroom…</main>}><ClassroomClient /></Suspense>;
}
