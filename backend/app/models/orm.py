from datetime import datetime
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, DateTime, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PhaseConfig(Base):
    __tablename__ = "phase_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase_name: Mapped[str] = mapped_column(String(50), nullable=False)
    points_winner: Mapped[int] = mapped_column(Integer, nullable=False)
    points_goal_diff: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    points_exact_score: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    match_date: Mapped[str] = mapped_column(String(10), nullable=False)
    kickoff_time: Mapped[str | None] = mapped_column(String(30), nullable=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    actual_home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    metrics: Mapped["ScrapedMetrics | None"] = relationship("ScrapedMetrics", back_populates="match", uselist=False)
    suggestions: Mapped[list["Suggestion"]] = relationship("Suggestion", back_populates="match")
    prediction_log: Mapped["PredictionLog | None"] = relationship("PredictionLog", back_populates="match", uselist=False)


class ScrapedMetrics(Base):
    __tablename__ = "scraped_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    xg_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    xg_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_home_win_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_draw_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_away_win_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    implied_prob_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    implied_prob_draw: Mapped[float | None] = mapped_column(Float, nullable=True)
    implied_prob_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    lambda_xg_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    lambda_xg_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    lambda_market_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    lambda_market_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    scraper_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    odds_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="metrics")


class ModelWeights(Base):
    __tablename__ = "model_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    weight_xg: Mapped[float] = mapped_column(Float, default=0.5)
    weight_market: Mapped[float] = mapped_column(Float, default=0.5)
    matches_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False)
    phase_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("phase_config.id"), nullable=True)
    score_home: Mapped[int] = mapped_column(Integer, nullable=False)
    score_away: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    ev: Mapped[float] = mapped_column(Float, nullable=False)
    suggestion_type: Mapped[str] = mapped_column(String(20), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match: Mapped["Match"] = relationship("Match", back_populates="suggestions")


class PredictionLog(Base):
    __tablename__ = "prediction_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)
    actual_home_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_away_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    prob_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_draw: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_a_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_b_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_xg_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_market_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_xg_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_market_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match: Mapped["Match"] = relationship("Match", back_populates="prediction_log")
