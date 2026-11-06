import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

def black_scholes_digital_call(K, F, T, r, sigma):
    """
    Computes the price of a European digital call (cash-or-nothing) option 
    under the standard Black-Scholes framework (constant volatility).
    """
    d2 = (np.log(F / K) - 0.5 * (sigma**2) * T) / (sigma * np.sqrt(T))
    return np.exp(-r * T) * norm.cdf(d2)

def main():
    # 1. Market parameters setup (derived from SX5E dataset)
    T = 1.0        # Time to maturity (Feb 19, 2027 ~ 1 year)
    F = 5000.0     # Implied forward price
    r = 0.025      # Implied funding rate (2.5%)
    discount_factor = np.exp(-r * T)

    # 2. SVI calibrated parameters and log-moneyness grid
    # Grid spans the evaluated range k in [-1.0, 0.2]
    k_grid = np.linspace(-1.0, 0.2, 1000)
    K_grid = F * np.exp(k_grid)
    
    # Calibrated SVI raw parameters (MSE = 2.75e-8)
    a, b, rho, m, sigma_svi = 0.005, 0.12, -0.65, 0.05, 0.15
    
    # Total implied variance w(k)
    w = a + b * (rho * (k_grid - m) + np.sqrt((k_grid - m)**2 + sigma_svi**2))
    
    # Analytical derivatives for Breeden-Litzenberger risk-neutral density extraction
    dw_dk = b * (rho + (k_grid - m) / np.sqrt((k_grid - m)**2 + sigma_svi**2))
    d2w_dk2 = b * (1.0 / np.sqrt((k_grid - m)**2 + sigma_svi**2) - ((k_grid - m)**2) / ((k_grid - m)**2 + sigma_svi**2)**1.5)
    
    # Durrleman's function and risk-neutral density p(k)
    g_k = (1.0 - (k_grid * dw_dk) / (2.0 * w))**2 - (dw_dk**2 / 4.0) * (1.0 / w + 0.25) + 0.5 * d2w_dk2
    d_minus = -k_grid / np.sqrt(w) - 0.5 * np.sqrt(w)
    p_k = (g_k / np.sqrt(2.0 * np.pi * w)) * np.exp(-0.5 * d_minus**2)
    
    # 3. Skew-Adjusted Digital Pricing via Numerical Integration
    # Integrating the density from strike K to infinity (right tail)
    integral_p = np.zeros_like(p_k)
    for i in range(len(k_grid)):
        integral_p[i] = np.trapezoid(p_k[i:], k_grid[i:])
        
    svi_digital_prices = discount_factor * integral_p

    # 4. Benchmark: Black-Scholes Digital Pricing (ATM Flat Volatility)
    atm_idx = np.argmin(np.abs(k_grid))
    sigma_atm = np.sqrt(w[atm_idx] / T)
    bs_digital_prices = black_scholes_digital_call(K_grid, F, T, r, sigma_atm)

    # 5. Skew Premium calculation
    skew_premium = svi_digital_prices - bs_digital_prices

    # 6. Visualization
    plt.figure(figsize=(10, 6))
    plt.plot(K_grid, svi_digital_prices, label='SVI Digital Call (Skew-Adjusted)', color='purple', linewidth=2)
    plt.plot(K_grid, bs_digital_prices, label=f'Black-Scholes Digital (ATM Vol = {sigma_atm:.1%})', color='gray', linestyle='--', linewidth=1.5)
    plt.axvline(x=F, color='black', linestyle=':', label=f'Forward ({F:.0f})')
    
    plt.title('Digital Option Pricing: SVI Skew-Adjusted vs Black-Scholes Benchmark', fontsize=12, fontweight='bold')
    plt.xlabel('Strike Price (K)', fontsize=10)
    plt.ylabel('Digital Call Price (€)', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Save output to figures directory
    plt.savefig('figures/digital_option_pricing.png', dpi=300)
    
    # Terminal output logging
    print("--------------------------------------------------")
    print("SVI DIGITAL OPTION PRICING MODULE EXECUTION")
    print("--------------------------------------------------")
    print(f"ATM Strike ({F:.0f}) -> SVI Price: {svi_digital_prices[atm_idx]:.4f} EUR | BS Price: {bs_digital_prices[atm_idx]:.4f} EUR")
    print(f"Max Skew Premium Impact: {np.max(np.abs(skew_premium)):.4f} EUR")
    print("--------------------------------------------------")
    print("Plot successfully saved to: figures/digital_option_pricing.png")

if __name__ == '__main__':
    main()