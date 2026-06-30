import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"
CHILE_TZ = ZoneInfo("America/Santiago")


def _today_chile() -> str:
    return datetime.now(CHILE_TZ).date().isoformat()


def _utc_str_to_chile_date(utc_str: str) -> str:
    """Convert '2026-06-19T01:00:00Z' to Chile local date.

    Matches kicking off between 00:00 and 01:59 Chile time are assigned
    to the previous day so suggestions are visible before midnight.
    """
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        chile_dt = dt.astimezone(CHILE_TZ)
        if chile_dt.hour < 2:
            return (chile_dt.date() - timedelta(days=1)).isoformat()
        return chile_dt.date().isoformat()
    except Exception:
        return _today_chile()


async def get_today_matches() -> list[dict]:
    """Fetch matches for yesterday+today+tomorrow UTC range.

    Chile is UTC-3 in winter, so a match at 00:30 UTC June 19 is
    21:30 Chile June 18. Querying only today Chile date would miss it.
    We fetch a 3-day UTC window and let _utc_str_to_chile_date assign
    the correct Chile date to each match.
    """
    today_chile = datetime.now(CHILE_TZ).date()
    date_from = (today_chile - timedelta(days=1)).isoformat()
    date_to = (today_chile + timedelta(days=1)).isoformat()
    today_str = today_chile.isoformat()

    url = f"{BASE_URL}/competitions/WC/matches"
    headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}
    params = {"dateFrom": date_from, "dateTo": date_to}

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
            home = m.get("homeTeam", {}).get("name")
            away = m.get("awayTeam", {}).get("name")
            if not home or not away:
                continue  # knockout placeholder — teams not yet determined
            utc_date = m.get("utcDate", "")
            chile_date = _utc_str_to_chile_date(utc_date) if utc_date else today_str
            api_status = m.get("status", "SCHEDULED")
            entry = {
                "external_id": str(m["id"]),
                "match_date": chile_date,
                "kickoff_time": utc_date,
                "home_team": home,
                "away_team": away,
                "phase": m.get("stage"),
                "status": api_status,
            }
            if api_status == "FINISHED":
                score_obj = m.get("score", {})
                ft = _regular_time_score(score_obj)
                if ft.get("home") is not None and ft.get("away") is not None:
                    entry["score_home"] = ft["home"]
                    entry["score_away"] = ft["away"]
            matches.append(entry)
        return matches

    except httpx.HTTPError as e:
        logger.error(f"Fixtures scraper error: {e}")
        return []


def _regular_time_score(score_obj: dict) -> dict:
    """Return the 90-minute score, ignoring extra time and penalty goals.

    football-data.org v4 uses fullTime for the cumulative score at the end of
    play (including ET goals). regularTime holds only the 90-minute result for
    matches that went beyond regular time.
    """
    duration = score_obj.get("duration", "REGULAR")
    if duration in ("EXTRA_TIME", "PENALTY_SHOOTOUT"):
        reg = score_obj.get("regularTime") or {}
        if reg.get("home") is not None and reg.get("away") is not None:
            return reg
    return score_obj.get("fullTime") or {}


async def get_all_wc_matches() -> list[dict]:
    """Fetch the full WC 2026 schedule (all matchdays) for DB completeness."""
    today = _today_chile()
    url = f"{BASE_URL}/competitions/WC/matches"
    headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 429:
            logger.warning("football-data.org rate limit hit on full WC fetch")
            return []
        if resp.status_code == 404:
            return []

        resp.raise_for_status()
        data = resp.json()
        matches = []
        for m in data.get("matches", []):
            home = m.get("homeTeam", {}).get("name")
            away = m.get("awayTeam", {}).get("name")
            if not home or not away:
                continue  # knockout placeholder — teams not yet determined
            utc_date = m.get("utcDate", "")
            chile_date = _utc_str_to_chile_date(utc_date) if utc_date else today
            api_status = m.get("status", "SCHEDULED")
            entry = {
                "external_id": str(m["id"]),
                "match_date": chile_date,
                "kickoff_time": utc_date,
                "home_team": home,
                "away_team": away,
                "phase": m.get("stage"),
                "status": api_status,
            }
            if api_status == "FINISHED":
                score_obj = m.get("score", {})
                ft = _regular_time_score(score_obj)
                if ft.get("home") is not None and ft.get("away") is not None:
                    entry["score_home"] = ft["home"]
                    entry["score_away"] = ft["away"]
            matches.append(entry)
        return matches

    except httpx.HTTPError as e:
        logger.error(f"Full WC fixtures scraper error: {e}")
        return []
