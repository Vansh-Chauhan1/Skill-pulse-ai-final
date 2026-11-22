import pandas as pd
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "processed_employment_data.csv"
MODEL_FILE = BASE_DIR / "ml" / "skill_gap_model.pkl"


def train_model():

    print("\n========== SKILLPULSE ML TRAINING ==========\n")

    # Load processed dataset
    df = pd.read_csv(DATA_FILE)

    # Input features
    X = df[[
        "demand",
        "available_workers"
    ]]

    # Target variable
    y = df["gap_status"]

    # Initialize model
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    # Train model
    model.fit(X, y)

    # Save trained model
    joblib.dump(model, MODEL_FILE)

    print("Model training completed!")

    print("Training records:", len(X))

    print("\nClasses learned:")
    print(model.classes_)

    print("\nModel saved at:")
    print(MODEL_FILE)

    print("\n========== TRAINING COMPLETE ==========")


if __name__ == "__main__":
    train_model()