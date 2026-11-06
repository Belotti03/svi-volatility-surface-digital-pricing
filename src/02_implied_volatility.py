import os
import numpy as np
import pandas as pd
from scipy.stats import norm, linregress
from scipy.optimize import brentq

def black76_price(F: float, K: float, T: float, r: float, vol: float, option_type: str) -> float:
    """
    Prices a European option using the Black-76 model.
    """
    d1 = (np.log(F / K) + 0.5 * vol**2 * T) / (vol * np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)
    df_discount = np.exp(-r * T)
    
    if option_type == 'Call':
        return df_discount * (F * norm.cdf(d1) - K * norm.cdf(d2))
    return df_discount * (K * norm.cdf(-d2) - F * norm.cdf(-d1))

def implied_vol_objective(vol: float, target_price: float, F: float, K: float, T: float, r: float, option_type: str) -> float:
    """
    Objective function for implied volatility root-finding.
    """
    return black76_price(F, K, T, r, vol, option_type) - target_price

def main():
    # 1. Load raw data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, '..', 'data', 'raw', 'real_options.csv')
    df = pd.read_csv(input_path)
    
    calls = df[df['Type'] == 'Call'][['Strike', 'Mid']].rename(columns={'Mid': 'Call_Mid'})
    puts = df[df['Type'] == 'Put'][['Strike', 'Mid']].rename(columns={'Mid': 'Put_Mid'})
    options = pd.merge(calls, puts, on='Strike')
    
    T = 0.25 
    
    # 2. Put-Call Parity Regression for Forward and Risk-Free Rate extraction
    Y = options['Call_Mid'] - options['Put_Mid']
    X = options['Strike']
    slope, intercept, r_value, p_value, std_err = linregress(X, Y)
    
    discount_factor = -slope
    implied_F = intercept / discount_factor
    implied_r = -np.log(discount_factor) / T
    
    print("--- PUT-CALL PARITY RESULTS ---")
    print(f"Implied Risk-Free Rate: {implied_r:.4%} (Target: 3.00%)")
    print(f"Implied Forward Price:  {implied_F:.2f} (Target: 5000.00)\n")
    
    # 3. Implied Volatility Extraction (OTM filtering)
    iv_results = []
    for _, row in options.iterrows():
        K = row['Strike']
        
        if K >= implied_F:
            opt_type = 'Call'
            target_price = row['Call_Mid']
        else:
            opt_type = 'Put'
            target_price = row['Put_Mid']
            
        try:
            iv = brentq(implied_vol_objective, 1e-4, 3.0, 
                        args=(target_price, implied_F, K, T, implied_r, opt_type))
            iv_results.append({
                'Strike': K,
                'Log_Moneyness': np.log(K / implied_F),
                'Implied_Vol': iv,
                'Total_Variance': iv**2 * T
            })
        except ValueError:
            pass
            
    df_iv = pd.DataFrame(iv_results)
    
    # 4. Save processed data
    output_dir = os.path.join(current_dir, '..', 'data')
    output_path = os.path.join(output_dir, 'implied_vols.csv')
    df_iv.to_csv(output_path, index=False)
    
    print("--- IMPLIED VOLATILITY EXTRACTION ---")
    print(f"Processed {len(df_iv)} valid strikes.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()