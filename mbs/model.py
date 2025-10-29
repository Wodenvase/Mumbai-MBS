import polars as pl
from typing import Dict

# Try to import Rust engine, fall back to Python implementation
try:
    import mbs_core
    USE_RUST = True
    print("✅ Using high-performance Rust engine for MBS calculations")
except ImportError:
    USE_RUST = False
    print("⚠️  Rust engine not available. Using pure Python implementation.")
    print("   To use the high-performance Rust engine:")
    print("   1. Accept Xcode license: sudo xcodebuild -license accept")
    print("   2. Build Rust engine: maturin develop")
    
    # Import fallback implementations
    from mbs.fallback import (
        aggregate_cash_flows_py,
        compute_mbs_metrics_py
    )

def aggregate_cash_flows(loans_df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate monthly cash flows for all loans using the best available engine."""
    if USE_RUST:
        return mbs_core.aggregate_cash_flows_py(loans_df)
    else:
        return aggregate_cash_flows_py(loans_df)

def compute_mbs_metrics(cash_flows_df: pl.DataFrame, discount_rate: float = 0.07) -> Dict:
    """Compute average life, Macaulay duration, and convexity using the best available engine."""
    if USE_RUST:
        return mbs_core.compute_mbs_metrics_py(cash_flows_df, discount_rate)
    else:
        return compute_mbs_metrics_py(cash_flows_df, discount_rate)

# Legacy functions for backward compatibility (converted to use DataFrame)
def aggregate_cash_flows_legacy(loans_df: pl.DataFrame) -> list:
    """Legacy function that returns list of dicts for backward compatibility."""
    cash_flows_df = aggregate_cash_flows(loans_df)
    return cash_flows_df.to_dicts()

def compute_mbs_metrics_legacy(cash_flows: list, discount_rate: float = 0.07) -> Dict:
    """Legacy function that accepts list of dicts for backward compatibility."""
    # Convert list to DataFrame
    cash_flows_df = pl.DataFrame(cash_flows)
    return compute_mbs_metrics(cash_flows_df, discount_rate) 