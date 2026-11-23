"""Companion Python code extracted from chapters/ch04_black_scholes_model.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

class NumericMethod:
    def __init__(self, T, N, beta, U0=1.0):
        self.T = T
        self.N = N
        self.beta = beta
        self.U0 = U0
        self.dt = self.T / self.N
    
    def explicit_euler(self):
        t_values = np.arange(0, self.T + self.dt, self.dt)
        U_values = [self.U0]
        for i in range(1, len(t_values)):
            U_values.append(U_values[-1] + self.dt* self.beta * U_values[-1])
        return t_values, U_values

    def implicit_euler(self):
        t_values = np.arange(0, self.T + self.dt, self.dt)
        U_values = [self.U0]
        for i in range(1, len(t_values)):
            U_values.append(U_values[-1] / (1 - self.beta * self.dt))
        return t_values, U_values

    def crank_nicolson(self):
        t_values = np.arange(0, self.T + self.dt, self.dt)
        U_values = [self.U0]
        for i in range(1, len(t_values)):
            U_values.append(U_values[-1]* (1 + 0.5 * self.beta * self.dt) / (1 - 0.5 * self.beta * self.dt))
        return t_values, U_values

def plot_results(beta, Time, Num, method, ax, title):
    for i in range(len(Num)):
        problem = NumericMethod(Time, Num[i],beta=beta)
        if method == 'explicit':
            t_values, U_values = problem.explicit_euler()
        elif method == 'implicit':
            t_values, U_values = problem.implicit_euler()
        elif method == 'crank-nicolson':
            t_values, U_values = problem.crank_nicolson()
        # Smooth the curve
        t_smooth = np.linspace(t_values.min(), t_values.max(), 500)
        U_smooth = make_interp_spline(t_values, U_values)(t_smooth)
        ax.plot(t_smooth, U_smooth, label=f'N={Num[i]}')
        # Other settings

# --- Snippet 2 ---
from scipy.stats import norm
def bs_call_price(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

# --- Snippet 3 ---
import numpy as np
# Parameters
r, sigma, T, t0, K = 0.05, 0.2, 1.0, 0.0, 150
num_assets = 2  # number of assets
num_simulations = 10000  # number of Monte Carlo simulations

# Correlation matrix and Cholesky decomposition
corr_matrix = np.full((num_assets, num_assets), rho)
np.fill_diagonal(corr_matrix, 1.0)
L = np.linalg.cholesky(corr_matrix)

# Generate correlated random variables
np.random.seed(42)  # for reproducibility
Z_perp = np.random.normal(size=(num_assets, num_simulations))
Z = L @ Z_perp

# Define a grid of initial prices for asset 1 and asset 2
S1_range = np.linspace(0, 300, 100)
S2_range = np.linspace(0, 300, 100)
S1_grid, S2_grid = np.meshgrid(S1_range, S2_range)

# Calculate option prices for each combination of S1 and S2
def calculate_option_price(S_0):
    S_T = S_0[:, np.newaxis] * np.exp((r - 0.5 * sigma**2) * (T - t0) + sigma * np.sqrt(T - t0) * Z)
    payoff = np.maximum(np.sum(S_T, axis=0) - K, 0)
    option_price = np.exp(-r * (T - t0)) * np.mean(payoff) # Monte Carlo estimator
    return option_price

option_prices = np.array([[calculate_option_price(np.array([S1, S2])) for S1 in S1_range] for S2 in S2_range])
payoff = np.maximum(S1_grid + S2_grid - K, 0)

# --- Snippet 4 ---
class basket:
    def __init__(self, num_assets, S0, K, r, sigma, T, t0, rho, num_simulations):
        self.num_assets, self.S0, self.K, self.r, self.sigma, self.T, self.t0, self.rho, self.num_simulations = num_assets, S0, K, r, sigma, T, t0, rho, num_simulations
        
    def generate_Z(self):
        corr_matrix = np.full((self.num_assets, self.num_assets), self.rho)
        np.fill_diagonal(corr_matrix, 1.0)
        L = np.linalg.cholesky(corr_matrix)
        Z_perp = np.random.normal(size=(self.num_assets, self.num_simulations))
        Z = L @ Z_perp
        return Z
    
    def payoff(self):
        S_T = self.S0[:, np.newaxis] * np.exp((self.r - 0.5 * self.sigma**2) * (self.T - self.t0) + self.sigma * np.sqrt(self.T - self.t0) * self.generate_Z())
        M_0 = np.max(self.S0)
        M_T = np.max(S_T, axis=0)
        payoff_0 = np.maximum(M_0 - self.K, 0)
        payoff_T = np.maximum(M_T - self.K, 0)
        return [payoff_0, payoff_T]
    
    def price(self):
        payoff = self.payoff()[1]
        option_price = np.exp(-self.r * (self.T - self.t0)) * np.mean(payoff)
        return option_price

