"""Companion Python code extracted from chapters/ch05_implied_volatility.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
def volatility_smile(strike_prices, at_the_money_vol, skew, kurtosis):
    return at_the_money_vol * (1 + skew * (strike_prices - 100) / 100 + kurtosis * ((strike_prices - 100) / 100) ** 2)

