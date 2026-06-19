import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

CHILE_TZ = ZoneInfo("America/Santiago")

from app.crud import matches as matches_crud
from app.crud import metrics as metrics_crud
from app.crud import suggestions as suggestions_crud
from app.crud.phase_config import get_active_phase
from app.crud.weights import get_weights
from app.services.scrapers import fixtures as fixtures_scraper
from app.services.scrapers import odds as odds_scraper
from app.services.scrapers import xg as xg_scraper
from app.services.engine.calibrator import solve_lambdas
from app.services.engine.ensemble import ensemble_distribution
from app.services.engine.ev import calculate_ev
from app.services.engine.suggester import get_suggestions

logger = logging.getLogger(__name__)

# In-memory job status store
job_status: dict[str, dict] = {}

_executor = ThreadPoolExecutor(max_workers=2)


async def run_daily_sync(db: AsyncSession, job_id: str) -> None:
    job_status[job_id] = {
        "job_id": job_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "results": {},
    }

    fixtures_synced = 0
    odds_synced = 0
    xg_synced = 0
    xg_source = None
    errors = []

    try:
        # Step 1: Fetch fixtures (3-day window to correct UTC/Chile date mismatches)
        logger.info(f"[{job_id}] Fetching fixtures (yesterday/today/tomorrow)...")
        today_str = datetime.now(CHILE_TZ).date().isoformat()
        all_matches = await fixtures_scraper.get_today_matches()
        match_objects = []
        for m in all_matches:
            obj = await matches_crud.upsert_match(db, m)
            fixtures_synced += 1
            if obj.match_date == today_str:
                match_objects.append(obj)

        if not match_objects:
            logger.info(f"[{job_id}] No matches today.")
            job_status[job_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "results": {
                    "fixtures_synced": 0,
                    "odds_synced": 0,
                    "xg_synced": 0,
                    "errors": [],
                },
            })
            return

        # Step 2: Fetch odds
        logger.info(f"[{job_id}] Fetching odds...")
        team_pairs = [(m.home_team, m.away_team) for m in match_objects]
        odds_data = await odds_scraper.get_odds_for_matches(team_pairs)

        for match in match_objects:
            key = frozenset([match.home_team.lower().strip(), match.away_team.lower().strip()])
            if key in odds_data:
                od = odds_data[key]
                prob_h = od["implied_prob_home"]
                prob_d = od["implied_prob_draw"]
                prob_a = od["implied_prob_away"]
                lh_mkt, la_mkt = solve_lambdas(prob_h, prob_d, prob_a)

                await metrics_crud.upsert_metrics(db, match.id, {
                    "odds_home_win_raw": od["odds_home_win_raw"],
                    "odds_draw_raw": od["odds_draw_raw"],
                    "odds_away_win_raw": od["odds_away_win_raw"],
                    "implied_prob_home": prob_h,
                    "implied_prob_draw": prob_d,
                    "implied_prob_away": prob_a,
                    "lambda_market_home": lh_mkt,
                    "lambda_market_away": la_mkt,
                    "odds_source": "the_odds_api",
                })
                odds_synced += 1

        # Step 3: Fetch xG (sync scraper in thread executor)
        logger.info(f"[{job_id}] Fetching xG from FBref...")
        loop = asyncio.get_event_loop()
        xg_data = await loop.run_in_executor(_executor, xg_scraper.get_xg_today)

        if xg_data is not None:
            xg_source = "fbref"
            for match in match_objects:
                key = (match.home_team.lower().strip(), match.away_team.lower().strip())
                if key in xg_data:
                    xg_h, xg_a = xg_data[key]
                    await metrics_crud.upsert_metrics(db, match.id, {
                        "xg_home": xg_h,
                        "xg_away": xg_a,
                        "lambda_xg_home": xg_h,
                        "lambda_xg_away": xg_a,
                        "scraper_source": "fbref",
                    })
                    xg_synced += 1
        else:
            logger.warning(f"[{job_id}] FBref xG scraping failed — using market-calibrated lambdas only")
            for match in match_objects:
                metrics = await metrics_crud.get_metrics_for_match(db, match.id)
                if metrics and metrics.lambda_market_home:
                    await metrics_crud.upsert_metrics(db, match.id, {
                        "lambda_xg_home": metrics.lambda_market_home,
                        "lambda_xg_away": metrics.lambda_market_away,
                    })

        # Step 4: Run engine for each match
        logger.info(f"[{job_id}] Running predictive engine...")
        phase = await get_active_phase(db)
        weights = await get_weights(db)

        for match in match_objects:
            metrics = await metrics_crud.get_metrics_for_match(db, match.id)
            if metrics is None:
                continue
            if not (metrics.lambda_xg_home and metrics.lambda_market_home):
                continue

            prob_matrix = ensemble_distribution(metrics, weights)

            if phase:
                ev_matrix = calculate_ev(prob_matrix, phase)
            else:
                import numpy as np
                ev_matrix = prob_matrix.copy()

            result = get_suggestions(ev_matrix, prob_matrix)
            sugg_list = [result["conservative"], result["aggressive"]]
            await suggestions_crud.upsert_suggestions(db, match.id, sugg_list)

        job_status[job_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "results": {
                "fixtures_synced": fixtures_synced,
                "odds_synced": odds_synced,
                "xg_synced": xg_synced,
                "xg_source": xg_source,
                "errors": errors,
            },
        })
        logger.info(f"[{job_id}] Sync completed.")

    except Exception as e:
        logger.exception(f"[{job_id}] Sync failed: {e}")
        job_status[job_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "results": {"errors": [str(e)]},
        })
