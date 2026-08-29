from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_ticks, load_tick_history


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Professional Deriv matches and differs signal analysis tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to the tick history CSV file.")
    parser.add_argument("--window", type=int, default=20, help="Number of recent ticks to evaluate.")
    parser.add_argument(
        "--target-digit",
        type=int,
        choices=range(10),
        help="Optional target digit to prioritize when evaluating match probability.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the analysis summary in JSON format instead of human-readable text.",
    )
    return parser


def format_summary(summary) -> str:
    lines = [
        "Deriv Matches Analysis",
        "=" * 24,
        f"Sample size: {summary.sample_size}",
        f"Likely match digit: {summary.likely_match_digit}",
        f"Likely match probability: {summary.likely_match_probability:.2%}",
        f"Differ probability: {summary.differ_probability:.2%}",
        f"Average move: {summary.average_move}",
        f"Volatility: {summary.volatility}",
        f"Up ratio: {summary.up_ratio:.2%}",
        f"Down ratio: {summary.down_ratio:.2%}",
        f"Current streak: {summary.current_streak}",
        f"Longest streak: {summary.longest_streak}",
        f"Signal strength: {summary.signal_strength}",
        f"Recommendation: {summary.recommendation}",
        "Digit distribution:",
    ]

    for digit, count in summary.last_digit_distribution.items():
        lines.append(f"  Digit {digit}: {count} ticks")

    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    values = load_tick_history(Path(args.input))
    summary = analyze_ticks(values, window=args.window, target_digit=args.target_digit)

    if args.json:
        print(json.dumps(summary.__dict__, indent=2, sort_keys=True))
    else:
        print(format_summary(summary))


if __name__ == "__main__":
    main()
