# Mikhno SaaS Strategy

Date: 2026-06-22

## Strategic Position

Build a restaurant operating cockpit for Mikhno and his team as an individual
pilot first, then package the reusable core as a SaaS/iiko partner product.

The product should not be sold as "another analytics dashboard". The sharper
promise:

> Every morning the owner and managers see what changed, what is at risk, and
> what to do today across sales, menu, team, and guest experience.

Receptor remains the source code donor:

- iiko Cloud/RMS client layer
- dashboard and BI primitives
- Daily Brief domain logic
- Copilot/tool runner
- Tech Card Studio and menu tools
- venue intelligence profile
- Telegram delivery hooks

The Mikhno product can be individualized in UI, roles, language, and workflows,
but the core should stay productizable.

## Customer Hypothesis

Primary buyer: owner/managing partner of several restaurant projects.

Daily users:

- owner
- operations director
- venue manager
- chef/brand chef
- marketer/SMM

Their pain is not lack of reports. Their pain is that iiko contains facts, but
the team still needs a person to read reports, interpret them, notice risks,
and turn them into tasks.

## MVP For Mikhno

### 1. Owner Morning Brief

The flagship screen and Telegram message.

It answers:

- What happened yesterday?
- What changed against the previous comparable period?
- Which venue, shift, category, or dish needs attention?
- What should each responsible person do today?

### 2. Multi-Venue Cockpit

For a team with multiple places:

- revenue and checks by venue
- day/week/month comparison
- venue ranking
- red/yellow/green risk state
- drilldown into one venue

### 3. Menu Intelligence

Use existing Receptor modules:

- top dishes
- category mix
- menu engineering quadrants
- survival/risk score
- dish launch pack
- tech card studio where useful

### 4. Team Tasks

Small but sellable layer:

- convert insights into tasks
- assign to owner/manager/chef/marketer
- due today / this week
- Telegram summary

Do not build a full task manager yet. Start with generated action list and
manual completion state.

### 5. Copilot With Guardrails

Copilot should answer only from connected data and venue profile. No invented
numbers. Every strategic answer should include:

1. fact
2. interpretation
3. action
4. missing data

## If Mikhno's iiko Key Arrives Tomorrow

1. Connect one real venue.
2. Validate organization selection and credentials storage.
3. Generate first live Daily Brief.
4. Compare numbers against iiko manually.
5. Tune copy and executive framing.
6. Prepare a 2-week paid pilot proposal.

## If Mikhno's Key Does Not Arrive

Use today/tomorrow to avoid blocking:

1. Request iiko sandbox/developer access.
2. Keep building against deterministic Receptor fixtures.
3. Add a "pilot mode" setup flow that can work with mock data or live iiko.
4. Prepare the sales/demo shell: one-page offer, dashboard route, sample brief.
5. Add integration readiness checklist in-app.

## iiko Partner Path

Verified on 2026-06-22 against public iiko materials.

Official iiko materials describe three cooperation formats:

- Custom: one-off integration for a customer.
- Connector: certified integration module for connecting our service to iiko;
  we sell and bill the product ourselves.
- Solution: full solution promoted with iiko and sold through their dealer
  network.

For us:

- Short term: Custom/pilot with Mikhno.
- Mid term: Connector if we sell independently and just need official iiko
  integration status.
- Long term: Solution if we can prove demand and want iiko sales/dealer channel.

Important public requirements before iiko price-list / Solution motion:

- pilot with real iiko clients before review:
  - Connector: 10-12 clients in 3 months;
  - Solution: 30 clients in 6 months;
- for price-list inclusion, public requirements mention either 100 existing
  integrated clients or at least 30 startup-project clients using iiko;
- documentation, support model, landing/materials;
- sales materials for iiko partners;
- onboarding/training materials;
- value proven with numbers and cases;
- architecture description and information about used iiko APIs;
- support categories, SLA and incident/update notification process;
- revenue share with iiko and dealers.

Publicly stated Solution split in the iiko certification/pricing document:

- 45% vendor/technology partner
- 40% iiko partner/dealer
- 15% iiko

This means iiko Solution is not the first sales motion. It is a scaling channel
after we have pilots, proof, and support process.

Sources:

- iiko developer / partner formats: https://api.iiko.ru/
- Certification and price-list requirements:
  https://iiko.ru/assets/data/trebovaniya_price.pdf
- iiko contacts and official developer entry points: https://iiko.ru/contacts
- iikoStore: https://store.iiko.ru/

Practical conclusion:

- Do not wait for marketplace approval.
- Ask iiko for sandbox and recommended API path now.
- Sell Mikhno as direct paid pilot / Custom.
- Package Connector materials after 2-3 real pilots.
- Treat Solution/dealer-channel as a 6+ month scale path, not launch path.

## What To Ask iiko

Subject: Developer sandbox and partner path for AI restaurant operations cockpit

Draft:

Hello iiko team.

We are building an AI operations cockpit for restaurants on top of iiko data:
daily owner brief, multi-venue analytics, menu intelligence, and manager action
recommendations.

We are preparing a pilot with restaurants using iiko and want to build the
integration correctly from the start.

Could you please advise:

1. Is there a developer sandbox/test organization for iiko Cloud API?
2. What is the recommended path for a SaaS product that reads sales/menu data
   and generates analytics and operational recommendations?
3. Should we start as Custom/Connector and later apply for Solution?
4. What API scopes/endpoints are recommended for revenue, checks, menu items,
   categories, shifts, and organizations?
5. Are there technical or certification constraints for AI/analytics products?
6. What materials should we prepare before applying for marketplace or partner
   review?

Thank you.

## Pricing Hypothesis

Do not start cheap. The product saves owner attention and can affect revenue.

Pilot:

- 2 weeks
- 1-3 venues
- setup + daily brief + dashboard + end report
- fixed pilot fee or free only if Mikhno is strategic access

SaaS after pilot:

- Starter: 1 venue, owner brief and dashboard
- Pro: 2-5 venues, Telegram, Copilot, menu intelligence
- Group: multi-location, roles, weekly strategy report, support

iiko marketplace pricing will need margin room because Solution may split
revenue across vendor, dealer, and iiko.

## Build Plan

### Phase 0: Today Strategy

- Decide product promise.
- Prepare iiko outreach.
- Define Mikhno pilot scope.
- Identify code modules to reuse from Receptor.
- Create the first sales/demo checklist.

### Phase 1: No-Key Development

- Add pilot setup state: mock/live/awaiting key.
- Polish demo dashboard for owner-grade decision language.
- Add a sample Telegram Daily Brief preview.
- Add integration readiness checklist.
- Add one-page pilot proposal route or document.

### Phase 2: Live iiko Key

- Connect real apiLogin.
- Validate organization selection.
- Verify sales/menu numbers against iiko.
- Generate first live morning brief.
- Add live/demo badges and integration health.

### Phase 3: Paid Pilot

- Daily brief delivery.
- Weekly report.
- Feedback capture.
- Before/after case material.
- Sales screenshots and partner docs.

### Phase 4: Productization

- Multi-tenant Supabase data model.
- Roles and team access.
- Billing only after repeatable pilot value.
- iiko Connector/Solution preparation package.

## Immediate Coding Backlog

Done:

- Added a Pilot Command Center surface for demo/live readiness.
- Added product-level pilot states:
   - mock demo
   - waiting for iiko key
   - connected
   - error

Next:

1. Add Telegram Daily Brief preview using existing brief generator.
2. Add owner action list generated from survival/menu/brief modules.
3. Add a lightweight pilot proposal page.
4. Fix existing lint warnings when touching nearby files.
5. Later: rename Next.js middleware to proxy to clear build warning.

## Decision

Today we should not wait for the key. Build the sales shell and pilot workflow
around Receptor's mock/live split, then swap in Mikhno's real iiko data as soon
as the key arrives.
