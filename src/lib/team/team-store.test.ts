import { describe, expect, test } from "vitest";
import {
  mapAnnouncementRow,
  mapAnnouncementReadRow,
  mapAuditEventRow,
  mapCommentRow,
  mapLearningStandardRow,
  mapLearningProgressRow,
  mapMembershipRow,
  mapShiftPlanRow,
  mapTaskRow,
  normalizeTeamRoleId,
} from "./team-store";

describe("Team OS store mapping", () => {
  test("normalizes unknown roles to service", () => {
    expect(normalizeTeamRoleId("chef")).toBe("chef");
    expect(normalizeTeamRoleId("unknown")).toBe("service");
  });

  test("maps membership rows into staff members", () => {
    const member = mapMembershipRow({
      id: "member-1",
      venue_id: "venue-1",
      user_id: "user-1",
      full_name: "Алина",
      email: "alina@staff.receptorai.pro",
      role: "venue_manager",
      status: "active",
      shift_label: "12:00-23:00",
      hourly_rate: 450,
      shift_pay: "1200.50",
      revenue_bonus_pct: "1.5",
    });

    expect(member).toMatchObject({
      id: "member-1",
      userId: "user-1",
      name: "Алина",
      email: "alina@staff.receptorai.pro",
      roleId: "venue_manager",
      venueId: "venue-1",
      status: "active",
      shiftLabel: "12:00-23:00",
      hourlyRate: 450,
      shiftPay: 1200.5,
      revenueBonusPct: 1.5,
    });
  });

  test("maps role tasks into Team OS tasks", () => {
    const task = mapTaskRow({
      id: "task-1",
      venue_id: "venue-1",
      title: "Проверить стоп-лист",
      source: "chef",
      priority: "high",
      status: "accepted",
      audience_type: "role",
      audience_member_id: null,
      audience_role: "line_cook",
      due_label: "сегодня",
    });

    expect(task.audience).toEqual({ type: "role", roleId: "line_cook" });
    expect(task.source).toBe("chef");
    expect(task.priority).toBe("high");
  });

  test("maps member and venue audiences", () => {
    expect(
      mapTaskRow({
        id: "task-2",
        venue_id: "venue-1",
        title: "Личная задача",
        source: "manager",
        priority: "medium",
        status: "new",
        audience_type: "member",
        audience_member_id: "member-1",
        audience_role: null,
        due_label: "",
      }).audience,
    ).toEqual({ type: "member", memberId: "member-1" });

    expect(
      mapTaskRow({
        id: "task-3",
        venue_id: "venue-1",
        title: "Объявление",
        source: "manager",
        priority: "low",
        status: "new",
        audience_type: "venue",
        audience_member_id: null,
        audience_role: null,
        due_label: "",
      }).audience,
    ).toEqual({ type: "venue", venueId: "venue-1" });
  });

  test("maps task comments with membership author when present", () => {
    const comment = mapCommentRow(
      {
        id: "comment-1",
        venue_id: "venue-1",
        task_id: "task-1",
        author_membership_id: "member-1",
        body: "Проверил.",
        created_at: "2026-06-22T10:20:00.000Z",
      },
      [
        {
          id: "member-1",
          name: "Роман",
          roleId: "chef",
          venueId: "venue-1",
          status: "active",
          shiftLabel: "",
        },
      ],
    );

    expect(comment.authorName).toBe("Роман");
    expect(comment.taskId).toBe("task-1");
  });

  test("maps announcement audiences", () => {
    const roleAnnouncement = mapAnnouncementRow({
      id: "announcement-1",
      venue_id: "venue-1",
      title: "Кухня",
      body: "Проверить стоп-лист.",
      priority: "important",
      audience_type: "role",
      audience_role: "chef",
      created_at: null,
    });

    expect(roleAnnouncement.priority).toBe("important");
    expect(roleAnnouncement.audience).toEqual({ type: "role", roleId: "chef" });
  });

  test("maps announcement read receipts", () => {
    const read = mapAnnouncementReadRow({
      announcement_id: "announcement-1",
      membership_id: "member-1",
      read_at: "2026-06-29T09:15:00.000Z",
    });

    expect(read).toMatchObject({
      announcementId: "announcement-1",
      memberId: "member-1",
    });
    expect(read.readAtLabel).not.toBe("");
  });

  test("maps audit events", () => {
    const event = mapAuditEventRow({
      id: "audit-1",
      venue_id: "venue-1",
      event_type: "member_password_reset",
      target_type: "member",
      target_id: "member-1",
      summary: "Пароль сотрудника обновлен.",
      created_at: "2026-06-23T09:40:00.000Z",
    });

    expect(event).toMatchObject({
      id: "audit-1",
      venueId: "venue-1",
      type: "member_password_reset",
      targetType: "member",
      targetId: "member-1",
      summary: "Пароль сотрудника обновлен.",
    });
    expect(event.createdAtLabel).not.toBe("");
  });

  test("keeps labor rate audit events", () => {
    const event = mapAuditEventRow({
      id: "audit-labor",
      venue_id: "venue-1",
      event_type: "member_labor_rate_updated",
      target_type: "member",
      target_id: "member-1",
      summary: "Ставки ФОТ обновлены.",
      created_at: null,
    });

    expect(event.type).toBe("member_labor_rate_updated");
  });

  test("maps learning standard audit events", () => {
    const event = mapAuditEventRow({
      id: "audit-learning",
      venue_id: "venue-1",
      event_type: "learning_standard_updated",
      target_type: "learning_standard",
      target_id: null,
      summary: "Стандарт обучения обновлен.",
      created_at: null,
    });

    expect(event.type).toBe("learning_standard_updated");
    expect(event.targetType).toBe("learning_standard");
  });

  test("maps learning progress rows", () => {
    const progress = mapLearningProgressRow({
      venue_id: "venue-1",
      membership_id: "member-1",
      user_id: "user-1",
      module_id: "service-recommendation",
      best_percentage: 100,
      last_percentage: 67,
      correct_count: 2,
      total_questions: 3,
      passed: true,
      answers: [1, "0", 2],
      completed_at: "2026-06-26T10:00:00.000Z",
      updated_at: null,
    });

    expect(progress).toMatchObject({
      venueId: "venue-1",
      membershipId: "member-1",
      moduleId: "service-recommendation",
      bestPercentage: 100,
      lastPercentage: 67,
      correct: 2,
      total: 3,
      passed: true,
      answers: [1, 0, 2],
    });
  });

  test("maps learning standard rows", () => {
    const standard = mapLearningStandardRow({
      venue_id: "venue-1",
      role: "service",
      module_id: "guest-feedback",
      status: "required",
      updated_at: "2026-06-28T08:00:00.000Z",
    });

    expect(standard).toEqual({
      venueId: "venue-1",
      roleId: "service",
      moduleId: "guest-feedback",
      status: "required",
      updatedAt: "2026-06-28T08:00:00.000Z",
    });
  });

  test("maps shift plan rows", () => {
    const plan = mapShiftPlanRow({
      id: "plan-1",
      venue_id: "venue-1",
      membership_id: "member-1",
      shift_date: "2026-06-29",
      shift_start: "12:00:00",
      shift_end: "23:30:00",
      is_day_off: false,
      note: "зал",
      updated_at: "2026-06-27T10:00:00.000Z",
    });

    expect(plan).toEqual({
      id: "plan-1",
      venueId: "venue-1",
      memberId: "member-1",
      shiftDate: "2026-06-29",
      shiftStart: "12:00",
      shiftEnd: "23:30",
      isDayOff: false,
      note: "зал",
      updatedAt: "2026-06-27T10:00:00.000Z",
    });
  });
});
