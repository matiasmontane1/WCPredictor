# Data Model: WCPredictor

**Feature**: 001-wc-predictor
**Database**: Supabase Postgres (prod) / SQLite (local dev)

---

## Entity Relationship Overview

```
PhaseConfig ─────────────────────────────────┐
                                             │ (active config drives EV calc)
Match ──────────── ScrapedMetrics            │
  │                                          │
  ├──── Suggestion (conservative/aggressive) │
  │                                          │
  └──── PredictionLog (for feedback loop) ───┘

ModelWeights (singleton row — one active state)
```

---

## Tables

### `phase_config`

Stores user-defined scoring rules per tournament phase. Only one row can be `is_active = true` at a time.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | SERIAL | PK | Auto-increment |
| phase_name | VARCHAR(50) | NOT NULL | e.g. "Grupos", "Octavos", "Final" |
| points_winner | INTEGER | NOT NULL, ≥ 0 | Points for predicting the correct winner (or draw) |
| points_exact_score | INTEGER | NOT NULL, ≥ 0 | Additional points for predicting the exact score |
| is_active | BOOLEAN | DEFAULT false | Only one row true at a time (enforced in app logic) |
| created_at | TIMESTAMP | DEFAULT now() | |

**State transition:** When the user activates a new phase, the app sets all rows `is_active = false` then sets the selected row to `true`.

---

### `matches`

One row per tournament fixture. Populated by the football-data.org scraper on sync.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | SERIAL | PK | |
| external_id | VARCHAR(50) | UNIQUE, NOT NULL | ID from football-data.org |
| match_date | DATE | NOT NULL | Date of the match (UTC) |
| kickoff_time | TIMESTAMP | | Full kickoff datetime (UTC) |
| home_team | VARCHAR(100) | NOT NULL | |
| away_team | VARCHAR(100) | NOT NULL | |
| phase | VARCHAR(50) | | e.g. "GROUP_STAGE", "ROUND_OF_16" |
| status | VARCHAR(20) | DEFAULT 'scheduled' | scheduled / finished |
| actual_home_goals | INTEGER | NULLABLE | Entered manually by user post-match |
| actual_away_goals | INTEGER | NULLABLE | Entered manually by user post-match |
| created_at | TIMESTAMP | DEFAULT now() | |

**Validation:** `actual_home_goals` and `actual_away_goals` must both be set together (atomic update).

---

### `scraped_metrics`

Raw and normalized data from external sources for a given match. One row per sync run per match.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | SERIAL | PK | |
| match_id | INTEGER | FK → matches.id, NOT NULL | |
| scraped_at | TIMESTAMP | DEFAULT now() | |
| xg_home | REAL | NULLABLE | xG from FBref (may be null if not yet played) |
| xg_away | REAL | NULLABLE | |
| odds_home_win_raw | REAL | NULLABLE | Raw decimal odds (e.g. 2.10) |
| odds_draw_raw | REAL | NULLABLE | |
| odds_away_win_raw | REAL | NULLABLE | |
| implied_prob_home | REAL | NULLABLE | Normalized (overround removed), sums to 1.0 |
| implied_prob_draw | REAL | NULLABLE | |
| implied_prob_away | REAL | NULLABLE | |
| lambda_xg_home | REAL | NULLABLE | λ for Model A (directly from xG) |
| lambda_xg_away | REAL | NULLABLE | |
| lambda_market_home | REAL | NULLABLE | λ for Model B (solved from 1X2 probs) |
| lambda_market_away | REAL | NULLABLE | |
| scraper_source | VARCHAR(50) | | "fbref", "sofascore_fallback" |
| odds_source | VARCHAR(50) | | "the_odds_api" |

---

### `model_weights`

Singleton table (always exactly one row). Tracks current ensemble weights.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PK, DEFAULT 1 | Always 1 |
| weight_xg | REAL | DEFAULT 0.5 | Weight for Model A (xG-Poisson) |
| weight_market | REAL | DEFAULT 0.5 | Weight for Model B (Market-Poisson). weight_xg + weight_market = 1.0 |
| matches_evaluated | INTEGER | DEFAULT 0 | Total matches used in feedback loop |
| last_updated_at | TIMESTAMP | | |

**Invariant:** `weight_xg + weight_market = 1.0` always. Enforced before each write.

---

### `suggestions`

Computed suggestions per match, regenerated on each sync or phase config change.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | SERIAL | PK | |
| match_id | INTEGER | FK → matches.id, NOT NULL | |
| score_home | INTEGER | NOT NULL, 0–9 | |
| score_away | INTEGER | NOT NULL, 0–9 | |
| probability | REAL | NOT NULL | P_final for this exact score |
| ev | REAL | NOT NULL | Expected Value given active phase config |
| suggestion_type | VARCHAR(20) | NOT NULL | 'conservative' or 'aggressive' |
| generated_at | TIMESTAMP | DEFAULT now() | |

**Selection logic:**
- `conservative`: row with highest `probability` among all computed scores
- `aggressive`: row with highest `ev` that is NOT the conservative pick (finds value)

---

### `prediction_log`

Audit log for the feedback loop. One row per match once results are entered.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | SERIAL | PK | |
| match_id | INTEGER | FK → matches.id, UNIQUE | One evaluation per match |
| actual_home_goals | INTEGER | NOT NULL | |
| actual_away_goals | INTEGER | NOT NULL | |
| model_a_error | REAL | | Brier score component for Model A |
| model_b_error | REAL | | Brier score component for Model B |
| weight_xg_before | REAL | | Snapshot of weight before update |
| weight_market_before | REAL | | |
| weight_xg_after | REAL | | |
| weight_market_after | REAL | | |
| evaluated_at | TIMESTAMP | DEFAULT now() | |

**Feedback algorithm:** After N matches (configurable, default 5), compute cumulative Brier scores for each model. Update weights proportionally: `W_a = (1 - BrierScore_a) / ((1 - BS_a) + (1 - BS_b))`.

---

## Indexes

```sql
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_scraped_metrics_match ON scraped_metrics(match_id);
CREATE INDEX idx_suggestions_match ON suggestions(match_id);
CREATE INDEX idx_prediction_log_match ON prediction_log(match_id);
```

---

## Validation Rules

| Rule | Entity | Detail |
|---|---|---|
| Only one active phase | phase_config | App-level: deactivate all before activating new |
| Probability sums to 1.0 | scraped_metrics | Enforced in overround-removal function |
| Weights sum to 1.0 | model_weights | Enforced before every write |
| Score range 0–9 | suggestions | Scores beyond 9 are computationally zeroed |
| Actual goals non-negative | matches | Validated at API boundary |
| Results only for finished | matches | API rejects result input if status ≠ 'finished' |
