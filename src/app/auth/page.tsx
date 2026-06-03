import type { Metadata } from "next";
import Link from "next/link";
import { AuthForm } from "./auth-form";
import { isSupabaseConfigured } from "@/lib/db/env";

export const metadata: Metadata = {
  title: "Вход — RECEPTOR",
};

export default function AuthPage() {
  const demoMode = !isSupabaseConfigured();

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 py-16">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-20%] h-[520px] w-[700px] -translate-x-1/2 rounded-full bg-brand/12 blur-[150px]" />
      </div>

      <div className="w-full max-w-md">
        <Link
          href="/"
          className="mb-10 flex items-baseline justify-center gap-2"
        >
          <span className="text-[15px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
          <span className="font-display italic text-muted-foreground text-[15px]">
            чувствует кухню
          </span>
        </Link>

        <AuthForm demoMode={demoMode} />

        <p className="mt-8 text-center text-[12px] text-muted-foreground">
          Нажимая «Прислать ссылку», вы соглашаетесь с условиями использования.
        </p>
      </div>
    </main>
  );
}
