import logging
import time
import unicodedata

import requests
from bs4 import BeautifulSoup

from app.services.engine.calibrator import solve_lambdas

logger = logging.getLogger(__name__)

ELO_URL = "https://eloratings.net/"
REQUEST_DELAY = 2.0
DRAW_RATE = 0.25  # WC historical group-stage draw rate

# Team name aliases: normalize API names → eloratings.net names
_ALIASES: dict[str, str] = {
    "usa": "united states",
    "us": "united states",
    "czechia": "czech republic",
    "south korea": "korea republic",
    "korea dpr": "north korea",
    "ivory coast": "cote d'ivoire",
    "côte d'ivoire": "cote d'ivoire",
    "bosnia-herzegovina": "bosnia-herzegovina",
    "trinidad & tobago": "trinidad and tobago",
    "cape verde islands": "cape verde",
}

# Approximate fallback ratings for WC 2026 teams (used when scraping fails)
_FALLBACK: dict[str, float] = {
    "france": 2100,
    "argentina": 2080,
    "brazil": 2050,
    "england": 2020,
    "spain": 2010,
    "germany": 1990,
    "portugal": 1940,
    "netherlands": 1930,
    "belgium": 1880,
    "italy": 1870,
    "croatia": 1800,
    "uruguay": 1820,
    "colombia": 1810,
    "united states": 1800,
    "mexico": 1790,
    "morocco": 1780,
    "senegal": 1740,
    "japan": 1750,
    "denmark": 1760,
    "switzerland": 1740,
    "austria": 1720,
    "turkey": 1700,
    "ukraine": 1700,
    "poland": 1700,
    "sweden": 1760,
    "serbia": 1730,
    "czech republic": 1700,
    "slovakia": 1650,
    "australia": 1700,
    "korea republic": 1680,
    "south africa": 1520,
    "ecuador": 1660,
    "canada": 1650,
    "chile": 1700,
    "peru": 1640,
    "cameroon": 1600,
    "nigeria": 1600,
    "ghana": 1580,
    "egypt": 1620,
    "algeria": 1600,
    "tunisia": 1600,
    "ivory coast": 1640,
    "cote d'ivoire": 1640,
    "mali": 1560,
    "saudi arabia": 1580,
    "iran": 1600,
    "iraq": 1580,
    "japan": 1750,
    "uzbekistan": 1540,
    "qatar": 1500,
    "costa rica": 1580,
    "panama": 1540,
    "honduras": 1520,
    "paraguay": 1580,
    "bolivia": 1500,
    "venezuela": 1540,
    "new zealand": 1480,
    "bosnia-herzegovina": 1620,
    "wales": 1700,
    "scotland": 1660,
    "ireland": 1620,
    "slovenia": 1640,
    "finland": 1640,
    "norway": 1700,
    "romania": 1620,
    "hungary": 1650,
    "albania": 1580,
    "greece": 1640,
    "israel": 1620,
    "georgia": 1620,
}


def _normalize(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = n.lower().strip()
    return _ALIASES.get(n, n)


def _fetch_live_ratings() -> dict[str, float]:
    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(
            ELO_URL,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
            timeout=10,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        ratings: dict[str, float] = {}
        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            try:
                name = _normalize(cols[1].get_text(strip=True))
                rating = float(cols[2].get_text(strip=True).replace(",", ""))
                if name and rating > 500:
                    ratings[name] = rating
            except (ValueError, IndexError):
                continue

        if len(ratings) >= 20:
            logger.info(f"Elo: fetched {len(ratings)} ratings from eloratings.net")
            return ratings

        logger.warning(f"Elo: only parsed {len(ratings)} teams — falling back to hardcoded")
        return {}

    except Exception as e:
        logger.warning(f"Elo: scraping failed ({e}), using hardcoded fallback")
        return {}


def _lookup(team: str, live: dict[str, float]) -> float:
    key = _normalize(team)
    if key in live:
        return live[key]
    if key in _FALLBACK:
        return _FALLBACK[key]
    # Partial match in fallback
    for k, v in _FALLBACK.items():
        if k in key or key in k:
            logger.debug(f"Elo: partial match '{team}' → '{k}'")
            return v
    logger.warning(f"Elo: no rating for '{team}', using default 1700")
    return 1700.0


def get_elo_lambdas(home_team: str, away_team: str) -> tuple[float, float] | None:
    """
    Returns (lambda_home, lambda_away) derived from Elo ratings.
    Uses WC neutral-venue formula (no home advantage adjustment).
    """
    live = _fetch_live_ratings()
    elo_h = _lookup(home_team, live)
    elo_a = _lookup(away_team, live)

    # Standard Elo win expectancy (neutral venue)
    E_home = 1.0 / (1.0 + 10.0 ** ((elo_a - elo_h) / 400.0))

    # Map to 1X2 with fixed draw rate
    p_home = E_home * (1.0 - DRAW_RATE)
    p_draw = DRAW_RATE
    p_away = (1.0 - E_home) * (1.0 - DRAW_RATE)

    try:
        lh, la = solve_lambdas(p_home, p_draw, p_away)
        logger.info(
            f"Elo: {home_team}({elo_h:.0f}) vs {away_team}({elo_a:.0f}) "
            f"→ p=[{p_home:.2f},{p_draw:.2f},{p_away:.2f}] λ=[{lh:.2f},{la:.2f}]"
        )
        return lh, la
    except Exception as e:
        logger.error(f"Elo: solve_lambdas failed for {home_team} vs {away_team}: {e}")
        return None
