# Deriv Matches/Differs Signal Predictor & Market Analysis Tool

## Overview

A professional, advanced analytical tool designed for educational and research purposes that connects to the official Deriv API, analyzes live tick data from synthetic indices, and generates probability-based insights for Matches/Differs contracts.

**⚠️ DISCLAIMER**: Market signals are statistical estimates based on historical and live tick data. Random or synthetic market outcomes cannot be predicted with certainty. Past patterns and backtest results do not guarantee future performance. This tool is for analysis and decision support only.

## Key Features

✅ **Live Deriv API Connection**
- Real-time WebSocket connection to Deriv
- Support for synthetic indices (R_50, R_100, Volatility Index, etc.)
- Connection status monitoring and automatic reconnect
- Live tick streaming with timestamp tracking

✅ **Advanced Tick Analysis**
- Configurable rolling windows (50, 100, 250, 500, 1000, 5000 ticks)
- Last-digit extraction with decimal precision normalization
- Real-time frequency calculations and updates
- Historical tick storage and management

✅ **Statistical Probability Engine**
- Digit frequency analysis (0-9)
- Hot/Cold digit detection
- Recent vs. long-term frequency comparison
- Frequency trending and momentum analysis
- Confidence scoring with transparency

✅ **Matches Probability Analysis**
- Historical frequency-based probability
- Recent frequency weighting
- Short-term momentum indicators
- Digit recurrence patterns
- Transition statistics integration
- Rolling-window consistency checks

✅ **Differs Probability Analysis**
- Barrier-based differs probability calculation
- Historical differs rate tracking
- Recent differs rate trending
- Stability and risk scoring
- Confidence metrics

✅ **Advanced Pattern Detection**
- Digit streak detection (repeated digits, long absences)
- Consecutive sequences and alternating patterns
- Cluster identification
- Return interval analysis
- 10×10 Transition Matrix (digit-to-digit relationships)

✅ **Signal Generation Engine**
- Multi-level signal system (STRONG WATCH, WATCH, NEUTRAL, WEAK, AVOID)
- Configurable threshold-based alerts
- Risk scoring and warnings
- Sample size validation
- Supporting indicator tracking

✅ **Backtesting Module**
- Historical signal performance analysis
- Match rate and differs rate calculation
- Probability calibration metrics
- Winning/losing streak tracking
- Performance by barrier digit
- CSV export for further analysis

✅ **Risk Management Dashboard**
- Optional bankroll tracking
- Daily stop limits
- Maximum consecutive loss limits
- Session statistics
- Suggested exposure limits

✅ **Modern Trading Dashboard**
- Real-time probability visualizations
- Hot/Cold digit heatmap
- Live tick chart
- Frequency distribution charts
- Signal history and alerts
- Responsive dark theme UI

✅ **Transparency & Honesty**
- No false certainty claims
- Clear confidence level indicators
- Sample size validation
- Variance and stability metrics
- Educational disclaimers throughout

## Technical Stack

### Backend
- **Python 3.9+**
- **FastAPI** - REST API framework
- **WebSockets** - Real-time data streaming
- **Pandas & NumPy** - Data processing
- **SQLite / PostgreSQL** - Data persistence
- **SciPy** - Statistical calculations
- **python-dotenv** - Configuration management

### Frontend
- **React 18+** - UI framework
- **TailwindCSS** - Styling
- **Chart.js / ApexCharts** - Data visualization
- **Axios** - API client
- **Socket.io-client** - Real-time updates

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Uvicorn** - ASGI server

## Project Structure

```
deriv-matches-predictor/
├── backend/
│   ├── app.py                    # Main FastAPI application
│   ├── config.py                 # Configuration management
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment template
│   └── src/
│       ├── __init__.py
│       ├── deriv_client.py        # Deriv WebSocket connection
│       ├── tick_stream.py         # Tick buffer and management
│       ├── digit_extractor.py     # Last-digit extraction logic
│       ├── frequency_analyzer.py  # Frequency calculations
│       ├── transition_matrix.py   # Digit transition analysis
│       ├── probability_engine.py  # Matches/Differs probability
│       ├── signal_engine.py       # Signal generation
│       ├── confidence_engine.py   # Confidence scoring
│       ├── backtester.py          # Backtesting module
│       ├── risk_manager.py        # Risk management
│       ├── database.py            # Database operations
│       └── models.py              # Data models
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── LeftPanel.jsx
│   │   │   ├── MainDashboard.jsx
│   │   │   ├── RightPanel.jsx
│   │   │   └── BottomSection.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Backtesting.jsx
│   │   │   └── Settings.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── styles/
│   │   │   └── globals.css
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── docs/
    ├── SETUP.md
    ├── API.md
    ├── METHODOLOGY.md
    └── DISCLAIMER.md
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose (optional)
- Deriv account (API token)

### Local Setup

#### 1. Clone Repository
```bash
git clone https://github.com/ngunidaniel33-rgb/deriv-matches-predictor.git
cd deriv-matches-predictor
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Deriv API token

# Run backend
python app.py
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

Access dashboard at: `http://localhost:3000`

### Docker Setup

```bash
docker-compose up -d
```

Access dashboard at: `http://localhost:3000`

## API Documentation

### WebSocket Endpoints

#### `/ws/live-data`
Real-time tick and analysis updates

```json
{
  "type": "tick_update",
  "tick": 12345.67,
  "last_digit": 7,
  "timestamp": 1692806400000,
  "market": "R_50"
}
```

#### `/ws/signals`
Real-time signal updates

```json
{
  "type": "signal",
  "contract_type": "MATCHES",
  "barrier": 5,
  "probability": 0.142,
  "confidence": "MEDIUM",
  "signal_level": "WATCH",
  "timestamp": 1692806400000
}
```

### REST Endpoints

- `GET /api/markets` - Available markets
- `GET /api/analysis` - Current analysis data
- `GET /api/history` - Tick history
- `POST /api/backtest` - Run backtesting
- `GET /api/signals` - Recent signals
- `POST /api/export` - Export data

## Configuration

### Environment Variables (.env)

```
DERIV_API_TOKEN=your_api_token_here
DERIV_APP_ID=your_app_id
TICK_WINDOW_SIZE=1000
ANALYSIS_UPDATE_INTERVAL=1000
DATABASE_URL=sqlite:///./data.db
LOG_LEVEL=INFO
```

### Settings

Configurable through dashboard:
- Tick window size (50-5000)
- Signal sensitivity
- Confidence thresholds
- Alert preferences
- Risk limits

## Methodology

### Probability Calculations

**Matches Probability:**
```
P(Matches) = Historical Frequency + Recent Weight + Momentum Factor
```

**Differs Probability:**
```
P(Differs) = 1 - P(Matches)
```

**Confidence Scoring:**
- Sample size validation
- Consistency across rolling windows
- Indicator agreement
- Recency weighting
- Variance analysis

See `docs/METHODOLOGY.md` for detailed statistical approach.

## Signal System

### Signal Levels
- **STRONG WATCH**: High probability, high confidence, strong consensus
- **WATCH**: Above-average probability, medium confidence
- **NEUTRAL**: Probability near expected frequency
- **WEAK**: Below-average probability
- **AVOID**: Very low probability or high uncertainty

### Signal Conditions

Signals are generated when:
1. Probability deviates significantly from expected (50% for binary)
2. Confidence score meets minimum threshold
3. Multiple indicators agree
4. Sample size is sufficient
5. Recency trend supports signal

## Backtesting

Test analysis signals against historical data:

```bash
curl -X POST http://localhost:8000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "min_confidence": "MEDIUM",
    "contract_type": "MATCHES"
  }'
```

Results include:
- Match rate (actual vs. predicted)
- Differs rate
- Maximum winning streak
- Maximum losing streak
- Calibration error
- Performance by barrier digit

## Risk Management

### Built-in Safeguards
- Daily loss limits
- Maximum consecutive loss limits
- Exposure percentage caps
- Bankroll tracking
- Session statistics

### Default Settings
- Analysis mode (no automated trading)
- Manual signal confirmation required
- Demo account recommended
- Hard risk limits enforced

## Transparency & Honesty

### What This Tool Does
✅ Analyzes historical and live tick patterns
✅ Calculates empirical frequencies
✅ Identifies statistical anomalies
✅ Provides decision support for analysis
✅ Tracks historical performance

### What This Tool Does NOT Do
❌ Predict random outcomes with certainty
❌ Guarantee profitable signals
❌ Eliminate market risk
❌ Replace professional financial advice
❌ Work perfectly in all market conditions

### Language Policy

This application **NEVER** uses:
- "Guaranteed win"
- "100% accurate"
- "Certain prediction"
- "Sure signal"
- "Risk-free profit"
- "Can't lose"

Instead, it uses:
- "Estimated probability"
- "Historical frequency"
- "Confidence level"
- "Statistical likelihood"
- "Suggested action"
- "Consider this signal"

## Performance

### System Specifications
- **Tick Processing**: <10ms per tick
- **Analysis Update**: Real-time (configurable interval)
- **Memory Usage**: ~100-500MB typical
- **API Latency**: <50ms average
- **Concurrent Users**: 10-100 (depending on infrastructure)

### Scalability
- PostgreSQL for large-scale deployments
- Redis caching for performance
- Worker queues for backtesting
- Horizontal scaling support

## Troubleshooting

### Connection Issues
1. Verify Deriv API token is valid
2. Check internet connection
3. Ensure market is available
4. Review logs: `tail -f logs/app.log`

### Data Anomalies
1. Verify tick normalization (decimal places)
2. Check tick buffer isn't full
3. Review frequency calculations
4. Compare with raw tick data

### Performance Issues
1. Reduce tick window size
2. Increase analysis update interval
3. Close unused browser tabs
4. Check system resources

## Contributing

Contributions are welcome! Please:
1. Fork repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Submit pull request

## License

MIT License - See LICENSE.md

## Disclaimer

**IMPORTANT**: This tool is for educational and analytical purposes only. It does not provide financial advice, does not guarantee profits, and cannot predict random outcomes. Users assume full responsibility for any trading decisions. Always:

- Start with demo accounts
- Risk only capital you can afford to lose
- Implement proper risk management
- Never over-leverage
- Understand the markets you trade
- Verify all signals independently

## Support

- 📧 Email: support@example.com
- 📚 Documentation: See `docs/` folder
- 🐛 Issue Tracker: GitHub Issues
- 💬 Discussions: GitHub Discussions

## Roadmap

- [ ] Multi-market simultaneous analysis
- [ ] Machine learning confidence scoring
- [ ] Advanced Markov chain models
- [ ] Mobile app (React Native)
- [ ] Telegram/Discord bot integration
- [ ] Plugin system for custom indicators
- [ ] Cloud deployment templates
- [ ] Advanced data export formats

---

**Last Updated**: August 2026
**Version**: 1.0.0-alpha
