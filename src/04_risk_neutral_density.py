import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def svi_total_variance(k: np.ndarray, a: float, b: float, rho: float, m: float, sigma: float) -> np.ndarray:
    """
    Calculates the SVI total variance w(k).
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))

def black76_call(F: float, K: np.ndarray, T: float, r: float, vol: np.ndarray) -> np.ndarray:
    """
    Prices a European Call option using the Black-76 model.
    
    Parameters
    ----------
    F : float
        Forward price.
    K : np.ndarray
        Array of strike prices.
    T : float
        Time to maturity (in years).
    r : float
        Risk-free interest rate.
    vol : np.ndarray
        Array of implied volatilities corresponding to each strike.
        
    Returns
    -------
    np.ndarray
        European Call option prices.
    """
    d1 = (np.log(F / K) + 0.5 * vol**2 * T) / (vol * np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)
    return np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))

def main():
    # 1. Market constants derived from Put-Call Parity regression
    F = 5000.0
    r = 0.03
    T = 0.25
    
    # Calibrated SVI parameters from Step 3
    a_opt, b_opt, rho_opt, m_opt, sigma_opt = 0.0415, 0.0924, -0.7992, -0.0048, 0.0997
    
    # 2. Define a dense strike grid for numerical differentiation
    K_grid = np.linspace(3500, 6500, 1000)
    dK = K_grid[1] - K_grid[0]
    
    # 3. Compute continuous implied volatilities from the SVI model
    k_grid = np.log(K_grid / F)
    w_grid = svi_total_variance(k_grid, a_opt, b_opt, rho_opt, m_opt, sigma_opt)
    iv_grid = np.sqrt(w_grid / T)
    
    # 4. Generate theoretical Call prices across the grid
    call_prices = black76_call(F, K_grid, T, r, iv_grid)
    
    # 5. Breeden-Litzenberger: Second derivative via central finite differences
    # f(K) = exp(rT) * (C(K+dK) - 2C(K) + C(K-dK)) / (dK^2)
    d2C_dK2 = (call_prices[2:] - 2 * call_prices[1:-1] + call_prices[:-2]) / (dK**2)
    rnd = np.exp(r * T) * d2C_dK2
    
    # Align the grid size (first and last elements are dropped during differentiation)
    K_pdf = K_grid[1:-1]
    
    # 6. Butterfly Arbitrage Check
    min_density = np.min(rnd)
    is_arbitrage_free = min_density >= -1e-8  # Tolerance for microscopic numerical floating-point noise
    
    print("--- NO-ARBITRAGE CHECK ---")
    print(f"Minimum Density Value: {min_density:.2e}")
    print(f"Butterfly Arbitrage Free: {is_arbitrage_free}")
    
    # 7. Visualization
    plt.figure(figsize=(10, 6))
    plt.plot(K_pdf, rnd, color='purple', linewidth=2, label='Implied RND (Breeden-Litzenberger)')
    plt.fill_between(K_pdf, rnd, 0, color='purple', alpha=0.1)
    
    plt.axvline(x=F, color='black', linestyle='--', linewidth=1.5, label=f'Forward ({F:.0f})')
    
    plt.title('Risk-Neutral Density (RND) from Calibrated SVI', fontsize=14, fontweight='bold')
    plt.xlabel('Strike (K)', fontsize=12)
    plt.ylabel('Probability Density', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fig_dir = os.path.join(current_dir, '..', 'figures')
    os.makedirs(fig_dir, exist_ok=True)
    
    fig_path = os.path.join(fig_dir, 'risk_neutral_density.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"Density graph saved successfully in: {fig_path}")

if __name__ == "__main__":
    main()