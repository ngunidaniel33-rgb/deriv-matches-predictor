from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: install websockets with 'python -m pip install websockets'.") from exc

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8765"))
DERIV_WS_URL = "wss://ws.deriv.com/websockets/v3"


# ============= Data Models =============
@dataclass
class TickData:
    timestamp: float
    value: float
    symbol: str = "UNKNOWN"


@dataclass
class StrategyResult:
    strategy: str
    timestamp: float
    likely_digit: int
    match_probability: float
    signal_strength: float
    recommendation: str
    metrics: dict = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    strategy: str
    total_signals: int
    win_rate: float
    avg_signal_strength: float
    best_signal: float
    worst_signal: float
    latest_10_results: list[StrategyResult] = field(default_factory=list)


# ============= Global State =============
tick_history: deque = deque(maxlen=1000)  # Keep last 1000 ticks
analysis_history: deque = deque(maxlen=500)  # Keep last 500 analyses
live_websocket = None
connected_account = None


# ============= Analysis Functions =============
def calculate_rsi(values: list[float], period: int = 14) -> float | None:
    """Calculate Relative Strength Index."""
    if len(values) < period + 1:
        return None
    
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = sum(c for c in changes if c > 0) / period
    losses = abs(sum(c for c in changes if c < 0)) / period
    
    if losses == 0:
        return 100 if gains > 0 else 0
    
    rs = gains / losses
    return 100 - (100 / (1 + rs))


def calculate_moving_averages(values: list[float], periods: list[int] = None) -> dict[int, float]:
    """Calculate exponential moving averages."""
    if periods is None:
        periods = [5, 10, 20]
    
    result = {}
    for period in periods:
        if len(values) >= period:
            result[period] = sum(values[-period:]) / period
    return result


def calculate_bollinger_bands(values: list[float], period: int = 20) -> dict[str, float] | None:
    """Calculate Bollinger Bands."""
    if len(values) < period:
        return None
    
    recent = values[-period:]
    sma = sum(recent) / period
    variance = sum((v - sma) ** 2 for v in recent) / period
    std_dev = variance ** 0.5
    
    return {
        "upper": sma + (2 * std_dev),
        "middle": sma,
        "lower": sma - (2 * std_dev),
    }


def analyze_classic(values: list[float], window: int = 20, target_digit: int | None = None) -> StrategyResult:
    """Classic probability-based strategy."""
    recent = values[-window:] if len(values) >= window else values
    
    digit_counts = {}
    for v in recent:
        digit = round(v) % 10
        digit_counts[digit] = digit_counts.get(digit, 0) + 1
    
    total = sum(digit_counts.values()) or 1
    if target_digit is None:
        target_digit = max(digit_counts, key=digit_counts.get, default=0)
    
    match_prob = digit_counts.get(target_digit, 0) / total
    
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    up_ratio = sum(1 for c in changes if c > 0) / len(changes) if changes else 0
    down_ratio = sum(1 for c in changes if c < 0) / len(changes) if changes else 0
    
    signal_strength = max(0, (match_prob - 0.1) * 100 + (up_ratio - down_ratio) * 50)
    signal_strength = min(100, signal_strength)
    
    recommendation = "Balanced market" if signal_strength < 50 else "Strong signal"
    
    return StrategyResult(
        strategy="classic",
        timestamp=time.time(),
        likely_digit=target_digit,
        match_probability=match_prob,
        signal_strength=signal_strength,
        recommendation=recommendation,
        metrics={
            "up_ratio": up_ratio,
            "down_ratio": down_ratio,
            "digit_distribution": digit_counts,
        },
    )


def analyze_rsi(values: list[float], window: int = 20, target_digit: int | None = None) -> StrategyResult:
    """RSI-based strategy."""
    rsi = calculate_rsi(values)
    
    recent = values[-window:] if len(values) >= window else values
    digit_counts = {}
    for v in recent:
        digit = round(v) % 10
        digit_counts[digit] = digit_counts.get(digit, 0) + 1
    
    total = sum(digit_counts.values()) or 1
    if target_digit is None:
        target_digit = max(digit_counts, key=digit_counts.get, default=0)
    
    match_prob = digit_counts.get(target_digit, 0) / total
    
    # RSI-based signal
    if rsi is None:
        signal_strength = 50
    elif rsi > 70:
        signal_strength = 75
    elif rsi < 30:
        signal_strength = 75
    else:
        signal_strength = abs(rsi - 50)
    
    recommendation = "Overbought" if rsi and rsi > 70 else ("Oversold" if rsi and rsi < 30 else "Neutral")
    
    return StrategyResult(
        strategy="rsi",
        timestamp=time.time(),
        likely_digit=target_digit,
        match_probability=match_prob,
        signal_strength=min(100, signal_strength),
        recommendation=recommendation,
        metrics={
            "rsi": rsi,
            "digit_distribution": digit_counts,
        },
    )


def analyze_volatility(values: list[float], window: int = 20, target_digit: int | None = None) -> StrategyResult:
    """Volatility-based strategy."""
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    mean_change = sum(changes) / len(changes) if changes else 0
    variance = sum((c - mean_change) ** 2 for c in changes) / len(changes) if changes else 0
    volatility = variance ** 0.5
    
    recent = values[-window:] if len(values) >= window else values
    digit_counts = {}
    for v in recent:
        digit = round(v) % 10
        digit_counts[digit] = digit_counts.get(digit, 0) + 1
    
    total = sum(digit_counts.values()) or 1
    if target_digit is None:
        target_digit = max(digit_counts, key=digit_counts.get, default=0)
    
    match_prob = digit_counts.get(target_digit, 0) / total
    
    # Volatility-based signal
    signal_strength = min(100, volatility * 10)
    
    recommendation = "High volatility" if volatility > 5 else ("Low volatility" if volatility < 1 else "Medium volatility")
    
    return StrategyResult(
        strategy="volatility",
        timestamp=time.time(),
        likely_digit=target_digit,
        match_probability=match_prob,
        signal_strength=signal_strength,
        recommendation=recommendation,
        metrics={
            "volatility": volatility,
            "digit_distribution": digit_counts,
        },
    )


# ============= HTTP Handlers =============
def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    content_length = int(handler.headers.get("Content-Length", "0") or "0")
    raw_body = handler.rfile.read(content_length).decode("utf-8")
    if not raw_body.strip():
        return {}
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        raise ValueError("Request body must be valid JSON.")


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


async def authorize_deriv(app_id: str, access_token: str) -> dict:
    """Authorize with Deriv via websocket."""
    global connected_account
    
    if not app_id or not access_token:
        return {"connected": False, "error": "Missing Deriv app ID or access token."}

    try:
        uri = f"{DERIV_WS_URL}?app_id={app_id}"
        async with websockets.connect(uri, ping_interval=None, timeout=15) as websocket:
            await websocket.send(json.dumps({"authorize": access_token}))
            auth_reply = json.loads(await websocket.recv())

            if auth_reply.get("error"):
                return {"connected": False, "error": auth_reply.get("error", {}).get("message", "Auth failed.")}

            if auth_reply.get("authorize"):
                connected_account = {
                    "loginid": auth_reply.get("authorize", {}).get("loginid"),
                    "app_id": app_id,
                    "token": access_token,
                }
                return {
                    "connected": True,
                    "message": "Authorized successfully.",
                    "account": connected_account["loginid"],
                    "environment": "real" if str(app_id) not in {"1089", "16929"} else "demo",
                }

            return {"connected": False, "error": "No account details in response."}
    except Exception as exc:
        return {"connected": False, "error": f"Connection failed: {exc}"}


class AdvancedDerivHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/deriv/health":
            send_json(self, 200, {"status": "ok", "service": "deriv-connector-advanced"})
            return

        if path == "/api/ticks/history":
            send_json(self, 200, {"ticks": list(tick_history), "count": len(tick_history)})
            return

        if path == "/api/analysis/history":
            send_json(self, 200, {"analyses": [asdict(a) for a in analysis_history], "count": len(analysis_history)})
            return

        if path == "/api/metrics/performance":
            metrics = {}
            for strategy in ["classic", "rsi", "volatility"]:
                strategy_results = [a for a in analysis_history if a.strategy == strategy]
                if strategy_results:
                    wins = sum(1 for r in strategy_results if r.signal_strength > 50)
                    metrics[strategy] = {
                        "total_signals": len(strategy_results),
                        "win_rate": (wins / len(strategy_results) * 100) if strategy_results else 0,
                        "avg_signal": sum(r.signal_strength for r in strategy_results) / len(strategy_results),
                        "best_signal": max(r.signal_strength for r in strategy_results),
                    }
            send_json(self, 200, {"metrics": metrics})
            return

        send_json(self, 404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/deriv/connect":
            try:
                payload = read_json_body(self)
                app_id = str(payload.get("appId", "")).strip()
                access_token = str(payload.get("accessToken", "")).strip()
                
                result = asyncio.run(authorize_deriv(app_id, access_token))
                send_json(self, 200 if result.get("connected") else 401, result)
            except Exception as exc:
                send_json(self, 500, {"connected": False, "error": str(exc)})
            return

        if path == "/api/analysis/analyze":
            try:
                payload = read_json_body(self)
                values = payload.get("values", [])
                window = payload.get("window", 20)
                target_digit = payload.get("target_digit")
                strategy = payload.get("strategy", "classic")

                if not values:
                    send_json(self, 400, {"error": "No values provided."})
                    return

                values = [float(v) for v in values]

                if strategy == "classic":
                    result = analyze_classic(values, window, target_digit)
                elif strategy == "rsi":
                    result = analyze_rsi(values, window, target_digit)
                elif strategy == "volatility":
                    result = analyze_volatility(values, window, target_digit)
                else:
                    send_json(self, 400, {"error": f"Unknown strategy: {strategy}"})
                    return

                analysis_history.append(result)
                send_json(self, 200, asdict(result))
            except Exception as exc:
                send_json(self, 400, {"error": str(exc)})
            return

        if path == "/api/analysis/backtest":
            try:
                payload = read_json_body(self)
                values = payload.get("values", [])
                strategy = payload.get("strategy", "classic")

                if not values:
                    send_json(self, 400, {"error": "No values provided."})
                    return

                values = [float(v) for v in values]
                results = []

                for i in range(20, min(len(values), 200), 5):
                    if strategy == "classic":
                        result = analyze_classic(values[:i], 20)
                    elif strategy == "rsi":
                        result = analyze_rsi(values[:i], 20)
                    elif strategy == "volatility":
                        result = analyze_volatility(values[:i], 20)
                    else:
                        send_json(self, 400, {"error": f"Unknown strategy: {strategy}"})
                        return
                    results.append(asdict(result))

                win_count = sum(1 for r in results if r["signal_strength"] > 50)
                win_rate = (win_count / len(results) * 100) if results else 0

                send_json(self, 200, {
                    "strategy": strategy,
                    "total_tests": len(results),
                    "win_rate": win_rate,
                    "avg_signal_strength": sum(r["signal_strength"] for r in results) / len(results) if results else 0,
                    "results": results,
                })
            except Exception as exc:
                send_json(self, 400, {"error": str(exc)})
            return

        if path == "/api/analysis/compare":
            try:
                payload = read_json_body(self)
                values = payload.get("values", [])

                if not values:
                    send_json(self, 400, {"error": "No values provided."})
                    return

                values = [float(v) for v in values]

                comparison = {}
                for strategy_name in ["classic", "rsi", "volatility"]:
                    if strategy_name == "classic":
                        result = analyze_classic(values, 20)
                    elif strategy_name == "rsi":
                        result = analyze_rsi(values, 20)
                    else:
                        result = analyze_volatility(values, 20)

                    comparison[strategy_name] = asdict(result)

                send_json(self, 200, {"comparison": comparison})
            except Exception as exc:
                send_json(self, 400, {"error": str(exc)})
            return

        send_json(self, 404, {"error": "Not found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), AdvancedDerivHandler)
    print(f"Advanced Deriv connector running on http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /api/deriv/health")
    print("  POST /api/deriv/connect")
    print("  POST /api/analysis/analyze")
    print("  POST /api/analysis/backtest")
    print("  POST /api/analysis/compare")
    print("  GET  /api/ticks/history")
    print("  GET  /api/analysis/history")
    print("  GET  /api/metrics/performance")
    server.serve_forever()
