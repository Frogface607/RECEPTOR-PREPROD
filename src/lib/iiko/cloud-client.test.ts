import { describe, expect, test, vi, afterEach } from "vitest";
import { CloudIikoClient } from "./cloud-client";

/**
 * Real `CloudIikoClient` cannot be exercised against the live iiko Cloud API
 * inside CI — there is no shared test apiLogin and no sandbox environment.
 *
 * Instead we mock `globalThis.fetch` and assert the SHAPE of the HTTP
 * conversation: auth endpoint, headers, body, response parsing.
 *
 * This is enough to guarantee that when a live apiLogin arrives,
 * the wiring is correct end-to-end.
 */

const API_LOGIN = "test-api-login";
const ORG_ID = "sandbox-org";
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

  test("explains 401 as an invalid API key", async () => {
    mockFetchSequence([
      { url: "auth", data: { error: "unauthorized" }, status: 401 },
    ]);

    const client = new CloudIikoClient({
      apiLogin: "EdisonCraft",
      organizationId: ORG_ID,
      today: ANCHOR,
    });

    await expect(client.getRevenueSummary({ type: "TODAY" })).rejects.toThrow(
      /не принял API ключ/i,
    );
  });

  test("explains 423 as an expired Cloud API license", async () => {
    mockFetchSequence([
      {
        url: "auth",
        data: {
          errorDescription:
            "Apilogin's license for using the Cloud API has expired.",
        },
        status: 423,
      },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });

    await expect(client.getRevenueSummary({ type: "TODAY" })).rejects.toThrow(
      /Лицензия iiko Cloud API истекла/i,
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

describe("CloudIikoClient.listOrganizations", () => {
  test("fetches organizations after auth and normalizes id/name", async () => {
    const { calls } = mockFetchSequence([
      { url: "auth", data: { token: TOKEN } },
      {
        url: "organizations",
        data: {
          organizations: [
            { id: "org-1", name: "Pilot Group" },
            { id: "org-2", name: "Second Venue" },
          ],
        },
      },
    ]);

    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: "",
      today: ANCHOR,
    });

    await expect(client.listOrganizations()).resolves.toEqual([
      { id: "org-1", name: "Pilot Group" },
      { id: "org-2", name: "Second Venue" },
    ]);
    expect(calls[1].url).toContain("/api/1/organizations");
    expect(calls[1].init?.method).toBe("POST");
    expect(JSON.parse(calls[1].init?.body as string)).toEqual({});
    expect(new Headers(calls[1].init?.headers).get("Authorization")).toBe(
      `Bearer ${TOKEN}`,
    );
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

// getDishStatistics / getCategoryStatistics / getShifts are now ported via
// OLAP — see cloud-client.olap.test.ts. searchNomenclature degrades to an
// empty list on Cloud (documented in REAL_CONNECT.md), no longer throws.
describe("CloudIikoClient.searchNomenclature", () => {
  test("returns empty list on Cloud (graceful deferral)", async () => {
    const client = new CloudIikoClient({
      apiLogin: API_LOGIN,
      organizationId: ORG_ID,
      today: ANCHOR,
    });
    await expect(client.searchNomenclature("burger")).resolves.toEqual([]);
  });
});
