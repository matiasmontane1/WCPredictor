# API Contracts: WCPredictor Backend

**Base URL (local):** `http://localhost:8000/api/v1`
**Base URL (prod):** `https://<render-service>.onrender.com/api/v1`
**Format:** JSON, UTF-8
**Auth:** None (single-user, personal app)

---

## Health

### `GET /health`

Quick liveness check.

**Response 200:**
```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Matches

### `GET /matches/today`

Returns all matches scheduled for today (UTC) with their top suggestions embedded.

**Response 200:**
```json
[
  {
    "id": 1,
    "match_date": "2026-06-18",
    "kickoff_time": "2026-06-18T18:00:00Z",
    "home_team": "Argentina",
    "away_team": "Brazil",
    "phase": "GROUP_STAGE",
    "status": "scheduled",
    "suggestions": {
      "conservative": {
        "score": "1-0",
        "probability": 0.142,
        "ev": 1.85
      },
      "aggressive": {
        "score": "2-1",
        "probability": 0.091,
        "ev": 2.34
      }
    },
    "has_metrics": true
  }
]
```

**Empty state:** Returns `[]` if no matches today or sync not yet run.

---

### `GET /matches/{match_id}`

Returns a single match with the full probability distribution for all computed scores.

**Response 200:**
```json
{
  "id": 1,
  "home_team": "Argentina",
  "away_team": "Brazil",
  "phase": "GROUP_STAGE",
  "status": "scheduled",
  "kickoff_time": "2026-06-18T18:00:00Z",
  "metrics": {
    "xg_home": 1.42,
    "xg_away": 0.98,
    "implied_prob_home": 0.52,
    "implied_prob_draw": 0.28,
    "implied_prob_away": 0.20,
    "lambda_xg_home": 1.42,
    "lambda_xg_away": 0.98,
    "lambda_market_home": 1.38,
    "lambda_market_away": 1.01
  },
  "score_distribution": [
    { "score": "1-0", "probability": 0.142, "ev": 1.85, "rank": 1 },
    { "score": "1-1", "probability": 0.118, "ev": 0.94, "rank": 2 },
    { "score": "0-0", "probability": 0.091, "ev": 0.73, "rank": 3 }
  ],
  "suggestions": {
    "conservative": { "score": "1-0", "probability": 0.142, "ev": 1.85 },
    "aggressive": { "score": "2-1", "probability": 0.091, "ev": 2.34 }
  }
}
```

**Response 404:** `{ "detail": "Match not found" }`

---

### `POST /matches/{match_id}/result`

User submits the actual final score after a match ends. Triggers feedback loop weight update.

**Request body:**
```json
{
  "goals_home": 2,
  "goals_away": 1
}
```

**Response 200:**
```json
{
  "match_id": 1,
  "result_recorded": "2-1",
  "weights_updated": true,
  "new_weights": {
    "weight_xg": 0.52,
    "weight_market": 0.48
  },
  "matches_evaluated": 6
}
```

**Response 400:** `{ "detail": "Both goals_home and goals_away are required" }`
**Response 409:** `{ "detail": "Result already recorded for this match" }`

---

## Sync

### `POST /sync`

Triggers the daily data synchronization in the background. Returns immediately.

**Request body:** `{}` (empty)

**Response 202:**
```json
{
  "job_id": "sync_20260618_183042",
  "status": "started",
  "message": "Sync running in background. Check /sync/status/{job_id} for progress."
}
```

---

### `GET /sync/status/{job_id}`

Polls the status of a running or completed sync job.

**Response 200:**
```json
{
  "job_id": "sync_20260618_183042",
  "status": "completed",
  "started_at": "2026-06-18T18:30:42Z",
  "completed_at": "2026-06-18T18:31:15Z",
  "results": {
    "fixtures_synced": 4,
    "odds_synced": 4,
    "xg_synced": 2,
    "xg_source": "fbref",
    "errors": []
  }
}
```

**`status` values:** `started`, `running`, `completed`, `failed`

**Response 404:** `{ "detail": "Job not found" }`

---

## Phase Configuration

### `GET /config/phase`

Returns all configured phases with the active one flagged.

**Response 200:**
```json
[
  {
    "id": 1,
    "phase_name": "Grupos",
    "points_winner": 1,
    "points_exact_score": 3,
    "is_active": true
  },
  {
    "id": 2,
    "phase_name": "Octavos",
    "points_winner": 2,
    "points_exact_score": 5,
    "is_active": false
  }
]
```

---

### `POST /config/phase`

Creates a new phase configuration.

**Request body:**
```json
{
  "phase_name": "Cuartos de Final",
  "points_winner": 3,
  "points_exact_score": 7
}
```

**Response 201:** Returns the created PhaseConfig object.

**Validation errors 422:**
- `phase_name` required, max 50 chars
- `points_winner` ≥ 0
- `points_exact_score` ≥ 0

---

### `PUT /config/phase/{id}/activate`

Sets the given phase as active (deactivates all others). Also triggers suggestion regeneration for today's matches.

**Response 200:** Returns the now-active PhaseConfig object.

**Response 404:** `{ "detail": "Phase config not found" }`

---

### `DELETE /config/phase/{id}`

Deletes a phase. Cannot delete the currently active phase.

**Response 204:** No content.
**Response 400:** `{ "detail": "Cannot delete the active phase" }`

---

## Intuition Validator

### `POST /validate`

Calculates the probability and EV for a user-provided score, given the current active phase.

**Request body:**
```json
{
  "match_id": 1,
  "goals_home": 3,
  "goals_away": 1
}
```

**Response 200:**
```json
{
  "score": "3-1",
  "probability": 0.048,
  "ev": 0.62,
  "rank_among_computed": 8,
  "total_scores_computed": 36,
  "verdict": "below_average"
}
```

**`verdict` values:** `top_pick` (rank 1–2), `above_average` (rank 3–6), `below_average` (rank 7+)

**Response 400:** `{ "detail": "Match metrics not available. Run sync first." }`

---

## Model Weights

### `GET /weights`

Returns the current ensemble model weights and evaluation history.

**Response 200:**
```json
{
  "weight_xg": 0.52,
  "weight_market": 0.48,
  "matches_evaluated": 6,
  "last_updated_at": "2026-06-18T20:15:00Z"
}
```

---

## Error Format

All errors follow the same format:
```json
{
  "detail": "Human-readable error message"
}
```

HTTP status codes used: 200, 201, 202, 204, 400, 404, 409, 422, 500.
