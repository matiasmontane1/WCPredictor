import logging
from collections import Counter
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
BASE_URL = "https://api.football-data.org/v4"


async def fetch_team_stats(team_ext_id: str, sample: int = 15) -> dict | None:
    url = f"{BASE_URL}/teams/{team_ext_id}/matches"
    headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}
    params = {"limit": sample, "status": "FINISHED"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)

        if resp.status_code == 429:
            logger.warning(f"Rate limit hit for team {team_ext_id}")
            return None
        if resp.status_code in (403, 404):
            return None
        resp.raise_for_status()

        data = resp.json()
        raw = data.get("matches", [])

        # Keep only finished with valid scores, sort newest first
        matches = []
        for m in raw:
            ft = m.get("score", {}).get("fullTime", {})
            if ft.get("home") is not None and ft.get("away") is not None:
                matches.append(m)
        matches.sort(key=lambda m: m.get("utcDate", ""), reverse=True)
        matches = matches[:sample]

        if not matches:
            return None

        tid = int(team_ext_id)
        goals_scored, goals_conceded, results, score_labels = [], [], [], []

        for m in matches:
            ft = m["score"]["fullTime"]
            is_home = m["homeTeam"]["id"] == tid
            gs = ft["home"] if is_home else ft["away"]
            gc = ft["away"] if is_home else ft["home"]
            goals_scored.append(gs)
            goals_conceded.append(gc)
            results.append("W" if gs > gc else ("D" if gs == gc else "L"))
            score_labels.append(f"{gs}-{gc}")

        most_common = Counter(score_labels).most_common(1)[0][0]
        n = len(matches)

        return {
            "sample_size": n,
            "avg_goals_scored": round(sum(goals_scored) / n, 2),
            "avg_goals_conceded": round(sum(goals_conceded) / n, 2),
            "clean_sheet_pct": round(sum(1 for gc in goals_conceded if gc == 0) / n, 3),
            "most_common_result": most_common,
            "form": ",".join(results[:5]),  # newest first
        }

    except Exception as e:
        logger.error(f"Team stats error for {team_ext_id}: {e}")
        return None
