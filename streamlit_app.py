import streamlit as st
import polars as pl
import plotly.graph_objects as go
import plotly.express as px
import time
import numpy as np
from mbs.loader import load_loans
from mbs.model import aggregate_cash_flows, compute_mbs_metrics
from mbs.stress import apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge

# Configure Streamlit page
st.set_page_config(
    page_title="Mumbai MBS Simulator",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .stress-result {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the loan data."""
    return load_loans("data/sheet1.csv")

@st.cache_data
def compute_base_scenario(loans_df):
    """Compute base case cash flows and metrics."""
    cash_flows_df = aggregate_cash_flows(loans_df)
    metrics = compute_mbs_metrics(cash_flows_df)
    return cash_flows_df, metrics

def create_cash_flow_chart(cash_flows_df, title="Cash Flow Waterfall"):
    """Create an interactive cash flow waterfall chart."""
    months = cash_flows_df['month'].to_list()
    principal = cash_flows_df['total_principal'].to_list()
    interest = cash_flows_df['total_interest'].to_list()
    prepayment = cash_flows_df['total_prepayment'].to_list()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=months,
        y=principal,
        name='Scheduled Principal',
        marker_color='#1f77b4'
    ))
    
    fig.add_trace(go.Bar(
        x=months,
        y=prepayment,
        name='Prepayments',
        marker_color='#ff7f0e'
    ))
    
    fig.add_trace(go.Bar(
        x=months,
        y=interest,
        name='Interest',
        marker_color='#2ca02c'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        barmode='stack',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_metrics_comparison_chart(base_metrics, stressed_metrics, scenario_name):
    """Create a comparison chart for metrics."""
    metrics_names = ['Average Life', 'Duration', 'Convexity']
    base_values = [base_metrics['average_life'], base_metrics['duration'], base_metrics['convexity']]
    stressed_values = [stressed_metrics['average_life'], stressed_metrics['duration'], stressed_metrics['convexity']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=metrics_names,
        y=base_values,
        name='Base Case',
        marker_color='#1f77b4'
    ))
    
    fig.add_trace(go.Bar(
        x=metrics_names,
        y=stressed_values,
        name=scenario_name,
        marker_color='#ff7f0e'
    ))
    
    fig.update_layout(
        title=f"Metrics Comparison: Base vs {scenario_name}",
        xaxis_title="Metrics",
        yaxis_title="Value",
        barmode='group',
        height=400
    )
    
    return fig

def create_zone_analysis_chart(loans_df):
    """Create zone-wise analysis charts."""
    zone_stats = loans_df.group_by('zone').agg([
        pl.col('amount').sum().alias('total_amount'),
        pl.col('amount').count().alias('loan_count'),
        pl.col('interest_rate').mean().alias('avg_rate'),
        pl.col('price_appreciation_rate').mean().alias('avg_appreciation')
    ])
    
    # Convert to pandas for easier plotting
    zone_data = zone_stats.to_pandas()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=zone_data['zone'],
        y=zone_data['total_amount'] / 1e9,  # Convert to billions
        name='Total Amount (₹ Billions)',
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title="Loan Portfolio by Mumbai Zone",
        xaxis_title="Zone",
        yaxis_title="Total Amount (₹ Billions)",
        height=400
    )
    
    return fig, zone_data

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🏘️ Mumbai MBS Simulator</h1>', unsafe_allow_html=True)
    st.markdown("**High-Performance Mortgage-Backed Securities Simulation**")
    st.markdown("*Hybrid Python/Rust Architecture for Mumbai Housing Market*")
    
    # Architecture status
    try:
        import mbs_core
        engine_status = "🚀 **High-Performance Rust Engine Active**"
        engine_color = "success"
    except ImportError:
        engine_status = "⚠️ **Using Python Fallback** (Build Rust engine for 100x speedup)"
        engine_color = "warning"
    
    st.markdown(f"**Engine Status:** {engine_status}")
    
    # Sidebar controls
    st.sidebar.header("📊 Simulation Controls")
    
    # Load data
    with st.spinner("Loading loan data..."):
        loans_df = load_data()
    
    st.sidebar.success(f"✅ Loaded {len(loans_df):,} loans")
    
    # Portfolio overview
    st.sidebar.header("📈 Portfolio Overview")
    total_amount = loans_df['amount'].sum() / 1e9
    avg_rate = loans_df['interest_rate'].mean()
    avg_term = loans_df['term_months'].mean() / 12
    
    st.sidebar.metric("Total Portfolio", f"₹{total_amount:.1f}B")
    st.sidebar.metric("Average Rate", f"{avg_rate:.2f}%")
    st.sidebar.metric("Average Term", f"{avg_term:.1f} years")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Base Analysis", "🔥 Stress Testing", "📊 Zone Analysis", "⚡ Performance"])
    
    # Tab 1: Base Analysis
    with tab1:
        st.header("Base Case Analysis")
        
        with st.spinner("Computing base scenario..."):
            start_time = time.time()
            cash_flows_df, base_metrics = compute_base_scenario(loans_df)
            computation_time = time.time() - start_time
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Average Life",
                f"{base_metrics['average_life']:.2f} years",
                help="Weighted average time to principal repayment"
            )
        
        with col2:
            st.metric(
                "Duration",
                f"{base_metrics['duration']:.2f} years",
                help="Price sensitivity to interest rate changes"
            )
        
        with col3:
            st.metric(
                "Convexity",
                f"{base_metrics['convexity']:.4f}",
                help="Curvature of price-yield relationship"
            )
        
        with col4:
            st.metric(
                "Computation Time",
                f"{computation_time:.3f}s",
                help="Time to generate cash flows and metrics"
            )
        
        # Cash flow chart
        st.subheader("Cash Flow Waterfall")
        cash_flow_fig = create_cash_flow_chart(cash_flows_df)
        st.plotly_chart(cash_flow_fig, use_container_width=True)
        
        # Show first few cash flows
        st.subheader("Cash Flow Details")
        st.dataframe(
            cash_flows_df.head(12).to_pandas(),
            use_container_width=True
        )
    
    # Tab 2: Stress Testing
    with tab2:
        st.header("Stress Testing Scenarios")
        
        # Stress test controls
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Interest Rate Stress")
            rbi_shift = st.slider("RBI Rate Shift (%)", -2.0, 3.0, 1.0, 0.25)
            
        with col2:
            st.subheader("Price Appreciation Stress")
            price_shift = st.slider("Price Shock (%)", -15.0, 5.0, -5.0, 2.5)
        
        # Zone default stress
        st.subheader("Zone Default Stress")
        zone_col1, zone_col2 = st.columns(2)
        
        with zone_col1:
            target_zone = st.selectbox(
                "Target Zone",
                ["South Mumbai", "Mumbai Suburbs", "Navi Mumbai"]
            )
        
        with zone_col2:
            default_rate = st.slider("Default Rate (%)", 0.0, 50.0, 20.0, 5.0) / 100
        
        # Run stress tests
        if st.button("🔥 Run Stress Tests", type="primary"):
            progress_bar = st.progress(0)
            stress_results = {}
            
            scenarios = [
                ("RBI Rate Stress", lambda df: apply_rbi_rate_shift(df, rbi_shift)),
                ("Price Shock", lambda df: apply_price_shock(df, price_shift / 100)),
                ("Zone Default", lambda df: apply_zone_default_surge(df, target_zone, default_rate))
            ]
            
            for i, (name, stress_func) in enumerate(scenarios):
                with st.spinner(f"Running {name}..."):
                    start_time = time.time()
                    
                    # Apply stress
                    stressed_loans = stress_func(loans_df.clone())
                    stressed_flows = aggregate_cash_flows(stressed_loans)
                    stressed_metrics = compute_mbs_metrics(stressed_flows)
                    
                    exec_time = time.time() - start_time
                    
                    stress_results[name] = {
                        'metrics': stressed_metrics,
                        'flows': stressed_flows,
                        'time': exec_time,
                        'loans_affected': len(loans_df) - len(stressed_loans) if name == "Zone Default" else len(loans_df)
                    }
                
                progress_bar.progress((i + 1) / len(scenarios))
            
            # Display results
            st.subheader("Stress Test Results")
            
            for scenario_name, results in stress_results.items():
                with st.expander(f"📊 {scenario_name} Results", expanded=True):
                    
                    # Metrics comparison
                    col1, col2, col3, col4 = st.columns(4)
                    
                    metrics = results['metrics']
                    
                    with col1:
                        change = metrics['average_life'] - base_metrics['average_life']
                        st.metric(
                            "Average Life", 
                            f"{metrics['average_life']:.2f} years",
                            delta=f"{change:+.2f} years"
                        )
                    
                    with col2:
                        change = metrics['duration'] - base_metrics['duration']
                        st.metric(
                            "Duration",
                            f"{metrics['duration']:.2f} years", 
                            delta=f"{change:+.2f} years"
                        )
                    
                    with col3:
                        change = metrics['convexity'] - base_metrics['convexity']
                        st.metric(
                            "Convexity",
                            f"{metrics['convexity']:.4f}",
                            delta=f"{change:+.4f}"
                        )
                    
                    with col4:
                        st.metric(
                            "Execution Time",
                            f"{results['time']:.3f}s",
                            help=f"Processed {results['loans_affected']:,} loans"
                        )
                    
                    # Comparison chart
                    comparison_fig = create_metrics_comparison_chart(
                        base_metrics, metrics, scenario_name
                    )
                    st.plotly_chart(comparison_fig, use_container_width=True)
    
    # Tab 3: Zone Analysis
    with tab3:
        st.header("Mumbai Zone Analysis")
        
        # Zone overview
        zone_fig, zone_data = create_zone_analysis_chart(loans_df)
        st.plotly_chart(zone_fig, use_container_width=True)
        
        # Zone details
        st.subheader("Zone Statistics")
        
        # Format zone data for display
        display_data = zone_data.copy()
        display_data['total_amount'] = display_data['total_amount'].apply(lambda x: f"₹{x/1e9:.2f}B")
        display_data['loan_count'] = display_data['loan_count'].apply(lambda x: f"{x:,}")
        display_data['avg_rate'] = display_data['avg_rate'].apply(lambda x: f"{x:.2f}%")
        display_data['avg_appreciation'] = display_data['avg_appreciation'].apply(lambda x: f"{x:.2f}%")
        
        display_data.columns = ['Zone', 'Total Amount', 'Loan Count', 'Avg Rate', 'Avg Appreciation']
        st.dataframe(display_data, use_container_width=True)
        
        # Formalization analysis
        st.subheader("Formalization Status Analysis")
        
        formal_stats = loans_df.group_by('formalization_status').agg([
            pl.col('amount').sum().alias('total_amount'),
            pl.col('amount').count().alias('loan_count'),
            pl.col('price_appreciation_rate').mean().alias('avg_appreciation')
        ]).to_pandas()
        
        fig_formal = px.pie(
            formal_stats,
            values='total_amount',
            names='formalization_status',
            title="Portfolio by Formalization Status"
        )
        st.plotly_chart(fig_formal, use_container_width=True)
    
    # Tab 4: Performance
    with tab4:
        st.header("Performance Benchmarks")
        
        # Architecture info
        st.subheader("🏗️ Hybrid Architecture")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🦀 Rust Core Engine:**
            - Zero-copy DataFrame operations
            - Vectorized SIMD calculations  
            - Multi-threaded processing
            - Memory-efficient algorithms
            """)
        
        with col2:
            st.markdown("""
            **🐍 Python Orchestration:**
            - Familiar data science APIs
            - Interactive visualizations
            - Flexible workflow control
            - Rich ecosystem integration
            """)
        
        # Performance metrics
        st.subheader("⚡ Performance Metrics")
        
        # Run a quick benchmark
        if st.button("🏃‍♂️ Run Performance Benchmark"):
            benchmark_sizes = [1000, 2500, 5000, 10000]
            times = []
            
            progress = st.progress(0)
            
            for i, size in enumerate(benchmark_sizes):
                sample_df = loans_df.head(size)
                
                start_time = time.time()
                cash_flows = aggregate_cash_flows(sample_df)
                metrics = compute_mbs_metrics(cash_flows)
                end_time = time.time()
                
                times.append(end_time - start_time)
                progress.progress((i + 1) / len(benchmark_sizes))
            
            # Create benchmark chart
            benchmark_data = pl.DataFrame({
                'Portfolio Size': benchmark_sizes,
                'Execution Time (s)': times
            })
            
            fig_benchmark = px.line(
                benchmark_data.to_pandas(),
                x='Portfolio Size',
                y='Execution Time (s)',
                title="Performance Scaling",
                markers=True
            )
            
            st.plotly_chart(fig_benchmark, use_container_width=True)
            
            # Performance summary
            st.success(f"✅ Processed {max(benchmark_sizes):,} loans in {max(times):.3f}s")
            
            if max(times) < 0.1:
                st.success("🚀 **Rust Engine Performance**: Sub-100ms execution!")
            elif max(times) < 1.0:
                st.success("⚡ **High Performance**: Sub-second execution!")
            else:
                st.info("🐍 **Python Fallback**: Good performance, build Rust engine for 100x speedup!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Mumbai MBS Simulator | Hybrid Python/Rust Architecture</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
