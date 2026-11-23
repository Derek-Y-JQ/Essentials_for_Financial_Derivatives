"""Companion Python code extracted from chapters/ch01_introduction.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
import numpy as np
def forward_price(S0, r, T):
    return S0*np.exp(r*T)

