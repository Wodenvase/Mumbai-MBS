use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, NaiveDate};
use polars::prelude::*;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoanRecord {
    pub loan_id: String,
    pub amount: f64,
    pub interest_rate: f64,
    pub term_months: i32,
    pub zone: String,
    pub origination_date: String,
    pub price_appreciation_rate: f64,
    pub formalization_status: String,
    pub rbi_rate_at_origination: f64,
}

impl LoanRecord {
    /// Create a LoanRecord from a Polars DataFrame row
    pub fn from_row(row: &AnyValue, schema: &Schema) -> PolarsResult<Self> {
        // This would be used if we need to convert individual rows
        // For now, we'll work directly with DataFrames
        todo!("Implement if needed for individual row processing")
    }
    
    /// Validate loan record data
    pub fn validate(&self) -> Result<(), String> {
        if self.amount <= 0.0 {
            return Err("Loan amount must be positive".to_string());
        }
        if self.interest_rate < 0.0 {
            return Err("Interest rate cannot be negative".to_string());
        }
        if self.term_months <= 0 {
            return Err("Term must be positive".to_string());
        }
        if !["South Mumbai", "Mumbai Suburbs", "Navi Mumbai"].contains(&self.zone.as_str()) {
            return Err("Invalid zone".to_string());
        }
        if !["Formal", "Informal"].contains(&self.formalization_status.as_str()) {
            return Err("Invalid formalization status".to_string());
        }
        Ok(())
    }
}

/// Cash flow entry for a single period
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CashFlowEntry {
    pub month: i32,
    pub payment: f64,
    pub principal: f64,
    pub interest: f64,
    pub prepayment: f64,
    pub total_principal: f64,
    pub remaining_balance: f64,
}

/// Aggregated cash flows for all loans
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregateCashFlow {
    pub month: i32,
    pub total_principal: f64,
    pub total_interest: f64,
    pub total_prepayment: f64,
    pub total_payment: f64,
}

/// MBS pool metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MbsMetrics {
    pub average_life: f64,
    pub duration: f64,
    pub convexity: f64,
}
