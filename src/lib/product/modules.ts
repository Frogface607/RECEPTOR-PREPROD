export type ProductModuleId =
  | "owner_cockpit"
  | "context_engine"
  | "menu_os"
  | "team_os"
  | "guest_os"
  | "delivery_os"
  | "marketing_os"
  | "integration_pack";

export type ProductModule = {
  id: ProductModuleId;
  title: string;
  shortTitle: string;
  promise: string;
  includes: string[];
  displayOrder: number;
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
    displayOrder: 1,
  },
  {
    id: "context_engine",
    title: "Context Engine",
    shortTitle: "Context",
    promise:
      "Venue memory: format, goals, team, systems, constraints and decision rules.",
    includes: [
      "venue questionnaire",
      "owner goals",
      "team and role map",
      "brand and service standards",
      "AI/data policy",
    ],
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
    displayOrder: 4,
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
    displayOrder: 5,
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
    displayOrder: 8,
  },
];

export const FOUNDATION_MODULE_IDS: ProductModuleId[] = [
  "owner_cockpit",
  "context_engine",
  "menu_os",
  "integration_pack",
];

export function getProductModule(id: ProductModuleId): ProductModule {
  const productModule = RESTAURANT_OS_MODULES.find((item) => item.id === id);
  if (!productModule) throw new Error(`Unknown product module: ${id}`);
  return productModule;
}

export function listFoundationModules(): ProductModule[] {
  return FOUNDATION_MODULE_IDS.map(getProductModule);
}

export function listProductModules(): ProductModule[] {
  return [...RESTAURANT_OS_MODULES].sort(
    (a, b) => a.displayOrder - b.displayOrder,
  );
}
