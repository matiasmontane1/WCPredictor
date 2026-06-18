# Quickstart Validation Guide: WCPredictor

**Goal:** Confirm each major feature works end-to-end before considering the implementation complete.

---

## Prerequisites

### Accounts to create (in order)
1. [football-data.org](https://www.football-data.org/client/register) — free, email only → get `FOOTBALL_DATA_API_KEY`
2. [The Odds API](https://the-odds-api.com) — free, email only → get `ODDS_API_KEY`
3. [Supabase](https://supabase.com) → create project → get `SUPABASE_URL` and `SUPABASE_ANON_KEY`
4. [Render](https://render.com) — free, GitHub login
5. [Vercel](https://vercel.com) — free, GitHub login

### Local requirements
- Python 3.11+
- Node.js 18+
- Git

---

## Local Setup

```bash
# 1. Clone and set up environment files
cp backend/.env.example backend/.env
# Fill in: ODDS_API_KEY, FOOTBALL_DATA_API_KEY, SUPABASE_URL, SUPABASE_KEY
# For local dev, also set: ENV=development (uses SQLite instead of Supabase)

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API running at http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

---

## Validation Scenarios

### V1 — Phase configuration
**Goal:** Confirm phase scoring config saves and activates correctly.

1. Open `http://localhost:5173` → go to Settings
2. Create phase: name = "Grupos", winner points = 1, exact score points = 3
3. Click "Activar"
4. Verify: `GET http://localhost:8000/api/v1/config/phase` returns the phase with `"is_active": true`
5. Create a second phase: name = "Octavos", winner = 2, exact = 5 → Activate
6. Verify: "Grupos" now shows `"is_active": false`

**Expected:** Only one phase active at a time. EV calculations update immediately on activation.

---

### V2 — Daily sync
**Goal:** Confirm scraping pipeline runs without error and populates matches.

1. Click "Sincronizar Hoy" on the Dashboard
2. Observe the progress indicator (should not freeze the UI)
3. Wait for completion toast/notification
4. Verify: matches for today appear on the Dashboard with team names and kickoff times
5. Verify: `GET /api/v1/sync/status/{job_id}` shows `"status": "completed"`

**If no WC matches today:** The dashboard shows empty state with a clear message. Verify sync still completes without error (0 matches synced is valid).

**Fallback test:** Manually enter a fixture via the Settings > Fixtures page to confirm the dashboard populates.

---

### V3 — Suggestions with EV
**Goal:** Confirm the predictive engine generates Conservative + Aggressive picks.

Prerequisites: V1 and V2 complete, at least one match with synced metrics.

1. Click any match card on the Dashboard
2. On the Match Detail page, verify two suggestions appear:
   - **Conservadora**: labeled with score, probability %, EV value
   - **Arriesgada**: a different score with higher EV but lower probability
3. Go to Settings → change the exact score points from 3 to 10 → activate
4. Verify: the Arriesgada suggestion may change (EV is now recalculated with higher multiplier)

**Expected:** Changing phase config immediately re-renders suggestions without page refresh.

---

### V4 — Intuition Validator
**Goal:** Confirm real-time probability lookup for a user-entered score.

Prerequisites: V2 complete for the selected match.

1. On Match Detail page, click into the "¿Tenés un presentimiento?" input field
2. Type `3-1`
3. Verify: probability % and EV appear within 500ms (no submit button needed — reactive)
4. Clear the input → verify the validator resets cleanly
5. Type `0-0` → verify the numbers update

**Expected:** The validator calls `POST /api/v1/validate` on each debounced input change.

---

### V5 — Result entry and feedback loop
**Goal:** Confirm entering actual match results triggers weight updates.

Prerequisites: At least one match with synced metrics and suggestions.

1. Navigate to Results tab
2. Select a match and enter the actual final score (e.g., 2-1)
3. Click "Confirmar Resultado"
4. Verify: success toast appears with "Pesos actualizados"
5. Call `GET /api/v1/weights` → verify `matches_evaluated` incremented by 1
6. If 5+ results entered: verify `weight_xg` or `weight_market` changed from 0.5

**Expected:** Weights only shift after 5 matches evaluated (warmup period). Before that, they remain at 0.5/0.5.

---

### V6 — Mobile PWA install (production only)
**Goal:** Confirm the app is installable as a PWA on Android.

Prerequisites: App deployed to Vercel (HTTPS required for PWA).

1. Open the Vercel URL on an Android device with Chrome
2. Chrome shows "Add to Home Screen" install banner (or tap ⋮ menu → Install app)
3. Install the app → open from home screen
4. Verify: opens in standalone mode (no browser address bar)

**iOS:** Open in Safari → tap Share → "Add to Home Screen". Does not auto-prompt.

---

## Deployment Smoke Test

After deploying to Render + Vercel + Supabase:

```bash
# 1. Health check
curl https://<render-url>.onrender.com/api/v1/health
# Expected: {"status": "ok"}

# 2. Trigger sync
curl -X POST https://<render-url>.onrender.com/api/v1/sync
# Expected: {"status": "started", ...}

# 3. Today's matches
curl https://<render-url>.onrender.com/api/v1/matches/today
# Expected: JSON array (possibly empty if no matches today)
```

**Cold start note:** First request after 15min inactivity takes 30–60s. This is normal for Render free tier.
