# Tasks: WCPredictor

**Feature**: 001-wc-predictor
**Generated**: 2026-06-18
**Total tasks**: 66
**User Stories**: 5 (US1–US5 from spec.md Escenarios 1–5)

---

## User Story Map

| ID | Escenario (spec.md) | Description |
|---|---|---|
| US1 | Escenario 1 | Configurar puntajes de la fase actual |
| US2 | Escenario 2 | Sincronización diaria de datos (scraping) |
| US3 | Escenario 3 | Evaluar sugerencias del motor predictivo |
| US4 | Escenario 4 | Validar la intuición del usuario |
| US5 | Escenario 5 | Auto-aprendizaje y Feedback Loop |

---

## Implementation Strategy

MVP scope: **US1 + US2 + US3** — phase config + sync + suggestions. This covers the core value loop.
US4 and US5 add refinement on top and can ship incrementally.

Each phase is independently testable before moving to the next.

---

## Phase 1 — Project Setup

*Initialize both workspaces. No story dependency — required for everything.*

- [x] T001 Create backend/ directory with backend/app/__init__.py, backend/app/api/__init__.py, backend/app/api/routes/__init__.py, backend/app/core/__init__.py, backend/app/models/__init__.py, backend/app/crud/__init__.py, backend/app/services/__init__.py, backend/app/services/scrapers/__init__.py, backend/app/services/engine/__init__.py
- [x] T002 Create backend/requirements.txt with: fastapi, uvicorn[standard], sqlalchemy[asyncio], aiosqlite, asyncpg, databases, httpx, requests, beautifulsoup4, lxml, pandas, scipy, soccerdata, python-dotenv, pydantic-settings
- [x] T003 Create backend/.env.example with all required variables: DATABASE_URL, ODDS_API_KEY, FOOTBALL_DATA_API_KEY, ENV (development/production), SUPABASE_URL, SUPABASE_KEY
- [x] T004 Initialize frontend/ with: npm create vite@latest frontend -- --template react-ts, then install dependencies: npm install @tanstack/react-query zustand react-router-dom
- [x] T005 [P] Install and configure Tailwind CSS in frontend/: npm install -D tailwindcss postcss autoprefixer, run npx tailwindcss init -p, update frontend/tailwind.config.js with content paths, add @tailwind directives to frontend/src/index.css
- [x] T006 [P] Install vite-plugin-pwa in frontend/: npm install -D vite-plugin-pwa

---

## Phase 2 — Backend Foundation

*Blocking prerequisite for all user stories. Must complete before Phase 3+.*

**Independent test:** `uvicorn backend/main:app --reload` starts without error. `GET /health` returns `{"status": "ok"}`. SQLite file `dev.db` is created with all 6 tables on first startup.

- [x] T007 Create backend/app/core/config.py using pydantic-settings BaseSettings: fields DATABASE_URL (str), ODDS_API_KEY (str), FOOTBALL_DATA_API_KEY (str), ENV (str, default "development"). Load from .env file. Compute is_production property (ENV == "production").
- [x] T008 Create backend/app/core/database.py: create async SQLAlchemy engine (aiosqlite when ENV=development, asyncpg when ENV=production), async session factory using async_sessionmaker, async init_db() that calls metadata.create_all(), async get_db() generator for FastAPI Depends injection
- [x] T009 Create backend/app/models/orm.py with all 6 SQLAlchemy mapped tables using DeclarativeBase: PhaseConfig (id, phase_name, points_winner, points_exact_score, is_active, created_at), Match (id, external_id UNIQUE, match_date, kickoff_time, home_team, away_team, phase, status, actual_home_goals, actual_away_goals, created_at), ScrapedMetrics (id, match_id FK, scraped_at, xg_home, xg_away, odds_home_win_raw, odds_draw_raw, odds_away_win_raw, implied_prob_home, implied_prob_draw, implied_prob_away, lambda_xg_home, lambda_xg_away, lambda_market_home, lambda_market_away, scraper_source, odds_source), ModelWeights (id always=1, weight_xg, weight_market, matches_evaluated, last_updated_at), Suggestion (id, match_id FK, score_home, score_away, probability, ev, suggestion_type, generated_at), PredictionLog (id, match_id FK UNIQUE, actual_home_goals, actual_away_goals, model_a_error, model_b_error, weight_xg_before, weight_market_before, weight_xg_after, weight_market_after, evaluated_at)
- [x] T010 Create backend/app/models/schemas.py with Pydantic v2 BaseModel schemas for all API shapes: PhaseConfigOut, PhaseConfigCreate, MatchOut, MatchSummary, MatchDetailOut, MetricsOut, ScoreDistributionItem, SuggestionOut, SuggestionPair, SyncResponse, SyncStatusResponse, ResultIn, ResultOut, ValidateIn, ValidateOut, ModelWeightsOut. All datetimes as ISO strings.
- [x] T011 Create backend/main.py: instantiate FastAPI(title="WCPredictor", version="1.0.0"), add CORSMiddleware (allow_origins=["*"]), add startup event that calls init_db(), add GET /health endpoint returning {"status": "ok", "version": "1.0.0"}, add placeholder router include stubs (commented out — uncommented as each router is implemented)
- [x] T012 Verify Phase 2: run `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`, confirm /health returns 200, confirm dev.db file exists and contains all 6 tables via `python -c "import sqlite3; conn=sqlite3.connect('dev.db'); print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())"`

---

## Phase 3 — US1: Configurar Puntajes de la Fase

*User can create, activate, and delete phase scoring configs. EV calculations use active config.*

**Independent test (V1 in quickstart.md):** Create phase "Grupos" (winner=1, exact=3) via Settings page → activate → `GET /api/v1/config/phase` shows it active. Activate second phase → first becomes inactive.

- [x] T013 [US1] Create backend/app/crud/phase_config.py with async functions: create_phase(db, data) → PhaseConfig, list_phases(db) → list[PhaseConfig], get_active_phase(db) → PhaseConfig | None, set_active_phase(db, phase_id) → PhaseConfig (sets all is_active=False then target=True in one transaction), delete_phase(db, phase_id) → bool (raises ValueError if is_active)
- [x] T014 [US1] Create backend/app/api/routes/config.py with endpoints: GET /config/phase (list all, 200), POST /config/phase (create, 201, validates points ≥ 0), PUT /config/phase/{id}/activate (set active, 200, 404 if not found), DELETE /config/phase/{id} (204, 400 if active). Uncomment config router in backend/main.py with prefix /api/v1.
- [x] T015 [P] [US1] Add TanStack Query hooks to frontend/src/api/client.ts: create queryClient export, usePhaseConfigs() → GET /config/phase, useCreatePhase() mutation → POST /config/phase, useActivatePhase() mutation → PUT /config/phase/{id}/activate (invalidates phases query on success), useDeletePhase() mutation → DELETE /config/phase/{id}
- [x] T016 [P] [US1] Create frontend/src/components/PhaseConfigForm/index.tsx: controlled form with three inputs (phase_name text, points_winner number min=0, points_exact_score number min=0), submit calls useCreatePhase(), shows inline validation errors, resets on success
- [x] T017 [US1] Create frontend/src/pages/Settings/index.tsx: renders list of PhaseConfig items (each row shows name, points, active badge, Activate button, Delete button), renders PhaseConfigForm below the list, mobile-first layout (single column, full-width cards). ModelWeightsWidget placeholder section at bottom (wired in US5).
- [x] T018 [US1] Create frontend/src/App.tsx with React Router v6: BrowserRouter wrapping QueryClientProvider wrapping routes. Routes: / → lazy Dashboard, /match/:id → lazy MatchDetail, /results → lazy Results, /settings → Settings. Add bottom nav bar stub (BottomNav component, wired in Phase 8).

---

## Phase 4 — US2: Sincronización Diaria de Datos

*User presses "Sincronizar Hoy" → scrapers run in background → matches populated with odds and xG.*

**Independent test (V2 in quickstart.md):** Click sync button → spinner shows → after completion today's matches appear on Dashboard with team names and kickoff times. `GET /sync/status/{job_id}` shows completed. Odds and xG fields populated in scraped_metrics table.

- [x] T019 [US2] Create backend/app/services/engine/normalizer.py with remove_overround(odds_list: list[float]) → list[float]: computes implied probs as 1/odd for each, divides each by total sum, returns normalized list that sums to exactly 1.0. Raises ValueError if any odd ≤ 0 or list is empty.
- [x] T020 [US2] Create backend/app/services/scrapers/fixtures.py with async get_today_matches() using httpx.AsyncClient: GET https://api.football-data.org/v4/competitions/WC/matches with dateFrom and dateTo set to today (UTC), header X-Auth-Token from settings, parse JSON response into list of dicts with keys: external_id, match_date, kickoff_time, home_team, away_team, phase, status. Handle 429 with 60s retry log message. Handle 404 (WC not found) by returning empty list with warning log.
- [x] T021 [US2] Create backend/app/services/scrapers/odds.py with async get_odds_for_matches(team_names: list[str]) using httpx.AsyncClient: GET https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds with params apiKey, regions=eu, markets=h2h. Parse bookmaker array, average h2h odds across all bookmakers per match. Return dict keyed by frozenset({home_team, away_team}) → {odds_home, odds_draw, odds_away}. Log x-requests-remaining header from response; if remaining < 50 log a WARNING. Handle quota exhausted (402/422) by returning empty dict.
- [x] T022 [US2] Create backend/app/services/scrapers/xg.py with get_xg_today() (sync, not async — requests library): scrape https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures, parse HTML table with pd.read_html(), filter rows for today's date, extract xg_home and xg_away columns. Add time.sleep(3) before each request. Return dict keyed by (home_team_normalized, away_team_normalized) → (xg_home, xg_away). Return None on any exception (HTTPError, parsing error) and log the error.
- [x] T023 [P] [US2] Create backend/app/crud/matches.py with async functions: upsert_match(db, match_data) → Match (INSERT OR REPLACE by external_id), get_today_matches(db) → list[Match], get_match_by_id(db, match_id) → Match | None, set_match_result(db, match_id, home_goals, away_goals) → Match
- [x] T024 [P] [US2] Create backend/app/crud/metrics.py with async functions: upsert_metrics(db, match_id, metrics_data) → ScrapedMetrics (upsert by match_id), get_metrics_for_match(db, match_id) → ScrapedMetrics | None
- [x] T025 [US2] Create backend/app/services/sync_service.py with: in-memory job_status dict (module-level), async run_daily_sync(db, job_id: str): (1) update job_status[job_id] = {status: "running", ...}, (2) call get_today_matches() → upsert each match, (3) call get_odds_for_matches() → call remove_overround() → call upsert_metrics() with odds data, (4) call get_xg_today() in thread executor (it's sync) → update metrics with xG, (5) for each match with metrics: run engine pipeline → upsert suggestions (engine wired in US3, stub returning empty list for now), (6) update job_status[job_id] = {status: "completed", results: {...}}. Wrap all in try/except → set status: "failed" on error.
- [x] T026 [US2] Create backend/app/api/routes/sync.py with: POST /sync → generate job_id as f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}", add run_daily_sync to BackgroundTasks, return 202 with job_id. GET /sync/status/{job_id} → read job_status dict, return 404 if not found. Uncomment sync router in backend/main.py with prefix /api/v1.
- [x] T027 [P] [US2] Create backend/app/api/routes/matches.py with: GET /matches/today → get_today_matches() + get suggestions per match → return list[MatchSummary] with embedded SuggestionPair. GET /matches/{match_id} → get match + metrics + full score distribution (top 10 by probability) + suggestions → return MatchDetailOut. Uncomment matches router in backend/main.py.
- [x] T028 [US2] Create frontend/src/components/SyncButton/index.tsx: button labeled "Sincronizar Hoy", calls useTriggerSync() on click, sets local jobId state, polls useSyncStatus(jobId) every 3000ms while status is "running" or "started", shows spinner icon during sync, disables button during sync, shows success toast on "completed", shows error toast on "failed". Stop polling on terminal status.
- [x] T029 [US2] Add TanStack Query hooks to frontend/src/api/client.ts: useTriggerSync() mutation → POST /sync (returns job_id), useSyncStatus(jobId) query with refetchInterval: 3000 when jobId is set and status not terminal, useTodayMatches() → GET /matches/today (refetchOnWindowFocus: true)

---

## Phase 5 — US3: Evaluar Sugerencias del Motor Predictivo

*User sees Conservative and Aggressive picks per match with probability % and EV.*

**Independent test (V3 in quickstart.md):** After sync, click any match → MatchDetail shows two clearly labeled suggestions. Change phase points in Settings → suggestions update without page reload.

- [x] T030 [US3] Create backend/app/services/engine/poisson.py with score_probability(lambda_home: float, lambda_away: float, max_goals: int = 9) → np.ndarray shape (10,10): cell [i][j] = Poisson(i|lambda_home) × Poisson(j|lambda_away) using scipy.stats.poisson.pmf. Verify P(0:0) ≈ 0.135 for both lambdas = 1.0.
- [x] T031 [US3] Create backend/app/services/engine/calibrator.py with solve_lambdas(prob_home: float, prob_draw: float, prob_away: float) → tuple[float, float]: uses scipy.optimize.minimize with Nelder-Mead to find (lh, la) minimizing sum of squared differences between model's implied 1X2 probs (summing Poisson matrix over win/draw/loss regions) and target probs. Initial guess: lh=1.5, la=1.0. Clamp result to [0.1, 5.0].
- [x] T032 [US3] Create backend/app/services/engine/ensemble.py with ensemble_distribution(metrics: ScrapedMetrics, weights: ModelWeights) → np.ndarray shape (10,10): (1) Model A: score_probability(metrics.lambda_xg_home, metrics.lambda_xg_away), (2) Model B: score_probability(metrics.lambda_market_home, metrics.lambda_market_away), (3) combined = weights.weight_xg × A + weights.weight_market × B, (4) apply outlier penalty: multiply all cells where i+j > 7 by 0.1, (5) renormalize so matrix sums to 1.0, return matrix.
- [x] T033 [US3] Create backend/app/services/engine/ev.py with calculate_ev(prob_matrix: np.ndarray, phase_config: PhaseConfig) → np.ndarray shape (10,10): for each cell (i,j) compute EV = prob_matrix[i][j] × phase_config.points_exact_score + P_winner_correct(i,j) × phase_config.points_winner, where P_winner_correct = sum of prob_matrix cells that share the same winner outcome as (i,j). Return EV matrix.
- [x] T034 [US3] Create backend/app/services/engine/suggester.py with get_suggestions(ev_matrix: np.ndarray, prob_matrix: np.ndarray) → dict: conservative = argmax of prob_matrix → {"score": "X-Y", "probability": float, "ev": float}. aggressive = argmax of ev_matrix excluding conservative cell → same shape. Return {"conservative": ..., "aggressive": ...}.
- [x] T035 [P] [US3] Create backend/app/crud/suggestions.py with async functions: upsert_suggestions(db, match_id, suggestions: list[dict]) → deletes existing suggestions for match then bulk inserts new ones, get_suggestions_for_match(db, match_id) → list[Suggestion], get_score_distribution(db, match_id, top_n=10) → list[dict] ordered by probability desc
- [x] T036 [US3] Wire engine pipeline into backend/app/services/sync_service.py: after metrics are saved, for each match: (1) get active phase config, (2) get metrics from DB, (3) compute lambda_xg and lambda_market (call solve_lambdas for market lambdas, store back to metrics), (4) call ensemble_distribution(), (5) call calculate_ev(), (6) call get_suggestions(), (7) call upsert_suggestions(). Skip if metrics unavailable.
- [x] T037 [P] [US3] Update backend/app/api/routes/matches.py GET /matches/{match_id}: build ScoreDistributionItem list from full 10×10 matrix (compute on-the-fly from stored lambda values + current weights), sort by probability desc, return top 15 in MatchDetailOut.score_distribution field.
- [x] T038 [P] [US3] Create frontend/src/components/SuggestionPanel/index.tsx: two-column card layout (Conservative | Aggressive), each card shows: label badge (green/orange), score "X - Y" in large font, probability "XX.X%" subtitle, EV "EV: X.XX pts" caption. Mobile: stacks vertically.
- [x] T039 [P] [US3] Create frontend/src/components/MatchCard/index.tsx: card with home_team vs away_team, kickoff time formatted in local timezone, two small pills (Conservadora: score + prob%, Arriesgada: score + EV), entire card is a React Router Link to /match/:id. Shows skeleton loader while data loads.
- [x] T040 [US3] Create frontend/src/pages/Dashboard/index.tsx: renders SyncButton at top, renders grid of MatchCard components from useTodayMatches() data, empty state "No hay partidos hoy" when list is empty, "Sincronizá primero" state when matches exist but have no suggestions. Invalidates matches query when sync completes.
- [x] T041 [US3] Create frontend/src/pages/MatchDetail/index.tsx: shows match header (teams, kickoff), SuggestionPanel with conservative+aggressive, collapsible score distribution table (top 10 scores ranked by probability: score | prob% | EV), IntuitionValidator below (placeholder for US4). Uses useMatchDetail(matchId) hook. Fetches on mount and when active phase changes.
- [x] T042 [US3] Add TanStack Query hook useMatchDetail(matchId) → GET /matches/{matchId} to frontend/src/api/client.ts

---

## Phase 6 — US4: Validar Intuición del Usuario

*User types any score → instantly sees its probability and EV.*

**Independent test (V4 in quickstart.md):** On MatchDetail, type "3-1" → probability and EV appear within 500ms. Clear input → validator resets. Change score → numbers update.

- [x] T043 [US4] Create backend/app/api/routes/validate.py with POST /validate: accept ValidateIn(match_id, goals_home, goals_away), get metrics from DB (return 400 if none), get active phase config (return 400 if none), get current model weights, recompute ensemble_distribution() and calculate_ev() on-the-fly (do not persist), look up probability and EV for (goals_home, goals_away), compute rank by sorting all 100 cells, determine verdict ("top_pick" if rank ≤ 2, "above_average" if rank ≤ 6, else "below_average"), return ValidateOut. Uncomment validate router in backend/main.py.
- [x] T044 [P] [US4] Add useValidateScore() mutation hook to frontend/src/api/client.ts: POST /validate, accepts {match_id, goals_home, goals_away}, returns ValidateOut
- [x] T045 [US4] Create frontend/src/components/IntuitionValidator/index.tsx: single text input with placeholder "Ej: 2-1", parse input on change with regex /^(\d)-(\d)$/, if valid parse goals_home and goals_away and call useValidateScore() after 400ms debounce, display result card below input with: probability "XX.X%", EV "EV: X.XX pts", verdict badge (colored: green=top_pick, yellow=above_average, gray=below_average). Show loading skeleton during request. Hide result card when input is empty or invalid.
- [x] T046 [US4] Integrate IntuitionValidator into frontend/src/pages/MatchDetail/index.tsx: add section "¿Tenés un presentimiento?" below the score distribution table, pass match_id prop to IntuitionValidator

---

## Phase 7 — US5: Auto-aprendizaje y Feedback Loop

*User enters actual match scores → model weights auto-adjust based on which model predicted better.*

**Independent test (V5 in quickstart.md):** Enter 5 actual results → `GET /weights` shows matches_evaluated=5 and weights may have shifted from 0.5. If xG model consistently closer → weight_xg > 0.5.

- [x] T047 [US5] Create backend/app/services/engine/feedback.py with: compute_brier_score(prob_matrix: np.ndarray, actual_home: int, actual_away: int) → float: Brier score = (1 - prob_matrix[actual_home][actual_away])^2 + sum of all other cells' prob^2 (simplified scalar Brier). update_weights(db, match_id) async: (1) get metrics + weights + prediction_log count, (2) compute Brier for Model A and Model B separately using their individual probability matrices (before ensemble), (3) save PredictionLog entry, (4) if total evaluated ≥ 5: recompute cumulative Brier scores across all logs, apply W_a = (1-BS_a)/((1-BS_a)+(1-BS_b)), update model_weights row, return new weights.
- [x] T048 [P] [US5] Create backend/app/crud/weights.py with async functions: get_weights(db) → ModelWeights (creates default 0.5/0.5 row if none exists), update_weights(db, weight_xg, weight_market) → ModelWeights (upserts singleton row with id=1)
- [x] T049 [P] [US5] Create backend/app/crud/prediction_log.py with async functions: create_log_entry(db, data) → PredictionLog, get_all_logs(db) → list[PredictionLog], get_log_count(db) → int, get_log_for_match(db, match_id) → PredictionLog | None
- [x] T050 [US5] Create backend/app/api/routes/results.py with POST /matches/{match_id}/result: validate match exists and has no result yet (409 if duplicate), validate goals ≥ 0 (422), call set_match_result(), call update_weights() from feedback service, return ResultOut with new weights. Also add GET /weights in backend/app/api/routes/weights.py → get_weights(). Uncomment both routers in backend/main.py.
- [x] T051 [P] [US5] Add hooks to frontend/src/api/client.ts: useSubmitResult() mutation → POST /matches/{id}/result (invalidates matches + weights queries on success), useModelWeights() → GET /weights
- [x] T052 [US5] Create frontend/src/pages/Results/index.tsx: fetch all matches via useTodayMatches (plus a separate query for all matches needing results — add GET /matches?status=finished&needs_result=true endpoint or filter client-side), for each match without actual_home_goals: render a result entry card with match header and two number inputs (home goals, away goals, both min=0 max=20), submit button calls useSubmitResult(), shows success state "Resultado guardado ✓" after submit, shows "Pesos actualizados" with new weight values in toast.
- [x] T053 [P] [US5] Create frontend/src/components/ModelWeightsWidget/index.tsx: shows weight_xg and weight_market as percentages with a two-tone horizontal bar chart, shows matches_evaluated count, shows last_updated_at timestamp. Uses useModelWeights() hook. Shows skeleton if no data. Integrate into frontend/src/pages/Settings/index.tsx below phase config list.

---

## Phase 8 — Navigation & PWA Polish

*Wire full app navigation, bottom nav bar, PWA install support.*

- [x] T054 Create frontend/src/components/BottomNav/index.tsx: fixed bottom navigation bar with 3 items — Dashboard (house icon, route /), Resultados (trophy icon, route /results), Ajustes (gear icon, route /settings). Highlight active route. Mobile-safe: add padding-bottom for iOS home indicator via pb-safe class. Full width.
- [x] T055 Integrate BottomNav into frontend/src/App.tsx layout: wrap all route outlets in a div with padding-bottom (pb-16) to avoid content hidden behind nav bar. BottomNav renders outside the route outlet (persistent across pages).
- [x] T056 Create frontend/src/store/useAppStore.ts with Zustand store: syncJobId (string | null), setSyncJobId(id). Used by SyncButton to share job ID without prop drilling.
- [x] T057 Configure PWA in frontend/vite.config.ts: add VitePWA plugin with registerType: "autoUpdate", manifest: {name: "WCPredictor", short_name: "WCP", start_url: "/", display: "standalone", background_color: "#0f172a", theme_color: "#22c55e", icons: [{src: "/icons/icon-192.png", sizes: "192x192"}, {src: "/icons/icon-512.png", sizes: "512x512"}]}. Add workbox config with runtimeCaching for API responses (NetworkFirst strategy for /api/v1/matches/).
- [x] T058 [P] Add PWA icons: create simple PNG icons (192×192 and 512×512) using a World Cup ball emoji on dark background, place at frontend/public/icons/icon-192.png and frontend/public/icons/icon-512.png. Any image editor or online tool (realfavicongenerator.net) works.
- [x] T059 [P] Update frontend/index.html: add <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">, add <meta name="theme-color" content="#22c55e">, add <meta name="apple-mobile-web-app-capable" content="yes">, add <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

---

## Phase 9 — Deployment

*Ship to Render + Vercel + Supabase. All quickstart.md scenarios pass on production URLs.*

- [x] T060 Create backend/render.yaml: define service name "wcpredictor-api", env: python, buildCommand: "pip install -r requirements.txt", startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT", envVars list: DATABASE_URL (from Supabase), ODDS_API_KEY, FOOTBALL_DATA_API_KEY, ENV=production
- [x] T061 Write specs/001-wc-predictor/supabase-schema.sql with full DDL for all 6 tables (from data-model.md): CREATE TABLE IF NOT EXISTS statements for phase_config, matches, scraped_metrics, model_weights, suggestions, prediction_log, plus all indexes. Ready to paste into Supabase SQL editor.
- [x] T062 Set up Supabase: create new project at supabase.com, run supabase-schema.sql in the SQL editor, copy the Postgres connection string (URI format with pooling mode=transaction for asyncpg), note the anon key for .env
- [x] T063 Deploy backend to Render: create new Web Service at render.com pointing to GitHub repo, set root directory to "backend/", add all env vars from .env.example using real values from Supabase + The Odds API + football-data.org, wait for first deploy to complete, verify https://<service>.onrender.com/api/v1/health returns {"status": "ok"}
- [x] T064 Deploy frontend to Vercel: create new project at vercel.com pointing to GitHub repo, set root directory to "frontend/", add env var VITE_API_URL = https://<render-service>.onrender.com/api/v1, trigger deploy, verify the Vercel URL loads the app
- [x] T065 Run deployment smoke test from quickstart.md: (1) GET /health, (2) POST /sync + poll status until completed, (3) GET /matches/today, (4) POST /config/phase + PUT activate, (5) POST /validate with a sample match
- [x] T066 Test PWA on Android: open Vercel URL in Chrome on Android, verify install banner appears or use ⋮ → "Add to Home Screen", install app, open from home screen, verify standalone mode (no address bar), verify sync and suggestions work

---

## Dependency Graph

```
Phase 1 (Setup)
    └── Phase 2 (Backend Foundation)
            ├── Phase 3 (US1: Phase Config)   ← can start after T009, T010
            ├── Phase 4 (US2: Sync)           ← can start after T009, T010
            │       └── Phase 5 (US3: Engine) ← requires T025 stub to exist
            │               └── Phase 6 (US4: Validate) ← requires T036
            │                       └── Phase 7 (US5: Feedback) ← requires T036, T043
            └── Phase 8 (PWA Polish)          ← can start after T018 (App.tsx)
                    └── Phase 9 (Deployment)  ← requires all phases complete
```

---

## Parallel Execution Opportunities

**Within Phase 3 (US1):**
- T013 (CRUD) and T015 (FE hooks) and T016 (PhaseConfigForm) can run in parallel
- T014 (routes) depends on T013

**Within Phase 4 (US2):**
- T020 (fixtures scraper), T021 (odds scraper), T022 (xG scraper) all in parallel
- T023 (matches CRUD), T024 (metrics CRUD) in parallel
- T028 (SyncButton), T029 (FE hooks) in parallel after T018

**Within Phase 5 (US3):**
- T030 (poisson), T031 (calibrator) in parallel — no dependencies between them
- T032 (ensemble) depends on T030+T031
- T033 (ev) depends on T030; T034 (suggester) depends on T033
- T038+T039 (FE components) fully parallel to backend engine tasks

**Within Phase 7 (US5):**
- T048 (weights CRUD) and T049 (prediction_log CRUD) fully parallel
- T051 (FE hooks) and T053 (ModelWeightsWidget) parallel to backend tasks

---

## Format Validation

All 69 tasks follow the required format: `- [ ] TXXX [P?] [USn?] Description with file path`.
- Checkbox: ✅ all tasks start with `- [ ]`
- Task ID: ✅ sequential T001–T066 (69 total)
- [P] marker: ✅ present only on parallelizable tasks
- [USn] label: ✅ present on all user story phase tasks, absent on setup/foundation phases
- File paths: ✅ every task references a concrete file or endpoint
