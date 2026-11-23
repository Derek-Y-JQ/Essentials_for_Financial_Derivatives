"""Companion Python code extracted from chapters/ch03_math_preliminaries.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
import numpy as np
def wiener_process(T, N):
    dt = T / N
    dW = np.sqrt(dt) * np.random.randn(N)
    W = np.cumsum(dW)
    return W

# --- Snippet 2 ---
def quadratic_variation(path):
    return np.cumsum(np.diff(path, prepend=path[0]) ** 2)


n = 1000
W = wiener_process(1, n)  # Use the function defined above
QV_W = quadratic_variation(W)


def quadratic_variation_smooth(f):
    """Quadratic variation sum of squared increments (converges to 0 for C^1 paths)."""
    return quadratic_variation(f)


def a_smooth_function(t):
    return np.sin(2 * np.pi * t) + np.exp(-t * np.cos(2 * np.pi * t))


time = np.linspace(0, 1, n)
f = a_smooth_function(time)
QV_f = quadratic_variation_smooth(f)

# --- Snippet 3 ---
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
BM = wiener_process(1, 1000)
def find_simple_process(process,n):
    t_points = np.linspace(0, 1, n)
    simple_process = np.zeros(n)
    for i in range(n):
        simple_process[i] = process[int(i*process.shape[0]/n)]
    return simple_process,t_points

steps=[10,25,50,100]
plt.figure(figsize=(10, 6))
sns.lineplot(x=np.linspace(0, 1, 1000), y=BM, label='Brownian Motion',color='skyblue',alpha=0.7)
for n in steps:
    simple_process,t_points = find_simple_process(BM,n)
    plt.step(t_points, simple_process, where='post',label=f'Simple Process with n={n}')
plt.xlabel('Time t')
plt.ylabel('$X_t$')
plt.title('Simple Process to Brownian Motion')
plt.legend()
plt.grid(True)
plt.show()

