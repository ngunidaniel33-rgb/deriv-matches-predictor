from pathlib import Path

from deriv_matches_analysis.analysis import analyze_ticks, load_tick_history


def test_load_tick_history_from_csv():
    values = load_tick_history(Path("sample_ticks.csv"))
    assert len(values) > 0
    assert all(isinstance(item, float) for item in values)


def test_analyze_ticks_returns_summary():
    values = list(range(1, 31))
    summary = analyze_ticks(values, window=10)
    assert summary.sample_size == 30
    assert summary.likely_match_digit is not None
    assert 0.0 <= summary.likely_match_probability <= 1.0
    assert 0.0 <= summary.differ_probability <= 1.0
    assert summary.recommendation


def test_target_digit_support():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0] * 3
    summary = analyze_ticks(values, target_digit=7)
    assert summary.likely_match_digit == 7
    assert summary.likely_match_probability >= 0.0
