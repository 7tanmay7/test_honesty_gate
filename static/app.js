/**
 * Test-Honesty Gate - Apple-Grade Interactive Web Application
 */

// Global State
const state = {
  theme: localStorage.getItem('theme') || 'dark',
  mockMode: true, // Default to mock mode or auto-detect
  activeFilter: 'all',
  currentContract: null,
  isLiveServer: false,
  simulating: false
};

// Fallback Mock Data in case server is starting up
const FALLBACK_CONTRACT = {
  pr_id: "pr-8429",
  verdict: "fail",
  mutants_tested: 5,
  mutants_caught: 2,
  mutants_survived: 3,
  duration_ms: 1830,
  results: [
    {
      mutant_id: "m1",
      operator: "equality_flip",
      location: "src/pricing.py:28",
      caught: false,
      explanation: "Flipped '==' to '!=' on discount condition. Your test 'test_volume_discount' passed because it used hardcoded sample prices that didn't hit the tier boundary.",
      diff_orig: "if discount_tier == 2:",
      diff_mutated: "if discount_tier != 2:"
    },
    {
      mutant_id: "m2",
      operator: "boundary_shift",
      location: "src/pricing.py:15",
      caught: false,
      explanation: "Shifted boundary condition '>' to '>='. No test checked exact boundary price of 100.00.",
      diff_orig: "if cart_total > 100.0:",
      diff_mutated: "if cart_total >= 100.0:"
    },
    {
      mutant_id: "m3",
      operator: "off_by_one",
      location: "src/pricing.py:37",
      caught: false,
      explanation: "Off-by-one error: changed index limit from len(items) to len(items) - 1. The last item in cart is skipped without triggering any test assertion.",
      diff_orig: "for i in range(len(items)):",
      diff_mutated: "for i in range(len(items) - 1):"
    },
    {
      mutant_id: "m4",
      operator: "return_null",
      location: "src/pricing.py:52",
      caught: true,
      explanation: "",
      diff_orig: "return total_price",
      diff_mutated: "return None"
    },
    {
      mutant_id: "m5",
      operator: "constant_replace",
      location: "src/pricing.py:08",
      caught: true,
      explanation: "",
      diff_orig: "TAX_RATE = 0.08",
      diff_mutated: "TAX_RATE = 0.0"
    }
  ]
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initEventListeners();
  checkServerHealth();
  fetchGateData();
});

// Theme Management
function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', state.theme);
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function updateThemeIcon() {
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.textContent = state.theme === 'dark' ? '☀️' : '🌙';
  }
}

// Event Listeners
function initEventListeners() {
  // Theme Toggle Button
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  // Mobile Menu Toggle
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const drawer = document.getElementById('mobile-drawer');
  if (mobileBtn && drawer) {
    mobileBtn.addEventListener('click', () => {
      drawer.classList.toggle('active');
    });

    const mobileLinks = drawer.querySelectorAll('.nav-link');
    mobileLinks.forEach(link => {
      link.addEventListener('click', () => {
        drawer.classList.remove('active');
      });
    });
  }

  // Mock / Live Mode Toggle
  const mockToggle = document.getElementById('mode-toggle-mock');
  const liveToggle = document.getElementById('mode-toggle-live');

  if (mockToggle && liveToggle) {
    mockToggle.addEventListener('click', () => {
      setMode(true);
    });
    liveToggle.addEventListener('click', () => {
      setMode(false);
    });
  }

  // Refresh Button
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      fetchGateData();
    });
  }

  // Filter Tabs
  const filterTabs = document.querySelectorAll('.filter-tab');
  filterTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      filterTabs.forEach(t => t.classList.remove('active'));
      e.target.classList.add('active');
      state.activeFilter = e.target.dataset.filter;
      renderMutants();
    });
  });

  // Simulator Run Button
  const simBtn = document.getElementById('run-sim-btn');
  if (simBtn) {
    simBtn.addEventListener('click', runSimulation);
  }

  // Copy Terminal Command
  const copyBtn = document.getElementById('copy-cmd-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText('./gate check pr-8429');
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = 'Copy';
      }, 2000);
    });
  }
}

function setMode(isMock) {
  state.mockMode = isMock;
  const mockBtn = document.getElementById('mode-toggle-mock');
  const liveBtn = document.getElementById('mode-toggle-live');

  if (isMock) {
    mockBtn.classList.add('active');
    liveBtn.classList.remove('active');
  } else {
    liveBtn.classList.add('active');
    mockBtn.classList.remove('active');
  }
  fetchGateData();
}

// Server Liveness Probe
async function checkServerHealth() {
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');

  try {
    const res = await fetch('/health', { method: 'GET', headers: { 'Accept': 'application/json' } });
    if (res.ok) {
      state.isLiveServer = true;
      if (statusDot) statusDot.classList.remove('offline');
      if (statusText) statusText.textContent = 'API Live';
    } else {
      throw new Error('Non-200 response');
    }
  } catch (err) {
    state.isLiveServer = false;
    if (statusDot) statusDot.classList.add('offline');
    if (statusText) statusText.textContent = 'Mock Mode (Local)';
  }
}

// Fetch Gate Contract Data
async function fetchGateData() {
  const url = state.mockMode ? '/gate?mock=true' : '/gate';

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('API request failed');
    const data = await response.json();
    state.currentContract = data;
  } catch (err) {
    console.warn('Backend API unreachable, using fallback data:', err);
    state.currentContract = FALLBACK_CONTRACT;
  }

  renderMetrics();
  renderMutants();
}

// Render Dashboard Metrics
function renderMetrics() {
  const c = state.currentContract || FALLBACK_CONTRACT;

  // Verdict Badge & Card Accent
  const verdictCard = document.getElementById('verdict-card');
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictText = document.getElementById('verdict-text');

  if (c.verdict === 'pass') {
    if (verdictCard) {
      verdictCard.className = 'metric-card glass-card verdict-pass';
    }
    if (verdictBadge) {
      verdictBadge.className = 'verdict-badge pass';
      verdictBadge.innerHTML = '<span>✓</span> PASSED';
    }
    if (verdictText) verdictText.textContent = 'All artificial mutations were caught by tests.';
  } else {
    if (verdictCard) {
      verdictCard.className = 'metric-card glass-card verdict-fail';
    }
    if (verdictBadge) {
      verdictBadge.className = 'verdict-badge fail';
      verdictBadge.innerHTML = '<span>✕</span> BLOCKED';
    }
    if (verdictText) verdictText.textContent = `${c.mutants_survived} mutant(s) survived your test suite.`;
  }

  // Counter Values
  setText('metric-tested', c.mutants_tested);
  setText('metric-caught', c.mutants_caught);
  setText('metric-survived', c.mutants_survived);
  setText('metric-duration', `${c.duration_ms} ms`);
  setText('pr-id-label', `PR: ${c.pr_id || 'pr-8429'}`);
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// Render Mutant List
function renderMutants() {
  const container = document.getElementById('mutant-list-container');
  if (!container) return;

  const c = state.currentContract || FALLBACK_CONTRACT;
  let results = c.results || [];

  if (state.activeFilter === 'survived') {
    results = results.filter(r => !r.caught);
  } else if (state.activeFilter === 'caught') {
    results = results.filter(r => r.caught);
  }

  if (results.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 3rem; color: var(--color-text-secondary);">
        <p>No mutants found for filter: <strong>${state.activeFilter}</strong></p>
      </div>
    `;
    return;
  }

  container.innerHTML = results.map(m => {
    const isSurvived = !m.caught;
    const badgeClass = isSurvived ? 'mutant-status-badge survived' : 'mutant-status-badge caught';
    const badgeText = isSurvived ? 'SURVIVED (BLOCKED)' : 'CAUGHT (PASSED)';

    const diffHtml = m.diff_orig ? `
      <div style="margin-top: 0.75rem; background: #070a12; padding: 0.75rem 1rem; border-radius: 8px; font-family: var(--font-mono); font-size: 0.8125rem;">
        <div style="color: #ff7b72;">- ${escapeHtml(m.diff_orig)}</div>
        <div style="color: #7ee787;">+ ${escapeHtml(m.diff_mutated)}</div>
      </div>
    ` : '';

    const explanationHtml = isSurvived && m.explanation ? `
      <div class="explanation-box">
        <div class="explanation-header">✨ LLM Root Cause Explanation</div>
        <div>${escapeHtml(m.explanation)}</div>
      </div>
    ` : '';

    return `
      <div class="mutant-item">
        <div class="mutant-item-header">
          <div class="mutant-info">
            <span class="operator-tag">${escapeHtml(m.operator)}</span>
            <span class="location-tag">📍 ${escapeHtml(m.location)}</span>
            <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--color-text-tertiary);">ID: ${escapeHtml(m.mutant_id)}</span>
          </div>
          <span class="${badgeClass}">${badgeText}</span>
        </div>
        ${diffHtml}
        ${explanationHtml}
      </div>
    `;
  }).join('');
}

// Live Interactive Simulation Engine
async function runSimulation() {
  if (state.simulating) return;
  state.simulating = true;

  const simBtn = document.getElementById('run-sim-btn');
  const simStatus = document.getElementById('sim-status');
  if (simBtn) simBtn.disabled = true;

  const steps = [
    "🔍 Step 1/4: Injecting mutation operators into src/pricing.py...",
    "🧪 Step 2/4: Running pytest suite against 5 mutated binaries...",
    "🧠 Step 3/4: LLM reasoning over 3 surviving mutants...",
    "✅ Step 4/4: Contract JSON generated. Gate verdict rendered!"
  ];

  for (let i = 0; i < steps.length; i++) {
    if (simStatus) simStatus.textContent = steps[i];
    await sleep(600);
  }

  // Trigger state refresh
  await fetchGateData();

  if (simStatus) simStatus.textContent = "Simulation completed cleanly!";
  if (simBtn) simBtn.disabled = false;
  state.simulating = false;
}

// Helpers
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
