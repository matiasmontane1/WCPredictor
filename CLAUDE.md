# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
uvicorn main:app --reload          # dev server (port 8000)
```
Requires a `.env` file in `backend/` with at minimum:
```
ODDS_API_KEY=...
FOOTBALL_DATA_API_KEY=...
```

### Frontend
```bash
cd frontend
npm run dev      # dev server (port 5173)
npm run build    # tsc + vite build
npm run lint     # eslint
```
Set `VITE_API_URL` to point at the backend (defaults to `/api/v1` which works when proxied).

### Deployment
Backend is deployed on Render via `backend/render.yaml`. Production uses PostgreSQL (Supabase) via the `DATABASE_URL` env var; dev uses SQLite (`dev.db`).

## Architecture

### Two-layer stack
- **Backend**: FastAPI + SQLAlchemy async + aiosqlite (dev) / asyncpg (prod). Entry point: `backend/main.py`. All routes under `/api/v1`.
- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS v4. SPA with React Router v7. All API calls are TanStack Query hooks defined in `frontend/src/api/client.ts` — no other files call `fetch` directly.

### Prediction engine (`backend/app/services/engine/`)
The core prediction flow runs inside `sync_service.py:run_daily_sync()` and produces two suggestion types (conservative/aggressive) per match:

1. **Two Poisson models** run in parallel:
   - Model A (`lambda_xg_*`): Elo-derived goal rate (from `scrapers/elo_scraper.py`)
   - Model B (`lambda_market_*`): implied by bookmaker odds, solved via `calibrator.py:solve_lambdas()`
2. **Ensemble** (`ensemble.py`): weighted sum of the two score-probability matrices; scores where total goals > 7 are penalized ×0.1.
3. **EV calculation** (`ev.py`): multiplies each score's probability by the active `PhaseConfig` point values (winner / goal-diff / exact-score).
4. **Suggester** (`suggester.py`): picks conservative (highest EV) and aggressive (high probability + good EV) scores.
5. **Feedback loop** (`feedback.py`): after a match finishes, computes 1X2 Brier scores for each model and uses inverse-error weighting to update `ModelWeights`. Weight update only fires when ≥ 5 matches have been evaluated (`MIN_MATCHES_FOR_UPDATE = 5`).

### Data model (`backend/app/models/orm.py`)
- `Match` ← one-to-one → `ScrapedMetrics` (raw odds + derived lambdas)
- `Match` ← one-to-many → `Suggestion` (conservative + aggressive, regenerated each sync)
- `Match` ← one-to-one → `PredictionLog` (feedback record; presence means match already evaluated)
- `ModelWeights` (single row, id=1) — `weight_xg` + `weight_market` always sum to 1
- `PhaseConfig` — scoring rules (points_winner / points_goal_diff / points_exact_score); only one row is `is_active` at a time

### Sync lifecycle (`backend/app/services/sync_service.py`)
Runs on startup and every 4 hours via APScheduler:
1. Upsert full WC schedule from football-data.org
2. Auto-evaluate any newly finished matches (calls `feedback_engine.update_weights`)
3. Fetch today's odds → compute market lambdas
4. Compute Elo lambdas (falls back to market lambdas if Elo scraper fails)
5. Run engine for each today's match that isn't locked (locked = kickoff - 10 min or already started)

### Frontend state
- **Server state**: TanStack Query (all hooks in `client.ts`; query keys are `['matches', ...]`, `['weights']`, `['phases']`, `['stats', 'wc']`)
- **Local/UI state**: Zustand store in `frontend/src/store/useAppStore.ts`
- Pages: Dashboard (today's matches), MatchDetail (score distribution + validator), Results (past matches), Stats (WC historical stats), Settings (phase config + weights)
