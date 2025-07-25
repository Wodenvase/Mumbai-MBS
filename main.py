from mbs.loader import load_loans
from mbs.model import aggregate_cash_flows, compute_mbs_metrics
from mbs.stress import apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge
from mbs.dashboard import plot_cash_flows, compare_scenarios, plot_zone_wise_cash_flows, plot_formalization_segmentation

if __name__ == "__main__":
    loans = load_loans("data/sheet1.csv")
    print(f"Loaded {len(loans)} valid loan records.")
    cash_flows = aggregate_cash_flows(loans)
    print(f"First 3 months of aggregate cash flows:")
    for row in cash_flows[:3]:
        print(row)
    metrics = compute_mbs_metrics(cash_flows)
    print("\nMBS Pool Metrics (Base):")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    # Stress 1: RBI rate +1%
    stressed_loans = apply_rbi_rate_shift(loans, 1.0)
    stressed_flows = aggregate_cash_flows(stressed_loans)
    stressed_metrics = compute_mbs_metrics(stressed_flows)
    print("\nMBS Pool Metrics (RBI rate +1%):")
    for k, v in stressed_metrics.items():
        print(f"{k}: {v:.4f}")

    # Plot base cash flows
    plot_cash_flows(cash_flows, title="Base Scenario: Aggregate Cash Flows")
    # Compare principal flows: base vs. RBI +1%
    compare_scenarios(cash_flows, stressed_flows, metric='total_principal', title="Principal: Base vs. RBI +1%")
    # Compare prepayment flows: base vs. RBI +1%
    compare_scenarios(cash_flows, stressed_flows, metric='total_prepayment', title="Prepayment: Base vs. RBI +1%")

    # Zone-wise prepayment speed
    plot_zone_wise_cash_flows(loans, metric='total_prepayment')
    # Formalization segmentation for prepayment
    plot_formalization_segmentation(loans, metric='total_prepayment')

    # Stress 2: Price appreciation -5%
    stressed_loans = apply_price_shock(loans, -0.05)
    stressed_flows = aggregate_cash_flows(stressed_loans)
    stressed_metrics = compute_mbs_metrics(stressed_flows)
    print("\nMBS Pool Metrics (Price appreciation -5%):")
    for k, v in stressed_metrics.items():
        print(f"{k}: {v:.4f}")

    # Stress 3: South Mumbai default surge (20%)
    stressed_loans = apply_zone_default_surge(loans, 'South Mumbai', 0.2)
    stressed_flows = aggregate_cash_flows(stressed_loans)
    stressed_metrics = compute_mbs_metrics(stressed_flows)
    print("\nMBS Pool Metrics (South Mumbai 20% default surge):")
    for k, v in stressed_metrics.items():
        print(f"{k}: {v:.4f}") 