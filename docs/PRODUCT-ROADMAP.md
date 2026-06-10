# Receptor Product Roadmap

## Positioning

Receptor is an operational copilot for restaurant owners and multi-location
operators. It connects to existing POS/back-office systems such as iiko Cloud
and, later, R-Keeper/RMS. It does not replace those systems. It turns their data
into daily decisions, alerts, and automation.

Core promise:

> Connect iiko or R-Keeper. Every morning Receptor tells the owner what changed,
> where money was lost or gained, and what the team should do today.

## Primary Customer

- Independent restaurant owners with 1-3 venues.
- Small holdings with 3-20 venues.
- Operators who already use iiko/R-Keeper but do not have fast daily analytics.

The buyer is usually the owner or managing partner. The daily user is the owner,
operations director, venue manager, chef, or marketer.

## Product Principles

1. Daily action beats static dashboards.
2. Existing POS remains the source of truth.
3. Every metric needs context: current value, comparison, reason, action.
4. AI must cite operational data and avoid invented numbers.
5. Demo fixtures are for development only; production flow starts from a real
   integration.

## MVP Shape

### 1. Connection Flow

- Sign in.
- Create venue.
- Paste iiko Cloud apiLogin.
- Fetch organizations.
- Select exact organization.
- Store encrypted credentials.
- Open BI on live data.

### 2. BI Cockpit

- Revenue summary.
- Average check and items sold when available.
- Top dishes.
- Category breakdown.
- Shift/day breakdown.
- Period comparison.
- Export.
- Clear integration health state.

### 3. Daily Brief

The flagship screen and automation.

Daily brief should answer:

- What happened yesterday?
- What changed against the comparison period?
- What sold best?
- What category or dish deserves attention?
- What should the manager do today?

Later delivery channels:

- In-app dashboard card.
- Email.
- Telegram.
- WhatsApp/Bitrix integrations if customers ask.

### 4. Copilot

Copilot answers owner questions using BI tools:

- "What happened yesterday?"
- "Which dishes dropped?"
- "Compare this week with last week."
- "What should we push this weekend?"
- "Which venue in the holding is underperforming?"

Copilot should show tool calls and avoid unsupported claims.

### 5. Multi-Location View

For holdings:

- List all venues.
- Rank by revenue.
- Flag venues down against previous period.
- Compare venue vs group average.
- Generate group-level daily brief.

## Near-Term Build Order

1. Finish iiko Cloud production flow.
   - Organization selection.
   - Encrypted credentials.
   - Real venue list in settings.
   - Integration health state.

2. Build Daily Brief foundation.
   - Domain module that composes iiko metrics.
   - Tests on mock client.
   - Dashboard card.
   - API route/server action.

3. Improve BI from "numbers" to "decisions".
   - Period deltas.
   - Top movers.
   - Empty/error states.
   - Clear live/demo badges.

4. Add automation channel.
   - Start with Telegram daily brief.
   - User-configured delivery time.
   - Manual "send test brief".

5. Add multi-location skeleton.
   - Settings list.
   - Group overview.
   - Venue ranking.

6. Add R-Keeper/RMS channel.
   - Model a generic integration connection.
   - Implement one second source only after iiko Cloud flow is stable.

## Sales Pilot

Sell a 2-week pilot, not a vague subscription.

Pilot scope:

- 1-3 venues connected.
- Daily brief every morning.
- BI cockpit.
- Copilot for owner questions.
- End-of-pilot report: discovered issues, revenue/category changes, recommended
  actions.

The sales artifact should be a real daily brief screenshot, not a feature list.

## What Not To Build Yet

- Full POS replacement.
- Staff scheduling.
- Inventory write-back.
- Complex CRM.
- Billing automation before pilots.
- A large marketplace of generic AI tools.

Those can come later if pilots prove demand.
