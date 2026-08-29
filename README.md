# deriv-matches-predictor

Professional Deriv Matches/Differs Signal Predictor and Market Analysis Tool.

Features
- Real-time tick analysis and probability engine
- Multiple analysis strategies (classic, RSI, volatility)
- Backtesting and strategy comparison endpoints
- Minimal web UI for local exploration

Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
```

2. Run tests:

```bash
pytest -q
```

3. Start the simple connector service (used by the frontend):

```bash
python server.py
# or for the advanced API endpoints:
python server_advanced.py
```

4. Open the frontend in a browser:

Open `frontend/index.html` in your browser (or serve the `frontend/` folder with a static file server).

Notes
- The server components require `websockets` for contacting Deriv endpoints. Provide a valid `appId` and `accessToken` when connecting from the UI.
- This repository is a small toolkit and demo; review the code before using with real funds.

License
- MIT

