# Receptor Tools Audit

Date: 2026-06-10

## Honest Read

The current 27 tools are useful as a library, but too noisy as the main product story.
Most of them are prompt forms: input, model call, markdown output. That is fine for
quick wins and lead generation, but premium SaaS value will come from connected
restaurant workflows with venue memory, real iiko data, saved history, exports, and
clear business decisions.

The right packaging is not "27 AI tools". The right packaging is:

1. Venue Profile and Copilot memory.
2. BI diagnostics from real iiko data.
3. Tech Card and Menu Studio.
4. Service and sales enablement.
5. Reputation and marketing support.

## Keep As Core

These should become first-class product workflows, not isolated prompts.

| Area | Tools | Why it matters |
| --- | --- | --- |
| Tech cards and menu | Recipe generator, food cost, KBJU, allergens, HACCP, menu descriptions | Direct restaurant pain: time, cost control, menu quality, compliance. |
| Owner operations | Menu audit, expense optimizer, morning briefing, stop-list | Speaks to the owner: what happened, what to do today, where money leaks. |
| Sales and service | Waiter script, complaint handling, training quiz | Turns menu and BI insights into team behavior. |
| Reputation | Review response, promo ideas | Good retention layer and free acquisition path. |

## Good Lead Magnets

These are useful as free or low-friction tools that bring restaurateurs into the
product:

- KBJU calculator.
- Food cost calculator.
- Review response.
- Job post generator.
- Morning briefing.
- Menu description batch.

The free promise should be narrow and practical: "get a useful restaurant document
in 60 seconds". The upsell is saved history, venue context, PDF/export, team access,
and iiko data.

## Needs Caution

These should not be presented as authoritative until backed by current references
or verified data:

- SanPiN check.
- Advertising law check.
- Competitor analysis without deep research.

They can stay, but the UI should frame them as a draft assistant, not legal or
research truth.

## Legacy Receptor Lessons

The strongest legacy direction was the tech-card pipeline:

- generate or import a tech card;
- validate yield, units, ingredients, and quality;
- map ingredients to iiko nomenclature articles;
- export iiko-compatible XLSX;
- export printable PDF / GOST-style document;
- keep versions and diffs;
- support skeletons before TTK import when iiko requires missing items to exist.

That is a real product. It is harder than prompt tools, but it is defensible and
sellable.

## Product Direction

### 1. Tech Card Studio

This should become the hero workflow inside tools:

- dish profile: name, concept, portion/yield, category;
- ingredients table: name, gross/net, unit, price, losses, article mapping;
- computed blocks: food cost, KBJU, allergens, HACCP;
- outputs: PDF/GOST print, menu description, waiter script, iiko export;
- history: versions, changes, previous exports.

### 2. Menu Studio

Batch work for real menus:

- paste menu or import from iiko;
- generate descriptions in venue tone;
- flag weak names, duplicates, price inconsistencies;
- create sales scripts for waiters;
- generate seasonal replacements and promo bundles.

### 3. Owner Cockpit

The tool block should feed the BI product:

- today's brief;
- what changed vs previous period;
- which dishes/categories depend too heavily on one item;
- stop-list and substitution advice;
- tasks for manager, chef, and service team.

## Demo Strategy

For a serious restaurant owner, do not demo all 27 tools.

Demo this sequence:

1. Venue Profile: Receptor understands the restaurant and its context.
2. BI: Receptor explains sales and operational signals.
3. Tech Card/Menu scenario: Receptor produces a concrete working artifact.
4. Copilot: ask "what should I do this week?" and show that the answer uses context.

The 27 tools become supporting evidence: "under the hood we also have a library of
restaurant assistants, but the product focus is operating intelligence."

## Next Build Steps

1. Repackage `/tools` around workflows instead of categories.
2. Add strategic labels: core, free entry, support, caution, later.
3. Build Tech Card Studio MVP with structured inputs and print/PDF output.
4. Connect tool prompts to venue profile context.
5. Restore legacy iiko ingredient/article mapping after working Cloud API pilot.
