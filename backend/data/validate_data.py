import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent / "employment_data.csv"

REQUIRED_COLUMNS = [
    "state",
    "industry",
    "skill",
    "demand",
    "available_workers"
]


def validate_employment_data():

    print("\n========== SKILLPULSE DATA VALIDATION ==========\n")

    if not DATA_FILE.exists():
        print("ERROR: employment_data.csv not found!")
        return

    df = pd.read_csv(DATA_FILE)

    # 1. Check required columns
    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        print("ERROR: Missing columns:", missing_columns)
        return

    print("1. Required columns: PASSED")

    # 2. Check missing values
    missing_values = df[REQUIRED_COLUMNS].isnull().sum()

    if missing_values.sum() == 0:
        print("2. Missing values: NONE")
    else:
        print("2. Missing values:")
        print(missing_values[missing_values > 0])

    # 3. Check negative values
    invalid_values = df[
        (df["demand"] < 0) |
        (df["available_workers"] < 0)
    ]

    if invalid_values.empty:
        print("3. Negative values: NONE")
    else:
        print("3. Invalid records found:")
        print(invalid_values)

    # 4. Check duplicate records
    duplicates = df.duplicated(
        subset=["state", "industry", "skill"]
    )

    if not duplicates.any():
        print("4. Duplicate records: NONE")
    else:
        print("4. Duplicate records found:")
        print(df[duplicates])

    # 5. Verify skill-gap calculations
    calculated_gap = (
        df["demand"] - df["available_workers"]
    )

    if "skill_gap" in df.columns:
        correct = (
            calculated_gap == df["skill_gap"]
        ).all()

        print(
            "5. Skill-gap calculation:",
            "PASSED" if correct else "FAILED"
        )
    else:
        print("5. Skill-gap column: Not present (will be calculated)")

    print("\n========== VALIDATION COMPLETE ==========")
    print("Total records:", len(df))


if __name__ == "__main__":
    validate_employment_data()