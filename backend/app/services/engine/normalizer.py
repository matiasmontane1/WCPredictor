def remove_overround(odds_list: list[float]) -> list[float]:
    if not odds_list:
        raise ValueError("odds_list cannot be empty")
    if any(o <= 0 for o in odds_list):
        raise ValueError("All odds must be > 0")
    implied = [1.0 / o for o in odds_list]
    total = sum(implied)
    return [p / total for p in implied]
