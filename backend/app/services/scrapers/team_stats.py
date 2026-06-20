import logging
import re
import time
from collections import Counter

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FBREF_BASE = "https://fbref.com"
WC_SCHEDULE_URL = "https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures"
REQUEST_DELAY = 5.0

# football-data.org name → FBref name where they differ
_NAME_ALIASES: dict[str, str] = {
    "ivory coast": "côte d'ivoire",
    "korea republic": "south korea",
    "china pr": "china",
    "usa": "united states",
    "trinidad and tobago": "trinidad & tobago",
}

# In-process cache: normalized team name → squad matchlogs URL
_matchlog_url_cache: dict[str, str] = {}


def _norm(name: str) -> str:
    return name.lower().strip()


def _build_matchlog_url(squad_stats_url: str) -> str | None:
    m = re.search(r"/squads/([a-f0-9]+)/(.+)-Stats", squad_stats_url)
    if not m:
        return None
    squad_id, slug = m.group(1), m.group(2)
    return f"{FBREF_BASE}/en/squads/{squad_id}/all_comps/matchlogs/{slug}-Match-Logs-All-Competitions"


def _load_squad_urls() -> None:
    """Scrape WC schedule page once to build team → matchlog URL cache."""
    global _matchlog_url_cache
    try:
        time.sleep(REQUEST_DELAY)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = requests.get(WC_SCHEDULE_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        found = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/squads/" in href and "-Stats" in href:
                name = _norm(a.text.strip())
                if name:
                    ml_url = _build_matchlog_url(FBREF_BASE + href)
                    if ml_url:
                        _matchlog_url_cache[name] = ml_url
                        found += 1
        logger.info(f"FBref team stats: cached {found} squad matchlog URLs")
    except Exception as e:
        logger.error(f"FBref squad URL scrape error: {e}")


def _get_matchlog_url(team_name: str) -> str | None:
    if not _matchlog_url_cache:
        _load_squad_urls()

    name = _norm(team_name)
    url = _matchlog_url_cache.get(name)
    if not url:
        alias = _NAME_ALIASES.get(name)
        if alias:
            url = _matchlog_url_cache.get(alias)
    return url


def get_team_stats(team_name: str, sample: int = 15) -> dict | None:
    """Sync function — run in thread executor. Returns stats dict or None."""
    matchlog_url = _get_matchlog_url(team_name)
    if not matchlog_url:
        logger.warning(f"FBref: no matchlog URL for '{team_name}'")
        return None

    try:
        time.sleep(REQUEST_DELAY)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = requests.get(matchlog_url, headers=headers, timeout=15)
        resp.raise_for_status()

        tables = pd.read_html(resp.text)
        if not tables:
            logger.warning(f"FBref: no tables on matchlog page for {team_name}")
            return None

        df = tables[0]

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [" ".join(str(c) for c in col).strip() for col in df.columns]
        df.columns = [str(c).lower().strip() for c in df.columns]

        result_col = next((c for c in df.columns if c in ("result", "res")), None)
        gf_col = next((c for c in df.columns if c in ("gf", "goals for", "f")), None)
        ga_col = next((c for c in df.columns if c in ("ga", "goals against", "a")), None)
        date_col = next((c for c in df.columns if "date" in c), None)

        if not all([result_col, gf_col, ga_col]):
            logger.warning(f"FBref: missing columns for {team_name}. Found: {list(df.columns)}")
            return None

        # Keep only rows with valid W/D/L results
        df = df[df[result_col].isin(["W", "D", "L"])].copy()

        if date_col:
            df = df.sort_values(date_col, ascending=False)

        df = df.head(sample)

        if df.empty:
            return None

        goals_scored, goals_conceded, results, score_labels = [], [], [], []
        for _, row in df.iterrows():
            try:
                gf = int(float(str(row[gf_col])))
                ga = int(float(str(row[ga_col])))
                res = str(row[result_col]).strip()
                goals_scored.append(gf)
                goals_conceded.append(ga)
                results.append(res)
                score_labels.append(f"{gf}-{ga}")
            except (ValueError, TypeError):
                continue

        if not goals_scored:
            return None

        n = len(goals_scored)
        return {
            "sample_size": n,
            "avg_goals_scored": round(sum(goals_scored) / n, 2),
            "avg_goals_conceded": round(sum(goals_conceded) / n, 2),
            "clean_sheet_pct": round(sum(1 for ga in goals_conceded if ga == 0) / n, 3),
            "most_common_result": Counter(score_labels).most_common(1)[0][0],
            "form": ",".join(results[:5]),
        }

    except Exception as e:
        logger.error(f"FBref matchlog error for {team_name}: {e}")
        return None
