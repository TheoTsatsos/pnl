import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def load_data(path: str) -> pd.DataFrame:
    """Load csv file with ';' separator and ensure numeric columns."""
    df = pd.read_csv(path, sep=';')
    # Convert numeric fields, coercing invalid values to NaN
    for col in ["tradePx", "tradeAmt"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Identify rows where conversion failed
    invalid_rows = df[df[["tradePx", "tradeAmt"]].isna().any(axis=1)]
    if not invalid_rows.empty:
        print(
            f"Warning: dropping {len(invalid_rows)} rows due to invalid tradePx/tradeAmt"
        )
        df = df.dropna(subset=["tradePx", "tradeAmt"])

    return df


def calculate_filled_trades(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with only filled trades and compute signed pnl."""
    filled = df[df["action"] == "filled"].copy()
    sign = np.where(filled["orderSide"] == "buy", -1, 1)
    filled["signed_pnl"] = filled["tradePx"] * filled["tradeAmt"] * sign
    return filled


def total_gross_pnl(filled: pd.DataFrame) -> float:
    return filled['signed_pnl'].sum()


def gross_pnl_by_asset(filled: pd.DataFrame) -> pd.Series:
    return filled.groupby('orderProduct')['signed_pnl'].sum()


def cumulative_gross_pnl(filled: pd.DataFrame) -> pd.DataFrame:
    """Return cumulative gross PnL with timestamps sorted chronologically."""
    filled_sorted = filled.copy().sort_values("currentTime")
    filled_sorted["currentTime"] = pd.to_datetime(
        filled_sorted["currentTime"], unit="ns"
    )
    filled_sorted["cumulative_pnl"] = filled_sorted["signed_pnl"].cumsum()
    return filled_sorted[["currentTime", "cumulative_pnl"]]


def plot_cumulative_pnl(cum_df: pd.DataFrame, output_file: str) -> None:
    """Plot the cumulative PnL time series."""
    plt.figure(figsize=(10, 5))
    plt.plot(cum_df['currentTime'], cum_df['cumulative_pnl'], marker='o')
    plt.xlabel('Timestamp')
    plt.ylabel('Cumulative Gross PnL')
    plt.title('Cumulative Gross PnL over Time')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def main(log_file: str, output_image: str = 'cumulative_pnl.png') -> None:
    data = load_data(log_file)
    filled = calculate_filled_trades(data)

    total_pnl = total_gross_pnl(filled)
    pnl_by_asset = gross_pnl_by_asset(filled)
    cumulative = cumulative_gross_pnl(filled)

    print(f"Total gross PnL: {total_pnl}")
    print("Gross PnL by asset:")
    for asset, pnl in pnl_by_asset.items():
        print(f"  {asset}: {pnl}")

    plot_cumulative_pnl(cumulative, output_image)
    print(f"Cumulative PnL plot saved to {output_image}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calculate PnL statistics.")
    parser.add_argument("log_file", help="Path to test_logs.csv")
    parser.add_argument("--output", default="cumulative_pnl.png", help="Output image file")
    args = parser.parse_args()

    main(args.log_file, args.output)
