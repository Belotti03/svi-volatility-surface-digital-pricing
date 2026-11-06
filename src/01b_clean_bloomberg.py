import os
import numpy as np
import pandas as pd

def parse_bloomberg_omon(file_path: str, target_expiry: str) -> pd.DataFrame:
    """
    Parses a raw Bloomberg OMON (Option Monitor) Excel export and standardizes 
    the options chain for a specific expiration date.
    
    Parameters
    ----------
    file_path : str
        Absolute or relative path to the raw Bloomberg Excel file.
    target_expiry : str
        String identifier for the target expiration (e.g., '19-Feb-27').
        
    Returns
    -------
    pd.DataFrame
        Cleaned dataset containing Strike, Type, Bid, Ask, and Mid prices.
    """
    df_raw = pd.read_excel(file_path, header=None)
    
    start_idx = None
    for idx, val in df_raw[0].items():
        if isinstance(val, str) and target_expiry in val:
            start_idx = idx
            break
            
    if start_idx is None:
        raise ValueError(f"Expiration '{target_expiry}' not found in the dataset.")
        
    data_rows = []
    for idx in range(start_idx + 1, len(df_raw)):
        val = df_raw.iloc[idx, 0]
        if pd.isna(val) or not isinstance(val, (int, float)):
            break
        data_rows.append(idx)
        
    df_block = df_raw.iloc[data_rows]
    
    calls = pd.DataFrame({
        'Strike': pd.to_numeric(df_block[0], errors='coerce'),
        'Type': 'Call',
        'Bid': pd.to_numeric(df_block[2], errors='coerce'),
        'Ask': pd.to_numeric(df_block[3], errors='coerce')
    })
    
    puts = pd.DataFrame({
        'Strike': pd.to_numeric(df_block[7], errors='coerce'),
        'Type': 'Put',
        'Bid': pd.to_numeric(df_block[9], errors='coerce'),
        'Ask': pd.to_numeric(df_block[10], errors='coerce')
    })
    
    df_clean = pd.concat([calls, puts], ignore_index=True)
    
    df_clean.dropna(subset=['Strike', 'Bid', 'Ask'], inplace=True)
    df_clean = df_clean[df_clean['Bid'] > 0.0].copy()
    df_clean['Mid'] = (df_clean['Bid'] + df_clean['Ask']) / 2.0
    
    df_clean.sort_values(by=['Type', 'Strike'], inplace=True)
    return df_clean

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, '..', 'data', 'raw', 'bloomberg_raw.xlsx')
    
    target_expiry = '19-Feb-27'
    
    print(f"Parsing raw Bloomberg data for expiry: {target_expiry}...")
    df_real = parse_bloomberg_omon(input_path, target_expiry)
    
    output_path = os.path.join(current_dir, '..', 'data', 'raw', 'real_options.csv')
    df_real.to_csv(output_path, index=False)
    
    print(f"Extraction successful. Processed {len(df_real)} liquid options contracts.")
    print(f"Standardized data saved to: {output_path}")

if __name__ == "__main__":
    main()