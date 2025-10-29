use pyo3::prelude::*;
use pyo3_polars::PyDataFrame;

mod loan_record;
mod prepayment;
mod amortization;
mod aggregation;
mod stress;

use loan_record::LoanRecord;
use aggregation::{aggregate_cash_flows, compute_mbs_metrics, MbsMetrics};
use stress::{apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge};

/// A Python module implemented in Rust.
#[pymodule]
fn mbs_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(aggregate_cash_flows_py, m)?)?;
    m.add_function(wrap_pyfunction!(compute_mbs_metrics_py, m)?)?;
    m.add_function(wrap_pyfunction!(apply_rbi_rate_shift_py, m)?)?;
    m.add_function(wrap_pyfunction!(apply_price_shock_py, m)?)?;
    m.add_function(wrap_pyfunction!(apply_zone_default_surge_py, m)?)?;
    Ok(())
}

/// Aggregate cash flows for all loans using zero-copy DataFrame operations
#[pyfunction]
fn aggregate_cash_flows_py(py: Python, df: PyDataFrame) -> PyResult<PyDataFrame> {
    let polars_df = df.into();
    let result = aggregate_cash_flows(polars_df)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Rust error: {}", e)))?;
    Ok(PyDataFrame(result))
}

/// Compute MBS metrics from cash flows DataFrame
#[pyfunction]
fn compute_mbs_metrics_py(py: Python, df: PyDataFrame, discount_rate: Option<f64>) -> PyResult<PyObject> {
    let polars_df = df.into();
    let rate = discount_rate.unwrap_or(0.07);
    let metrics = compute_mbs_metrics(polars_df, rate)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Rust error: {}", e)))?;
    
    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("average_life", metrics.average_life)?;
    dict.set_item("duration", metrics.duration)?;
    dict.set_item("convexity", metrics.convexity)?;
    Ok(dict.into())
}

/// Apply RBI rate shift stress test
#[pyfunction]
fn apply_rbi_rate_shift_py(py: Python, df: PyDataFrame, rate_shift: f64) -> PyResult<PyDataFrame> {
    let polars_df = df.into();
    let result = apply_rbi_rate_shift(polars_df, rate_shift)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Rust error: {}", e)))?;
    Ok(PyDataFrame(result))
}

/// Apply price shock stress test
#[pyfunction]
fn apply_price_shock_py(py: Python, df: PyDataFrame, appreciation_shift: f64) -> PyResult<PyDataFrame> {
    let polars_df = df.into();
    let result = apply_price_shock(polars_df, appreciation_shift)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Rust error: {}", e)))?;
    Ok(PyDataFrame(result))
}

/// Apply zone default surge stress test
#[pyfunction]
fn apply_zone_default_surge_py(py: Python, df: PyDataFrame, zone: String, default_rate: f64) -> PyResult<PyDataFrame> {
    let polars_df = df.into();
    let result = apply_zone_default_surge(polars_df, &zone, default_rate)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Rust error: {}", e)))?;
    Ok(PyDataFrame(result))
}
