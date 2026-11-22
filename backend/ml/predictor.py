import joblib
import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = BASE_DIR / "ml" / "skill_gap_model.pkl"


def load_model():

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "Trained model not found. Run train_model.py first."
        )

    return joblib.load(MODEL_FILE)


def predict_skill_gap(demand, available_workers):

    model = load_model()

    # Prepare input features
    input_data = pd.DataFrame({
        "demand": [demand],
        "available_workers": [available_workers]
    })

    # Predict skill-gap category
    prediction = model.predict(input_data)[0]

    # Calculate actual skill gap
    skill_gap = demand - available_workers

    gap_percentage = (
        (skill_gap / demand) * 100
        if demand > 0 else None
    )

    return {
        "demand": demand,
        "available_workers": available_workers,
        "skill_gap": skill_gap,
        "gap_percentage": gap_percentage,
        "predicted_status": prediction
    }


if __name__ == "__main__":

    result = predict_skill_gap(
        demand=10000,
        available_workers=7000
    )

    print("\n========== SKILLPULSE AI PREDICTION ==========")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n========== PREDICTION COMPLETE ==========")