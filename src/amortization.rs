use polars::prelude::*;
use crate::prepayment::add_prepayment_rates;
use std::collections::HashMap;

/// Generate amortization schedule for all loans using vectorized operations
pub fn generate_loan_schedules(df: DataFrame) -> PolarsResult<DataFrame> {
    // Find the maximum term to know how many months to generate
    let max_term = df
        .column("term_months")?
        .i32()?
        .max()
        .unwrap_or(360) as usize;
    
    let mut all_schedules = Vec::new();
    
    // Process each month across all loans
    for month in 1..=max_term {
        let month_schedule = generate_month_schedule(&df, month as i32)?;
        if month_schedule.height() > 0 {
            all_schedules.push(month_schedule);
        }
    }
    
    if all_schedules.is_empty() {
        // Return empty DataFrame with correct schema
        return Ok(df.clear());
    }
    
    // Concatenate all monthly schedules
    let result = concat(&all_schedules, UnionArgs::default())?;
    Ok(result)
}

/// Generate schedule for a specific month across all active loans
fn generate_month_schedule(loans_df: &DataFrame, month: i32) -> PolarsResult<DataFrame> {
    // Filter loans that are still active in this month
    let active_loans = loans_df
        .lazy()
        .filter(col("term_months").gte(lit(month)))
        .collect()?;
    
    if active_loans.height() == 0 {
        return Ok(active_loans);
    }
    
    // Add prepayment rates for this month
    let with_prepay = add_prepayment_rates(active_loans, month)?;
    
    // Calculate monthly payment components
    let schedule = with_prepay
        .lazy()
        .with_columns([
            lit(month).alias("month"),
            
            // Monthly interest rate
            (col("interest_rate") / lit(100.0) / lit(12.0)).alias("monthly_rate"),
            
            // Remaining balance calculation (simplified - assumes constant amortization)
            // In practice, this would need to track running balance
            (col("amount") * (lit(1.0) - (lit(month - 1).cast(DataType::Float64) / col("term_months").cast(DataType::Float64))))
                .alias("remaining_balance_start"),
        ])
        .with_columns([
            // Monthly payment calculation
            when(col("monthly_rate").eq(lit(0.0)))
                .then(col("amount") / col("term_months").cast(DataType::Float64))
                .otherwise(
                    col("amount") * col("monthly_rate") * 
                    (lit(1.0) + col("monthly_rate")).pow(col("term_months").cast(DataType::Float64)) /
                    ((lit(1.0) + col("monthly_rate")).pow(col("term_months").cast(DataType::Float64)) - lit(1.0))
                )
                .alias("monthly_payment"),
            
            // Interest payment
            (col("remaining_balance_start") * col("monthly_rate")).alias("interest"),
        ])
        .with_columns([
            // Principal payment
            (col("monthly_payment") - col("interest")).alias("principal"),
            
            // Prepayment calculation
            ((col("remaining_balance_start") - col("principal")) * col("smm")).alias("prepayment"),
        ])
        .with_columns([
            // Total principal
            (col("principal") + col("prepayment")).alias("total_principal"),
            
            // Remaining balance after payments
            (col("remaining_balance_start") - col("total_principal")).alias("remaining_balance"),
        ])
        .select([
            col("loan_id"),
            col("month"),
            col("monthly_payment").alias("payment"),
            col("principal"),
            col("interest"),
            col("prepayment"),
            col("total_principal"),
            col("remaining_balance"),
        ])
        .collect()?;
    
    Ok(schedule)
}

/// Generate a complete amortization schedule with proper balance tracking
pub fn generate_complete_amortization_schedule(df: DataFrame) -> PolarsResult<DataFrame> {
    let loans = df.clone();
    let loan_ids: Vec<String> = loans
        .column("loan_id")?
        .utf8()?
        .into_iter()
        .map(|opt| opt.unwrap_or("").to_string())
        .collect();
    
    let mut all_schedules = Vec::new();
    
    // Process each loan individually for accurate balance tracking
    for loan_id in loan_ids {
        let loan_data = loans
            .lazy()
            .filter(col("loan_id").eq(lit(&loan_id)))
            .collect()?;
        
        if loan_data.height() == 0 {
            continue;
        }
        
        let schedule = generate_single_loan_schedule(&loan_data)?;
        all_schedules.push(schedule);
    }
    
    if all_schedules.is_empty() {
        return Ok(loans.clear());
    }
    
    concat(&all_schedules, UnionArgs::default())
}

/// Generate amortization schedule for a single loan
fn generate_single_loan_schedule(loan_df: &DataFrame) -> PolarsResult<DataFrame> {
    // Extract loan parameters
    let amount = loan_df.column("amount")?.f64()?.get(0).unwrap_or(0.0);
    let interest_rate = loan_df.column("interest_rate")?.f64()?.get(0).unwrap_or(0.0);
    let term_months = loan_df.column("term_months")?.i32()?.get(0).unwrap_or(0);
    let loan_id = loan_df.column("loan_id")?.utf8()?.get(0).unwrap_or("");
    let zone = loan_df.column("zone")?.utf8()?.get(0).unwrap_or("");
    let price_appreciation_rate = loan_df.column("price_appreciation_rate")?.f64()?.get(0).unwrap_or(0.0);
    let formalization_status = loan_df.column("formalization_status")?.utf8()?.get(0).unwrap_or("");
    
    let monthly_rate = interest_rate / 100.0 / 12.0;
    let monthly_payment = if monthly_rate == 0.0 {
        amount / term_months as f64
    } else {
        amount * monthly_rate * (1.0 + monthly_rate).powi(term_months) / 
        ((1.0 + monthly_rate).powi(term_months) - 1.0)
    };
    
    let mut schedule_data = Vec::new();
    let mut remaining_balance = amount;
    
    for month in 1..=term_months {
        if remaining_balance <= 0.001 {
            break;
        }
        
        let interest = remaining_balance * monthly_rate;
        let principal = monthly_payment - interest;
        
        // Calculate prepayment
        let cpr = crate::prepayment::monthly_prepayment_rate(
            price_appreciation_rate,
            zone,
            formalization_status,
            month,
            Some(100.0),
        );
        let smm = 1.0 - (1.0 - cpr).powf(1.0 / 12.0);
        let prepayment = (remaining_balance - principal) * smm;
        
        let total_principal = principal + prepayment;
        remaining_balance = (remaining_balance - total_principal).max(0.0);
        
        schedule_data.push((
            loan_id.to_string(),
            month,
            monthly_payment,
            principal,
            interest,
            prepayment,
            total_principal,
            remaining_balance,
        ));
    }
    
    // Convert to DataFrame
    let df = df! [
        "loan_id" => schedule_data.iter().map(|x| x.0.clone()).collect::<Vec<_>>(),
        "month" => schedule_data.iter().map(|x| x.1).collect::<Vec<_>>(),
        "payment" => schedule_data.iter().map(|x| x.2).collect::<Vec<_>>(),
        "principal" => schedule_data.iter().map(|x| x.3).collect::<Vec<_>>(),
        "interest" => schedule_data.iter().map(|x| x.4).collect::<Vec<_>>(),
        "prepayment" => schedule_data.iter().map(|x| x.5).collect::<Vec<_>>(),
        "total_principal" => schedule_data.iter().map(|x| x.6).collect::<Vec<_>>(),
        "remaining_balance" => schedule_data.iter().map(|x| x.7).collect::<Vec<_>>(),
    ]?;
    
    Ok(df)
}
