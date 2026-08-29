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
};

let tickChart;
let distributionChart;

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

function analyzeValues(values, window, targetDigit) {
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

  let signalStrength = Math.max(0, (matchProbability - 0.1) * 100 + (upRatio - downRatio) * 50);
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
    signalStrength,
    recommendation,
    badgeClass,
    badgeText,
    distribution: Array.from({ length: 10 }, (_, i) => ({ digit: i, count: counts[i] || 0 })),
    values,
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

  renderTickChart(summary.values);
  renderDistributionChart(summary.distribution);
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
    const summary = analyzeValues(values, window, targetDigit);
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

const derivForm = document.getElementById('deriv-form');
if (derivForm) {
  derivForm.addEventListener('submit', (event) => {
    event.preventDefault();
    connectToDeriv();
  });
}

if (elements.tickInput) {
  clearInputs();
  loadDemo();
}
