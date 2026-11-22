import numpy as np
import pandas as pd
import scipy.stats as stats
from config import SIM_KEYS, STAGES, THEORY_COLUMNS

def get_theoretical_stats(params: dict) -> pd.DataFrame:
    rows = {}
    
    for stage in STAGES:
        for metric in ("T", "C"):
            p = params[stage][metric]
            key = f"{metric}_{stage}"
            
            a = float(p["a"])
            b = float(p["b"])
            
            if p["dist"] == "uniform":
                dist = stats.uniform(loc=a, scale=b - a)
            else:
                c = float(p["c"])
                shape = (c - a) / (b - a)
                dist = stats.triang(c=shape, loc=a, scale=b - a)
                
            rows[key] = {
                "mean": float(dist.mean()),
                "var": float(dist.var()),
                "std": float(dist.std()),
                "p95": float(dist.ppf(0.95)),
                "p95_kind": "exact"
            }
            
    for metric in ("T", "C"):
        total_key = f"{metric}_total"
        
        mean_sum = sum(rows[f"{metric}_{stage}"]["mean"] for stage in STAGES)
        var_sum = sum(rows[f"{metric}_{stage}"]["var"] for stage in STAGES)
        std_sum = float(np.sqrt(var_sum))
        
        p95_val = float(stats.norm(loc=mean_sum, scale=std_sum).ppf(0.95))
        
        rows[total_key] = {
            "mean": mean_sum,
            "var": var_sum,
            "std": std_sum,
            "p95": p95_val,
            "p95_kind": "normal_approx"
        }
        
    df = pd.DataFrame.from_dict(rows, orient="index")
    df = df.reindex(index=list(SIM_KEYS), columns=list(THEORY_COLUMNS))
    
    return df


def analyze_simulation(sim_data: dict, max_days: float, max_budget: float) -> dict:
    t_arr = sim_data["T_total"]
    c_arr = sim_data["C_total"]
    
    return {
        "mean_T": float(np.mean(t_arr)),
        "std_T": float(np.std(t_arr)),
        "median_T": float(np.median(t_arr)),
        "p95_T": float(np.percentile(t_arr, 95)),
        "P_over_days": float(np.mean(t_arr > max_days)),
        
        "mean_C": float(np.mean(c_arr)),
        "std_C": float(np.std(c_arr)),
        "median_C": float(np.median(c_arr)),
        "p95_C": float(np.percentile(c_arr, 95)),
        "P_over_budget": float(np.mean(c_arr > max_budget)),
        
        "P_success": float(np.mean((t_arr <= max_days) & (c_arr <= max_budget)))
    }