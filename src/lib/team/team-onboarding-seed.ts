import { listLearningItemsForRole } from "./team-learning";
import type { TeamLearningStandardStatus } from "./team-learning-standards";
import type { TeamRoleId, TeamTask } from "./team-os";

export type OnboardingVenueType =
  "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";

export type TeamOnboardingSeedInput = {
  venueId: string;
  venueName: string;
  venueType: OnboardingVenueType;
  ownerUserId: string;
  ownerEmail: string | null;
  createdAt: string;
};

export type TeamOnboardingMembershipRow = {
  venue_id: string;
  user_id: string;
  full_name: string;
  email: string | null;
  role: TeamRoleId;
  status: "active";
  shift_label: string;
  created_by: string;
};

export type TeamOnboardingTaskRow = {
  venue_id: string;
  title: string;
  source: TeamTask["source"];
  priority: TeamTask["priority"];
  status: TeamTask["status"];
  audience_type: "venue";
  audience_member_id: null;
  audience_role: null;
  due_label: string;
  created_by: string;
};

export type TeamOnboardingAnnouncementRow = {
  venue_id: string;
  title: string;
  body: string;
  priority: "important";
  audience_type: "venue";
  audience_role: null;
  created_by: string;
};

export type TeamOnboardingLearningStandardRow = {
  venue_id: string;
  role: TeamRoleId;
  module_id: string;
  status: TeamLearningStandardStatus;
  updated_by: string;
  updated_at: string;
};

export type TeamOnboardingSeed = {
  ownerMembership: TeamOnboardingMembershipRow;
  tasks: TeamOnboardingTaskRow[];
  announcement: TeamOnboardingAnnouncementRow;
  learningStandards: TeamOnboardingLearningStandardRow[];
};

type LearningPreset = {
  role: TeamRoleId;
  moduleId: string;
  status: TeamLearningStandardStatus;
};

const BASE_LEARNING_PRESET: LearningPreset[] = [
  { role: "owner", moduleId: "owner-morning", status: "required" },
  { role: "operations_manager", moduleId: "shift-brief", status: "required" },
  { role: "venue_manager", moduleId: "shift-brief", status: "required" },
  { role: "chef", moduleId: "kitchen-stop-list", status: "required" },
  { role: "chef", moduleId: "tech-card-discipline", status: "required" },
  { role: "line_cook", moduleId: "kitchen-stop-list", status: "required" },
  { role: "service", moduleId: "service-recommendation", status: "required" },
  { role: "service", moduleId: "guest-feedback", status: "required" },
  { role: "marketing", moduleId: "guest-feedback", status: "required" },
];

const COFFEE_LEARNING_PRESET: LearningPreset[] = BASE_LEARNING_PRESET.filter(
  (preset) => preset.role !== "chef" && preset.role !== "line_cook",
);

function learningPresetForVenue(
  venueType: OnboardingVenueType,
): LearningPreset[] {
  if (venueType === "coffee") return COFFEE_LEARNING_PRESET;
  return BASE_LEARNING_PRESET;
}

function ownerNameFromEmail(email: string | null): string {
  if (!email) return "Owner";
  const local = email.split("@")[0]?.trim();
  return local || email;
}

function validLearningPreset(preset: LearningPreset): boolean {
  return listLearningItemsForRole(preset.role).some(
    (item) => item.id === preset.moduleId,
  );
}

export function buildTeamOnboardingSeed(
  input: TeamOnboardingSeedInput,
): TeamOnboardingSeed {
  const venueLabel = input.venueName.trim() || "ресторан";
  const learningStandards = learningPresetForVenue(input.venueType)
    .filter(validLearningPreset)
    .map((preset) => ({
      venue_id: input.venueId,
      role: preset.role,
      module_id: preset.moduleId,
      status: preset.status,
      updated_by: input.ownerUserId,
      updated_at: input.createdAt,
    }));

  return {
    ownerMembership: {
      venue_id: input.venueId,
      user_id: input.ownerUserId,
      full_name: ownerNameFromEmail(input.ownerEmail),
      email: input.ownerEmail,
      role: "owner",
      status: "active",
      shift_label: "owner",
      created_by: input.ownerUserId,
    },
    tasks: [
      {
        venue_id: input.venueId,
        title: "Добавить управляющего и ключевых сотрудников в Team OS",
        source: "copilot",
        priority: "high",
        status: "new",
        audience_type: "venue",
        audience_member_id: null,
        audience_role: null,
        due_label: "сегодня",
        created_by: input.ownerUserId,
      },
      {
        venue_id: input.venueId,
        title: "Заполнить ставки ФОТ для сотрудников из iiko",
        source: "copilot",
        priority: "high",
        status: "new",
        audience_type: "venue",
        audience_member_id: null,
        audience_role: null,
        due_label: "сегодня",
        created_by: input.ownerUserId,
      },
      {
        venue_id: input.venueId,
        title: "Проверить техкарты и закупочные цены для маржи",
        source: "copilot",
        priority: "high",
        status: "new",
        audience_type: "venue",
        audience_member_id: null,
        audience_role: null,
        due_label: "до первого разбора",
        created_by: input.ownerUserId,
      },
      {
        venue_id: input.venueId,
        title: "Утвердить стандарты допуска к смене по ролям",
        source: "copilot",
        priority: "medium",
        status: "new",
        audience_type: "venue",
        audience_member_id: null,
        audience_role: null,
        due_label: "на этой неделе",
        created_by: input.ownerUserId,
      },
    ],
    announcement: {
      venue_id: input.venueId,
      title: "Receptor подключен",
      body: `${venueLabel}: стартовый контур создан. Первые шаги - команда, ставки ФОТ, техкарты и стандарты допуска.`,
      priority: "important",
      audience_type: "venue",
      audience_role: null,
      created_by: input.ownerUserId,
    },
    learningStandards,
  };
}
