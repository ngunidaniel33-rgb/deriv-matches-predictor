from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev


@dataclass
class MatchAnalysisSummary:
    sample_size: int
    likely_match_digit: int | None
    likely_match_probability: float
    differ_probability: float
    average_move: float
    volatility: float
    up_ratio: float
    down_ratio: float
    current_streak: int
    longest_streak: int
    recommendation: str
    signal_strength: float
    last_digit_distribution: dict[int, int]


def load_tick_history(csv_path: str | Path) -> list[float]:
    """Load recent tick or price data from a CSV file.

    Supported inputs include a single numeric column or a CSV with common Deriv field names such as
    tick, price, value, close, last, last_price, and deriv_tick.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Tick history not found: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        return []

    if len(rows[0]) == 1:
        values: list[float] = []
        for row in rows:
            if not row or not row[0].strip():
                continue
            raw_value = row[0].strip()
            if raw_value.lower() in {"tick", "price", "value", "close", "last", "last_price", "deriv_tick"}:
                continue
            try:
                values.append(float(raw_value))
            except ValueError:
                continue
        return values

    header = [cell.strip().lower() for cell in rows[0]]
    key = next(
        (
            name
            for name in ("tick", "price", "value", "close", "last", "last_price", "deriv_tick")
            if name in header
        ),
        None,
    )
    if key is None:
        raise ValueError(
            "CSV must contain a tick/price column such as tick, price, value, or close."
        )

    index = header.index(key)
    values: list[float] = []
    for row in rows[1:]:
        if len(row) <= index:
            continue
        raw_value = row[index].strip()
        if raw_value:
            try:
                values.append(float(raw_value))
            except ValueError:
                continue
    return values


def _calculate_streaks(changes: list[float]) -> tuple[int, int]:
    if not changes:
        return 0, 0

    current = 1
    longest = 1
    last_sign = 1 if changes[0] >= 0 else -1

    for change in changes[1:]:
        sign = 1 if change >= 0 else -1
        if sign == last_sign:
            current += 1
        else:
            current = 1
            last_sign = sign
        longest = max(longest, current)

    return current, longest


def analyze_ticks(values: list[float], window: int = 20, target_digit: int | None = None) -> MatchAnalysisSummary:
    """Evaluate a sequence of tick values and summarize the recent market bias."""
    if not values:
        raise ValueError("No tick values provided for analysis.")

    recent_values = values[-window:]
    last_digit_distribution = Counter(int(round(value)) % 10 for value in recent_values)
    total_recent = sum(last_digit_distribution.values())

    if total_recent == 0:
        likely_digit = None
        likely_probability = 0.0
    else:
        likely_digit, count = max(last_digit_distribution.items(), key=lambda item: (item[1], -item[0]))
        likely_probability = count / total_recent
    differ_probability = 1.0 - likely_probability

    if len(values) > 1:
        changes = [current - previous for previous, current in zip(values, values[1:])]
        average_move = abs(mean(changes)) if changes else 0.0
        volatility = pstdev(changes) if len(changes) > 1 else 0.0
        up_count = sum(1 for change in changes if change > 0)
        down_count = sum(1 for change in changes if change < 0)
        flat_count = len(changes) - up_count - down_count
        up_ratio = up_count / len(changes)
        down_ratio = down_count / len(changes)
        current_streak, longest_streak = _calculate_streaks(changes)
    else:
        changes = []
        average_move = 0.0
        volatility = 0.0
        up_count = 0
        down_count = 0
        flat_count = 0
        up_ratio = 0.0
        down_ratio = 0.0
        current_streak = 0
        longest_streak = 0

    if target_digit is not None:
        target_probability = last_digit_distribution.get(target_digit % 10, 0) / total_recent if total_recent else 0.0
        likely_digit = target_digit % 10
        likely_probability = target_probability
        differ_probability = 1.0 - target_probability

    signal_strength = max(0.0, (likely_probability - 0.10) * 100 + (up_ratio - down_ratio) * 50)

    if likely_probability >= 0.35:
        recommendation = f"Bias toward MATCH on digit {likely_digit}."
    elif differ_probability >= 0.65:
        recommendation = "Bias toward DIFFER on recent tick pattern."
    elif flat_count > max(up_count, down_count):
        recommendation = "Market is balanced; wait for a break in direction."
    elif up_ratio > down_ratio:
        recommendation = "Upward bias; watch for continuation before taking a match call."
    else:
        recommendation = "Downward bias; monitor for reversal before taking a position."

    return MatchAnalysisSummary(
        sample_size=len(values),
        likely_match_digit=likely_digit,
        likely_match_probability=round(likely_probability, 4),
        differ_probability=round(differ_probability, 4),
        average_move=round(average_move, 4),
        volatility=round(volatility, 4),
        up_ratio=round(up_ratio, 4),
        down_ratio=round(down_ratio, 4),
        current_streak=current_streak,
        longest_streak=longest_streak,
        recommendation=recommendation,
        signal_strength=round(signal_strength, 2),
        last_digit_distribution=dict(sorted(last_digit_distribution.items())),
    )


def summarize_to_dict(summary: MatchAnalysisSummary) -> dict:
    return asdict(summary)
