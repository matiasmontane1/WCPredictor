import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"
CHILE_TZ = ZoneInfo("America/Santiago")
UTC_TZ = ZoneInfo("UTC")


def _today_chile() -> str:
    return datetime.now(CHILE_TZ).date().isoformat()


def _utc_str_to_chile_date(utc_str: str) -> str:
    """Convert '2026-06-19T01:00:00Z' to Chile local date."""
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        return dt.astimezone(CHILE_TZ).date().isoformat()
    except Exception:
        return _today_chile()


async def get_today_matches() -> list[dict]:
    today = _today_chile()
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
            logger.warning("WC competition not found on football-data.org")
            return []

        resp.raise_for_status()
        data = resp.json()
        matches = []
        for m in data.get("matches", []):
            utc_date = m.get("utcDate", "")
            chile_date = _utc_str_to_chile_date(utc_date) if utc_date else today
            api_status = m.get("status", "SCHEDULED")
            matches.append({
                "external_id": str(m["id"]),
                "match_date": chile_date,
                "kickoff_time": utc_date,
                "home_team": m["homeTeam"]["name"],
                "away_team": m["awayTeam"]["name"],
                "phase": m.get("stage"),
                "status": api_status,
            })
        return matches

    except httpx.HTTPError as e:
        logger.error(f"Fixtures scraper error: {e}")
        return []
