import logging

import httpx

from app.core.config import settings
from app.services.engine.normalizer import remove_overround

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "soccer_fifa_world_cup"


_ALIASES: dict[str, str] = {
    # Czechia (FD) ↔ Czech Republic (Odds)
    "czechia": "czech republic",
    "czech republic": "czechia",
    # Bosnia (FD uses dash, Odds uses ampersand)
    "bosnia-herzegovina": "bosnia & herzegovina",
    "bosnia & herzegovina": "bosnia-herzegovina",
    "bosnia and herzegovina": "bosnia-herzegovina",
    # Cape Verde (FD uses "Islands", Odds doesn't)
    "cape verde islands": "cape verde",
    "cape verde": "cape verde islands",
    # Congo (FD = "Congo DR", Odds = "DR Congo")
    "congo dr": "dr congo",
    "dr congo": "congo dr",
    "democratic republic of congo": "dr congo",
    # USA (FD = "United States", Odds = "USA")
    "united states": "usa",
    "usa": "united states",
    # Other common variants
    "côte d'ivoire": "ivory coast",
    "ivory coast": "côte d'ivoire",
    "korea republic": "south korea",
    "south korea": "korea republic",
    "republic of ireland": "ireland",
}


def _normalize_team(name: str) -> str:
    return name.lower().strip()


def _team_keys(name: str) -> set[str]:
    n = _normalize_team(name)
    keys = {n}
    if n in _ALIASES:
        keys.add(_ALIASES[n])
    return keys


async def get_odds_for_matches(team_names: list[tuple[str, str]]) -> dict:
    if not settings.ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set — skipping odds scraping")
        return {}

    url = f"{BASE_URL}/sports/{SPORT}/odds"
    params = {
        "apiKey": settings.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)

        remaining = resp.headers.get("x-requests-remaining", "?")
        logger.info(f"Odds API requests remaining: {remaining}")
        if int(remaining) < 50 if remaining.isdigit() else False:
            logger.warning(f"Odds API quota low: {remaining} requests remaining")

        if resp.status_code in (402, 422, 429):
            logger.error(f"Odds API quota/limit issue: {resp.status_code}")
            return {}

        resp.raise_for_status()
        events = resp.json()

        result = {}
        for event in events:
            home = event.get("home_team", "")
            away = event.get("away_team", "")

            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            all_home, all_draw, all_away = [], [], []
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] != "h2h":
                        continue
                    outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                    if home in outcomes and away in outcomes and "Draw" in outcomes:
                        all_home.append(outcomes[home])
                        all_draw.append(outcomes["Draw"])
                        all_away.append(outcomes[away])

            if not all_home:
                continue

            avg_odds = [
                sum(all_home) / len(all_home),
                sum(all_draw) / len(all_draw),
                sum(all_away) / len(all_away),
            ]
            probs = remove_overround(avg_odds)

            home_keys = _team_keys(home)
            away_keys = _team_keys(away)
            for hk in home_keys:
                for ak in away_keys:
                    result[frozenset([hk, ak])] = {
                "odds_home_win_raw": avg_odds[0],
                "odds_draw_raw": avg_odds[1],
                "odds_away_win_raw": avg_odds[2],
                "implied_prob_home": probs[0],
                "implied_prob_draw": probs[1],
                "implied_prob_away": probs[2],
                "odds_source": "the_odds_api",
                        "home_team": home,
                        "away_team": away,
                    }

        return result

    except httpx.HTTPError as e:
        logger.error(f"Odds scraper error: {e}")
        return {}
