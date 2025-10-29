use polars::prelude::*;
use crate::loan_record::LoanRecord;

/// PSA curve calculation - returns annualized CPR
pub fn psa_curve(month: i32, psa_speed: f64) -> f64 {
    // Standard PSA: 0.2% CPR in month 1, increasing by 0.2% per month until month 30, then flat
    let base_cpr = (0.002 * month as f64).min(0.06); // 0.2% * month, max 6% annualized
    base_cpr * (psa_speed / 100.0)
}

/// Mumbai-specific PSA multiplier based on loan characteristics
pub fn mumbai_psa_multiplier(
    price_appreciation_rate: f64,
    zone: &str,
    formalization_status: &str,
) -> f64 {
    // Price appreciation multiplier
    let price_mult = if price_appreciation_rate > 0.08 {
        2.0
    } else if price_appreciation_rate > 0.05 {
        1.5
    } else {
        1.0
    };

    // Zone multiplier
    let zone_mult = match zone {
        "South Mumbai" => 1.5,
        "Mumbai Suburbs" => 1.0,
        "Navi Mumbai" => 0.5,
        _ => 1.0,
    };

    // Formalization multiplier
    let formal_mult = if formalization_status == "Formal" { 1.2 } else { 1.0 };

    price_mult * zone_mult * formal_mult
}

/// Calculate monthly prepayment rate (CPR) for a loan in a specific month
pub fn monthly_prepayment_rate(
    price_appreciation_rate: f64,
    zone: &str,
    formalization_status: &str,
    month: i32,
    psa_speed: Option<f64>,
) -> f64 {
    let psa_speed = psa_speed.unwrap_or(100.0);
    let base_cpr = psa_curve(month, psa_speed);
    let multiplier = mumbai_psa_multiplier(price_appreciation_rate, zone, formalization_status);
    base_cpr * multiplier
}

/// Add prepayment rates to a DataFrame using vectorized operations
pub fn add_prepayment_rates(df: DataFrame, month: i32) -> PolarsResult<DataFrame> {
    df.lazy()
        .with_columns([
            // Calculate PSA multiplier for each loan
            (when(col("price_appreciation_rate").gt(lit(0.08)))
                .then(lit(2.0))
                .when(col("price_appreciation_rate").gt(lit(0.05)))
                .then(lit(1.5))
                .otherwise(lit(1.0)))
            .alias("price_mult"),
            
            // Zone multiplier
            (when(col("zone").eq(lit("South Mumbai")))
                .then(lit(1.5))
                .when(col("zone").eq(lit("Mumbai Suburbs")))
                .then(lit(1.0))
                .when(col("zone").eq(lit("Navi Mumbai")))
                .then(lit(0.5))
                .otherwise(lit(1.0)))
            .alias("zone_mult"),
            
            // Formalization multiplier
            (when(col("formalization_status").eq(lit("Formal")))
                .then(lit(1.2))
                .otherwise(lit(1.0)))
            .alias("formal_mult"),
        ])
        .with_columns([
            // Combined multiplier
            (col("price_mult") * col("zone_mult") * col("formal_mult"))
                .alias("mumbai_multiplier"),
            
            // Base PSA curve value
            lit(psa_curve(month, 100.0)).alias("base_cpr"),
        ])
        .with_columns([
            // Final CPR for this month
            (col("base_cpr") * col("mumbai_multiplier")).alias("cpr"),
            
            // Convert CPR to SMM (Single Monthly Mortality)
            (lit(1.0) - (lit(1.0) - col("base_cpr") * col("mumbai_multiplier")).pow(lit(1.0/12.0)))
                .alias("smm"),
        ])
        .select([
            col("*"),
            col("cpr"),
            col("smm"),
        ])
        .collect()
}
