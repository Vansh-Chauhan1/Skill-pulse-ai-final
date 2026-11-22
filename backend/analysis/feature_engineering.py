import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed_employment_data.csv"
OUTPUT_FILE = BASE_DIR / "data" / "ml_features.csv"


def create_features():

    print("\n========== FEATURE ENGINEERING ==========\n")

    df = pd.read_csv(INPUT_FILE)

    # Select categorical and numerical features
    categorical_columns = [
        "state",
        "industry",
        "skill"
    ]

    numerical_columns = [
        "demand",
        "available_workers"
    ]

    # Prepare categorical features using One-Hot Encoding
    encoded_data = pd.get_dummies(
        df[categorical_columns],
        columns=categorical_columns,
        dtype=int
    )

    # Prepare numerical features
    numerical_data = df[numerical_columns].copy()

    # Combine all features
    features = pd.concat(
        [numerical_data, encoded_data],
        axis=1
    )

    # Save feature dataset
    features.to_csv(OUTPUT_FILE, index=False)

    print("Original dataset shape:", df.shape)
    print("Engineered features shape:", features.shape)

    print("\nGenerated feature columns:")
    print(features.columns.tolist())

    print("\nFeature dataset saved at:")
    print(OUTPUT_FILE)

    print("\n========== FEATURE ENGINEERING COMPLETE ==========")


if __name__ == "__main__":
    create_features()