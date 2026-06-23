from typing import Optional
from pydantic import BaseModel, field_validator


# --- Phase Config ---

class PhaseConfigCreate(BaseModel):
    phase_name: str
    points_winner: int
    points_goal_diff: int = 0
    points_exact_score: int

    @field_validator("phase_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("phase_name cannot be empty")
        if len(v) > 50:
            raise ValueError("phase_name max 50 chars")
        return v.strip()

    @field_validator("points_winner", "points_goal_diff", "points_exact_score")
    @classmethod
    def points_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Points must be >= 0")
        return v


class PhaseConfigOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    phase_name: str
    points_winner: int
    points_goal_diff: int = 0
    points_exact_score: int
    is_active: bool
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def format_datetime(cls, v):
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return str(v)


# --- Match ---

class ScoreDistributionItem(BaseModel):
    score: str
    probability: float
    ev: float
    rank: int


class SuggestionOut(BaseModel):
    score: str
    probability: float
    ev: float
    phase_id: Optional[int] = None


class SuggestionPair(BaseModel):
    conservative: Optional[SuggestionOut] = None
    aggressive: Optional[SuggestionOut] = None


class MetricsOut(BaseModel):
    model_config = {"from_attributes": True}
    xg_home: Optional[float] = None
    xg_away: Optional[float] = None
    implied_prob_home: Optional[float] = None
    implied_prob_draw: Optional[float] = None
    implied_prob_away: Optional[float] = None
    lambda_xg_home: Optional[float] = None
    lambda_xg_away: Optional[float] = None
    lambda_market_home: Optional[float] = None
    lambda_market_away: Optional[float] = None


class MatchSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    match_date: str
    kickoff_time: Optional[str] = None
    home_team: str
    away_team: str
    phase: Optional[str] = None
    status: str
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    suggestions: Optional[SuggestionPair] = None
    has_metrics: bool = False


class MatchDetailOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    home_team: str
    away_team: str
    phase: Optional[str] = None
    status: str
    kickoff_time: Optional[str] = None
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    metrics: Optional[MetricsOut] = None
    score_distribution: list[ScoreDistributionItem] = []
    suggestions: Optional[SuggestionPair] = None
    prob_home_win: Optional[float] = None
    prob_draw: Optional[float] = None
    prob_away_win: Optional[float] = None


# --- Sync ---

class SyncResponse(BaseModel):
    job_id: str
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    job_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: Optional[dict] = None


# --- Results ---

class ResultIn(BaseModel):
    goals_home: int
    goals_away: int

    @field_validator("goals_home", "goals_away")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Goals must be >= 0")
        return v


class ResultOut(BaseModel):
    match_id: int
    result_recorded: str
    weights_updated: bool
    new_weights: dict
    matches_evaluated: int


# --- Validate ---

class ValidateIn(BaseModel):
    match_id: int
    goals_home: int
    goals_away: int

    @field_validator("goals_home", "goals_away")
    @classmethod
    def valid_goals(cls, v: int) -> int:
        if v < 0 or v > 9:
            raise ValueError("Goals must be 0-9")
        return v


class ValidateOut(BaseModel):
    score: str
    probability: float
    ev: float
    rank_among_computed: int
    total_scores_computed: int
    verdict: str


# --- Weights ---

class ModelWeightsOut(BaseModel):
    model_config = {"from_attributes": True}
    weight_xg: float
    weight_market: float
    matches_evaluated: int
    last_updated_at: Optional[str] = None

    @field_validator("last_updated_at", mode="before")
    @classmethod
    def format_datetime(cls, v):
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return str(v)


# --- WC Stats ---

class ScorelineItem(BaseModel):
    score: str
    count: int
    pct: float


class TotalGoalsItem(BaseModel):
    goals: int
    count: int
    pct: float


class LastMatchItem(BaseModel):
    home_team: str
    away_team: str
    score: str
    kickoff_time: Optional[str] = None


class WCStatsOut(BaseModel):
    total_matches: int
    top_scorelines: list[ScorelineItem]
    margin_distribution: dict[str, float]
    total_goals_distribution: list[TotalGoalsItem]
    btts_percentage: float
    last_match: Optional[LastMatchItem] = None


# --- Feedback Logs ---

class FeedbackLogItem(BaseModel):
    match_id: int
    actual_score: str
    brier_xg: Optional[float] = None
    brier_market: Optional[float] = None
    weight_xg_before: Optional[float] = None
    weight_market_before: Optional[float] = None
    weight_xg_after: Optional[float] = None
    weight_market_after: Optional[float] = None
    evaluated_at: Optional[str] = None


class FeedbackLogsOut(BaseModel):
    total_logs: int
    logs: list[FeedbackLogItem]


# --- Health ---

class HealthOut(BaseModel):
    status: str
    version: str
