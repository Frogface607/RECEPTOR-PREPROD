import { describe, expect, test } from "vitest";
import {
  mapAnnouncementRow,
  mapAuditEventRow,
  mapCommentRow,
  mapMembershipRow,
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
    });

    expect(member).toEqual({
      id: "member-1",
      userId: "user-1",
      name: "Алина",
      email: "alina@staff.receptorai.pro",
      roleId: "venue_manager",
      venueId: "venue-1",
      status: "active",
      shiftLabel: "12:00-23:00",
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
});
