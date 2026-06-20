from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Match
from app.models.schemas import ScorelineItem, TotalGoalsItem, WCStatsOut

router = APIRouter(prefix="/stats", tags=["stats"])

_EMPTY = WCStatsOut(
    total_matches=0,
    top_scorelines=[],
    margin_distribution={"draw": 0.0, "one_goal": 0.0, "two_goals": 0.0, "three_plus": 0.0},
    total_goals_distribution=[],
    btts_percentage=0.0,
)


@router.get("/wc", response_model=WCStatsOut)
async def get_wc_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Match).where(
            Match.status == "FINISHED",
            Match.actual_home_goals.is_not(None),
            Match.actual_away_goals.is_not(None),
        )
    )
    matches = result.scalars().all()

    total = len(matches)
    if total == 0:
        return _EMPTY

    scoreline_ctr: Counter = Counter()
    margin_ctr: Counter = Counter()
    goals_ctr: Counter = Counter()
    btts = 0

    for m in matches:
        h, a = m.actual_home_goals, m.actual_away_goals
        scoreline_ctr[f"{h}-{a}"] += 1
        diff = abs(h - a)
        if diff == 0:
            margin_ctr["draw"] += 1
        elif diff == 1:
            margin_ctr["one_goal"] += 1
        elif diff == 2:
            margin_ctr["two_goals"] += 1
        else:
            margin_ctr["three_plus"] += 1
        goals_ctr[h + a] += 1
        if h > 0 and a > 0:
            btts += 1

    top_scorelines = [
        ScorelineItem(score=s, count=c, pct=round(c / total * 100, 1))
        for s, c in scoreline_ctr.most_common(5)
    ]

    margin_distribution: dict[str, float] = {
        k: round(margin_ctr.get(k, 0) / total * 100, 1)
        for k in ("draw", "one_goal", "two_goals", "three_plus")
    }

    max_g = max(goals_ctr.keys())
    total_goals_distribution = [
        TotalGoalsItem(goals=g, count=goals_ctr.get(g, 0), pct=round(goals_ctr.get(g, 0) / total * 100, 1))
        for g in range(max_g + 1)
    ]

    return WCStatsOut(
        total_matches=total,
        top_scorelines=top_scorelines,
        margin_distribution=margin_distribution,
        total_goals_distribution=total_goals_distribution,
        btts_percentage=round(btts / total * 100, 1),
    )
