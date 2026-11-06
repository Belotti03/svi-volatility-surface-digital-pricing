import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt

def svi_total_variance(k: np.ndarray, a: float, b: float, rho: float, m: float, sigma: float) -> np.ndarray:
    """
    Calculates the total variance w(k) using the Stochastic Volatility Inspired (SVI) raw parameterization.
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))

def objective_function(params: tuple, k_market: np.ndarray, w_market: np.ndarray) -> float:
    """
    Mean Squared Error (MSE) objective function for SVI calibration.
    """
    a, b, rho, m, sigma = params
    w_model = svi_total_variance(k_market, a, b, rho, m, sigma)
    return np.mean((w_market - w_model)**2)

def main():
    # 1. Load implied volatilities
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, '..', 'data', 'implied_vols.csv')
    
    df = pd.read_csv(input_path)
    k_market = df['Log_Moneyness'].values
    w_market = df['Total_Variance'].values
    
    # 2. Optimization setup
    bounds = ((None, None), (1e-5, None), (-0.99, 0.99), (None, None), (1e-5, None))
    best_result = None
    best_mse = np.inf
    rho_guesses = [-0.8, -0.4, 0.0, 0.4, 0.8]
    
    # 3. Multi-Start Optimization
    for rho_guess in rho_guesses:
        initial_guess = [np.min(w_market), 0.1, rho_guess, 0.0, 0.1]
        result = minimize(
            objective_function, initial_guess, args=(k_market, w_market),
            method='SLSQP', bounds=bounds, options={'ftol': 1e-9, 'maxiter': 1000}
        )
        if result.success and result.fun < best_mse:
            best_mse = result.fun
            best_result = result
            
    if best_result is not None:
        a_opt, b_opt, rho_opt, m_opt, sigma_opt = best_result.x
        print(f"Multi-Start Optimization Successful. Lowest MSE: {best_mse:.2e}")
        
        # 4. Plotting the Volatility Smile
        plt.figure(figsize=(10, 6))
        plt.scatter(k_market, w_market, color='red', label='Market Implied Variance (Noisy)', zorder=5)
        
        k_continuous = np.linspace(min(k_market), max(k_market), 100)
        w_svi = svi_total_variance(k_continuous, a_opt, b_opt, rho_opt, m_opt, sigma_opt)
        
        plt.plot(k_continuous, w_svi, color='blue', linewidth=2, label='Calibrated SVI Curve')
        plt.title('SVI Calibration Fit vs Market Data', fontsize=14, fontweight='bold')
        plt.xlabel('Log-Moneyness (k = ln(K/F))', fontsize=12)
        plt.ylabel('Total Variance (w)', fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # 5. Save the figure
        fig_dir = os.path.join(current_dir, '..', 'figures')
        os.makedirs(fig_dir, exist_ok=True)
        fig_path = os.path.join(fig_dir, 'svi_smile_fit.png')
        
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved successfully in: {fig_path}")
    else:
        print("All optimization attempts failed.")

if __name__ == "__main__":
    main()