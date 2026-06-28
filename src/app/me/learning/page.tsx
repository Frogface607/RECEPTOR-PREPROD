import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowLeft, GraduationCap, LogOut } from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { Badge } from "@/components/ui/badge";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import { getLearningItem } from "@/lib/team/team-learning";
import { listLearningItemsForRoleWithStandards } from "@/lib/team/team-learning-standards";
import { progressToSnapshotMap } from "@/lib/team/team-learning-progress";
import { getTeamRole } from "@/lib/team/team-os";
import { getPersonalTeamWorkspace } from "@/lib/team/team-store";
import { LearningWorkspace } from "./learning-workspace";

export const metadata: Metadata = {
  title: "Обучение — RECEPTOR",
  description: "Материалы, стандарты и тесты сотрудника в Receptor.",
};

function parseParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

async function getFirstOwnedVenueId(): Promise<string | null> {
  const [user, supabase] = await Promise.all([
    getCurrentUser(),
    getServerSupabase(),
  ]);
  if (!user || user.isDemo || !supabase) return null;

  const { data } = await supabase
    .from("venues")
    .select("id")
    .eq("owner_user_id", user.id)
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle<{ id: string }>();

  return data?.id ?? null;
}

export default async function EmployeeLearningPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [workspace, sp] = await Promise.all([
    getPersonalTeamWorkspace(),
    searchParams,
  ]);

  if (!workspace.ok) {
    if (workspace.reason === "unauthenticated" && isSupabaseConfigured()) {
      redirect("/auth?next=/me/learning");
    }
    if (workspace.reason === "no_membership" && isSupabaseConfigured()) {
      const venueId = await getFirstOwnedVenueId();
      if (venueId) {
        redirect(`/dashboard/${venueId}`);
      }
      redirect("/onboarding?new=1");
    }

    return (
      <AppShell activeHref="/me" chat={false}>
        <main className="flex-1">
          <section className="mx-auto max-w-3xl px-6 py-20">
            <Badge variant="outline" className="border-brand/30 text-brand">
              Обучение
            </Badge>
            <h1 className="mt-6 text-4xl font-medium">
              Для обучения нужна роль в заведении.
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Попросите владельца или управляющего добавить сотрудника в Team OS
              и выдать доступ.
            </p>
            <Link
              href="/auth/signout"
              prefetch={false}
              className="mt-8 inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-4 text-sm text-foreground transition-colors hover:border-brand/40"
            >
              <LogOut className="size-4" />
              Выйти
            </Link>
          </section>
        </main>
      </AppShell>
    );
  }

  const role = getTeamRole(workspace.member.roleId);
  const learningItems = listLearningItemsForRoleWithStandards(
    workspace.member.roleId,
    workspace.learningStandards,
  );
  const requestedModule = parseParam(sp.module);
  const initialModule =
    learningItems.find((item) => item.id === requestedModule) ??
    getLearningItem(requestedModule) ??
    learningItems[0];

  return (
    <AppShell
      activeHref="/me"
      venueId={workspace.venueId}
      venueName={workspace.venueName}
      venueMeta="Обучение"
    >
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-8">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <Link
                  href="/me"
                  className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  <ArrowLeft className="size-4" />
                  Мой кабинет
                </Link>
                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <Badge
                    variant="outline"
                    className="border-brand/30 text-brand"
                  >
                    Обучение
                  </Badge>
                  <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    {role.title}
                  </span>
                </div>
                <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2rem,4vw,3.25rem)] font-medium leading-[1.04]">
                  Стандарты смены и короткие тесты.
                </h1>
                <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                  {workspace.member.name} · {workspace.venueName}. Материалы
                  привязаны к роли и ежедневным задачам.
                </p>
              </div>
              <div className="rounded-lg border border-border/60 bg-card/50 p-4">
                <div className="flex items-center gap-3">
                  <GraduationCap className="size-5 text-brand" />
                  <div>
                    <p className="text-sm font-medium">Допуск к стандарту</p>
                    <p className="mt-1 text-[12px] text-muted-foreground">
                      Проходной балл указан внутри каждого материала.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <LearningWorkspace
          items={learningItems}
          initialModuleId={initialModule?.id ?? learningItems[0]?.id ?? ""}
          initialProgress={progressToSnapshotMap(workspace.learningProgress)}
          memberName={workspace.member.name}
          roleTitle={role.title}
          venueId={workspace.venueId}
          venueName={workspace.venueName}
        />
      </main>
    </AppShell>
  );
}
