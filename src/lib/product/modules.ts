export type ProductModuleId =
  | "owner_cockpit"
  | "context_engine"
  | "menu_os"
  | "team_os"
  | "guest_os"
  | "delivery_os"
  | "marketing_os"
  | "integration_pack";

export type ProductModulePhase = "pilot" | "saas" | "scale";

export type ProductModule = {
  id: ProductModuleId;
  title: string;
  shortTitle: string;
  promise: string;
  includes: string[];
  source: "receptor" | "edison" | "new";
  phase: ProductModulePhase;
  pilotPriority: number;
};

export type PilotReadinessState =
  | "mock"
  | "waiting_key"
  | "connected"
  | "error";

export type PilotReadinessTone = "ready" | "active" | "waiting" | "error";

export type PilotCommandCheck = {
  label: string;
  status: "done" | "next" | "waiting" | "blocked";
  detail: string;
};

export type PilotCommandState = {
  id: PilotReadinessState;
  label: string;
  statusLabel: string;
  tone: PilotReadinessTone;
  score: number;
  title: string;
  summary: string;
  ownerMessage: string;
  primaryAction: string;
  secondaryAction: string;
  checks: PilotCommandCheck[];
};

export type PilotReadinessInput = {
  liveTargetSelected?: boolean;
  targetHasIikoKey?: boolean;
  iikoConnected?: boolean;
  hasConnectionError?: boolean;
};

export const RESTAURANT_OS_MODULES: ProductModule[] = [
  {
    id: "owner_cockpit",
    title: "Owner Cockpit",
    shortTitle: "Cockpit",
    promise: "Morning Brief, BI, risks, actions and owner Copilot.",
    includes: [
      "Daily Morning Brief",
      "iiko BI",
      "revenue, checks, shifts and dishes",
      "owner-level risks and actions",
      "weekly strategic report",
    ],
    source: "receptor",
    phase: "pilot",
    pilotPriority: 1,
  },
  {
    id: "context_engine",
    title: "Context Engine",
    shortTitle: "Context",
    promise: "Venue memory: format, goals, team, systems, constraints and decision rules.",
    includes: [
      "venue questionnaire",
      "owner goals",
      "team and role map",
      "brand and service standards",
      "AI/data policy",
    ],
    source: "receptor",
    phase: "pilot",
    pilotPriority: 2,
  },
  {
    id: "menu_os",
    title: "Menu OS",
    shortTitle: "Menu",
    promise: "QR menu, stop-list, tech cards, food cost and menu engineering.",
    includes: [
      "QR menu",
      "stop-list",
      "tech cards",
      "food cost",
      "dish launch pack",
      "iiko article mapping",
    ],
    source: "receptor",
    phase: "pilot",
    pilotPriority: 3,
  },
  {
    id: "team_os",
    title: "Team OS",
    shortTitle: "Team",
    promise: "Roles, access, shifts, knowledge base, tests and team messages.",
    includes: [
      "staff roles",
      "permissions",
      "shift schedule",
      "knowledge base",
      "quizzes and leaderboard",
      "team messages",
    ],
    source: "edison",
    phase: "saas",
    pilotPriority: 4,
  },
  {
    id: "guest_os",
    title: "Guest OS",
    shortTitle: "Guests",
    promise: "Bookings, waitlist, guest cabinet and web/Telegram conversation history.",
    includes: [
      "bookings",
      "waitlist",
      "floor plan",
      "guest cabinet",
      "web chat",
    ],
    source: "edison",
    phase: "saas",
    pilotPriority: 6,
  },
  {
    id: "delivery_os",
    title: "Delivery OS",
    shortTitle: "Delivery",
    promise: "Delivery and pickup workflow with statuses and guest notifications.",
    includes: [
      "delivery menu",
      "pickup orders",
      "order statuses",
      "guest notifications",
      "kitchen/admin workflow",
    ],
    source: "edison",
    phase: "saas",
    pilotPriority: 7,
  },
  {
    id: "marketing_os",
    title: "Marketing OS",
    shortTitle: "Marketing",
    promise: "Posts, events, posters, review replies and channel publishing.",
    includes: [
      "content generation",
      "event announcements",
      "poster workflow",
      "review replies",
      "Telegram/VK posting",
    ],
    source: "edison",
    phase: "saas",
    pilotPriority: 8,
  },
  {
    id: "integration_pack",
    title: "Integration Pack",
    shortTitle: "Integrations",
    promise: "iiko/R-Keeper, Telegram, VK and configurable AI providers.",
    includes: [
      "iiko Cloud/RMS",
      "R-Keeper later",
      "Telegram",
      "VK",
      "OpenAI/OpenRouter/YandexGPT/GigaChat/Qwen options",
    ],
    source: "new",
    phase: "scale",
    pilotPriority: 5,
  },
];

export const PILOT_BUNDLE_MODULE_IDS: ProductModuleId[] = [
  "owner_cockpit",
  "context_engine",
  "menu_os",
  "integration_pack",
];

export const PILOT_COMMAND_STATE_ORDER: PilotReadinessState[] = [
  "mock",
  "waiting_key",
  "connected",
  "error",
];

export const PILOT_COMMAND_STATES: Record<PilotReadinessState, PilotCommandState> = {
  mock: {
    id: "mock",
    label: "Mock demo",
    statusLabel: "Ready",
    tone: "ready",
    score: 72,
    title: "Demo cockpit can be shown today.",
    summary:
      "Receptor runs on deterministic iiko fixtures, context answers and owner-grade copy. This is enough for a sales demo while live access is pending.",
    ownerMessage:
      "We can show the operating rhythm now: morning facts, interpretation, actions and module plan.",
    primaryAction: "Open demo cockpit",
    secondaryAction: "Collect venue context",
    checks: [
      {
        label: "Receptor core",
        status: "done",
        detail: "BI, Copilot, Daily Brief and menu tools are available in code.",
      },
      {
        label: "Context Engine",
        status: "done",
        detail: "Demo context is complete enough for owner-facing answers.",
      },
      {
        label: "Live iiko data",
        status: "waiting",
        detail: "Switch from mock after apiLogin and organization validation.",
      },
    ],
  },
  waiting_key: {
    id: "waiting_key",
    label: "Waiting for iiko key",
    statusLabel: "Blocked by client key",
    tone: "active",
    score: 64,
    title: "Pilot is ready for the key handoff.",
    summary:
      "The product shell is ready. The only hard dependency for the first live brief is Mikhno's apiLogin or a technical contact who can create one.",
    ownerMessage:
      "Today we prepare the cockpit, context and offer. Tomorrow the key swaps demo facts for live facts.",
    primaryAction: "Request apiLogin",
    secondaryAction: "Send iiko sandbox request",
    checks: [
      {
        label: "Sales shell",
        status: "done",
        detail: "Pilot offer, modules and pricing are packaged as Restaurant OS.",
      },
      {
        label: "Mikhno apiLogin",
        status: "blocked",
        detail: "Need Cloud apiLogin or a responsible technical contact.",
      },
      {
        label: "iiko sandbox",
        status: "next",
        detail: "Ask iiko for developer sandbox and Connector/Solution route.",
      },
    ],
  },
  connected: {
    id: "connected",
    label: "Live iiko connected",
    statusLabel: "Live",
    tone: "ready",
    score: 91,
    title: "Live pilot can produce the first Morning Brief.",
    summary:
      "Credentials are stored, organization is selected and the dashboard can read live sales/menu data for a controlled first venue.",
    ownerMessage:
      "Now the work shifts from setup to verification: compare numbers with iiko and send the first brief.",
    primaryAction: "Generate live brief",
    secondaryAction: "Verify iiko numbers",
    checks: [
      {
        label: "Credentials",
        status: "done",
        detail: "apiLogin is available and mapped to a selected organization.",
      },
      {
        label: "Data verification",
        status: "next",
        detail: "Compare yesterday revenue, checks and top dishes with iiko UI.",
      },
      {
        label: "Pilot report",
        status: "next",
        detail: "Start collecting before/after evidence for the sales case.",
      },
    ],
  },
  error: {
    id: "error",
    label: "Connection error",
    statusLabel: "Needs fix",
    tone: "error",
    score: 38,
    title: "Live path is failing, demo path stays usable.",
    summary:
      "A failed iiko call must not kill the pilot. Keep the mock cockpit available, show the exact failure and fix credentials/scopes separately.",
    ownerMessage:
      "The client should still see the operating workflow while we isolate the integration issue.",
    primaryAction: "Inspect iiko error",
    secondaryAction: "Fallback to mock",
    checks: [
      {
        label: "Client demo",
        status: "done",
        detail: "Mock mode remains available for the sales conversation.",
      },
      {
        label: "Credentials or scopes",
        status: "blocked",
        detail: "Check token, organization access and required OLAP permissions.",
      },
      {
        label: "Recovery note",
        status: "next",
        detail: "Log the failure and document the fix for the support playbook.",
      },
    ],
  },
};

export function getProductModule(id: ProductModuleId): ProductModule {
  const productModule = RESTAURANT_OS_MODULES.find((item) => item.id === id);
  if (!productModule) throw new Error(`Unknown product module: ${id}`);
  return productModule;
}

export function listPilotBundleModules(): ProductModule[] {
  return PILOT_BUNDLE_MODULE_IDS.map(getProductModule);
}

export function listModulesByPhase(phase: ProductModulePhase): ProductModule[] {
  return RESTAURANT_OS_MODULES.filter((item) => item.phase === phase).sort(
    (a, b) => a.pilotPriority - b.pilotPriority,
  );
}

export function getPilotCommandState(
  state: PilotReadinessState,
): PilotCommandState {
  return PILOT_COMMAND_STATES[state];
}

export function listPilotCommandStates(): PilotCommandState[] {
  return PILOT_COMMAND_STATE_ORDER.map(getPilotCommandState);
}

export function resolvePilotReadinessState(
  input: PilotReadinessInput,
): PilotReadinessState {
  if (input.hasConnectionError) return "error";
  if (input.iikoConnected) return "connected";
  if (input.liveTargetSelected && !input.targetHasIikoKey) return "waiting_key";
  return "mock";
}
