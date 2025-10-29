use polars::prelude::*;
use crate::loan_record::MbsMetrics;
use crate::amortization::generate_complete_amortization_schedule;

/// Aggregate cash flows for all loans
pub fn aggregate_cash_flows(loans_df: DataFrame) -> PolarsResult<DataFrame> {
    // Generate complete amortization schedules for all loans
    let schedules = generate_complete_amortization_schedule(loans_df)?;
    
    if schedules.height() == 0 {
        return Ok(schedules);
    }
    
    // Aggregate by month
    let aggregated = schedules
        .lazy()
        .group_by([col("month")])
        .agg([
            col("principal").sum().alias("total_principal"),
            col("interest").sum().alias("total_interest"),
            col("prepayment").sum().alias("total_prepayment"),
            col("payment").sum().alias("total_payment"),
        ])
        .sort("month", SortOptions::default())
        .collect()?;
    
    Ok(aggregated)
}

/// Compute MBS metrics from aggregated cash flows
pub fn compute_mbs_metrics(cash_flows_df: DataFrame, discount_rate: f64) -> PolarsResult<MbsMetrics> {
    if cash_flows_df.height() == 0 {
        return Ok(MbsMetrics {
            average_life: 0.0,
            duration: 0.0,
            convexity: 0.0,
        });
    }
    
    // Extract columns
    let months = cash_flows_df.column("month")?.i32()?;
    let total_principal = cash_flows_df.column("total_principal")?.f64()?;
    let total_prepayment = cash_flows_df.column("total_prepayment")?.f64()?;
    
    let mut total_principal_sum = 0.0;
    let mut pv_total = 0.0;
    let mut pv_weighted_time = 0.0;
    let mut pv_weighted_time2 = 0.0;
    let mut weighted_time_principal = 0.0;
    
    let monthly_discount_rate = discount_rate / 12.0;
    
    for i in 0..cash_flows_df.height() {
        let month = months.get(i).unwrap_or(0) as f64;
        let principal = total_principal.get(i).unwrap_or(0.0);
        let prepayment = total_prepayment.get(i).unwrap_or(0.0);
        let total_principal_payment = principal + prepayment;
        
        if total_principal_payment > 0.0 {
            total_principal_sum += total_principal_payment;
            weighted_time_principal += month * total_principal_payment;
            
            // Present value calculations
            let pv_factor = 1.0 / (1.0 + monthly_discount_rate).powf(month);
            let pv = total_principal_payment * pv_factor;
            
            pv_total += pv;
            pv_weighted_time += month * pv;
            pv_weighted_time2 += month * (month + 1.0) * pv;
        }
    }
    
    if total_principal_sum == 0.0 || pv_total == 0.0 {
        return Ok(MbsMetrics {
            average_life: 0.0,
            duration: 0.0,
            convexity: 0.0,
        });
    }
    
    // Calculate metrics
    let average_life = weighted_time_principal / total_principal_sum / 12.0; // Convert to years
    let duration = pv_weighted_time / pv_total / 12.0; // Convert to years
    let convexity = pv_weighted_time2 / (pv_total * (1.0 + monthly_discount_rate).powi(2)) / (12.0 * 12.0); // Convert to years²
    
    Ok(MbsMetrics {
        average_life,
        duration,
        convexity,
    })
}

/// Compute pool-level statistics
pub fn compute_pool_statistics(loans_df: &DataFrame) -> PolarsResult<PoolStatistics> {
    let stats = loans_df
        .lazy()
        .select([
            col("amount").sum().alias("total_amount"),
            col("amount").mean().alias("avg_amount"),
            col("interest_rate").mean().alias("avg_interest_rate"),
            col("term_months").mean().alias("avg_term_months"),
            col("price_appreciation_rate").mean().alias("avg_price_appreciation"),
            count().alias("loan_count"),
        ])
        .collect()?;
    
    let total_amount = stats.column("total_amount")?.f64()?.get(0).unwrap_or(0.0);
    let avg_amount = stats.column("avg_amount")?.f64()?.get(0).unwrap_or(0.0);
    let avg_interest_rate = stats.column("avg_interest_rate")?.f64()?.get(0).unwrap_or(0.0);
    let avg_term_months = stats.column("avg_term_months")?.f64()?.get(0).unwrap_or(0.0);
    let avg_price_appreciation = stats.column("avg_price_appreciation")?.f64()?.get(0).unwrap_or(0.0);
    let loan_count = stats.column("loan_count")?.len() as u32;
    
    // Zone distribution
    let zone_dist = loans_df
        .lazy()
        .group_by([col("zone")])
        .agg([
            col("amount").sum().alias("zone_amount"),
            count().alias("zone_count"),
        ])
        .collect()?;
    
    Ok(PoolStatistics {
        total_amount,
        avg_amount,
        avg_interest_rate,
        avg_term_months,
        avg_price_appreciation,
        loan_count,
        zone_distribution: zone_dist,
    })
}

#[derive(Debug, Clone)]
pub struct PoolStatistics {
    pub total_amount: f64,
    pub avg_amount: f64,
    pub avg_interest_rate: f64,
    pub avg_term_months: f64,
    pub avg_price_appreciation: f64,
    pub loan_count: u32,
    pub zone_distribution: DataFrame,
}
