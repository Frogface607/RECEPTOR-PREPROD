# Receptor OS Roadmap

Date: 2026-06-10

## Positioning

Receptor can be positioned as an AI operating system for restaurants.

Not a POS replacement. Not another BI dashboard. Not a bundle of prompts.

Receptor sits above iiko and the restaurant's daily workflows:

- reads business data from iiko;
- understands the venue profile;
- explains what is happening;
- creates operational artifacts;
- helps the owner, manager, chef, and team act faster.

## Why This Sounds Expensive

The phrase "operating system" is justified only if the product connects multiple
business surfaces. Current and planned Receptor surfaces already support this:

- BI cockpit from iiko;
- Copilot with venue context;
- Tech Card Studio;
- AI tools/workflows;
- onboarding and venue research;
- future team, menu, booking, and comms modules.

The sellable promise:

> One AI-powered operating layer for restaurant decisions: sales, menu, kitchen,
> team, reputation, and daily control.

## Edison Admin Features Worth Productizing

The Edison Bar admin has several modules that map naturally into Receptor OS.

| Edison feature | Receptor OS module | Priority | Notes |
| --- | --- | --- | --- |
| Menu admin and stop-list | Menu Studio | High | Connect with iiko menu, tech cards, descriptions, availability. |
| Staff roles and login | Team OS | High | Roles: owner, manager, chef, waiter. Needed for serious SaaS. |
| Staff knowledge base and quizzes | Training OS | High | Strong for service standards, onboarding, tests, leaderboard. |
| Booking dashboard and tables | Floor Control | Medium | Useful, but only after iiko/BI core unless pilot asks for it. |
| Telegram staff messages | Team Comms | Medium | Later daily brief delivery, tasks, manager notifications. |
| QR menu | Guest Surface | Medium | Valuable, but can become a separate upsell module. |
| Event/content generation | Marketing OS | Medium | Great for bars and venues with events, less universal for restaurants. |
| Artist/contract tools | Venue-specific | Low | Strong for Edison-like music venues, not generic restaurant core. |
| Admin chat | Internal Comms | Low | Useful later, not urgent for pilot. |

## Product Pillars

### 1. Owner Cockpit

The daily owner view:

- revenue and checks;
- categories and dishes;
- day/week/month comparison;
- risk signals;
- Copilot recommendations.

### 2. Kitchen and Menu

The chef/manager workflow:

- Tech Card Studio;
- food cost;
- KBJU;
- allergen/HACCP;
- menu descriptions;
- iiko article mapping;
- PDF and iiko export.

### 3. Team OS

The manager workflow:

- roles and access;
- training articles;
- quizzes;
- shift briefing;
- service scripts;
- Telegram delivery.

### 4. Reputation and Marketing

The growth workflow:

- review replies;
- promo ideas;
- content calendar;
- event announcements;
- venue tone from profile.

## Near-Term Plan

1. Make the website and app speak in OS language. Done.
2. Keep tools grouped as workflows, not categories. Done.
3. Build Tech Card Studio MVP. Done.
4. Connect venue profile context into tool prompts. Done.
5. Add Tech Card AI autofill. Done.
6. Save tech card history in Supabase.
7. Restore iiko article mapping after a working pilot key.
8. Add a minimal Team OS module inspired by Edison knowledge base.

## Current Context Layer

Implemented:

- tool runner can send venue profile context into AI prompts;
- tools still fall back safely to deterministic mock when AI fails;
- Tech Card Studio includes venue format, positioning, and owner goal in markdown/PDF;
- venue context is editable in UI while full persisted profile comes from onboarding later.

## Current Tech Card AI Layer

Implemented:

- AI draft endpoint for Tech Card Studio;
- strict JSON contract normalized into editable ingredient rows;
- venue profile context included in prompt;
- fallback draft when AI is unavailable;
- UI action to fill dish, category, output, ingredients, prices, KBJU, and process.

## Demo Framing

For tomorrow:

1. "This is not a replacement for iiko. It sits above iiko."
2. "iiko stores operations. Receptor explains and automates owner decisions."
3. "We start with BI and Copilot. Then we connect menu, tech cards, team, and daily briefings."
4. "For your pilot, I want one real restaurant, one real iiko key, and one week of feedback."
