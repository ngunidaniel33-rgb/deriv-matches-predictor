"""Professional Deriv matches and differs market analysis toolkit."""

from .analysis import MatchAnalysisSummary, analyze_ticks, load_tick_history

__version__ = "0.1.0"

__all__ = ["MatchAnalysisSummary", "analyze_ticks", "load_tick_history", "__version__"]
