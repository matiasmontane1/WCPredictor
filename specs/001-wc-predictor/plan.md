# Implementation Plan: WCPredictor

**Feature**: 001-wc-predictor
**Date**: 2026-06-18
**Status**: Ready for Task Generation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  FRONTEND (Vercel)                              │
│  React + Vite + TypeScript + vite-plugin-pwa    │
│  Tailwind CSS — Mobile-first PWA                │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/JSON
┌─────────────────▼───────────────────────────────┐
│  BACKEND (Render free tier)                     │
│  Python 3.11 + FastAPI + uvicorn                │
│  Async scrapers + Predictive engine             │
└──────┬──────────────────────────┬───────────────┘
       │                          │
┌──────▼──────┐        ┌──────────▼──────────────┐
│  Supabase   │        │  External APIs           │
│  Postgres   │        │  - football-data.org     │
│  (free tier)│        │  - The Odds API (h2h)    │
└─────────────┘        │  - FBref (scraping/xG)   │
                       └─────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend language | Python 3.11 | FastAPI ecosystem |
| Web framework | FastAPI | Async, auto OpenAPI docs |
| ORM / DB client | SQLAlchemy 2 + asyncpg | Async Postgres; aiosqlite for local dev |
| Database (prod) | Supabase free Postgres | Persistent, always-on |
| Database (dev) | SQLite via aiosqlite | Same schema, no external deps |
| HTTP client | httpx | Async requests for APIs |
| HTML scraper | requests + BeautifulSoup4 | FBref scraping |
| Stats helper | soccerdata (pip) | FBref wrapper with rate-limiting |
| Background tasks | FastAPI BackgroundTasks | Sync runs async without blocking |
| Frontend | React 18 + Vite + TypeScript | |
| Styling | Tailwind CSS | Mobile-first |
| PWA | vite-plugin-pwa | Auto service worker (Workbox) |
| State management | Zustand | Lightweight, no boilerplate |
| HTTP client (FE) | TanStack Query v5 | Caching, background refetch |
| Deployment (FE) | Vercel | Free static, CDN, HTTPS |
| Deployment (BE) | Render | Free web service, spins down |
| CI | None | Personal tool, manual deploys |

---

## Project Structure

```
WCPredictor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── matches.py
│   │   │       ├── sync.py
│   │   │       ├── config.py
│   │   │       ├── results.py
│   │   │       ├── validate.py
│   │   │       └── weights.py
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings (env vars)
│   │   │   └── database.py        # Engine, session, init_db
│   │   ├── models/
│   │   │   ├── orm.py             # SQLAlchemy table definitions
│   │   │   └── schemas.py         # Pydantic request/response schemas
│   │   ├── crud/
│   │   │   ├── matches.py
│   │   │   ├── metrics.py
│   │   │   ├── suggestions.py
│   │   │   ├── phase_config.py
│   │   │   └── weights.py
│   │   └── services/
│   │       ├── scrapers/
│   │       │   ├── fixtures.py    # football-data.org client
│   │       │   ├── odds.py        # The Odds API client
│   │       │   └── xg.py          # FBref scraper
│   │       └── engine/
│   │           ├── normalizer.py  # Overround removal
│   │           ├── poisson.py     # Bivariate Poisson model
│   │           ├── calibrator.py  # Solve λ from 1X2 market probs
│   │           ├── ensemble.py    # Weighted average of two models
│   │           ├── ev.py          # EV calculation per phase config
│   │           ├── suggester.py   # Conservative + Aggressive selection
│   │           └── feedback.py    # Brier score + weight updater
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts          # TanStack Query hooks
│   │   ├── components/
│   │   │   ├── MatchCard/
│   │   │   ├── SuggestionPanel/
│   │   │   ├── IntuitionValidator/
│   │   │   ├── SyncButton/
│   │   │   └── PhaseConfigForm/
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   ├── MatchDetail/
│   │   │   ├── Results/
│   │   │   └── Settings/
│   │   ├── store/
│   │   │   └── useAppStore.ts     # Zustand global state
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   │   ├── icons/
│   │   │   ├── icon-192.png
│   │   │   └── icon-512.png
│   │   └── manifest.json          # PWA manifest
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── package.json
└── specs/
    └── 001-wc-predictor/          # This directory
```

---

## Implementation Phases

### Phase 1 — Backend Foundation
*Set up the skeleton: FastAPI, database connection, ORM models, config.*

**Tasks:**
1. Initialize `backend/` with `requirements.txt` and `main.py` (health endpoint only)
2. Create `app/core/config.py` using Pydantic Settings — load `DATABASE_URL`, `ODDS_API_KEY`, `FOOTBALL_DATA_API_KEY`, `ENV`
3. Create `app/core/database.py` — async SQLAlchemy engine, session factory, `init_db()` that creates tables
4. Create `app/models/orm.py` — SQLAlchemy ORM tables: `phase_config`, `matches`, `scraped_metrics`, `model_weights`, `suggestions`, `prediction_log`
5. Create `app/models/schemas.py` — Pydantic schemas for all API request/response shapes
6. Add `ENV=development` SQLite path and `ENV=production` Supabase Postgres path in database.py
7. Run `uvicorn main:app --reload` — confirm `/health` returns 200

**Success:** `GET /health` returns `{"status": "ok"}`. All tables created in local SQLite.

---

### Phase 2 — Data Scrapers
*Fetch fixtures, odds, and xG from external sources.*

**Tasks:**
1. `services/scrapers/fixtures.py` — football-data.org client
   - `get_today_matches()` → fetch `/v4/competitions/WC/matches?dateFrom=today&dateTo=today`
   - Parse response → return list of match dicts
   - Handle 429 (rate limit) gracefully
2. `services/scrapers/odds.py` — The Odds API client
   - `get_odds_for_matches(team_names)` → fetch `soccer_fifa_world_cup` h2h odds
   - Match API response to local match by team name fuzzy matching
   - Handle quota exhaustion (500 req/month) — log remaining quota from response headers
3. `services/scrapers/xg.py` — FBref scraper
   - `get_xg_today()` → scrape FBref WC match log for today's date
   - Use `requests` + `pd.read_html` to parse shooting table
   - Add 3s delay between requests
   - Return dict keyed by `(home_team, away_team)` → `(xg_home, xg_away)`
   - On failure: return `None` (SofaScore fallback not implemented in MVP)
4. Unit tests for normalizer: given raw odds `[2.10, 3.40, 3.60]`, confirm normalized probs sum to exactly 1.0

**Success:** Running scrapers manually against live APIs returns valid data for at least one WC match.

---

### Phase 3 — Predictive Engine
*Bivariate Poisson, ensemble, EV, and suggestion generation.*

**Tasks:**
1. `services/engine/normalizer.py`
   - `remove_overround(odds_list)` → normalized implied probabilities
2. `services/engine/poisson.py`
   - `score_probability(lambda_home, lambda_away, max_goals=9)` → 10×10 matrix of P(X:Y)
   - Uses `scipy.stats.poisson.pmf` for each cell
3. `services/engine/calibrator.py`
   - `solve_lambdas(prob_home_win, prob_draw, prob_away_win)` → `(lambda_home, lambda_away)`
   - Uses `scipy.optimize.minimize` to find λ pair that reproduces the 1X2 distribution
4. `services/engine/ensemble.py`
   - `ensemble_distribution(metrics, weights)` → 10×10 combined probability matrix
   - Applies outlier penalty: scores where X+Y > 7 multiplied by 0.1
5. `services/engine/ev.py`
   - `calculate_ev(score_matrix, phase_config)` → 10×10 EV matrix
   - EV(X:Y) = P(X:Y) × points_exact + P(correct winner) × points_winner
6. `services/engine/suggester.py`
   - `get_suggestions(ev_matrix, prob_matrix)` → `{conservative, aggressive}`
   - Conservative: max probability score
   - Aggressive: max EV score that differs from conservative
7. Unit tests:
   - Poisson: P(0:0) for λ=1.0, λ=1.0 should be ≈ 0.135
   - Ensemble with 50/50 weights + identical inputs = same as single model
   - EV with 0 points config = all zeros

**Success:** All unit tests pass. For a known match (e.g., Argentina vs Brazil with λ=1.5/0.9), the top-5 suggestions are footballistically reasonable scores.

---

### Phase 4 — Sync Orchestrator & CRUD
*Wire scrapers to database. Implement all CRUD operations.*

**Tasks:**
1. `crud/` — async CRUD functions for each entity (create, read, update, delete)
2. `services/sync_service.py` — orchestrator:
   - `run_daily_sync(db)`:
     1. Fetch today's fixtures → upsert to `matches`
     2. Fetch odds → store raw + normalized in `scraped_metrics`
     3. Fetch xG → add to same `scraped_metrics` row
     4. Run engine → upsert `suggestions` for each match
     5. Write sync job status to in-memory dict (keyed by job_id)
3. `api/routes/sync.py` — `POST /sync` triggers `BackgroundTasks.add_task(run_daily_sync)`, `GET /sync/status/{job_id}` reads in-memory status dict
4. `api/routes/matches.py` — `GET /matches/today`, `GET /matches/{id}`
5. `api/routes/config.py` — phase CRUD endpoints
6. `api/routes/results.py` — `POST /matches/{id}/result` → store actual score → call feedback service
7. `api/routes/validate.py` — `POST /validate` → recompute P and EV for a given score on-the-fly
8. `api/routes/weights.py` — `GET /weights`
9. Register all routers in `main.py` with `/api/v1` prefix, add CORS middleware (allow all origins for personal tool)

**Success:** Full sync runs end-to-end in < 60s. All endpoints return correct JSON shapes as defined in `contracts/api.md`.

---

### Phase 5 — Feedback Loop
*Update weights based on actual match results.*

**Tasks:**
1. `services/engine/feedback.py`
   - `evaluate_match(actual_home, actual_away, metrics, current_weights)` → compute Brier score for each model
   - `update_weights(db, match_id)` → after N=5 evaluated matches, recalculate weights using cumulative Brier scores
   - Weight update formula: `W_a = (1 - BS_a) / ((1 - BS_a) + (1 - BS_b))`
   - Save `prediction_log` row, update `model_weights` singleton
2. Wire into `results.py` route: after saving actual score, call `update_weights(db, match_id)`
3. Regenerate suggestions for all future matches after weight update

**Success:** After entering 5 match results where FBref xG was consistently more accurate, `weight_xg` increases above 0.5.

---

### Phase 6 — Frontend
*React PWA with all pages and components.*

**Tasks:**
1. Initialize Vite + React + TypeScript + Tailwind + vite-plugin-pwa
2. Configure `vite.config.ts` with PWA manifest (app name: "WCPredictor", icons, display: standalone)
3. `api/client.ts` — TanStack Query setup with base URL from env var `VITE_API_URL`
4. **Dashboard page** — today's matches grid; "Sincronizar Hoy" button; sync progress indicator
5. **MatchCard component** — team names, kickoff time, Conservative/Aggressive pills with score + EV
6. **MatchDetail page** — full suggestion panel + probability distribution table (top 10 scores)
7. **IntuitionValidator component** — text input (format "X-Y"), debounced `POST /validate`, displays probability + EV + verdict badge
8. **Settings page** — phase config list, create/activate/delete controls
9. **Results page** — list of matches without result, score input form per match
10. **ModelWeightsWidget** — small info panel showing current W_xg / W_market and matches evaluated

**UX rules:**
- Mobile-first: all layouts work on 375px screen
- Sync button shows spinner and disables during sync; polling `GET /sync/status` every 3s
- Phase activation immediately invalidates and refetches today's matches query
- Empty states: "No hay partidos hoy" / "Sincronizá primero"

**Success:** V1–V5 scenarios in quickstart.md all pass on the running dev server.

---

### Phase 7 — Deployment
*Ship to Render + Vercel + Supabase.*

**Tasks:**
1. **Supabase**: Create project, run the DDL schema (from `data-model.md`) in the SQL editor, get connection string
2. **Render**: Create web service pointing to `backend/`, set env vars (`DATABASE_URL`, `ODDS_API_KEY`, `FOOTBALL_DATA_API_KEY`, `ENV=production`)
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Create `render.yaml` for config-as-code
3. **Vercel**: Create project pointing to `frontend/`, set `VITE_API_URL` to Render URL
   - Build command: `npm run build`
   - Output dir: `dist`
4. Run deployment smoke test from `quickstart.md`
5. Test PWA install on Android device

**Success:** All quickstart.md scenarios pass against the production Vercel URL.

---

## Key Constraints & Risks

| Risk | Mitigation |
|---|---|
| football-data.org WC 2026 coverage not yet active | Manual fixture entry fallback in Settings |
| FBref DOM changes break xG scraper | Modular scraper interface — swap implementation without changing callers |
| The Odds API 500 req/month quota exhausted | Log remaining quota in sync response; warn user when < 50 remain |
| Render 15min sleep causes slow first request | User will run sync manually once/day — cold start is acceptable |
| xG not available pre-match (FBref only has post-match xG) | Use historical average xG for teams as proxy; scrape from competition stats page |

---

## Cross-References

- Data model: `data-model.md`
- API contracts: `contracts/api.md`
- Validation guide: `quickstart.md`
- Research decisions: `research.md`
- Feature spec: `spec.md`
