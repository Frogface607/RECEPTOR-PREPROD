# Receptor Restaurant OS

Date: 2026-06-21

## Positioning

Receptor is an operating system for restaurant management.

It is not a ChatGPT wrapper and not only a BI dashboard. Receptor combines:

- operational data from iiko/R-Keeper;
- a deep venue context profile;
- role-based workflows for the team;
- modular restaurant tools;
- a Copilot that turns facts into actions.

Core promise:

> Receptor helps the owner and team understand what is happening in the restaurant and what to do today.

## Why This Is Defensible

Restaurants already have tools, but the work is fragmented:

- iiko stores facts but does not create management decisions;
- Telegram chats lose context;
- staff knowledge lives in heads or random docs;
- QR menu, booking, delivery, content and analytics are separate systems;
- owners still need to manually interpret reports.

Receptor should become the operating layer above these systems.

## Product Pillars

### 1. Owner Cockpit

- Daily Morning Brief
- iiko BI
- revenue, checks, shifts, categories and dishes
- risks and opportunities
- owner Copilot
- weekly strategic report

### 2. Context Engine

The main difference from generic AI tools.

Before Receptor gives serious advice, it collects venue context:

- format and positioning;
- city, location and audience;
- owner goals;
- team structure;
- menu priorities and margin logic;
- service standards;
- current pains;
- systems in use;
- data/compliance constraints;
- brand tone.

Every Copilot answer should use this context together with live data.

### 3. Menu OS

From Receptor and Edison Bar:

- QR menu;
- stop-list;
- tech cards;
- food cost;
- KBJU/allergens;
- menu engineering;
- dish launch pack;
- iiko article mapping.

### 4. Team OS

From Edison Bar:

- staff roles;
- permissions;
- PIN/staff login;
- shifts;
- knowledge base;
- quizzes;
- leaderboard;
- internal messages.

### 5. Guest OS

- booking;
- waitlist;
- table/floor plan;
- guest cabinet;
- web chat;
- Telegram/web conversation history.

### 6. Delivery OS

- delivery and pickup menu;
- order statuses;
- guest notifications;
- kitchen/admin workflow.

### 7. Marketing OS

- content generation;
- event announcements;
- posters;
- review replies;
- Telegram/VK/social posting.

## Modular Subscription Logic

The public promise can be broad, but first sales should be narrow.

Recommended initial bundles:

### Pilot Bundle

- Owner Cockpit
- Morning Brief
- Copilot
- iiko integration
- one custom module by pain: Menu OS or Team OS

### Starter

- one venue
- Daily Brief
- basic BI
- context profile

### Pro

- 2-5 venues
- Copilot
- Telegram/web delivery
- Menu OS
- basic Team OS

### Group

- holdings
- multi-venue cockpit
- roles and permissions
- weekly report
- priority support

Possible add-ons:

- QR Menu
- Booking
- Team OS
- Guest Chat
- Delivery/Pickup
- Marketing OS
- Local/Russian-friendly AI provider mode

## Mikhno Strategy

Tomorrow, if we get the iiko key:

1. Connect one live venue.
2. Verify numbers against iiko manually.
3. Generate the first real Morning Brief.
4. Show the owner-grade cockpit.
5. Sell a 2-week pilot.
6. Customize the holding workflow while keeping the core productizable.

If we do not get the key:

1. Continue with mock data.
2. Request iiko sandbox access.
3. Build the context questionnaire.
4. Build module/subscription model.
5. Prepare founder-led content and demo screens.

## Founder-Led Sales

The founder story matters.

Position Sergey Orlov as a restaurant/operator building practical restaurant
software through Frogface, not as an AI hype vendor.

Content pillars:

- what a restaurant owner should count every morning;
- why iiko data still needs interpretation;
- mistakes when opening a restaurant;
- menu engineering and margin;
- staff standards and training;
- AI with restaurant context;
- automation that works in Russia without fragile integrations.

CTA:

> Write "pilot" if you want this cockpit for your restaurant.

## AI Provider Position

Do not make the product dependent on one model provider.

Architecture direction:

- provider adapter interface;
- OpenAI/OpenRouter for quality and development;
- YandexGPT/GigaChat/Qwen-compatible option for Russia/data requirements;
- deterministic fallback for tests and demos;
- explicit separation of operational data, venue profile and generated text.

## Immediate Product Backlog

Done:

- Added venue context questionnaire.
- Added module catalog and subscription model.
- Added pilot/live/mock integration states.
- Improved `/pilot` into a sales command center.
- Added Owner Cockpit v1 framing on the dashboard: data mode, headline,
  owner actions and context readiness before BI charts.
- Added Team OS skeleton: roles, permissions, staff roster, role-based tasks
  and first `/team` screen.
- Added Team OS persistence layer: `venue_memberships`, `team_tasks`, RLS,
  owner membership seed on onboarding and live/sandbox team workspace reader.
- Added Team OS write actions: invite member, create task and update task
  status from the `/team` surface.
- Added Team OS communication layer: task comments, role/venue announcements,
  migration, read store and `/team` forms.

Next:

1. Add RLS-backed staff login/invite acceptance flow.
2. Add Telegram Daily Brief preview using the existing brief generator.
3. Add realtime transport for comments/announcements after write workflow is stable.
4. Prepare iiko sandbox/partner email.
5. When Mikhno key arrives, connect live data and generate first real brief.
