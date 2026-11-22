import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "employment_data.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed_employment_data.csv"


def preprocess_data():

    print("\n========== SKILLPULSE DATA PREPROCESSING ==========\n")

    # Load raw dataset
    df = pd.read_csv(INPUT_FILE)

    print("Original records:", len(df))

    # Remove unnecessary spaces from text columns
    text_columns = ["state", "industry", "skill"]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    # Convert numerical columns
    numerical_columns = ["demand", "available_workers"]

    for column in numerical_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove incomplete records
    df = df.dropna(
        subset=text_columns + numerical_columns
    )

    # Remove invalid negative values
    df = df[
        (df["demand"] >= 0) &
        (df["available_workers"] >= 0)
    ]

    # Remove duplicate records
    df = df.drop_duplicates(
        subset=["state", "industry", "skill"]
    )

    # Calculate skill gap
    df["skill_gap"] = (
        df["demand"] - df["available_workers"]
    )

    # Calculate gap percentage safely
    df["gap_percentage"] = (
        df["skill_gap"]
        .div(df["demand"].replace(0, pd.NA))
        .mul(100)
    )

    # Add shortage classification
    df["gap_status"] = df["skill_gap"].apply(
        lambda gap:
            "Shortage" if gap > 0
            else "Surplus" if gap < 0
            else "Balanced"
    )

    # Save processed dataset
    df.to_csv(OUTPUT_FILE, index=False)

    print("Processed records:", len(df))
    print("\nGap status distribution:")
    print(df["gap_status"].value_counts())

    print("\nProcessed dataset saved at:")
    print(OUTPUT_FILE)

    print("\n========== PREPROCESSING COMPLETE ==========")


if __name__ == "__main__":
    preprocess_data()
    