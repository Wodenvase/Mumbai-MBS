import polars as pl

# Try to import Rust engine, fall back to Python implementation
try:
    import mbs_core
    USE_RUST = True
except ImportError:
    USE_RUST = False
    # Import fallback implementations
    from mbs.fallback import (
        apply_rbi_rate_shift_py,
        apply_price_shock_py,
        apply_zone_default_surge_py
    )

def apply_rbi_rate_shift(loans_df: pl.DataFrame, rate_shift: float) -> pl.DataFrame:
    """Apply an RBI rate shift (in percentage points) to all loans' interest rates."""
    if USE_RUST:
        return mbs_core.apply_rbi_rate_shift_py(loans_df, rate_shift)
    else:
        return apply_rbi_rate_shift_py(loans_df, rate_shift)

def apply_price_shock(loans_df: pl.DataFrame, appreciation_shift: float) -> pl.DataFrame:
    """Apply a price appreciation shock (additive, e.g., -0.05 for -5%) to all loans."""
    if USE_RUST:
        return mbs_core.apply_price_shock_py(loans_df, appreciation_shift)
    else:
        return apply_price_shock_py(loans_df, appreciation_shift)

def apply_zone_default_surge(loans_df: pl.DataFrame, zone: str, default_rate: float) -> pl.DataFrame:
    """Simulate a default surge in a specific zone by removing a fraction of loans from that zone."""
    if USE_RUST:
        return mbs_core.apply_zone_default_surge_py(loans_df, zone, default_rate)
    else:
        return apply_zone_default_surge_py(loans_df, zone, default_rate) 