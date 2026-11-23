# Essentials for Financial Derivatives

[![Web Edition](https://img.shields.io/badge/Web_Edition-GitHub_Pages-1D4ED8?style=flat-square)](https://derek-y-jq.github.io/Essentials_for_Financial_Derivatives/)
[![PDF Edition](https://img.shields.io/badge/PDF-183_Pages_(Libertinus)-0F172A?style=flat-square)](Essentials_for_Financial_Derivatives.pdf)
[![LaTeX](https://img.shields.io/badge/Typeset-XeLaTeX_%2B_Libertinus_Math-0D9488?style=flat-square)](#building-from-source)

A rigorous, self-contained monograph on **Mathematical Finance and Financial Derivatives**, bridging classical no-arbitrage pricing theory with modern quantitative desk practice and contemporary research frontiers.

- **Read Online (Interactive Web Edition):** [derek-y-jq.github.io/Essentials_for_Financial_Derivatives](https://derek-y-jq.github.io/Essentials_for_Financial_Derivatives/) — includes **8 interactive quantitative labs** (Payoffs, CRR Convergence, Fractional Brownian Motion, Black–Scholes & 2nd-order Greeks, SVI/Rough Volatility, Barrier/BGK Correction, Perpetual American Free Boundary, and CIR/Vasicek Yield Curves & CDS).
- **Download PDF Edition:** [Essentials_for_Financial_Derivatives.pdf](Essentials_for_Financial_Derivatives.pdf) — 183 pages, typeset in the **Libertinus** family (Serif, Sans, Mono, and Math) via XeLaTeX.
- **Companion Python Scripts:** See [`code/`](code/README.md) for runnable numerical experiments separated cleanly from the mathematical text.

---

## Table of Contents

| Chapter / Appendix | Topic | Key Highlights & Modern Extensions |
|---|---|---|
| **Chapter 1** | [Introduction](chapters/ch01_introduction.tex) | No-arbitrage, dividend cost-of-carry, Forwards vs. Futures & CCPs, Put–Call Parity, **0DTE options** & intraday Gamma |
| **Chapter 2** | [Discrete Time Models](chapters/ch02_discrete_time_models.tex) | Multi-period self-financing replication, CRR trees, **Discrete FTAP 1 & 2**, dividends & negative-rate early exercise |
| **Chapter 3** | [Math Preliminaries](chapters/ch03_math_preliminaries.tex) | Brownian motion, Itô calculus, multi-D Itô, Girsanov, Feynman–Kac, **Merton jump-diffusion**, **Fractional Brownian Motion ($W^H$)** |
| **Chapter 4** | [Black–Scholes Model](chapters/ch04_black_scholes_model.tex) | PDE & log-space FD (**Rannacher stepping**), 1st & 2nd-order Greeks (**Vanna, Volga, Charm**), Black (1976), **Deep Hedging** |
| **Chapter 5** | [Implied Volatility Skew (Smile)](chapters/ch05_implied_volatility.tex) | Static no-arbitrage, Breeden–Litzenberger, **SVI / SSVI**, Dupire, Heston/SABR, **Rough Volatility (rBergomi / Rough Heston)**, **LSV**, **Variance Swaps & VIX** |
| **Chapter 6** | [Exotic Options](chapters/ch06_exotic_options.tex) | Digital options & **Pin Risk / Call-Spread Overhedging**, Barrier options & **BGK discrete correction**, **Autocallables / Snowballs**, Asian (**Kemna–Vorst CV**), Lookback, FX & Quanto |
| **Chapter 7** | [American Options](chapters/ch07_american_options.tex) | Snell envelope, LCP & smooth pasting, perpetual Put & dividend Call, **PSOR**, **Longstaff–Schwartz (LSM)**, **Deep Optimal Stopping** |
| **Chapter 8** | [Interest Rate Modelling](chapters/ch08_interest_rate_modelling.tex) | Ho–Lee, Vasicek, **CIR (Feller)**, **HJM**, **Bachelier / Shifted Lognormal**, **Post-LIBOR SOFR & OIS Multi-Curve**, **FMM**, **ISDA CDS & XVA (CVA/DVA/FVA)** |
| **Chapter 9** | [Problem Set](chapters/ch09_problem_set.tex) | 21 analytical and numerical exercises spanning discrete trees, stochastic calculus, PDEs, Monte Carlo, and FX vol bootstrapping |
| **Appendices A–E** | Mathematical & Reference Appendices | Measure-theoretic expectation & conditioning (A), **Monte Carlo, SDE Schemes, Variance Reduction & QMC** (B), Alternative BS PDE (C), **Proofs of Key Stochastic Calculus Theorems: SDE Well-Posedness, MRT & Girsanov** (D), English–Chinese Glossary (E) |

---

## Repository Structure

```text
.
├── main.tex                     # Master LaTeX entry point
├── outline.tex                  # Preamble (Libertinus Serif/Sans/Mono/Math, macros, theorem styles)
├── chapters/                    # Modular chapter & appendix .tex sources (14 files)
├── Figure/                      # Vector & raster diagrams referenced in the book
├── code/                        # Companion Python scripts (kept separate from textbook prose)
├── scripts/build_web.py         # LaTeX-to-HTML static site generator for the web edition
├── docs/                        # Generated GitHub Pages interactive web textbook
├── Makefile                     # One-command PDF and web edition build
└── Essentials_for_Financial_Derivatives.pdf
```

---

## Building from Source

### 1. Build the PDF (requires TeX Live with `xelatex` and Libertinus fonts)
```bash
make pdf
```

### 2. Rebuild the Interactive Web Edition (`docs/`)
```bash
make web
```
Then open `docs/index.html` in a browser (or serve locally with `python3 -m http.server -d docs 8000`).

---

## Author

**Junqi Yin (YIN JUNQI)** — National University of Singapore.
