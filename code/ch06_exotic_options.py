"""Companion Python code extracted from chapters/ch06_exotic_options.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
import numpy as np
from scipy.stats import norm


def standard_BSM_call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def down_and_in_call(S, K, B, T, r, sigma):
    """Down-and-in European call (assumes B <= K)."""
    if S <= B:
        return standard_BSM_call(S, K, T, r, sigma)
    alpha = (2 * r) / sigma ** 2 + 1
    return (B / S) ** (alpha - 2) * standard_BSM_call(B ** 2 / S, K, T, r, sigma)


def down_and_out_call(S, K, B, T, r, sigma):
    if S <= B:
        return 0.0
    return standard_BSM_call(S, K, T, r, sigma) - down_and_in_call(S, K, B, T, r, sigma)


K, B, T, r, sigma = 100, 80, 1.0, 0.05, 0.2
S_range = np.linspace(50, 150, 100)
call_prices_in = [down_and_in_call(S, K, B, T, r, sigma) for S in S_range]
call_prices_out = [down_and_out_call(S, K, B, T, r, sigma) for S in S_range]
vanilla_call_prices = [standard_BSM_call(S, K, T, r, sigma) for S in S_range]


# --- Snippet 2 ---
def asian_call(S0, K, r, sigma, T):
    """Closed-form continuous geometric Asian call at t=0."""
    mu = T * (r - 0.5 * sigma ** 2) / 2
    sigma_hat = sigma * np.sqrt(T) / np.sqrt(3)
    d2 = (np.log(S0 / K) + mu) / sigma_hat
    d1 = d2 + sigma_hat
    return (
        np.exp(-r * T) * S0 * np.exp(mu + 0.5 * sigma_hat ** 2) * norm.cdf(d1)
        - K * np.exp(-r * T) * norm.cdf(d2)
    )


# --- Snippet 3 ---
def simulate_geometric_brownian_motion(S0, r, sigma, T, N, M):
    """Simulate M paths of GBM over [0, T] with N steps."""
    dt = T / N
    paths = np.zeros((M, N + 1))
    paths[:, 0] = S0
    for t in range(1, N + 1):
        Z = np.random.standard_normal(M)
        paths[:, t] = paths[:, t - 1] * np.exp(
            (r - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * Z
        )
    return paths


def asian_call_simulate(St, r, sigma, tau, N, M, K):
    """Monte Carlo pricing of a freshly started geometric Asian call with maturity tau."""
    paths = simulate_geometric_brownian_motion(St, r, sigma, tau, N, M)
    geometric_average = np.exp(np.mean(np.log(paths[:, 1:]), axis=1))
    asian_call_payoff = np.maximum(geometric_average - K, 0.0)
    return np.exp(-r * tau) * np.mean(asian_call_payoff)

