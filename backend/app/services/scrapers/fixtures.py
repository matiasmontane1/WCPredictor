import logging
from datetime import date

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"


async def get_today_matches() -> list[dict]:
    today = date.today().isoformat()
    url = f"{BASE_URL}/competitions/WC/matches"
    headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}
    params = {"dateFrom": today, "dateTo": today}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)

        if resp.status_code == 429:
            logger.warning("football-data.org rate limit hit — retry later")
            return []

        if resp.status_code == 404:
            logger.warning("WC competition not found on football-data.org (tournament may not have started)")
            return []

        resp.raise_for_status()
        data = resp.json()
        matches = []
        for m in data.get("matches", []):
            matches.append({
                "external_id": str(m["id"]),
                "match_date": today,
                "kickoff_time": m.get("utcDate"),
                "home_team": m["homeTeam"]["name"],
                "away_team": m["awayTeam"]["name"],
                "phase": m.get("stage"),
                "status": "finished" if m.get("status") == "FINISHED" else "scheduled",
            })
        return matches

    except httpx.HTTPError as e:
        logger.error(f"Fixtures scraper error: {e}")
        return []
