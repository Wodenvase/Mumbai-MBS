from mbs.loader import load_loans
from mbs.model import aggregate_cash_flows, compute_mbs_metrics
from mbs.stress import apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge
from mbs.dashboard import plot_cash_flows, compare_scenarios, plot_zone_wise_cash_flows, plot_formalization_segmentation

if __name__ == "__main__":
    # Load loans as Polars DataFrame for zero-copy Rust integration
    loans_df = load_loans("data/sheet1.csv")
    print(f"Loaded {len(loans_df)} valid loan records.")
    
    try:
        # Generate cash flows using Rust engine
        cash_flows_df = aggregate_cash_flows(loans_df)
        print(f"Generated cash flows for {len(cash_flows_df)} months")
        
        # Show first 3 months
        print("First 3 months of aggregate cash flows:")
        print(cash_flows_df.head(3))
        
        # Compute MBS metrics using Rust engine
        metrics = compute_mbs_metrics(cash_flows_df)
        print("\nMBS Pool Metrics (Base):")
        for k, v in metrics.items():
            print(f"{k}: {v:.4f}")

        # Stress 1: RBI rate +1%
        stressed_loans_df = apply_rbi_rate_shift(loans_df, 1.0)
        stressed_flows_df = aggregate_cash_flows(stressed_loans_df)
        stressed_metrics = compute_mbs_metrics(stressed_flows_df)
        print("\nMBS Pool Metrics (RBI rate +1%):")
        for k, v in stressed_metrics.items():
            print(f"{k}: {v:.4f}")

        # Plot base cash flows
        plot_cash_flows(cash_flows_df, title="Base Scenario: Aggregate Cash Flows")
        
        # Compare principal flows: base vs. RBI +1%
        compare_scenarios(cash_flows_df, stressed_flows_df, metric='total_principal', 
                         title="Principal: Base vs. RBI +1%")
        
        # Compare prepayment flows: base vs. RBI +1%
        compare_scenarios(cash_flows_df, stressed_flows_df, metric='total_prepayment', 
                         title="Prepayment: Base vs. RBI +1%")

        # Zone-wise prepayment speed
        plot_zone_wise_cash_flows(loans_df, metric='total_prepayment')
        
        # Formalization segmentation for prepayment
        plot_formalization_segmentation(loans_df, metric='total_prepayment')

        # Stress 2: Price appreciation -5%
        stressed_loans_df2 = apply_price_shock(loans_df, -0.05)
        stressed_flows_df2 = aggregate_cash_flows(stressed_loans_df2)
        stressed_metrics2 = compute_mbs_metrics(stressed_flows_df2)
        print("\nMBS Pool Metrics (Price appreciation -5%):")
        for k, v in stressed_metrics2.items():
            print(f"{k}: {v:.4f}")

        # Stress 3: South Mumbai default surge (20%)
        stressed_loans_df3 = apply_zone_default_surge(loans_df, 'South Mumbai', 0.2)
        stressed_flows_df3 = aggregate_cash_flows(stressed_loans_df3)
        stressed_metrics3 = compute_mbs_metrics(stressed_flows_df3)
        print("\nMBS Pool Metrics (South Mumbai 20% default surge):")
        for k, v in stressed_metrics3.items():
            print(f"{k}: {v:.4f}")
            
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please build the Rust engine first with: maturin develop")
        print("Or install it with: pip install -e .") 