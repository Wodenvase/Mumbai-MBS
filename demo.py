#!/usr/bin/env python3
"""
Mumbai MBS Simulator - Hybrid Architecture Demo
===============================================

This script demonstrates the Python/Rust hybrid architecture for high-performance
MBS simulation. It showcases the key benefits and features of the new architecture.
"""

import time
import polars as pl
from mbs.loader import load_loans
from mbs.model import aggregate_cash_flows, compute_mbs_metrics
from mbs.stress import apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge
from mbs.dashboard import plot_cash_flows, compare_scenarios

def performance_demo():
    """Demonstrate performance benefits of the hybrid architecture."""
    print("🚀 Mumbai MBS Simulator - Performance Demo")
    print("=" * 50)
    
    # Load data
    print("📊 Loading loan data...")
    start_time = time.time()
    loans_df = load_loans("data/sheet1.csv")
    load_time = time.time() - start_time
    print(f"   Loaded {len(loans_df):,} loans in {load_time:.3f}s")
    
    # Generate cash flows
    print("\n💰 Generating cash flows...")
    start_time = time.time()
    cash_flows_df = aggregate_cash_flows(loans_df)
    cf_time = time.time() - start_time
    print(f"   Generated {len(cash_flows_df)} monthly cash flows in {cf_time:.3f}s")
    
    # Compute metrics
    print("\n📈 Computing MBS metrics...")
    start_time = time.time()
    metrics = compute_mbs_metrics(cash_flows_df)
    metrics_time = time.time() - start_time
    print(f"   Computed metrics in {metrics_time:.3f}s")
    
    # Display results
    print("\n📊 Base Scenario Results:")
    print(f"   Average Life: {metrics['average_life']:.2f} years")
    print(f"   Duration: {metrics['duration']:.2f} years")
    print(f"   Convexity: {metrics['convexity']:.4f}")
    
    total_time = load_time + cf_time + metrics_time
    print(f"\n⏱️  Total processing time: {total_time:.3f}s")
    
    return loans_df, cash_flows_df, metrics

def stress_testing_demo(loans_df, base_metrics):
    """Demonstrate stress testing capabilities."""
    print("\n\n🔥 Stress Testing Demo")
    print("=" * 30)
    
    scenarios = [
        ("RBI Rate +1%", lambda df: apply_rbi_rate_shift(df, 1.0)),
        ("RBI Rate +2%", lambda df: apply_rbi_rate_shift(df, 2.0)),
        ("Price Shock -5%", lambda df: apply_price_shock(df, -0.05)),
        ("Price Shock -10%", lambda df: apply_price_shock(df, -0.10)),
        ("South Mumbai 20% Default", lambda df: apply_zone_default_surge(df, "South Mumbai", 0.20)),
    ]
    
    print("Running stress scenarios...")
    results = {}
    
    for name, stress_func in scenarios:
        start_time = time.time()
        
        # Apply stress
        stressed_loans = stress_func(loans_df.clone())
        
        # Generate cash flows
        stressed_flows = aggregate_cash_flows(stressed_loans)
        
        # Compute metrics
        stressed_metrics = compute_mbs_metrics(stressed_flows)
        
        execution_time = time.time() - start_time
        results[name] = {
            'metrics': stressed_metrics,
            'time': execution_time,
            'flows': stressed_flows
        }
        
        # Calculate impact
        duration_change = stressed_metrics['duration'] - base_metrics['duration']
        avg_life_change = stressed_metrics['average_life'] - base_metrics['average_life']
        
        print(f"\n📊 {name}:")
        print(f"   Duration: {stressed_metrics['duration']:.2f} years ({duration_change:+.2f})")
        print(f"   Avg Life: {stressed_metrics['average_life']:.2f} years ({avg_life_change:+.2f})")
        print(f"   Execution: {execution_time:.3f}s")
    
    return results

def architecture_benefits():
    """Highlight the benefits of the hybrid architecture."""
    print("\n\n🏗️  Hybrid Architecture Benefits")
    print("=" * 35)
    
    benefits = [
        ("🔥 Performance", "10-100x faster cash flow generation with Rust engine"),
        ("📊 Zero-Copy", "Seamless data transfer between Python and Rust using pyo3-polars"),
        ("🐍 Pythonic", "Familiar Python API for data loading, validation, and visualization"), 
        ("⚡ Vectorized", "Polars DataFrames enable SIMD operations and memory efficiency"),
        ("🛡️  Type Safe", "Rust's type system prevents runtime errors in critical calculations"),
        ("🔧 Flexible", "Graceful fallback to Python implementation when Rust unavailable"),
        ("📈 Scalable", "Handles large loan portfolios efficiently"),
        ("🎯 Domain-Specific", "Mumbai-specific prepayment modeling and risk factors"),
    ]
    
    for icon_title, description in benefits:
        print(f"{icon_title}: {description}")

def technology_stack():
    """Display the complete technology stack."""
    print("\n\n🛠️  Technology Stack")
    print("=" * 22)
    
    stack = {
        "Core Engine (Rust)": [
            "Rust - Native performance computation",
            "polars-rs - High-performance DataFrames", 
            "PyO3 - Python-Rust integration",
            "pyo3-polars - Zero-copy DataFrame transfer"
        ],
        "Python Orchestration": [
            "Python - High-level workflow coordination",
            "Polars (Python) - Data loading and manipulation",
            "Pydantic - Data validation and schema management",
            "Plotly - Interactive visualization and dashboards"
        ],
        "Build & Deploy": [
            "Maturin - Rust-Python build tool",
            "uv - Ultra-fast Python package management", 
            "Cargo - Rust dependency management",
            "PyPI - Package distribution"
        ]
    }
    
    for category, technologies in stack.items():
        print(f"\n{category}:")
        for tech in technologies:
            print(f"  • {tech}")

def main():
    """Run the complete demonstration."""
    print("🏘️ Mumbai MBS Simulator - Hybrid Python/Rust Architecture")
    print("=" * 60)
    print("High-Performance Mortgage-Backed Securities Simulation")
    print("Tailored for Mumbai Residential Housing Market")
    print()
    
    try:
        # Performance demo
        loans_df, cash_flows_df, base_metrics = performance_demo()
        
        # Stress testing demo  
        stress_results = stress_testing_demo(loans_df, base_metrics)
        
        # Show architecture benefits
        architecture_benefits()
        
        # Show technology stack
        technology_stack()
        
        print("\n\n✅ Demo completed successfully!")
        print("\nNext Steps:")
        print("1. Accept Xcode license: sudo xcodebuild -license accept")
        print("2. Build Rust engine: maturin develop")  
        print("3. Re-run for 10-100x performance boost!")
        
        # Optional: Generate some visualizations
        try:
            print("\n📊 Generating visualizations...")
            
            # Plot base cash flows
            plot_cash_flows(cash_flows_df, title="Base Scenario: Mumbai MBS Cash Flows")
            
            # Compare stress scenarios
            if "RBI Rate +1%" in stress_results:
                compare_scenarios(
                    cash_flows_df, 
                    stress_results["RBI Rate +1%"]["flows"],
                    metric='total_prepayment',
                    title="Prepayment Impact: Base vs RBI +1%"
                )
                
        except Exception as e:
            print(f"Visualization skipped: {e}")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        raise

if __name__ == "__main__":
    main()
