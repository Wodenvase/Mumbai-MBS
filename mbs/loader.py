from pydantic import BaseModel, ValidationError
import polars as pl
from typing import List, Optional

class LoanRecord(BaseModel):
    loan_id: str
    amount: float
    interest_rate: float
    term_months: int
    zone: str
    origination_date: str
    price_appreciation_rate: float
    formalization_status: str
    rbi_rate_at_origination: float


def load_loans(csv_path: str) -> pl.DataFrame:
    """Load and validate loan records from a CSV file using Polars.
    
    Returns a Polars DataFrame for zero-copy integration with Rust engine.
    """
    df = pl.read_csv(csv_path)
    
    # Validate schema
    expected_columns = {
        'loan_id', 'amount', 'interest_rate', 'term_months', 'zone',
        'origination_date', 'price_appreciation_rate', 'formalization_status',
        'rbi_rate_at_origination'
    }
    
    if not expected_columns.issubset(set(df.columns)):
        missing = expected_columns - set(df.columns)
        raise ValueError(f"Missing columns: {missing}")
    
    # Basic data validation using Polars expressions
    validated_df = df.filter(
        (pl.col("amount") > 0) &
        (pl.col("interest_rate") >= 0) &
        (pl.col("term_months") > 0) &
        pl.col("zone").is_in(["South Mumbai", "Mumbai Suburbs", "Navi Mumbai"]) &
        pl.col("formalization_status").is_in(["Formal", "Informal"])
    )
    
    print(f"Loaded {len(validated_df)} valid records out of {len(df)} total records")
    return validated_df


def validate_loans_pydantic(df: pl.DataFrame) -> List[LoanRecord]:
    """Optional: Convert Polars DataFrame to Pydantic models for additional validation."""
    records = []
    for row in df.iter_rows(named=True):
        try:
            record = LoanRecord(**row)
            records.append(record)
        except ValidationError as e:
            # Optionally log or print the error and row
            pass
    return records 