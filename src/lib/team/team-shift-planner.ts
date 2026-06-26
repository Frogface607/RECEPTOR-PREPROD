import {
  TEAM_ROLES,
  type StaffMember,
  type TeamRoleId,
  type TeamTask,
} from "./team-os";

export type ShiftRoleCoverageStatus = "covered" | "invited" | "empty";

export type ShiftRoleCoverage = {
  roleId: TeamRoleId;
  title: string;
  staff: StaffMember[];
  shiftLabels: string[];
  openTasks: number;
  importantTasks: number;
  status: ShiftRoleCoverageStatus;
};

export type ShiftOverview = {
  activeStaff: number;
  invitedStaff: number;
  pausedStaff: number;
  openTasks: number;
  importantTasks: number;
  coveredRoles: number;
  uncoveredRoles: ShiftRoleCoverage[];
  coverage: ShiftRoleCoverage[];
};

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function taskTouchesRole(
  task: TeamTask,
  roleId: TeamRoleId,
  staff: StaffMember[],
): boolean {
  const { audience } = task;

  switch (audience.type) {
    case "role":
      return audience.roleId === roleId;
    case "venue":
      return true;
    case "member": {
      const member = staff.find((item) => item.id === audience.memberId);
      return member?.roleId === roleId;
    }
  }
}

function uniqueShiftLabels(staff: StaffMember[]): string[] {
  return [
    ...new Set(
      staff
        .map((member) => member.shiftLabel.trim())
        .filter((label) => label.length > 0),
    ),
  ];
}

export function buildShiftOverview(
  staff: StaffMember[],
  tasks: TeamTask[],
): ShiftOverview {
  const openTasks = tasks.filter(isOpenTask);

  const coverage = TEAM_ROLES.map((role): ShiftRoleCoverage => {
    const roleStaff = staff.filter((member) => member.roleId === role.id);
    const activeStaff = roleStaff.filter((member) => member.status === "active");
    const invitedStaff = roleStaff.filter((member) => member.status === "invited");
    const roleTasks = openTasks.filter((task) =>
      taskTouchesRole(task, role.id, staff),
    );
    const status: ShiftRoleCoverageStatus =
      activeStaff.length > 0
        ? "covered"
        : invitedStaff.length > 0
          ? "invited"
          : "empty";

    return {
      roleId: role.id,
      title: role.title,
      staff: activeStaff,
      shiftLabels: uniqueShiftLabels(activeStaff),
      openTasks: roleTasks.length,
      importantTasks: roleTasks.filter((task) => task.priority === "high").length,
      status,
    };
  });

  return {
    activeStaff: staff.filter((member) => member.status === "active").length,
    invitedStaff: staff.filter((member) => member.status === "invited").length,
    pausedStaff: staff.filter((member) => member.status === "paused").length,
    openTasks: openTasks.length,
    importantTasks: openTasks.filter((task) => task.priority === "high").length,
    coveredRoles: coverage.filter((item) => item.status === "covered").length,
    uncoveredRoles: coverage.filter((item) => item.status !== "covered"),
    coverage,
  };
}
