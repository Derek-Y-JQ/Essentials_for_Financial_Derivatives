"""Companion Python code extracted from chapters/ch02_discrete_time_models.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def binomial_tree(S, K, T, r, sigma, option_type="call", American = False, steps=100):
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))  # Up factor
    d = 1 / u  # Down factor
    p = (np.exp(r * dt) - d) / (u - d)  # Risk-neutral probability
    discount = np.exp(-r * dt) 
    
    # Initialize asset prices and option values
    asset_prices = np.zeros((steps + 1, steps + 1))
    option_values = np.zeros((steps + 1, steps + 1))
    
    for i in range(steps + 1):
        for j in range(i + 1):
            asset_prices[j, i] = S * (u ** (i - j)) * (d ** j)
    
    # Compute option values at expiration
    if option_type == "call":
        option_values[:, steps] = np.maximum(0, asset_prices[:, steps] - K)
    elif option_type == "put":
        option_values[:, steps] = np.maximum(0, K - asset_prices[:, steps])
    
    # Backward induction
    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            option_values[j, i] = discount * (p * option_values[j, i + 1] + (1 - p) * option_values[j + 1, i + 1])
            if American:
                # American option can be exercised at earlier time
                if option_type == "call":
                    option_values[j, i] = np.maximum(option_values[j, i], asset_prices[j, i] - K)
                elif option_type == "put":
                    option_values[j, i] = np.maximum(option_values[j, i], K - asset_prices[j, i])
    
    return asset_prices, option_values[0,0]

# Payoff functions
def payoff(S,K,option_type="call"):
    if option_type == "call":
        return np.maximum(S - K, 0)
    elif option_type == "put":
        return np.maximum(K - S, 0)

# Validate the binomial tree model
S = np.linspace(50, 150, 100)  
K = 100  
T = 1    
r = 0.05 
sigma = 0.2 
steps = 100  

# Calculate option prices and payoffs
call_prices = np.zeros(len(S))
put_prices = np.zeros(len(S))
for S0 in S:
    _, call_price = binomial_tree(S0, K, T, r, sigma, option_type="call", steps=steps)
    call_prices[np.where(S == S0)] = call_price

    _, put_price = binomial_tree(S0, K, T, r, sigma, option_type="put", steps=steps)
    put_prices[np.where(S == S0)] = put_price

call_payoffs = payoff(S, K)
put_payoffs = payoff(S, K, option_type="put")

plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
sns.lineplot(x=S, y=call_prices, label="Call Price", color="green")
sns.lineplot(x=S, y=call_payoffs, label="Call Payoff", linestyle="--", color="blue")
plt.title("Call Option Payoff and Pricing")

plt.subplot(1, 2, 2)
sns.lineplot(x=S, y=put_prices, label="Put Price", color="orange")
sns.lineplot(x=S, y=put_payoffs, label="Put Payoff", linestyle="--", color="blue")

plt.title("Put Option Payoff and Pricing")
plt.xlabel("Stock Price")
plt.ylabel("Payoff/Price")
plt.legend()

plt.show()

# --- Snippet 2 ---
import matplotlib.cm as cm
def plot_binomial_tree(tree, title):
    T = tree.shape[1] - 1
    fig, ax = plt.subplots()
    colors = cm.Blues(np.linspace(0.3, 1, T + 1))
    for t in range(T + 1):
        for i in range(t + 1):
            ax.plot(t, tree[i, t], 'o', color=colors[t], markersize=4)
            if t > 0:
                if i < t:
                    ax.plot([t - 1, t], [tree[i, t - 1], tree[i, t]], color=colors[t], linewidth=1)
                if i > 0:
                    ax.plot([t - 1, t], [tree[i - 1, t - 1], tree[i, t]], color=colors[t], linewidth=1)
    ax.set_xlabel('Time')
    ax.set_ylabel('Price of the underlying asset')
    ax.set_title(title)
    plt.show()

S0 = 100
asset_tree,_ = binomial_tree(S0, K, T, r, sigma, option_type="call", steps=20)
plot_binomial_tree(asset_tree, "Binomial Tree for Asset Prices")

# --- Snippet 3 ---
_, call_price = binomial_tree(S0, K, T, r, sigma, option_type="call", steps=steps, American=True)
_, put_price = binomial_tree(S0, K, T, r, sigma, option_type="put", steps=steps, American=True)

