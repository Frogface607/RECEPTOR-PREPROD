"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Loader2,
  LockKeyhole,
  Mail,
  UserRound,
} from "lucide-react";
import { normalizeStaffLoginToEmail } from "@/lib/auth/staff-login";
import { getBrowserSupabase } from "@/lib/db/browser";

type AuthMode = "password" | "magic";

type State =
  | { status: "idle" }
  | { status: "sending" }
  | { status: "sent"; email: string }
  | { status: "error"; message: string };

function safeNextPath(value: string): string {
  return value.startsWith("/") && !value.startsWith("//")
    ? value
    : "/me";
}

export function AuthForm({
  demoMode,
  developerMode,
  developerError,
  nextPath,
}: {
  demoMode: boolean;
  developerMode: boolean;
  developerError: boolean;
  nextPath: string;
}) {
  const [mode, setMode] = useState<AuthMode>("password");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (state.status === "sending") return;

    const email = normalizeStaffLoginToEmail(login);
    if (!email) {
      setState({
        status: "error",
        message:
          "Введите email или короткий латинский логин: masha, chef01, manager.bar.",
      });
      return;
    }

    if (mode === "password" && password.length < 6) {
      setState({
        status: "error",
        message: "Пароль должен быть не короче 6 символов.",
      });
      return;
    }

    const supabase = getBrowserSupabase();
    if (!supabase) {
      setState({
        status: "error",
        message: "Auth is not configured in this environment.",
      });
      return;
    }

    setState({ status: "sending" });
    const { error } =
      mode === "password"
        ? await supabase.auth.signInWithPassword({
            email,
            password,
          })
        : await supabase.auth.signInWithOtp({
            email,
            options: {
              emailRedirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(safeNextPath(nextPath))}`,
            },
          });

    if (error) {
      setState({ status: "error", message: error.message });
    } else if (mode === "password") {
      window.location.assign(safeNextPath(nextPath));
    } else {
      setState({ status: "sent", email });
    }
  };

  if (state.status === "sent") {
    return (
      <div className="rounded-xl border border-border/60 bg-card/55 p-8 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
          <CheckCircle2 className="size-6" />
        </div>
        <h2 className="mt-5 text-xl font-medium tracking-[-0.01em]">
          Письмо отправлено
        </h2>
        <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
          Ссылка для входа ушла на{" "}
          <span className="text-foreground">{state.email}</span>. Открой ее на
          этом устройстве, чтобы попасть в Receptor.
        </p>
        <button
          type="button"
          onClick={() => setState({ status: "idle" })}
          className="mt-6 text-[13px] text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
        >
          Ввести другой адрес
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border/60 bg-card/55 p-8">
      <h1 className="text-2xl font-medium tracking-[-0.02em]">Вход в Receptor</h1>
      <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">
        Войдите по логину и паролю, который выдал администратор ресторана.
      </p>

      <div className="mt-6 grid grid-cols-2 rounded-lg border border-border/60 bg-background/50 p-1">
        <button
          type="button"
          onClick={() => {
            setMode("password");
            setState({ status: "idle" });
          }}
          className={
            "rounded-md px-3 py-2 text-sm transition-colors " +
            (mode === "password"
              ? "bg-card text-foreground"
              : "text-muted-foreground hover:text-foreground")
          }
        >
          Логин
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("magic");
            setState({ status: "idle" });
          }}
          className={
            "rounded-md px-3 py-2 text-sm transition-colors " +
            (mode === "magic"
              ? "bg-card text-foreground"
              : "text-muted-foreground hover:text-foreground")
          }
        >
          Email-ссылка
        </button>
      </div>

      <form onSubmit={onSubmit} className="mt-7 flex flex-col gap-3">
        <div className="relative">
          {mode === "password" ? (
            <UserRound className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          ) : (
            <Mail className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          )}
          <input
            type="text"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            placeholder={mode === "password" ? "masha или name@company.ru" : "name@company.ru"}
            autoComplete={mode === "password" ? "username" : "email"}
            required
            className="w-full rounded-lg border border-border/60 bg-background/60 py-3 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-brand/50 focus:outline-none"
          />
        </div>

        {mode === "password" ? (
          <div className="relative">
            <LockKeyhole className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Пароль"
              autoComplete="current-password"
              required
              className="w-full rounded-lg border border-border/60 bg-background/60 py-3 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-brand/50 focus:outline-none"
            />
          </div>
        ) : null}

        <button
          type="submit"
          disabled={state.status === "sending"}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-50"
        >
          {state.status === "sending" ? (
            <>
              <Loader2 className="size-4 animate-spin" /> Проверяю...
            </>
          ) : mode === "password" ? (
            <>
              Войти <ArrowRight className="size-4" />
            </>
          ) : (
            <>
              Прислать ссылку <ArrowRight className="size-4" />
            </>
          )}
        </button>

        {state.status === "error" ? (
          <p className="text-[13px] text-destructive">{state.message}</p>
        ) : null}
      </form>

      {mode === "password" ? (
        <p className="mt-4 text-[12px] leading-relaxed text-muted-foreground">
          Короткий логин автоматически превращается во внутренний email вида
          login@staff.receptorai.pro. Для владельца можно использовать обычный
          email.
        </p>
      ) : null}

      {developerMode ? (
        <div className="mt-7 border-t border-border/40 pt-6">
          <p className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
            Developer access
          </p>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            Для тестирования без email-ссылки. Доступ появляется только когда
            включены dev-переменные окружения.
          </p>
          <form action="/api/auth/dev" method="post" className="mt-4 space-y-3">
            <input type="hidden" name="next" value={safeNextPath(nextPath)} />
            <div className="relative">
              <LockKeyhole className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="password"
                name="accessKey"
                placeholder="Developer key"
                required
                className="w-full rounded-lg border border-border/60 bg-background/60 py-2.5 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-brand/50 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border/60 bg-background/60 px-4 text-sm text-foreground transition-colors hover:border-brand/40 hover:bg-card"
            >
              Войти как разработчик
              <ArrowRight className="size-4 text-brand" />
            </button>
            {developerError ? (
              <p className="text-[13px] text-destructive">
                Ключ не подошел. Проверь RECEPTOR_DEV_ACCESS_KEY.
              </p>
            ) : null}
          </form>
        </div>
      ) : demoMode ? (
        <div className="mt-7 border-t border-border/40 pt-6">
          <p className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
            Режим разработчика
          </p>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            Auth еще не настроен в этом окружении. Можно открыть рабочий
            кабинет для проверки сценария.
          </p>
          <Link
            href="/dashboard/dev-venue"
            className="mt-4 inline-flex items-center gap-2 rounded-lg border border-border/60 bg-background/60 px-4 py-2.5 text-sm text-foreground transition-colors hover:border-brand/40 hover:bg-card"
          >
            Открыть кабинет
            <ArrowRight className="size-4 text-brand" />
          </Link>
        </div>
      ) : null}
    </div>
  );
}
