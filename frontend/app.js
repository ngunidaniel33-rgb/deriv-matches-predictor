const sampleData = `tick
1
2
3
4
5
6
7
8
9
0
1
2
3
4
5
6
7
8
9
0
1
2
3
4
5
6
7
8
9
0
1
2
3
4
5
6
7
8
9
0`;

const elements = {
  fileInput: document.getElementById('file-input'),
  windowInput: document.getElementById('window-input'),
  targetDigit: document.getElementById('target-digit'),
  tickInput: document.getElementById('tick-input'),
  analyzeBtn: document.getElementById('analyze-btn'),
  clearBtn: document.getElementById('clear-btn'),
  loadDemoBtn: document.getElementById('load-demo'),
  themeToggle: document.getElementById('theme-toggle'),
  likelyDigit: document.getElementById('likely-digit'),
  likelyProbability: document.getElementById('likely-probability'),
  differProbability: document.getElementById('differ-probability'),
  signalStrength: document.getElementById('signal-strength'),
  averageMove: document.getElementById('average-move'),
  volatility: document.getElementById('volatility'),
  directionalBias: document.getElementById('directional-bias'),
  directionalDetail: document.getElementById('directional-detail'),
  recommendation: document.getElementById('recommendation'),
  signalBadge: document.getElementById('signal-badge'),
  connectionStatus: document.getElementById('connection-status'),
  rsiValue: document.getElementById('rsi-value'),
  bollingerBands: document.getElementById('bollinger-bands'),
  movingAverage: document.getElementById('moving-average'),
  performanceMetrics: document.getElementById('performance-metrics'),
  strategySelect: document.getElementById('strategy-select'),
  exportBtn: document.getElementById('export-btn'),
  backtestBtn: document.getElementById('backtest-btn'),
  compareBtn: document.getElementById('compare-btn'),
};

let tickChart;
let distributionChart;
let analysisHistory = [];
let lastAnalysis = null;

function parseValues(rawText) {
  if (!rawText || !rawText.trim()) {
    throw new Error('Please provide tick data before analysis.');
  }

  const rows = rawText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const values = [];

  for (const row of rows) {
    const parts = row.split(',');

    if (parts.length > 1) {
      for (const part of parts) {
        const cleaned = part.trim();
        if (!cleaned) continue;
        const key = cleaned.toLowerCase();
        if (['tick', 'price', 'value', 'close', 'last', 'last_price', 'deriv_tick'].includes(key)) continue;
        const number = Number(cleaned);
        if (!Number.isNaN(number)) values.push(number);
      }
      continue;
    }

    const lower = row.toLowerCase();
    if (['tick', 'price', 'value', 'close', 'last', 'last_price', 'deriv_tick'].includes(lower)) continue;

    const number = Number(row);
    if (!Number.isNaN(number)) values.push(number);
  }

  if (values.length === 0) {
    throw new Error('No valid numeric tick values were found in the input.');
  }

  return values;
}

// Technical Indicators
function calculateRSI(values, period = 14) {
  if (values.length < period + 1) return null;
  const changes = [];
  for (let i = 1; i < values.length; i++) {
    changes.push(values[i] - values[i - 1]);
  }
  const gains = changes.filter(c => c > 0).reduce((s, c) => s + c, 0) / period;
  const losses = Math.abs(changes.filter(c => c < 0).reduce((s, c) => s + c, 0)) / period;
  if (losses === 0) return gains > 0 ? 100 : 0;
  const rs = gains / losses;
  return 100 - (100 / (1 + rs));
}

function calculateMovingAverages(values, periods = [5, 10, 20]) {
  return periods.map(period => ({
    period,
    value: values.length >= period ? values.slice(-period).reduce((a, b) => a + b) / period : null,
  }));
}

function calculateBollingerBands(values, period = 20, stdDev = 2) {
  if (values.length < period) return null;
  const recent = values.slice(-period);
  const sma = recent.reduce((a, b) => a + b) / period;
  const variance = recent.reduce((sum, v) => sum + (v - sma) ** 2, 0) / period;
  const std = Math.sqrt(variance);
  return {
    upper: sma + (std * stdDev),
    middle: sma,
    lower: sma - (std * stdDev),
  };
}

function analyzeValues(values, window, targetDigit, strategy = 'classic') {
  const recent = values.slice(-window);
  const counts = {};

  for (const value of recent) {
    const digit = Math.round(value) % 10;
    counts[digit] = (counts[digit] || 0) + 1;
  }

  const total = Object.values(counts).reduce((sum, count) => sum + count, 0) || 1;
  const sortedDigits = Object.entries(counts).sort((a, b) => b[1] - a[1] || Number(a[0]) - Number(b[0]));
  const likelyDigit = sortedDigits[0] ? Number(sortedDigits[0][0]) : 0;
  const chosenDigit = targetDigit !== '' ? Number(targetDigit) : likelyDigit;
  const matchProbability = counts[chosenDigit] ? counts[chosenDigit] / total : 0;
  const differProbability = 1 - matchProbability;

  const changes = [];
  for (let i = 1; i < values.length; i += 1) {
    changes.push(values[i] - values[i - 1]);
  }

  const avgMove = changes.length
    ? changes.reduce((sum, value) => sum + Math.abs(value), 0) / changes.length
    : 0;

  const mean = changes.length ? changes.reduce((sum, value) => sum + value, 0) / changes.length : 0;
  const volatility = changes.length > 1
    ? Math.sqrt(changes.reduce((sum, value) => sum + (value - mean) ** 2, 0) / changes.length)
    : 0;

  const upRatio = changes.length ? changes.filter((value) => value > 0).length / changes.length : 0;
  const downRatio = changes.length ? changes.filter((value) => value < 0).length / changes.length : 0;

  const rsi = calculateRSI(values);
  const mas = calculateMovingAverages(values);
  const bb = calculateBollingerBands(values);

  let signalStrength = Math.max(0, (matchProbability - 0.1) * 100 + (upRatio - downRatio) * 50);
  if (strategy === 'rsi' && rsi !== null) {
    signalStrength = Math.abs(rsi - 50) * 2;
  } else if (strategy === 'volatility') {
    signalStrength = Math.min(100, volatility * 10);
  }

  let recommendation = 'Market is balanced; waiting for stronger confirmation.';
  let badgeClass = 'neutral';
  let badgeText = 'Waiting';

  if (matchProbability >= 0.35) {
    recommendation = `Bias toward MATCH on digit ${chosenDigit}.`;
    badgeClass = 'match';
    badgeText = 'Match bias';
  } else if (differProbability >= 0.65) {
    recommendation = 'Bias toward DIFFER on recent tick pattern.';
    badgeClass = 'differ';
    badgeText = 'Differ bias';
  } else if (upRatio > downRatio) {
    recommendation = 'Upward bias; watch for continuation before taking a match call.';
    badgeClass = 'match';
    badgeText = 'Up trend';
  } else {
    recommendation = 'Downward bias; monitor for reversal before taking a position.';
    badgeClass = 'differ';
    badgeText = 'Down trend';
  }

  return {
    likelyDigit: chosenDigit,
    likelyProbability: matchProbability,
    differProbability,
    averageMove: avgMove,
    volatility,
    upRatio,
    downRatio,
    signalStrength: Math.min(100, signalStrength),
    recommendation,
    badgeClass,
    badgeText,
    distribution: Array.from({ length: 10 }, (_, i) => ({ digit: i, count: counts[i] || 0 })),
    values,
    rsi,
    movingAverages: mas,
    bollingerBands: bb,
    timestamp: new Date().toISOString(),
    strategy,
    dataPoints: values.length,
    window,
  };
}

function updateUI(summary) {
  elements.likelyDigit.textContent = String(summary.likelyDigit);
  elements.likelyProbability.textContent = `${(summary.likelyProbability * 100).toFixed(1)}% match probability`;
  elements.differProbability.textContent = `${(summary.differProbability * 100).toFixed(1)}%`;
  elements.signalStrength.textContent = `${summary.signalStrength.toFixed(1)}`;
  elements.averageMove.textContent = summary.averageMove.toFixed(4);
  elements.volatility.textContent = summary.volatility.toFixed(4);
  elements.directionalBias.textContent = summary.upRatio >= summary.downRatio ? 'Bullish' : 'Bearish';
  elements.directionalDetail.textContent = `${(summary.upRatio * 100).toFixed(1)}% up / ${(summary.downRatio * 100).toFixed(1)}% down`;
  elements.recommendation.textContent = summary.recommendation;
  elements.signalBadge.className = `signal-badge ${summary.badgeClass}`;
  elements.signalBadge.textContent = summary.badgeText;

  // Technical Indicators
  if (elements.rsiValue) {
    elements.rsiValue.textContent = summary.rsi !== null ? summary.rsi.toFixed(2) : 'N/A';
  }
  if (elements.bollingerBands && summary.bollingerBands) {
    elements.bollingerBands.textContent = `U: ${summary.bollingerBands.upper.toFixed(2)} | M: ${summary.bollingerBands.middle.toFixed(2)} | L: ${summary.bollingerBands.lower.toFixed(2)}`;
  }
  if (elements.movingAverage && summary.movingAverages) {
    elements.movingAverage.textContent = summary.movingAverages.map(ma => `MA${ma.period}: ${ma.value?.toFixed(2) || 'N/A'}`).join(' | ');
  }

  // Performance Metrics
  if (elements.performanceMetrics && analysisHistory.length > 1) {
    const recent = analysisHistory.slice(-10);
    const wins = recent.filter(a => a.signalStrength > 50).length;
    const winRate = (wins / recent.length * 100).toFixed(1);
    elements.performanceMetrics.textContent = `Win Rate: ${winRate}% | Analyses: ${analysisHistory.length} | Avg Signal: ${(recent.reduce((s, a) => s + a.signalStrength, 0) / recent.length).toFixed(1)}`;
  }

  renderTickChart(summary.values);
  renderDistributionChart(summary.distribution);
  
  lastAnalysis = summary;
  analysisHistory.push(summary);
}

function getThemeColors() {
  const isLight = document.body.classList.contains('theme-light');
  return {
    text: isLight ? '#0f172a' : '#e5f0ff',
    muted: isLight ? '#475569' : '#9db0c7',
    grid: isLight ? 'rgba(15,23,42,0.08)' : 'rgba(148,163,184,0.14)',
    accent: isLight ? '#0ea5e9' : '#6ee7f9',
    accentStrong: isLight ? '#14b8a6' : '#2dd4bf',
    danger: '#f87171',
    success: '#22c55e',
  };
}

function renderTickChart(values) {
  const colors = getThemeColors();

  if (tickChart) {
    tickChart.destroy();
  }

  tickChart = new Chart(document.getElementById('tick-chart'), {
    type: 'line',
    data: {
      labels: values.map((_, index) => index + 1),
      datasets: [{
        data: values,
        borderColor: colors.accent,
        backgroundColor: 'rgba(110, 231, 249, 0.15)',
        fill: true,
        tension: 0.25,
        pointRadius: 2,
        pointHoverRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { color: colors.grid },
          ticks: { color: colors.muted },
        },
        y: {
          grid: { color: colors.grid },
          ticks: { color: colors.muted },
        },
      },
    },
  });
}

function renderDistributionChart(distribution) {
  const colors = getThemeColors();

  if (distributionChart) {
    distributionChart.destroy();
  }

  distributionChart = new Chart(document.getElementById('distribution-chart'), {
    type: 'bar',
    data: {
      labels: distribution.map((item) => item.digit),
      datasets: [{
        label: 'Digit frequency',
        data: distribution.map((item) => item.count),
        backgroundColor: distribution.map((_, index) =>
          index % 2 === 0 ? colors.accent : colors.accentStrong
        ),
        borderRadius: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.muted },
        },
        y: {
          grid: { color: colors.grid },
          ticks: { color: colors.muted },
        },
      },
    },
  });
}

function analyze() {
  try {
    const values = parseValues(elements.tickInput.value);
    const window = Number(elements.windowInput.value) || 20;
    const targetDigit = elements.targetDigit.value;
    const strategy = elements.strategySelect?.value || 'classic';
    const summary = analyzeValues(values, window, targetDigit, strategy);
    updateUI(summary);
  } catch (error) {
    alert(error.message || 'Unable to analyze the provided data.');
  }
}

function clearInputs() {
  elements.tickInput.value = '';
  elements.fileInput.value = '';
  elements.windowInput.value = 20;
  elements.targetDigit.value = '';
  elements.likelyDigit.textContent = '--';
  elements.likelyProbability.textContent = '--';
  elements.differProbability.textContent = '--';
  elements.signalStrength.textContent = '--';
  elements.averageMove.textContent = '--';
  elements.volatility.textContent = '--';
  elements.directionalBias.textContent = '--';
  elements.directionalDetail.textContent = 'Up vs down';
  elements.recommendation.textContent = 'Waiting for market data to analyze.';
  elements.signalBadge.className = 'signal-badge neutral';
  elements.signalBadge.textContent = 'Waiting';
  
  if (elements.rsiValue) elements.rsiValue.textContent = '--';
  if (elements.bollingerBands) elements.bollingerBands.textContent = '--';
  if (elements.movingAverage) elements.movingAverage.textContent = '--';
  if (elements.performanceMetrics) elements.performanceMetrics.textContent = '--';

  if (tickChart) tickChart.destroy();
  if (distributionChart) distributionChart.destroy();
}

function loadDemo() {
  elements.tickInput.value = sampleData;
  elements.windowInput.value = 20;
  elements.targetDigit.value = '';
  analyze();
}

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (loadEvent) => {
    elements.tickInput.value = String(loadEvent.target?.result || '');
    analyze();
  };
  reader.readAsText(file);
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('theme-light');
  const toggleBtn = elements.themeToggle;
  toggleBtn.innerHTML = isLight
    ? '<span class="toggle-icon">🌙</span><span>Dark</span>'
    : '<span class="toggle-icon">☀️</span><span>Light</span>';

  if (elements.tickInput && elements.tickInput.value.trim()) {
    analyze();
  }
}

async function connectToDeriv() {
  const appId = document.getElementById('app-id')?.value?.trim();
  const accessToken = document.getElementById('access-token')?.value?.trim();
  const environment = document.getElementById('environment')?.value || 'real';
  const statusEl = elements.connectionStatus || document.getElementById('connection-status');

  if (!statusEl) return;

  if (!appId || !accessToken) {
    statusEl.textContent = 'Please provide both an App ID and Access Token.';
    statusEl.className = 'status-box error';
    return;
  }

  statusEl.textContent = 'Connecting to Deriv...';
  statusEl.className = 'status-box';

  try {
    const response = await fetch('http://localhost:8765/api/deriv/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appId, accessToken, environment }),
    });

    const data = await response.json();

    if (!response.ok || !data.connected) {
      statusEl.textContent = data.error || 'Connection failed.';
      statusEl.className = 'status-box error';
      return;
    }

    statusEl.textContent = `Connected to Deriv ${data.environment || environment} account: ${data.account}`;
    statusEl.className = 'status-box success';

    const compactPill = document.querySelector('.compact-pill');
    if (compactPill) {
      compactPill.innerHTML = '<span class="status-dot"></span>Connected';
    }
  } catch (error) {
    statusEl.textContent = `Unable to connect to Deriv: ${error.message}`;
    statusEl.className = 'status-box error';
  }
}

function exportAnalysis() {
  if (analysisHistory.length === 0) {
    alert('Run an analysis first before exporting.');
    return;
  }
  const json = JSON.stringify(analysisHistory, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `deriv-analysis-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function runBacktest() {
  try {
    const values = parseValues(elements.tickInput.value);
    if (values.length < 30) {
      alert('Need at least 30 data points for backtest.');
      return;
    }
    const strategy = elements.strategySelect?.value || 'classic';
    const statusEl = document.getElementById('backtest-status');
    if (statusEl) statusEl.textContent = 'Running...';
    const response = await fetch('http://localhost:8765/api/analysis/backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values, strategy }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    const resultsEl = document.getElementById('backtest-results');
    if (resultsEl) {
      resultsEl.innerHTML = '<strong>' + strategy + ' Strategy Backtest</strong><br>' +
        'Tests: ' + data.total_tests + '<br>' +
        'Win Rate: ' + data.win_rate.toFixed(1) + '%<br>' +
        'Avg Signal: ' + data.avg_signal_strength.toFixed(1);
    }
    if (statusEl) statusEl.textContent = 'Complete';
  } catch (error) {
    alert('Backtest failed: ' + error.message);
  }
}

async function compareStrategies() {
  try {
    const values = parseValues(elements.tickInput.value);
    if (values.length < 30) {
      alert('Need at least 30 data points for comparison.');
      return;
    }
    const response = await fetch('http://localhost:8765/api/analysis/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    const resultsEl = document.getElementById('comparison-results');
    if (resultsEl && data.comparison) {
      let html = '<table style="width: 100%; font-size: 0.85rem; border-collapse: collapse;">';
      html += '<tr style="border-bottom: 1px solid #444;"><th style="text-align: left; padding: 4px;">Strategy</th><th style="padding: 4px;">Signal</th><th style="padding: 4px;">Probability</th></tr>';
      for (const key in data.comparison) {
        const result = data.comparison[key];
        html += '<tr style="border-bottom: 1px solid #444;">' +
          '<td style="padding: 4px;">' + key + '</td>' +
          '<td style="padding: 4px;">' + result.signal_strength.toFixed(1) + '</td>' +
          '<td style="padding: 4px;">' + (result.match_probability * 100).toFixed(1) + '%</td>' +
          '</tr>';
      }
      html += '</table>';
      resultsEl.innerHTML = html;
    }
  } catch (error) {
    alert('Comparison failed: ' + error.message);
  }
}

// Event Listeners
if (elements.analyzeBtn) {
  elements.analyzeBtn.addEventListener('click', analyze);
}
if (elements.clearBtn) {
  elements.clearBtn.addEventListener('click', clearInputs);
}
if (elements.loadDemoBtn) {
  elements.loadDemoBtn.addEventListener('click', loadDemo);
}
if (elements.fileInput) {
  elements.fileInput.addEventListener('change', handleFileUpload);
}
if (elements.themeToggle) {
  elements.themeToggle.addEventListener('click', toggleTheme);
}
if (elements.exportBtn) {
  elements.exportBtn.addEventListener('click', exportAnalysis);
}
if (elements.strategySelect) {
  elements.strategySelect.addEventListener('change', analyze);
}

const backtestBtn = document.getElementById('backtest-btn');
if (backtestBtn) {
  backtestBtn.addEventListener('click', runBacktest);
}

const compareBtn = document.getElementById('compare-btn');
if (compareBtn) {
  compareBtn.addEventListener('click', compareStrategies);
}

const derivForm = document.getElementById('deriv-form');
if (derivForm) {
  derivForm.addEventListener('submit', (event) => {
    event.preventDefault();
    connectToDeriv();
  });
}

// Initialize
if (elements.tickInput) {
  clearInputs();
  loadDemo();
}
