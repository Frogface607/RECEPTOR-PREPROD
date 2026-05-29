import { describe, expect, test, beforeEach, vi, afterEach } from "vitest";
import { CloudIikoClient } from "./cloud-client";

/**
 * Real `CloudIikoClient` cannot be exercised against the live iiko Cloud API
 * inside CI — there is no shared test apiLogin and no sandbox environment.
 *
 * Instead we mock `globalThis.fetch` and assert the SHAPE of the HTTP
 * conversation: auth endpoint, headers, body, response parsing.
 *
 * This is enough to guarantee that when Edison apiLogin arrives (post-31-May),
 * the wiring is correct end-to-end.
 */

const API_LOGIN = "test-api-login";
const ORG_ID = "edison-bar-org";
const ANCHOR = "2026-05-29";
const TOKEN = "iiko-token-abc";

type JsonResp = { url: string; init?: RequestInit; data: unknown; status?: number };

function mockFetchSequence(responses: JsonResp[]): {
  fetchSpy: ReturnType<typeof vi.fn>;
  calls: { url: string; init?: RequestInit }[];
} {
  const calls: { url: string; init?: RequestInit }[] = [];
  const queue = [...responses];

  const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });

    const expected = queue.shift();
    if (!expected) throw new Error(`unexpected fetch to ${url}`);

    return new Response(JSON.stringify(expected.data), {
      status: expected.status ?? 200,
      headers: { "Content-Type": "application/json" },
    });
  });

  vi.stubGlobal("fetch", fetchSpy);
  return { fetchSpy, calls };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CloudIikoClient — authentication", () => {
  test("posts apiLogin to /api/1/access_token on first call", async () => {
    const { calls } = mockFetchSequence([
      {
        url: "auth",
        data: { token: TOKEN },
      },
      {
        url: "sales",
        data: { data: [] },
      },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });

    await client.getRevenueSummary({ type: "TODAY" });

    expect(calls[0].url).toContain("/api/1/access_token");
    expect(calls[0].init?.method).toBe("POST");
    const body = JSON.parse(calls[0].init?.body as string);
    expect(body.apiLogin).toBe(API_LOGIN);
  });

  test("caches token — second BI call within TTL skips re-auth", async () => {
    const { calls } = mockFetchSequence([
      { url: "auth", data: { token: TOKEN } },
      { url: "sales-1", data: { data: [] } },
      { url: "sales-2", data: { data: [] } },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    await client.getRevenueSummary({ type: "TODAY" });
    await client.getRevenueSummary({ type: "YESTERDAY" });

    const authCalls = calls.filter((c) => c.url.includes("/api/1/access_token"));
    expect(authCalls).toHaveLength(1);
  });

  test("throws clear error when token missing in response", async () => {
    mockFetchSequence([{ url: "auth", data: { error: "unauthorized" } }]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });

    await expect(client.getRevenueSummary({ type: "TODAY" })).rejects.toThrow(
      /token/i,
    );
  });

  test("includes Bearer header on BI requests", async () => {
    const { calls } = mockFetchSequence([
      { url: "auth", data: { token: TOKEN } },
      { url: "sales", data: { data: [] } },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    await client.getRevenueSummary({ type: "TODAY" });

    const saleHeaders = new Headers(calls[1].init?.headers);
    expect(saleHeaders.get("Authorization")).toBe(`Bearer ${TOKEN}`);
  });
});

describe("CloudIikoClient.getRevenueSummary", () => {
  test("parses iiko OLAP rows into RevenueSummary", async () => {
    mockFetchSequence([
      { url: "auth", data: { token: TOKEN } },
      {
        url: "sales",
        data: {
          data: [
            { OpenDate: "2026-05-28", DishDiscountSumInt: 195000 },
            { OpenDate: "2026-05-29", DishDiscountSumInt: 215000 },
          ],
        },
      },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    const summary = await client.getRevenueSummary({
      type: "CUSTOM",
      from: "2026-05-28",
      to: "2026-05-29",
    });

    expect(summary.points).toHaveLength(2);
    expect(summary.revenue).toBe(195000 + 215000);
  });

  test("sends organizationId and date range in POST body", async () => {
    const { calls } = mockFetchSequence([
      { url: "auth", data: { token: TOKEN } },
      { url: "sales", data: { data: [] } },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    await client.getRevenueSummary({
      type: "CUSTOM",
      from: "2026-05-01",
      to: "2026-05-29",
    });

    const body = JSON.parse(calls[1].init?.body as string);
    expect(body.organizationIds).toContain(ORG_ID);
    expect(body.dateFrom).toBe("2026-05-01");
    expect(body.dateTo).toBe("2026-05-29");
  });
});

describe("CloudIikoClient — methods deferred to post-31-May", () => {
  test.each([
    ["getDishStatistics", (c: CloudIikoClient) => c.getDishStatistics({ type: "TODAY" }, 10)],
    ["getCategoryStatistics", (c: CloudIikoClient) => c.getCategoryStatistics({ type: "TODAY" })],
    ["getShifts", (c: CloudIikoClient) => c.getShifts({ type: "TODAY" })],
    ["searchNomenclature", (c: CloudIikoClient) => c.searchNomenclature("burger")],
  ])("%s throws explicit deferral error", async (_label, call) => {
    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    await expect(call(client)).rejects.toThrow(/not yet implemented|deferred/i);
  });
});
