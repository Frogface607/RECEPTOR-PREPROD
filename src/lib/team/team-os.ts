export type TeamRoleId =
  | "owner"
  | "operations_manager"
  | "venue_manager"
  | "chef"
  | "line_cook"
  | "service"
  | "marketing";

export type TeamPermissionId =
  | "view_owner_cockpit"
  | "manage_venue"
  | "manage_staff"
  | "assign_tasks"
  | "view_all_tasks"
  | "complete_own_tasks"
  | "manage_learning"
  | "view_shifts"
  | "manage_menu"
  | "manage_marketing"
  | "view_guest_os";

export type TeamRole = {
  id: TeamRoleId;
  title: string;
  shortTitle: string;
  description: string;
  homeSections: string[];
};

export type TeamPermission = {
  id: TeamPermissionId;
  title: string;
  description: string;
};

export type StaffMember = {
  id: string;
  userId?: string | null;
  name: string;
  email?: string | null;
  roleId: TeamRoleId;
  venueId: string;
  status: "active" | "invited" | "paused";
  shiftLabel: string;
  hourlyRate?: number;
  shiftPay?: number;
  revenueBonusPct?: number;
};

export type TeamTaskAudience =
  | { type: "member"; memberId: string }
  | { type: "role"; roleId: TeamRoleId }
  | { type: "venue"; venueId: string };

export type TeamTask = {
  id: string;
  title: string;
  source: "owner" | "copilot" | "manager" | "chef";
  priority: "high" | "medium" | "low";
  status: "new" | "accepted" | "in_progress" | "done" | "verified";
  venueId: string;
  audience: TeamTaskAudience;
  dueLabel: string;
};

export type TeamTaskComment = {
  id: string;
  venueId: string;
  taskId: string;
  authorName: string;
  body: string;
  createdAtLabel: string;
};

export type TeamAnnouncementAudience =
  | { type: "role"; roleId: TeamRoleId }
  | { type: "venue"; venueId: string };

export type TeamAnnouncement = {
  id: string;
  venueId: string;
  title: string;
  body: string;
  priority: "normal" | "important";
  audience: TeamAnnouncementAudience;
  createdByName: string;
  createdAtLabel: string;
};

export type TeamAuditEventType =
  | "member_invited"
  | "member_status_updated"
  | "member_password_reset"
  | "member_labor_rate_updated"
  | "task_created"
  | "task_status_updated"
  | "comment_added"
  | "announcement_created";

export type TeamAuditEvent = {
  id: string;
  venueId: string;
  type: TeamAuditEventType;
  targetType: "member" | "task" | "comment" | "announcement";
  targetId: string | null;
  summary: string;
  createdAtLabel: string;
};

export type RoleHome = {
  role: TeamRole;
  permissions: TeamPermission[];
  visibleTasks: TeamTask[];
  sections: string[];
};

export const TEAM_PERMISSIONS: TeamPermission[] = [
  {
    id: "view_owner_cockpit",
    title: "Панель владельца",
    description: "Видит выручку, риски, утренний бриф и стратегические выводы.",
  },
  {
    id: "manage_venue",
    title: "Управление заведением",
    description: "Меняет настройки, видит операционный контур и интеграции.",
  },
  {
    id: "manage_staff",
    title: "Сотрудники",
    description: "Приглашает людей, меняет роли и доступы.",
  },
  {
    id: "assign_tasks",
    title: "Постановка задач",
    description: "Назначает задачи людям, ролям или всему заведению.",
  },
  {
    id: "view_all_tasks",
    title: "Все задачи",
    description: "Видит задачи команды и статусы выполнения.",
  },
  {
    id: "complete_own_tasks",
    title: "Мои задачи",
    description: "Принимает и закрывает задачи, назначенные лично или по роли.",
  },
  {
    id: "manage_learning",
    title: "Обучение",
    description: "Видит базу знаний, стандарты, тесты и прогресс команды.",
  },
  {
    id: "view_shifts",
    title: "Смены",
    description: "Видит расписание и свои смены.",
  },
  {
    id: "manage_menu",
    title: "Меню",
    description: "Работает с техкартами, стоп-листом, food cost и фокусом продаж.",
  },
  {
    id: "manage_marketing",
    title: "Маркетинг",
    description: "Готовит акции, события, посты и ответы на отзывы.",
  },
  {
    id: "view_guest_os",
    title: "Гости",
    description: "Видит брони, обращения и гостевые сценарии.",
  },
];

export const TEAM_ROLES: TeamRole[] = [
  {
    id: "owner",
    title: "Владелец",
    shortTitle: "Owner",
    description: "Видит всю систему, деньги, команду, модули и стратегию.",
    homeSections: ["Панель владельца", "Все задачи", "Команда", "Модули"],
  },
  {
    id: "operations_manager",
    title: "Операционный управляющий",
    shortTitle: "Ops",
    description: "Отвечает за несколько точек, задачи, стандарты и контроль.",
    homeSections: ["Дашборды", "Задачи команды", "Смены", "Стандарты"],
  },
  {
    id: "venue_manager",
    title: "Управляющий",
    shortTitle: "Manager",
    description: "Ведет смены, людей, задачи и ежедневную операционку точки.",
    homeSections: ["Сегодня", "Задачи", "Смены", "Объявления"],
  },
  {
    id: "chef",
    title: "Шеф",
    shortTitle: "Chef",
    description: "Отвечает за меню, техкарты, стоп-лист и кухонные задачи.",
    homeSections: ["Кухня", "Меню", "Техкарты", "Задачи"],
  },
  {
    id: "line_cook",
    title: "Повар",
    shortTitle: "Cook",
    description: "Видит свои задачи, смены, техкарты и обучение.",
    homeSections: ["Мои задачи", "Моя смена", "Техкарты", "Обучение"],
  },
  {
    id: "service",
    title: "Официант",
    shortTitle: "Service",
    description: "Видит свои смены, обучение, задачи и фокус продаж.",
    homeSections: ["Мои задачи", "Мои смены", "Обучение", "Фокус продаж"],
  },
  {
    id: "marketing",
    title: "Маркетолог",
    shortTitle: "Marketing",
    description: "Видит события, контент, акции, отзывы и задачи продвижения.",
    homeSections: ["Контент", "События", "Отзывы", "Задачи"],
  },
];

export const ROLE_PERMISSIONS: Record<TeamRoleId, TeamPermissionId[]> = {
  owner: [
    "view_owner_cockpit",
    "manage_venue",
    "manage_staff",
    "assign_tasks",
    "view_all_tasks",
    "manage_learning",
    "view_shifts",
    "manage_menu",
    "manage_marketing",
    "view_guest_os",
  ],
  operations_manager: [
    "view_owner_cockpit",
    "manage_venue",
    "manage_staff",
    "assign_tasks",
    "view_all_tasks",
    "manage_learning",
    "view_shifts",
    "manage_menu",
    "view_guest_os",
  ],
  venue_manager: [
    "assign_tasks",
    "view_all_tasks",
    "manage_learning",
    "view_shifts",
    "manage_menu",
    "view_guest_os",
  ],
  chef: [
    "assign_tasks",
    "view_all_tasks",
    "complete_own_tasks",
    "manage_learning",
    "view_shifts",
    "manage_menu",
  ],
  line_cook: ["complete_own_tasks", "manage_learning", "view_shifts", "manage_menu"],
  service: ["complete_own_tasks", "manage_learning", "view_shifts"],
  marketing: [
    "complete_own_tasks",
    "view_all_tasks",
    "manage_learning",
    "manage_marketing",
    "view_guest_os",
  ],
};

export const DEMO_STAFF: StaffMember[] = [
  {
    id: "staff-owner",
    name: "Сергей",
    roleId: "owner",
    venueId: "dev-venue",
    status: "active",
    shiftLabel: "владелец",
    shiftPay: 0,
  },
  {
    id: "staff-manager",
    name: "Алина",
    roleId: "venue_manager",
    venueId: "dev-venue",
    status: "active",
    shiftLabel: "сегодня 12:00-23:00",
    shiftPay: 4500,
  },
  {
    id: "staff-chef",
    name: "Роман",
    roleId: "chef",
    venueId: "dev-venue",
    status: "active",
    shiftLabel: "кухня 10:00-22:00",
    shiftPay: 5000,
  },
  {
    id: "staff-cook",
    name: "Илья",
    roleId: "line_cook",
    venueId: "dev-venue",
    status: "active",
    shiftLabel: "горячий цех 14:00-23:00",
    hourlyRate: 380,
  },
  {
    id: "staff-service",
    name: "Маша",
    roleId: "service",
    venueId: "dev-venue",
    status: "active",
    shiftLabel: "зал 16:00-00:00",
    hourlyRate: 350,
    revenueBonusPct: 1,
  },
  {
    id: "staff-marketing",
    name: "Катя",
    roleId: "marketing",
    venueId: "dev-venue",
    status: "invited",
    shiftLabel: "удаленно",
    shiftPay: 0,
  },
];

export const DEMO_TEAM_TASKS: TeamTask[] = [
  {
    id: "task-brief-1",
    title: "Разобрать просевшую смену и назвать одну причину до 17:00",
    source: "copilot",
    priority: "high",
    status: "new",
    venueId: "dev-venue",
    audience: { type: "role", roleId: "venue_manager" },
    dueLabel: "сегодня",
  },
  {
    id: "task-menu-1",
    title: "Проверить заготовки и стоп-лист по трем A-позициям",
    source: "owner",
    priority: "high",
    status: "accepted",
    venueId: "dev-venue",
    audience: { type: "role", roleId: "chef" },
    dueLabel: "до вечерней посадки",
  },
  {
    id: "task-service-1",
    title: "Пройти тест по стандарту рекомендации блюд",
    source: "manager",
    priority: "medium",
    status: "in_progress",
    venueId: "dev-venue",
    audience: { type: "role", roleId: "service" },
    dueLabel: "эта неделя",
  },
  {
    id: "task-cook-1",
    title: "Сверить техкарту фирменного блюда с текущей отдачей",
    source: "chef",
    priority: "medium",
    status: "new",
    venueId: "dev-venue",
    audience: { type: "member", memberId: "staff-cook" },
    dueLabel: "сегодня",
  },
  {
    id: "task-venue-1",
    title: "Прочитать объявление: фокус продаж на вечернюю смену",
    source: "manager",
    priority: "low",
    status: "new",
    venueId: "dev-venue",
    audience: { type: "venue", venueId: "dev-venue" },
    dueLabel: "перед сменой",
  },
];

export const DEMO_TASK_COMMENTS: TeamTaskComment[] = [
  {
    id: "comment-brief-1",
    venueId: "dev-venue",
    taskId: "task-brief-1",
    authorName: "Сергей",
    body: "Нужна короткая причина и одно действие на вечер, без большого отчета.",
    createdAtLabel: "10:20",
  },
  {
    id: "comment-menu-1",
    venueId: "dev-venue",
    taskId: "task-menu-1",
    authorName: "Роман",
    body: "По двум позициям заготовки в норме, по фирменному блюду проверяю отдачу.",
    createdAtLabel: "11:05",
  },
  {
    id: "comment-service-1",
    venueId: "dev-venue",
    taskId: "task-service-1",
    authorName: "Алина",
    body: "После теста закрепим фокус продаж на вечерней планерке.",
    createdAtLabel: "11:30",
  },
];

export const DEMO_TEAM_ANNOUNCEMENTS: TeamAnnouncement[] = [
  {
    id: "announcement-venue-1",
    venueId: "dev-venue",
    title: "Фокус вечерней смены",
    body: "Сегодня продаем понятный ужин: горячие позиции, вино по рекомендации и десерт в конце.",
    priority: "important",
    audience: { type: "venue", venueId: "dev-venue" },
    createdByName: "Алина",
    createdAtLabel: "09:40",
  },
  {
    id: "announcement-kitchen-1",
    venueId: "dev-venue",
    title: "Кухня: стоп-лист до 16:00",
    body: "Проверить A-позиции и заранее отдать залу список ограничений.",
    priority: "normal",
    audience: { type: "role", roleId: "chef" },
    createdByName: "Роман",
    createdAtLabel: "10:10",
  },
  {
    id: "announcement-service-1",
    venueId: "dev-venue",
    title: "Зал: стандарт рекомендации",
    body: "Каждый стол получает одну конкретную рекомендацию по блюду и напитку.",
    priority: "normal",
    audience: { type: "role", roleId: "service" },
    createdByName: "Алина",
    createdAtLabel: "10:45",
  },
];

export const DEMO_TEAM_AUDIT_EVENTS: TeamAuditEvent[] = [
  {
    id: "audit-access-1",
    venueId: "dev-venue",
    type: "member_invited",
    targetType: "member",
    targetId: "staff-service",
    summary: "Создан доступ для Маши, роль Официант.",
    createdAtLabel: "11:42",
  },
  {
    id: "audit-task-1",
    venueId: "dev-venue",
    type: "task_created",
    targetType: "task",
    targetId: "task-menu-1",
    summary: "Поставлена задача шефу по стоп-листу.",
    createdAtLabel: "11:50",
  },
  {
    id: "audit-status-1",
    venueId: "dev-venue",
    type: "task_status_updated",
    targetType: "task",
    targetId: "task-service-1",
    summary: "Задача официантов переведена в работу.",
    createdAtLabel: "12:05",
  },
];

export function getTeamRole(id: TeamRoleId): TeamRole {
  const role = TEAM_ROLES.find((item) => item.id === id);
  if (!role) throw new Error(`Unknown team role: ${id}`);
  return role;
}

export function getTeamPermission(id: TeamPermissionId): TeamPermission {
  const permission = TEAM_PERMISSIONS.find((item) => item.id === id);
  if (!permission) throw new Error(`Unknown team permission: ${id}`);
  return permission;
}

export function listRolePermissions(roleId: TeamRoleId): TeamPermission[] {
  return ROLE_PERMISSIONS[roleId].map(getTeamPermission);
}

export function roleCan(
  roleId: TeamRoleId,
  permissionId: TeamPermissionId,
): boolean {
  return ROLE_PERMISSIONS[roleId].includes(permissionId);
}

export function listTasksForRole(
  roleId: TeamRoleId,
  tasks: TeamTask[] = DEMO_TEAM_TASKS,
): TeamTask[] {
  if (roleCan(roleId, "view_all_tasks")) return tasks;

  return tasks.filter((task) => {
    if (task.audience.type === "role") return task.audience.roleId === roleId;
    if (task.audience.type === "venue") return true;
    return false;
  });
}

export function listTasksForMember(
  memberId: string,
  staff: StaffMember[] = DEMO_STAFF,
  tasks: TeamTask[] = DEMO_TEAM_TASKS,
): TeamTask[] {
  const member = staff.find((item) => item.id === memberId);
  if (!member) return [];

  return tasks.filter((task) => {
    if (task.audience.type === "member") {
      return task.audience.memberId === memberId;
    }
    if (task.audience.type === "role") {
      return task.audience.roleId === member.roleId;
    }
    return task.audience.venueId === member.venueId;
  });
}

export function listCommentsForTask(
  taskId: string,
  comments: TeamTaskComment[] = DEMO_TASK_COMMENTS,
): TeamTaskComment[] {
  return comments.filter((comment) => comment.taskId === taskId);
}

export function listAnnouncementsForRole(
  roleId: TeamRoleId,
  venueId = "dev-venue",
  announcements: TeamAnnouncement[] = DEMO_TEAM_ANNOUNCEMENTS,
): TeamAnnouncement[] {
  return announcements.filter((announcement) => {
    if (announcement.venueId !== venueId) return false;
    if (roleCan(roleId, "view_all_tasks")) return true;
    if (announcement.audience.type === "venue") return true;
    return announcement.audience.roleId === roleId;
  });
}

export function buildRoleHome(
  roleId: TeamRoleId,
  tasks: TeamTask[] = DEMO_TEAM_TASKS,
): RoleHome {
  const role = getTeamRole(roleId);

  return {
    role,
    permissions: listRolePermissions(roleId),
    visibleTasks: listTasksForRole(roleId, tasks),
    sections: role.homeSections,
  };
}
