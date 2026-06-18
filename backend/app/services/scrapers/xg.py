import logging
import time
from datetime import date

import requests
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FBREF_WC_URL = "https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures"
REQUEST_DELAY = 3.0


def _normalize_team(name: str) -> str:
    return name.lower().strip()


def get_xg_today() -> dict | None:
    today = date.today().isoformat()

    try:
        time.sleep(REQUEST_DELAY)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        resp = requests.get(FBREF_WC_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        tables = pd.read_html(resp.text)
        if not tables:
            logger.warning("FBref: no tables found")
            return None

        df = tables[0]
        # Normalize column names
        df.columns = [str(c).lower().strip() for c in df.columns]

        date_col = next((c for c in df.columns if "date" in c), None)
        home_col = next((c for c in df.columns if "home" in c and "xg" not in c), None)
        away_col = next((c for c in df.columns if "away" in c and "xg" not in c), None)
        xg_home_col = next((c for c in df.columns if "xg" in c and "home" in c.lower()), None)
        xg_away_col = next((c for c in df.columns if "xg" in c and "away" in c.lower()), None)

        # FBref sometimes has separate xg columns not labeled home/away
        if not xg_home_col:
            xg_cols = [c for c in df.columns if "xg" in c]
            if len(xg_cols) >= 2:
                xg_home_col, xg_away_col = xg_cols[0], xg_cols[1]

        if not all([date_col, home_col, away_col, xg_home_col, xg_away_col]):
            logger.warning(f"FBref: could not identify required columns. Found: {list(df.columns)}")
            return None

        today_df = df[df[date_col].astype(str) == today]
        if today_df.empty:
            logger.info(f"FBref: no matches found for {today}")
            return {}

        result = {}
        for _, row in today_df.iterrows():
            try:
                xg_h = float(row[xg_home_col])
                xg_a = float(row[xg_away_col])
                key = (_normalize_team(str(row[home_col])), _normalize_team(str(row[away_col])))
                result[key] = (xg_h, xg_a)
            except (ValueError, TypeError):
                continue

        return result

    except Exception as e:
        logger.error(f"FBref xG scraper error: {e}")
        return None
