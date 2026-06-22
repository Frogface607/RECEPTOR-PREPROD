export type ProductModuleId =
  | "owner_cockpit"
  | "context_engine"
  | "menu_os"
  | "team_os"
  | "guest_os"
  | "delivery_os"
  | "marketing_os"
  | "integration_pack";

export type ProductModulePhase = "core" | "operations" | "scale";

export type ProductModule = {
  id: ProductModuleId;
  title: string;
  shortTitle: string;
  promise: string;
  includes: string[];
  source: "receptor" | "edison" | "new";
  phase: ProductModulePhase;
  displayOrder: number;
};

export type IntegrationReadinessState =
  | "demo"
  | "waiting_credentials"
  | "connected"
  | "error";

export type IntegrationReadinessTone = "ready" | "active" | "waiting" | "error";

export type IntegrationReadinessCheck = {
  label: string;
  status: "done" | "next" | "waiting" | "blocked";
  detail: string;
};

export type IntegrationReadinessCard = {
  id: IntegrationReadinessState;
  label: string;
  statusLabel: string;
  tone: IntegrationReadinessTone;
  score: number;
  title: string;
  summary: string;
  ownerMessage: string;
  primaryAction: string;
  secondaryAction: string;
  checks: IntegrationReadinessCheck[];
};

export type IntegrationReadinessInput = {
  liveVenueSelected?: boolean;
  hasIikoCredentials?: boolean;
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
    phase: "core",
    displayOrder: 1,
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
    phase: "core",
    displayOrder: 2,
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
    phase: "core",
    displayOrder: 3,
  },
  {
    id: "team_os",
    title: "Team OS",
    shortTitle: "Team",
    promise: "Roles, access, shifts, knowledge base, tasks and team messages.",
    includes: [
      "staff roles",
      "permissions",
      "shift schedule",
      "knowledge base",
      "tasks",
      "team messages",
    ],
    source: "edison",
    phase: "operations",
    displayOrder: 4,
  },
  {
    id: "guest_os",
    title: "Guest OS",
    shortTitle: "Guests",
    promise: "Bookings, waitlist, guest cabinet and web conversation history.",
    includes: [
      "bookings",
      "waitlist",
      "floor plan",
      "guest cabinet",
      "web chat",
    ],
    source: "edison",
    phase: "operations",
    displayOrder: 6,
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
    phase: "operations",
    displayOrder: 7,
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
    phase: "operations",
    displayOrder: 8,
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
    displayOrder: 5,
  },
];

export const FOUNDATION_MODULE_IDS: ProductModuleId[] = [
  "owner_cockpit",
  "context_engine",
  "menu_os",
  "integration_pack",
];

export const INTEGRATION_READINESS_STATE_ORDER: IntegrationReadinessState[] = [
  "demo",
  "waiting_credentials",
  "connected",
  "error",
];

export const INTEGRATION_READINESS_STATES: Record<
  IntegrationReadinessState,
  IntegrationReadinessCard
> = {
  demo: {
    id: "demo",
    label: "Demo workspace",
    statusLabel: "Ready",
    tone: "ready",
    score: 74,
    title: "Workspace can be shown today.",
    summary:
      "Receptor can run on demo data, venue context and product modules. This is enough to show the operating system before live integrations are connected.",
    ownerMessage:
      "The restaurant sees the daily rhythm first: facts, interpretation, actions and responsible roles.",
    primaryAction: "Open demo cockpit",
    secondaryAction: "Complete venue context",
    checks: [
      {
        label: "Restaurant OS core",
        status: "done",
        detail: "Owner Cockpit, Context Engine, Menu OS and Team OS are available.",
      },
      {
        label: "Venue context",
        status: "done",
        detail: "The questionnaire creates memory for dashboards, briefs and Copilot answers.",
      },
      {
        label: "Live data",
        status: "waiting",
        detail: "Switch from demo to live after iiko credentials and organization validation.",
      },
    ],
  },
  waiting_credentials: {
    id: "waiting_credentials",
    label: "Waiting for credentials",
    statusLabel: "Setup",
    tone: "active",
    score: 66,
    title: "Product workspace is ready for live credentials.",
    summary:
      "The SaaS shell is ready. Live reports require iiko credentials or a technical user with the right organization access.",
    ownerMessage:
      "We prepare the cockpit, context and module set first. Credentials turn the same workspace into live operations.",
    primaryAction: "Add iiko credentials",
    secondaryAction: "Request sandbox access",
    checks: [
      {
        label: "Workspace",
        status: "done",
        detail: "Core modules and pricing are packaged as Restaurant OS.",
      },
      {
        label: "iiko credentials",
        status: "blocked",
        detail: "Need Cloud apiLogin or a responsible technical contact.",
      },
      {
        label: "Integration path",
        status: "next",
        detail: "Use sandbox access for testing and live access for customer data.",
      },
    ],
  },
  connected: {
    id: "connected",
    label: "Live iiko connected",
    statusLabel: "Live",
    tone: "ready",
    score: 91,
    title: "Live workspace can produce the first Morning Brief.",
    summary:
      "Credentials are stored, organization is selected and the dashboard can read live sales/menu data for the restaurant.",
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
        detail: "Compare revenue, checks and top dishes with iiko UI.",
      },
      {
        label: "Operating cadence",
        status: "next",
        detail: "Assign daily actions to owner, manager, kitchen and marketing.",
      },
    ],
  },
  error: {
    id: "error",
    label: "Connection error",
    statusLabel: "Needs fix",
    tone: "error",
    score: 38,
    title: "Live integration needs attention, demo workspace stays available.",
    summary:
      "A failed iiko call must not break the product experience. Keep demo data available, show the exact failure and fix credentials/scopes separately.",
    ownerMessage:
      "The restaurant should still see the operating workflow while the integration issue is isolated.",
    primaryAction: "Inspect iiko error",
    secondaryAction: "Fallback to demo",
    checks: [
      {
        label: "Product demo",
        status: "done",
        detail: "Demo mode remains available for product onboarding.",
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

export function listFoundationModules(): ProductModule[] {
  return FOUNDATION_MODULE_IDS.map(getProductModule);
}

export function listModulesByPhase(phase: ProductModulePhase): ProductModule[] {
  return RESTAURANT_OS_MODULES.filter((item) => item.phase === phase).sort(
    (a, b) => a.displayOrder - b.displayOrder,
  );
}

export function getIntegrationReadinessState(
  state: IntegrationReadinessState,
): IntegrationReadinessCard {
  return INTEGRATION_READINESS_STATES[state];
}

export function listIntegrationReadinessStates(): IntegrationReadinessCard[] {
  return INTEGRATION_READINESS_STATE_ORDER.map(getIntegrationReadinessState);
}

export function resolveIntegrationReadinessState(
  input: IntegrationReadinessInput,
): IntegrationReadinessState {
  if (input.hasConnectionError) return "error";
  if (input.iikoConnected) return "connected";
  if (input.liveVenueSelected && !input.hasIikoCredentials) {
    return "waiting_credentials";
  }
  return "demo";
}
