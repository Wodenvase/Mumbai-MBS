use polars::prelude::*;
use rand::prelude::*;

/// Apply RBI rate shift to all loans' interest rates
pub fn apply_rbi_rate_shift(loans_df: DataFrame, rate_shift: f64) -> PolarsResult<DataFrame> {
    loans_df
        .lazy()
        .with_columns([
            // Apply rate shift while ensuring non-negative rates
            (col("interest_rate") + lit(rate_shift))
                .clip(lit(0.0), None)
                .alias("interest_rate"),
            
            // Also update RBI rate at origination for consistency
            (col("rbi_rate_at_origination") + lit(rate_shift))
                .clip(lit(0.0), None)
                .alias("rbi_rate_at_origination"),
        ])
        .collect()
}

/// Apply price appreciation shock to all loans
pub fn apply_price_shock(loans_df: DataFrame, appreciation_shift: f64) -> PolarsResult<DataFrame> {
    loans_df
        .lazy()
        .with_columns([
            // Apply appreciation shift while ensuring non-negative rates
            (col("price_appreciation_rate") + lit(appreciation_shift))
                .clip(lit(0.0), None)
                .alias("price_appreciation_rate"),
        ])
        .collect()
}

/// Apply zone-specific default surge by randomly removing loans from the specified zone
pub fn apply_zone_default_surge(
    loans_df: DataFrame,
    zone: &str,
    default_rate: f64,
) -> PolarsResult<DataFrame> {
    // Generate random numbers for each loan
    let loan_count = loans_df.height();
    let mut rng = thread_rng();
    let random_numbers: Vec<f64> = (0..loan_count)
        .map(|_| rng.gen::<f64>())
        .collect();
    
    // Add random column to DataFrame
    let with_random = loans_df
        .lazy()
        .with_row_index("row_idx", None)
        .collect()?;
    
    let random_series = Series::new("random", random_numbers);
    let with_random = with_random.with_column(random_series)?;
    
    // Filter out defaulted loans from the specified zone
    let result = with_random
        .lazy()
        .filter(
            // Keep all loans not in the target zone
            col("zone").neq(lit(zone))
            .or(
                // Keep loans in target zone that survive (random > default_rate)
                col("zone").eq(lit(zone)).and(col("random").gt(lit(default_rate)))
            )
        )
        .drop(["row_idx", "random"])
        .collect()?;
    
    Ok(result)
}

/// Apply multiple stress scenarios simultaneously
pub fn apply_combined_stress(
    loans_df: DataFrame,
    rbi_rate_shift: Option<f64>,
    price_shock: Option<f64>,
    zone_defaults: Option<Vec<(String, f64)>>,
) -> PolarsResult<DataFrame> {
    let mut result = loans_df;
    
    // Apply RBI rate shift if specified
    if let Some(rate_shift) = rbi_rate_shift {
        result = apply_rbi_rate_shift(result, rate_shift)?;
    }
    
    // Apply price shock if specified
    if let Some(appreciation_shift) = price_shock {
        result = apply_price_shock(result, appreciation_shift)?;
    }
    
    // Apply zone defaults if specified
    if let Some(zone_default_list) = zone_defaults {
        for (zone, default_rate) in zone_default_list {
            result = apply_zone_default_surge(result, &zone, default_rate)?;
        }
    }
    
    Ok(result)
}

/// Generate stress test scenarios
pub fn generate_stress_scenarios(base_loans: DataFrame) -> PolarsResult<Vec<(String, DataFrame)>> {
    let mut scenarios = Vec::new();
    
    // Base scenario
    scenarios.push(("Base".to_string(), base_loans.clone()));
    
    // Single factor stresses
    scenarios.push((
        "RBI +1%".to_string(),
        apply_rbi_rate_shift(base_loans.clone(), 1.0)?,
    ));
    
    scenarios.push((
        "RBI +2%".to_string(),
        apply_rbi_rate_shift(base_loans.clone(), 2.0)?,
    ));
    
    scenarios.push((
        "Price -5%".to_string(),
        apply_price_shock(base_loans.clone(), -0.05)?,
    ));
    
    scenarios.push((
        "Price -10%".to_string(),
        apply_price_shock(base_loans.clone(), -0.10)?,
    ));
    
    scenarios.push((
        "South Mumbai 20% Default".to_string(),
        apply_zone_default_surge(base_loans.clone(), "South Mumbai", 0.20)?,
    ));
    
    // Combined stress scenarios
    scenarios.push((
        "RBI +2% + Price -10%".to_string(),
        apply_combined_stress(
            base_loans.clone(),
            Some(2.0),
            Some(-0.10),
            None,
        )?,
    ));
    
    scenarios.push((
        "Severe Stress".to_string(),
        apply_combined_stress(
            base_loans.clone(),
            Some(2.0),
            Some(-0.10),
            Some(vec![("South Mumbai".to_string(), 0.20)]),
        )?,
    ));
    
    Ok(scenarios)
}

/// Calculate stress impact metrics
pub fn calculate_stress_impact(
    base_metrics: &crate::loan_record::MbsMetrics,
    stressed_metrics: &crate::loan_record::MbsMetrics,
) -> StressImpact {
    StressImpact {
        average_life_change: stressed_metrics.average_life - base_metrics.average_life,
        duration_change: stressed_metrics.duration - base_metrics.duration,
        convexity_change: stressed_metrics.convexity - base_metrics.convexity,
        average_life_pct_change: if base_metrics.average_life != 0.0 {
            (stressed_metrics.average_life - base_metrics.average_life) / base_metrics.average_life * 100.0
        } else {
            0.0
        },
        duration_pct_change: if base_metrics.duration != 0.0 {
            (stressed_metrics.duration - base_metrics.duration) / base_metrics.duration * 100.0
        } else {
            0.0
        },
        convexity_pct_change: if base_metrics.convexity != 0.0 {
            (stressed_metrics.convexity - base_metrics.convexity) / base_metrics.convexity * 100.0
        } else {
            0.0
        },
    }
}

#[derive(Debug, Clone)]
pub struct StressImpact {
    pub average_life_change: f64,
    pub duration_change: f64,
    pub convexity_change: f64,
    pub average_life_pct_change: f64,
    pub duration_pct_change: f64,
    pub convexity_pct_change: f64,
}
