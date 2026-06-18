-- WCPredictor — Supabase Postgres schema
-- Run this in the Supabase SQL editor after creating your project

CREATE TABLE IF NOT EXISTS phase_config (
    id SERIAL PRIMARY KEY,
    phase_name VARCHAR(50) NOT NULL,
    points_winner INTEGER NOT NULL CHECK (points_winner >= 0),
    points_exact_score INTEGER NOT NULL CHECK (points_exact_score >= 0),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE NOT NULL,
    match_date VARCHAR(10) NOT NULL,
    kickoff_time VARCHAR(30),
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    phase VARCHAR(50),
    status VARCHAR(20) DEFAULT 'scheduled',
    actual_home_goals INTEGER,
    actual_away_goals INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scraped_metrics (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) NOT NULL UNIQUE,
    scraped_at TIMESTAMP DEFAULT NOW(),
    xg_home REAL,
    xg_away REAL,
    odds_home_win_raw REAL,
    odds_draw_raw REAL,
    odds_away_win_raw REAL,
    implied_prob_home REAL,
    implied_prob_draw REAL,
    implied_prob_away REAL,
    lambda_xg_home REAL,
    lambda_xg_away REAL,
    lambda_market_home REAL,
    lambda_market_away REAL,
    scraper_source VARCHAR(50),
    odds_source VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS model_weights (
    id INTEGER PRIMARY KEY DEFAULT 1,
    weight_xg REAL DEFAULT 0.5,
    weight_market REAL DEFAULT 0.5,
    matches_evaluated INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP
);

-- Seed default weights row
INSERT INTO model_weights (id, weight_xg, weight_market, matches_evaluated)
VALUES (1, 0.5, 0.5, 0)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS suggestions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) NOT NULL,
    score_home INTEGER NOT NULL,
    score_away INTEGER NOT NULL,
    probability REAL NOT NULL,
    ev REAL NOT NULL,
    suggestion_type VARCHAR(20) NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prediction_log (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) NOT NULL UNIQUE,
    actual_home_goals INTEGER NOT NULL,
    actual_away_goals INTEGER NOT NULL,
    model_a_error REAL,
    model_b_error REAL,
    weight_xg_before REAL,
    weight_market_before REAL,
    weight_xg_after REAL,
    weight_market_after REAL,
    evaluated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_scraped_metrics_match ON scraped_metrics(match_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_match ON suggestions(match_id);
CREATE INDEX IF NOT EXISTS idx_prediction_log_match ON prediction_log(match_id);
