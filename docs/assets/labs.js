// Essentials for Financial Derivatives — 8 Interactive Quantitative Finance Labs (Plotly.js)
(function () {
  // --- Core Mathematical Kernels ---
  function erf(x) {
    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x);
    const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * Math.exp(-x * x);
    return sign * y;
  }
  function normCDF(x) { return 0.5 * (1.0 + erf(x / Math.SQRT2)); }
  function normPDF(x) { return Math.exp(-0.5 * x * x) / Math.sqrt(2.0 * Math.PI); }

  function bsAll(S, K, r, q, sigma, T) {
    if (T <= 1e-8) {
      return {
        call: Math.max(S - K, 0), put: Math.max(K - S, 0),
        deltaC: S > K ? 1 : 0, deltaP: S < K ? -1 : 0,
        gamma: 0, vega: 0, thetaC: 0, thetaP: 0, vanna: 0, volga: 0
      };
    }
    const sqrtT = Math.sqrt(T);
    const d1 = (Math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
    const d2 = d1 - sigma * sqrtT;
    const discR = Math.exp(-r * T), discQ = Math.exp(-q * T);
    const pdf1 = normPDF(d1);
    const call = S * discQ * normCDF(d1) - K * discR * normCDF(d2);
    const put = K * discR * normCDF(-d2) - S * discQ * normCDF(-d1);
    const deltaC = discQ * normCDF(d1);
    const deltaP = -discQ * normCDF(-d1);
    const gamma = (discQ * pdf1) / (S * sigma * sqrtT);
    const vega = S * discQ * sqrtT * pdf1;
    const thetaC = -(S * discQ * pdf1 * sigma) / (2 * sqrtT) - r * K * discR * normCDF(d2) + q * S * discQ * normCDF(d1);
    const thetaP = -(S * discQ * pdf1 * sigma) / (2 * sqrtT) + r * K * discR * normCDF(-d2) - q * S * discQ * normCDF(-d1);
    const vanna = -discQ * pdf1 * d2 / sigma;
    const volga = vega * (d1 * d2) / sigma;
    return { call, put, deltaC, deltaP, gamma, vega, thetaC, thetaP, vanna, volga, d1, d2 };
  }

  function crrBinomial(S0, K, r, sigma, T, N, isCall) {
    const dt = T / N;
    const u = Math.exp(sigma * Math.sqrt(dt));
    const d = 1 / u;
    const disc = Math.exp(-r * dt);
    const q = (Math.exp(r * dt) - d) / (u - d);
    const vals = new Float64Array(N + 1);
    for (let i = 0; i <= N; i++) {
      const ST = S0 * Math.pow(u, N - i) * Math.pow(d, i);
      vals[i] = isCall ? Math.max(ST - K, 0) : Math.max(K - ST, 0);
    }
    for (let step = N - 1; step >= 0; step--) {
      for (let i = 0; i <= step; i++) {
        vals[i] = disc * (q * vals[i] + (1 - q) * vals[i + 1]);
      }
    }
    return vals[0];
  }

  // Seeded PRNG (Mulberry32) + Box-Muller for reproducible interactive paths
  function mulberry32(seed) {
    return function () {
      let t = (seed += 0x6D2B79F5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gaussianDraws(n, seed) {
    const rng = mulberry32(seed);
    const z = new Float64Array(n);
    for (let i = 0; i < n; i += 2) {
      const u1 = Math.max(1e-12, rng());
      const u2 = rng();
      const mag = Math.sqrt(-2 * Math.log(u1));
      z[i] = mag * Math.cos(2 * Math.PI * u2);
      if (i + 1 < n) z[i + 1] = mag * Math.sin(2 * Math.PI * u2);
    }
    return z;
  }

  // Exact Cholesky fBM path on [0, 1] with N steps
  function simulateFBM(H, N, seed) {
    const dt = 1.0 / N;
    const twoH = 2.0 * H;
    // Build lower-triangular Cholesky L of N x N covariance matrix
    const L = Array.from({ length: N }, () => new Float64Array(N));
    for (let i = 0; i < N; i++) {
      const ti = (i + 1) * dt;
      for (let j = 0; j <= i; j++) {
        const tj = (j + 1) * dt;
        let sum = 0.5 * (Math.pow(ti, twoH) + Math.pow(tj, twoH) - Math.pow(Math.abs(ti - tj), twoH));
        for (let k = 0; k < j; k++) sum -= L[i][k] * L[j][k];
        L[i][j] = i === j ? Math.sqrt(Math.max(sum, 1e-12)) : sum / L[j][j];
      }
    }
    const z = gaussianDraws(N, seed);
    const t = [0], w = [0], qv = [0];
    let cumQV = 0;
    for (let i = 0; i < N; i++) {
      let val = 0;
      for (let k = 0; k <= i; k++) val += L[i][k] * z[k];
      const dw = val - w[i];
      cumQV += dw * dw;
      t.push((i + 1) * dt);
      w.push(val);
      qv.push(cumQV);
    }
    return { t, w, qv };
  }

  // Up-and-out call (with exact digital knock-out term) and Down-and-in/out call
  function barrierCalls(S0, K, B, r, sigma, T, type) {
    const vanilla = bsAll(S0, K, r, 0, sigma, T).call;
    const alpha = (2 * r) / (sigma * sigma) + 1;
    if (type === 'down') {
      if (S0 <= B) return { vanilla, inPrice: vanilla, outPrice: 0 };
      const di = Math.pow(B / S0, alpha - 2) * bsAll((B * B) / S0, K, r, 0, sigma, T).call;
      return { vanilla, inPrice: di, outPrice: Math.max(vanilla - di, 0) };
    } else {
      if (S0 >= B || K >= B) return { vanilla, inPrice: vanilla, outPrice: 0 };
      const sqrtT = Math.sqrt(T);
      const d1B = (Math.log(S0 / B) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
      const dBarB = (Math.log(B / S0) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
      const reflK = Math.pow(B / S0, alpha - 2) * bsAll((B * B) / S0, K, r, 0, sigma, T).call;
      const bsB = bsAll(S0, B, r, 0, sigma, T).call;
      const reflB = Math.pow(B / S0, alpha - 2) * bsAll((B * B) / S0, B, r, 0, sigma, T).call;
      const digCorr = (B - K) * Math.exp(-r * T) * (normCDF(d1B - sigma * sqrtT) - Math.pow(B / S0, alpha - 2) * normCDF(dBarB - sigma * sqrtT));
      const uo = Math.max(vanilla - reflK - (bsB - reflB) - digCorr, 0);
      return { vanilla, inPrice: Math.max(vanilla - uo, 0), outPrice: uo };
    }
  }

  // Theme-aware Plotly layout helper
  function plotLayout(title, xTitle, yTitle, extra) {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    const fg = dark ? '#E2E8F0' : '#0F172A';
    const grid = dark ? '#1F2937' : '#E2E8F0';
    const bg = dark ? '#0F172A' : '#FFFFFF';
    return Object.assign({
      title: { text: title, font: { family: 'IBM Plex Sans, sans-serif', size: 14, color: fg } },
      paper_bgcolor: bg,
      plot_bgcolor: bg,
      font: { family: 'IBM Plex Sans, sans-serif', size: 12, color: fg },
      margin: { t: 44, r: 22, b: 48, l: 58 },
      xaxis: { title: xTitle, gridcolor: grid, zerolinecolor: grid },
      yaxis: { title: yTitle, gridcolor: grid, zerolinecolor: grid },
      legend: { orientation: 'h', y: -0.22 }
    }, extra || {});
  }

  const plotConfig = { responsive: true, displayModeBar: false };
  const activeUpdaters = [];

  // --- Lab 1: Option Payoff & Strategy Builder (Ch 1) ---
  function mountLab1(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 1</span><span class="lab-title">Payoff &amp; P&amp;L Strategy Explorer</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Strategy</label>
            <select id="l1-strat">
              <option value="call">Long European Call</option>
              <option value="put">Long European Put</option>
              <option value="straddle">Long Straddle (Call + Put)</option>
              <option value="bull">Bull Call Spread (K1, K2)</option>
              <option value="forward">Long Forward</option>
            </select>
          </div>
          <div class="lab-control"><label>Strike K <span class="val" id="l1-K-v">100</span></label><input id="l1-K" type="range" min="60" max="140" step="2" value="100"></div>
          <div class="lab-control"><label>Premium / Spread Width <span class="val" id="l1-P-v">10</span></label><input id="l1-P" type="range" min="2" max="25" step="1" value="10"></div>
        </div>
        <div id="l1-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const strat = el.querySelector('#l1-strat').value;
      const K = +el.querySelector('#l1-K').value;
      const P = +el.querySelector('#l1-P').value;
      el.querySelector('#l1-K-v').textContent = '$' + K;
      el.querySelector('#l1-P-v').textContent = '$' + P;
      const S = [], pay = [], pnl = [];
      for (let s = 40; s <= 160; s += 1) {
        S.push(s);
        let y = 0, net = 0;
        if (strat === 'call') { y = Math.max(s - K, 0); net = y - P; }
        else if (strat === 'put') { y = Math.max(K - s, 0); net = y - P; }
        else if (strat === 'straddle') { y = Math.abs(s - K); net = y - 1.8 * P; }
        else if (strat === 'bull') { const K2 = K + P; y = Math.max(s - K, 0) - Math.max(s - K2, 0); net = y - 0.45 * P; }
        else { y = s - K; net = y; }
        pay.push(y); pnl.push(net);
      }
      Plotly.newPlot('l1-plot', [
        { x: S, y: pay, name: 'Terminal Payoff', line: { color: '#1D4ED8', width: 2.6 } },
        { x: S, y: pnl, name: 'Net Profit / Loss', line: { color: '#0D9488', width: 2.2, dash: 'dash' } }
      ], plotLayout('Terminal Payoff vs. Net P&L', 'Terminal Spot S_T', 'USD ($)'), plotConfig);
    }
    el.querySelectorAll('input,select').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 2: CRR Binomial Convergence to Black-Scholes (Ch 2) ---
  function mountLab2(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 2</span><span class="lab-title">CRR Binomial Tree Convergence to Black–Scholes</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Strike K <span class="val" id="l2-K-v">100</span></label><input id="l2-K" type="range" min="70" max="130" step="2" value="100"></div>
          <div class="lab-control"><label>Volatility σ <span class="val" id="l2-sig-v">20%</span></label><input id="l2-sig" type="range" min="0.08" max="0.50" step="0.02" value="0.20"></div>
          <div class="lab-control"><label>Rate r <span class="val" id="l2-r-v">5%</span></label><input id="l2-r" type="range" min="0" max="0.12" step="0.01" value="0.05"></div>
          <div class="lab-control"><label>Max Steps N <span class="val" id="l2-N-v">60</span></label><input id="l2-N" type="range" min="15" max="120" step="5" value="60"></div>
        </div>
        <div class="lab-metrics" id="l2-metrics"></div>
        <div id="l2-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const S0 = 100, T = 1.0;
      const K = +el.querySelector('#l2-K').value;
      const sig = +el.querySelector('#l2-sig').value;
      const r = +el.querySelector('#l2-r').value;
      const maxN = +el.querySelector('#l2-N').value;
      el.querySelector('#l2-K-v').textContent = K;
      el.querySelector('#l2-sig-v').textContent = (sig * 100).toFixed(0) + '%';
      el.querySelector('#l2-r-v').textContent = (r * 100).toFixed(0) + '%';
      el.querySelector('#l2-N-v').textContent = maxN;
      const bsPrice = bsAll(S0, K, r, 0, sig, T).call;
      const ns = [], prices = [];
      for (let n = 1; n <= maxN; n++) { ns.push(n); prices.push(crrBinomial(S0, K, r, sig, T, n, true)); }
      const last = prices[prices.length - 1];
      el.querySelector('#l2-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">Black–Scholes Call</span><span class="v">${bsPrice.toFixed(4)}</span></div>
        <div class="lab-metric"><span class="k">CRR (N=${maxN})</span><span class="v">${last.toFixed(4)}</span></div>
        <div class="lab-metric"><span class="k">Absolute Error</span><span class="v">${Math.abs(last - bsPrice).toFixed(5)}</span></div>`;
      Plotly.newPlot('l2-plot', [
        { x: ns, y: prices, name: 'CRR Binomial Price', mode: 'lines+markers', marker: { size: 4 }, line: { color: '#1D4ED8', width: 1.8 } },
        { x: [1, maxN], y: [bsPrice, bsPrice], name: 'Black–Scholes Limit', line: { color: '#DC2626', width: 2.2, dash: 'dash' } }
      ], plotLayout('Odd–Even Oscillation & Convergence of CRR Tree', 'Number of Steps N', 'Call Price ($)'), plotConfig);
    }
    el.querySelectorAll('input').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 3: Fractional Brownian Motion & Quadratic Variation (Ch 3) ---
  function mountLab3(el) {
    let seed = 42;
    el.innerHTML = `
      <div class="lab-header">
        <div><span class="lab-badge">Interactive Lab 3</span><span class="lab-title">Fractional Brownian Motion W^H &amp; Quadratic Variation</span></div>
        <button class="btn-pill" id="l3-resample">Resample path</button>
      </div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Hurst Parameter H <span class="val" id="l3-H-v">0.50</span></label><input id="l3-H" type="range" min="0.10" max="0.88" step="0.02" value="0.50"></div>
          <div class="lab-control"><label>Grid Points N <span class="val" id="l3-N-v">120</span></label><input id="l3-N" type="range" min="40" max="180" step="20" value="120"></div>
        </div>
        <div class="lab-metrics" id="l3-metrics"></div>
        <div id="l3-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const H = +el.querySelector('#l3-H').value;
      const N = +el.querySelector('#l3-N').value;
      el.querySelector('#l3-H-v').textContent = H.toFixed(2);
      el.querySelector('#l3-N-v').textContent = N;
      const { t, w, qv } = simulateFBM(H, N, seed);
      const corr = Math.pow(2, 2 * H - 1) - 1;
      const regime = H < 0.48 ? 'Rough (Anti-persistent)' : (H > 0.52 ? 'Persistent (Long-memory)' : 'Standard Brownian');
      el.querySelector('#l3-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">Regime</span><span class="v">${regime}</span></div>
        <div class="lab-metric"><span class="k">Cov(W_1^H, W_2^H-W_1^H)</span><span class="v">${corr.toFixed(3)}</span></div>
        <div class="lab-metric"><span class="k">Sample QV at t=1</span><span class="v">${qv[qv.length - 1].toFixed(3)}</span></div>`;
      Plotly.newPlot('l3-plot', [
        { x: t, y: w, name: `Path W^H (H=${H.toFixed(2)})`, line: { color: '#1D4ED8', width: 1.9 } },
        { x: t, y: qv, name: 'Cumulative Quadratic Variation', yaxis: 'y2', line: { color: '#0D9488', width: 2, dash: 'dot' } }
      ], plotLayout('Sample Path & Realized Quadratic Variation', 'Time t', 'W_t^H', {
        yaxis2: { title: 'Quadratic Variation', overlaying: 'y', side: 'right', showgrid: false }
      }), plotConfig);
    }
    el.querySelector('#l3-resample').addEventListener('click', () => { seed += 7; update(); });
    el.querySelectorAll('input').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 4: Black-Scholes & 1st/2nd-Order Greeks Dashboard (Ch 4) ---
  function mountLab4(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 4</span><span class="lab-title">Black–Scholes Pricing &amp; Greeks (incl. Vanna &amp; Volga)</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Curve to Plot</label>
            <select id="l4-metric">
              <option value="price">Call &amp; Put Prices</option>
              <option value="delta">Delta (∂V/∂S)</option>
              <option value="gamma">Gamma (∂²V/∂S²)</option>
              <option value="vega">Vega (∂V/∂σ)</option>
              <option value="vanna">Vanna (∂²V/∂S∂σ)</option>
              <option value="volga">Volga / Vomma (∂²V/∂σ²)</option>
            </select>
          </div>
          <div class="lab-control"><label>Volatility σ <span class="val" id="l4-sig-v">20%</span></label><input id="l4-sig" type="range" min="0.05" max="0.60" step="0.01" value="0.20"></div>
          <div class="lab-control"><label>Maturity T <span class="val" id="l4-T-v">0.50y</span></label><input id="l4-T" type="range" min="0.02" max="2.00" step="0.02" value="0.50"></div>
          <div class="lab-control"><label>Rate r <span class="val" id="l4-r-v">5%</span></label><input id="l4-r" type="range" min="-0.02" max="0.12" step="0.01" value="0.05"></div>
        </div>
        <div class="lab-metrics" id="l4-metrics"></div>
        <div id="l4-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const K = 100, q = 0;
      const metric = el.querySelector('#l4-metric').value;
      const sig = +el.querySelector('#l4-sig').value;
      const T = +el.querySelector('#l4-T').value;
      const r = +el.querySelector('#l4-r').value;
      el.querySelector('#l4-sig-v').textContent = (sig * 100).toFixed(0) + '%';
      el.querySelector('#l4-T-v').textContent = T.toFixed(2) + 'y';
      el.querySelector('#l4-r-v').textContent = (r * 100).toFixed(0) + '%';
      const atm = bsAll(100, K, r, q, sig, T);
      el.querySelector('#l4-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">ATM Call</span><span class="v">${atm.call.toFixed(3)}</span></div>
        <div class="lab-metric"><span class="k">Delta</span><span class="v">${atm.deltaC.toFixed(3)}</span></div>
        <div class="lab-metric"><span class="k">Gamma</span><span class="v">${atm.gamma.toFixed(4)}</span></div>
        <div class="lab-metric"><span class="k">Vega</span><span class="v">${atm.vega.toFixed(2)}</span></div>
        <div class="lab-metric"><span class="k">Vanna</span><span class="v">${atm.vanna.toFixed(3)}</span></div>
        <div class="lab-metric"><span class="k">Volga</span><span class="v">${atm.volga.toFixed(2)}</span></div>`;
      const S = [], y1 = [], y2 = [];
      for (let s = 55; s <= 145; s += 1) {
        S.push(s);
        const g = bsAll(s, K, r, q, sig, T);
        if (metric === 'price') { y1.push(g.call); y2.push(g.put); }
        else if (metric === 'delta') { y1.push(g.deltaC); y2.push(g.deltaP); }
        else if (metric === 'gamma') { y1.push(g.gamma); }
        else if (metric === 'vega') { y1.push(g.vega); }
        else if (metric === 'vanna') { y1.push(g.vanna); }
        else { y1.push(g.volga); }
      }
      const traces = [{ x: S, y: y1, name: metric === 'price' ? 'Call Price' : (metric === 'delta' ? 'Call Delta' : metric.toUpperCase()), line: { color: '#1D4ED8', width: 2.5 } }];
      if (y2.length) traces.push({ x: S, y: y2, name: metric === 'price' ? 'Put Price' : 'Put Delta', line: { color: '#0D9488', width: 2.2, dash: 'dash' } });
      Plotly.newPlot('l4-plot', traces, plotLayout(`Black–Scholes ${metric.toUpperCase()} vs. Spot (K = 100)`, 'Spot Price S', metric.toUpperCase()), plotConfig);
    }
    el.querySelectorAll('input,select').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 5: SVI Implied Volatility Smile & Rough Volatility Skew (Ch 5) ---
  function mountLab5(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 5</span><span class="lab-title">SVI Implied Volatility Smile &amp; Rough Volatility Skew</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>SVI Slope b <span class="val" id="l5-b-v">0.12</span></label><input id="l5-b" type="range" min="0.02" max="0.30" step="0.01" value="0.12"></div>
          <div class="lab-control"><label>Skew ρ <span class="val" id="l5-rho-v">-0.65</span></label><input id="l5-rho" type="range" min="-0.95" max="0.50" step="0.05" value="-0.65"></div>
          <div class="lab-control"><label>Curvature σ_svi <span class="val" id="l5-s-v">0.15</span></label><input id="l5-s" type="range" min="0.03" max="0.40" step="0.01" value="0.15"></div>
          <div class="lab-control"><label>Rough Hurst H <span class="val" id="l5-H-v">0.10</span></label><input id="l5-H" type="range" min="0.05" max="0.50" step="0.05" value="0.10"></div>
        </div>
        <div id="l5-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const a = 0.03, m = 0.0, T = 1.0;
      const b = +el.querySelector('#l5-b').value;
      const rho = +el.querySelector('#l5-rho').value;
      const s = +el.querySelector('#l5-s').value;
      const H = +el.querySelector('#l5-H').value;
      el.querySelector('#l5-b-v').textContent = b.toFixed(2);
      el.querySelector('#l5-rho-v').textContent = rho.toFixed(2);
      el.querySelector('#l5-s-v').textContent = s.toFixed(2);
      el.querySelector('#l5-H-v').textContent = H.toFixed(2);
      const ks = [], iv = [];
      for (let k = -0.60; k <= 0.45; k += 0.015) {
        const w = Math.max(a + b * (rho * (k - m) + Math.sqrt((k - m) * (k - m) + s * s)), 1e-5);
        ks.push(k);
        iv.push(100 * Math.sqrt(w / T));
      }
      const Ts = [], skewRough = [], skewMark = [];
      for (let tau = 0.01; tau <= 1.0; tau += 0.015) {
        Ts.push(tau);
        skewRough.push(0.22 * Math.pow(tau, H - 0.5));
        skewMark.push(0.22 / (1 + 1.5 * tau));
      }
      Plotly.newPlot('l5-plot', [
        { x: ks, y: iv, name: 'SVI Implied Vol (%)', xaxis: 'x', yaxis: 'y', line: { color: '#1D4ED8', width: 2.5 } },
        { x: Ts, y: skewRough, name: `Rough Skew ~ T^(H-0.5) (H=${H.toFixed(2)})`, xaxis: 'x2', yaxis: 'y2', line: { color: '#DC2626', width: 2.3 } },
        { x: Ts, y: skewMark, name: 'Classical SV Skew O(1)', xaxis: 'x2', yaxis: 'y2', line: { color: '#0D9488', width: 2, dash: 'dash' } }
      ], plotLayout('Raw SVI Smile (Left) & Short-Dated ATM Skew Scaling (Right)', 'Log-Moneyness k = ln(K/F)', 'Implied Vol (%)', {
        grid: { rows: 1, columns: 2, pattern: 'independent' },
        xaxis: { title: 'Log-Moneyness k', domain: [0, 0.46] },
        xaxis2: { title: 'Maturity T (years)', domain: [0.54, 1.0] },
        yaxis2: { title: 'ATM Skew |∂σ/∂k|', anchor: 'x2' }
      }), plotConfig);
    }
    el.querySelectorAll('input').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 6: Barrier Options & BGK Discrete Monitoring Correction (Ch 6) ---
  function mountLab6(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 6</span><span class="lab-title">Barrier Options, In–Out Parity &amp; BGK Discrete Correction</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Barrier Type</label>
            <select id="l6-type">
              <option value="up">Up-and-Out / Up-and-In Call (B &gt; K)</option>
              <option value="down">Down-and-Out / Down-and-In Call (B &le; K)</option>
            </select>
          </div>
          <div class="lab-control"><label>Barrier Level B <span class="val" id="l6-B-v">120</span></label><input id="l6-B" type="range" min="70" max="140" step="2" value="120"></div>
          <div class="lab-control"><label>Monitoring Frequency</label>
            <select id="l6-freq">
              <option value="0">Continuous</option>
              <option value="252">Daily (M = 252)</option>
              <option value="52">Weekly (M = 52)</option>
              <option value="12">Monthly (M = 12)</option>
            </select>
          </div>
        </div>
        <div class="lab-metrics" id="l6-metrics"></div>
        <div id="l6-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const K = 100, r = 0.05, sig = 0.20, T = 1.0, beta = 0.5826;
      const type = el.querySelector('#l6-type').value;
      const B = +el.querySelector('#l6-B').value;
      const M = +el.querySelector('#l6-freq').value;
      el.querySelector('#l6-B-v').textContent = B;
      const Badj = M > 0 ? B * Math.exp((type === 'up' ? 1 : -1) * beta * sig * Math.sqrt(T / M)) : B;
      const ref = barrierCalls(100, K, Badj, r, sig, T, type);
      el.querySelector('#l6-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">Effective Barrier B_adj</span><span class="v">${Badj.toFixed(2)}</span></div>
        <div class="lab-metric"><span class="k">Vanilla Call (S=100)</span><span class="v">${ref.vanilla.toFixed(4)}</span></div>
        <div class="lab-metric"><span class="k">Knock-Out (S=100)</span><span class="v">${ref.outPrice.toFixed(4)}</span></div>
        <div class="lab-metric"><span class="k">Knock-In (S=100)</span><span class="v">${ref.inPrice.toFixed(4)}</span></div>`;
      const S = [], vArr = [], outArr = [], inArr = [];
      for (let s = 60; s <= 145; s += 1) {
        S.push(s);
        const res = barrierCalls(s, K, Badj, r, sig, T, type);
        vArr.push(res.vanilla); outArr.push(res.outPrice); inArr.push(res.inPrice);
      }
      Plotly.newPlot('l6-plot', [
        { x: S, y: vArr, name: 'Vanilla Call', line: { color: '#64748B', width: 1.8, dash: 'dot' } },
        { x: S, y: outArr, name: type === 'up' ? 'Up-and-Out Call' : 'Down-and-Out Call', line: { color: '#1D4ED8', width: 2.5 } },
        { x: S, y: inArr, name: type === 'up' ? 'Up-and-In Call' : 'Down-and-In Call', line: { color: '#0D9488', width: 2.2, dash: 'dash' } }
      ], plotLayout(`Barrier Call Profiles (K = 100, B_adj = ${Badj.toFixed(2)})`, 'Spot Price S_0', 'Option Price ($)'), plotConfig);
    }
    el.querySelectorAll('input,select').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 7: Perpetual American Put Free Boundary & Smooth Pasting (Ch 7) ---
  function mountLab7(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 7</span><span class="lab-title">Perpetual American Put: Free Boundary S* &amp; Smooth Pasting</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Strike K <span class="val" id="l7-K-v">100</span></label><input id="l7-K" type="range" min="70" max="130" step="5" value="100"></div>
          <div class="lab-control"><label>Rate r <span class="val" id="l7-r-v">5%</span></label><input id="l7-r" type="range" min="0.01" max="0.12" step="0.005" value="0.05"></div>
          <div class="lab-control"><label>Volatility σ <span class="val" id="l7-sig-v">20%</span></label><input id="l7-sig" type="range" min="0.10" max="0.50" step="0.02" value="0.20"></div>
        </div>
        <div class="lab-metrics" id="l7-metrics"></div>
        <div id="l7-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const K = +el.querySelector('#l7-K').value;
      const r = +el.querySelector('#l7-r').value;
      const sig = +el.querySelector('#l7-sig').value;
      el.querySelector('#l7-K-v').textContent = K;
      el.querySelector('#l7-r-v').textContent = (r * 100).toFixed(1) + '%';
      el.querySelector('#l7-sig-v').textContent = (sig * 100).toFixed(0) + '%';
      const gamma = (2 * r) / (sig * sig);
      const Sstar = (gamma / (1 + gamma)) * K;
      const valAtStar = K - Sstar;
      el.querySelector('#l7-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">Exponent γ = 2r/σ²</span><span class="v">${gamma.toFixed(3)}</span></div>
        <div class="lab-metric"><span class="k">Optimal Boundary S*</span><span class="v">${Sstar.toFixed(2)}</span></div>
        <div class="lab-metric"><span class="k">P_∞(S*) = K - S*</span><span class="v">${valAtStar.toFixed(2)}</span></div>
        <div class="lab-metric"><span class="k">ATM Value P_∞(K)</span><span class="v">${((K / (1 + gamma)) * Math.pow(Sstar / K, gamma)).toFixed(2)}</span></div>`;
      const S = [], pInf = [], intr = [];
      for (let s = 30; s <= 150; s += 1) {
        S.push(s);
        intr.push(Math.max(K - s, 0));
        pInf.push(s <= Sstar ? K - s : (K / (1 + gamma)) * Math.pow(Sstar / s, gamma));
      }
      Plotly.newPlot('l7-plot', [
        { x: S, y: pInf, name: 'Perpetual American Put P_∞(S)', line: { color: '#1D4ED8', width: 2.6 } },
        { x: S, y: intr, name: 'Intrinsic Payoff (K - S)⁺', line: { color: '#64748B', width: 1.8, dash: 'dash' } },
        { x: [Sstar], y: [valAtStar], name: `Smooth-Pasting Point S* = ${Sstar.toFixed(1)}`, mode: 'markers', marker: { color: '#DC2626', size: 10 } }
      ], plotLayout('Smooth-Pasting Tangency at the Free Boundary S*', 'Spot Price S', 'Put Value ($)'), plotConfig);
    }
    el.querySelectorAll('input').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  // --- Lab 8: CIR Yield Curve & CDS Par Spread Explorer (Ch 8) ---
  function mountLab8(el) {
    el.innerHTML = `
      <div class="lab-header"><div><span class="lab-badge">Interactive Lab 8</span><span class="lab-title">CIR Affine Yield Curve (Feller Condition) &amp; CDS Par Spread</span></div></div>
      <div class="lab-body">
        <div class="lab-controls">
          <div class="lab-control"><label>Initial Rate r_0 <span class="val" id="l8-r0-v">3.0%</span></label><input id="l8-r0" type="range" min="0.005" max="0.08" step="0.005" value="0.03"></div>
          <div class="lab-control"><label>Long-Run Mean θ <span class="val" id="l8-th-v">5.0%</span></label><input id="l8-th" type="range" min="0.01" max="0.09" step="0.005" value="0.05"></div>
          <div class="lab-control"><label>CIR Vol σ <span class="val" id="l8-sig-v">10%</span></label><input id="l8-sig" type="range" min="0.02" max="0.30" step="0.01" value="0.10"></div>
          <div class="lab-control"><label>Hazard Rate λ <span class="val" id="l8-lam-v">2.0%</span></label><input id="l8-lam" type="range" min="0.005" max="0.08" step="0.005" value="0.02"></div>
          <div class="lab-control"><label>Recovery R <span class="val" id="l8-R-v">40%</span></label><input id="l8-R" type="range" min="0.10" max="0.80" step="0.05" value="0.40"></div>
        </div>
        <div class="lab-metrics" id="l8-metrics"></div>
        <div id="l8-plot" class="lab-plot"></div>
      </div>`;
    function update() {
      const kappa = 0.40;
      const r0 = +el.querySelector('#l8-r0').value;
      const theta = +el.querySelector('#l8-th').value;
      const sig = +el.querySelector('#l8-sig').value;
      const lam = +el.querySelector('#l8-lam').value;
      const R = +el.querySelector('#l8-R').value;
      el.querySelector('#l8-r0-v').textContent = (r0 * 100).toFixed(1) + '%';
      el.querySelector('#l8-th-v').textContent = (theta * 100).toFixed(1) + '%';
      el.querySelector('#l8-sig-v').textContent = (sig * 100).toFixed(0) + '%';
      el.querySelector('#l8-lam-v').textContent = (lam * 100).toFixed(1) + '%';
      el.querySelector('#l8-R-v').textContent = (R * 100).toFixed(0) + '%';
      const fellerRatio = (2 * kappa * theta) / (sig * sig);
      const h = Math.sqrt(kappa * kappa + 2 * sig * sig);
      const Ts = [], yCIR = [], yCredit = [];
      for (let T = 0.25; T <= 30; T += 0.5) {
        const expHT = Math.exp(h * T);
        const denom = 2 * h + (kappa + h) * (expHT - 1);
        const B = (2 * (expHT - 1)) / denom;
        const A = ((2 * kappa * theta) / (sig * sig)) * Math.log((2 * h * Math.exp(0.5 * (kappa + h) * T)) / denom);
        const y = -(A - B * r0) / T;
        Ts.push(T);
        yCIR.push(100 * y);
        yCredit.push(100 * (y + lam * (1 - R)));
      }
      const parCDSbps = 10000 * lam * (1 - R);
      el.querySelector('#l8-metrics').innerHTML = `
        <div class="lab-metric"><span class="k">Feller 2κθ/σ²</span><span class="v">${fellerRatio.toFixed(2)} (${fellerRatio >= 1 ? 'r>0 a.s.' : 'hits 0'})</span></div>
        <div class="lab-metric"><span class="k">10Y Risk-Free Yield</span><span class="v">${yCIR[19].toFixed(2)}%</span></div>
        <div class="lab-metric"><span class="k">Approx. Par CDS Spread</span><span class="v">${parCDSbps.toFixed(0)} bps</span></div>`;
      Plotly.newPlot('l8-plot', [
        { x: Ts, y: yCIR, name: 'CIR Risk-Free Zero Yield (%)', line: { color: '#1D4ED8', width: 2.5 } },
        { x: Ts, y: yCredit, name: 'Credit-Risky Yield (+ λ(1-R))', line: { color: '#DC2626', width: 2.2, dash: 'dash' } }
      ], plotLayout('CIR Term Structure & Credit-Spread Adjusted Yield Curve', 'Maturity T (years)', 'Continuously Compounded Yield (%)'), plotConfig);
    }
    el.querySelectorAll('input').forEach(i => i.addEventListener('input', update));
    update(); activeUpdaters.push(update);
  }

  window.initQuantLabs = function () {
    const map = {
      'lab-1': mountLab1, 'lab-2': mountLab2, 'lab-3': mountLab3, 'lab-4': mountLab4,
      'lab-5': mountLab5, 'lab-6': mountLab6, 'lab-7': mountLab7, 'lab-8': mountLab8
    };
    Object.entries(map).forEach(([id, fn]) => {
      const el = document.getElementById(id);
      if (el) fn(el);
    });
    window.addEventListener('efd-theme-change', () => activeUpdaters.forEach(u => u()));
  };
})();
