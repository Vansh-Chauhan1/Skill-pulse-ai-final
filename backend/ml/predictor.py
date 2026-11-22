def predict_skill_gap(demand: float, available_workers: float):
    """
    Calculate the current workforce skill gap and classify it
    as Shortage, Surplus, or Balanced.
    """

    if demand < 0:
        raise ValueError("Demand cannot be negative.")

    if available_workers < 0:
        raise ValueError("Available workers cannot be negative.")

    # Calculate workforce gap
    skill_gap = demand - available_workers

    # Classify based on the mathematical result
    if skill_gap > 0:
        status = "Shortage"

    elif skill_gap < 0:
        status = "Surplus"

    else:
        status = "Balanced"

    # Calculate gap percentage
    if demand > 0:
        gap_percentage = (skill_gap / demand) * 100
    else:
        gap_percentage = None

    return {
        "demand": demand,
        "available_workers": available_workers,
        "skill_gap": skill_gap,
        "gap_percentage": gap_percentage,
        "predicted_status": status
    }


# Test the prediction function independently
if __name__ == "__main__":

    test_cases = [
        (10000, 7000),
        (6000, 7000),
        (8000, 8000)
    ]

    print("\n========== SKILLPULSE AI PREDICTION ==========")

    for demand, workers in test_cases:
        result = predict_skill_gap(demand, workers)

        print("\n--------------------------------")
        for key, value in result.items():
            print(f"{key}: {value}")

    print("\n========== PREDICTION COMPLETE ==========")