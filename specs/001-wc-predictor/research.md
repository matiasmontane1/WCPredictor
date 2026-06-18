# Research Findings: WCPredictor

**Date**: 2026-06-18
**Feature**: 001-wc-predictor

---

## Decision 1: Deployment Stack

**Decision:** Vercel (React PWA frontend) + Render free tier (FastAPI backend) + Supabase free Postgres (database)

**Rationale:**
- Render free tier supports Python/FastAPI natively (no Dockerfile required for simple apps)
- SQLite on free-tier hosting is not viable: Render free has no persistent disk, data is lost on every redeploy or after spin-down
- Supabase free Postgres (500MB, always-on) replaces SQLite at zero cost with full persistence
- Vercel is superior to Render static sites for React/Vite (faster global CDN, zero-config, always-on)
- Render backend spins down after 15 min inactivity — acceptable for a personal, manually-triggered tool (user presses "Sync" once/day; 30–60s cold start is tolerable)

**Alternatives considered:**
- Railway.app: Removed free tier in mid-2023, requires paid plan
- Fly.io: Requires credit card; volumes not truly free
- Koyeb: Always-on free but 512MB RAM is tight for Python + BeautifulSoup scraping
- Full SQLite on Render: Not viable due to ephemeral filesystem

---

## Decision 2: Fixtures Source

**Decision:** football-data.org free API (competition code: `WC`)

**Rationale:**
- Free registration (email only, no credit card), instant API key
- Free tier: 10 req/min
- Covers FIFA World Cup — confirmed for WC 2018 and 2022 under code `WC`
- Provides: fixtures, match dates, team names, kickoff times, results
- Sufficient for "today's matches" discovery feature

**Key endpoint:** `GET /v4/competitions/WC/matches` with header `X-Auth-Token: {key}`

**Risk:** WC 2026 fixtures may not be available until tournament starts. Fallback: manual fixture entry via the Settings page.

---

## Decision 3: Odds Source

**Decision:** The Odds API free tier (sport key: `soccer_fifa_world_cup`, market: `h2h`)

**Rationale:**
- 500 requests/month free — sufficient (≈64 WC matches × 1–2 syncs/day = ~130 requests total)
- Covers soccer 1X2 (h2h) markets for the World Cup
- **Exact score (correct score) markets are NOT available** on any tier of The Odds API
- Normalized 1X2 implied probabilities are used to calibrate the Poisson model's λ parameters

**Key endpoint:** `GET /v4/sports/soccer_fifa_world_cup/odds?markets=h2h&regions=eu`

**Important constraint:** Since exact score odds are unavailable for free, the ensemble model uses two Poisson calibrations (see Decision 5).

---

## Decision 4: xG Source

**Decision:** FBref.com scraping (requests + BeautifulSoup / `soccerdata` package) with SofaScore undocumented API as fallback

**Rationale:**
- FBref is the only reliable free source with xG data for international tournaments
- Understat covers only 6 club leagues — no World Cup data
- FBref competition URL: `https://fbref.com/en/comps/1/World-Cup-Stats`
- Match-level xG is in the shooting/match-log tables, parseable with `pd.read_html`
- `soccerdata` PyPI package wraps FBref and handles rate-limit delays automatically

**Fallback:** SofaScore unofficial JSON API (`https://api.sofascore.com/api/v1/event/<id>/statistics`) — returns xG per match without authentication. Unofficial and may break; used only when FBref scraping fails.

**Rate limit:** FBref enforces scraping limits. The scraper must add 2–5s delays between requests and only runs on manual "Sync" trigger, never on a cron.

---

## Decision 5: Ensemble Model Architecture

**Decision:** Two-source Poisson ensemble (no exact score market data available)

**The two models:**
- **Model A (xG-Poisson):** Uses xG values directly as Poisson rates. `λ_home = xG_home`, `λ_away = xG_away`. Generates P(X:Y) via independent bivariate Poisson.
- **Model B (Market-Poisson):** Numerically solves for `λ_home` and `λ_away` values that reproduce the 1X2 market probabilities (after overround removal). Generates P(X:Y) from those calibrated λ values.

**Ensemble formula (from spec):**
```
P_final(X:Y) = W_a × P_a(X:Y) + W_b × P_b(X:Y)
```
Weights start at 0.5 / 0.5 and are updated by the feedback loop after each match.

**EV calculation:**
```
EV(X:Y) = P_final(X:Y) × points_exact_score + P_final(winner) × points_winner
```
Where `P_final(winner)` = sum of P_final over all scores where the predicted winner matches.

**Outlier filtering:** Scores where X + Y > 7 are penalized (multiplied by 0.1) before ranking suggestions. Scores where either team scores > 5 are zeroed out.

**Mathematical grounding:** Both models produce valid bivariate Poisson distributions. The ensemble is a convex combination of two probability distributions and therefore also a valid probability distribution.

---

## Decision 6: Database

**Decision:** Supabase free Postgres (via `asyncpg` + `databases` for async FastAPI)

**Rationale:**
- Free tier: 500MB storage, 2 projects, always-on, email registration only
- Replaces SQLite for production — same SQL schema works for both
- `databases` library provides async query interface compatible with FastAPI

**Local development:** SQLite via SQLAlchemy (same schema), switched via `DATABASE_URL` env var:
- Local: `sqlite+aiosqlite:///./dev.db`
- Production: `postgresql+asyncpg://...` (Supabase connection string)

---

## Decision 7: Frontend PWA

**Decision:** React + Vite + TypeScript + `vite-plugin-pwa` + Tailwind CSS

**Rationale:**
- `vite-plugin-pwa` auto-generates service worker (Workbox-based) from `vite.config.ts`
- HTTPS required for service workers — provided by Vercel by default
- Android Chrome: shows automatic install banner when manifest + service worker are present
- iOS Safari: requires manual "Add to Home Screen" from share sheet (platform limitation, not fixable)
- Tailwind CSS chosen for mobile-first responsive design without heavy UI library overhead

**Required:** Two PNG icons (192×192 and 512×512) in `public/icons/`

---

## Accounts to Create (in order)

| Service | URL | Purpose | Notes |
|---|---|---|---|
| football-data.org | football-data.org/client/register | Fixtures API | Free, email only |
| The Odds API | the-odds-api.com | 1X2 odds | Free, 500 req/month |
| Supabase | supabase.com | Database | Free, email only |
| Render | render.com | FastAPI backend | Free, GitHub login |
| Vercel | vercel.com | React frontend | Free, GitHub login |
