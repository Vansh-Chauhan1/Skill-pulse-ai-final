import pandas as pd
from pathlib import Path


# Load employment dataset
def load_employment_data():

    file_path = (
        Path(__file__).parent.parent
        / "data"
        / "employment_data.csv"
    )

    df = pd.read_csv(file_path)

    return df


# Calculate overall skill gap
def calculate_skill_gaps():

    df = load_employment_data()

    df["skill_gap"] = (
        df["demand"] - df["available_workers"]
    )

    df["gap_percentage"] = (
        df["skill_gap"] / df["demand"]
    ) * 100

    return df


# Identify shortages and surpluses
def identify_shortages():

    df = calculate_skill_gaps()

    shortages = df[df["skill_gap"] > 0]

    return shortages.sort_values(
        by="skill_gap",
        ascending=False
    )


def identify_surpluses():

    df = calculate_skill_gaps()

    surpluses = df[df["skill_gap"] < 0]

    return surpluses.sort_values(
        by="skill_gap"
    )


# State-wise analysis
def state_wise_analysis():

    df = calculate_skill_gaps()

    result = df.groupby("state").agg(
        total_demand=("demand", "sum"),
        total_workers=("available_workers", "sum"),
        total_gap=("skill_gap", "sum")
    ).reset_index()

    result["gap_percentage"] = (
        result["total_gap"] / result["total_demand"]
    ) * 100

    return result.sort_values(
        by="total_gap",
        ascending=False
    )


# Most demanded skills
def most_demanded_skills():

    df = load_employment_data()

    result = df.groupby("skill")["demand"].sum()

    return result.sort_values(ascending=False)


# Industry-wise analysis
def industry_wise_analysis():

    df = calculate_skill_gaps()

    result = df.groupby("industry").agg(
        total_demand=("demand", "sum"),
        total_workers=("available_workers", "sum"),
        total_gap=("skill_gap", "sum")
    ).reset_index()

    return result.sort_values(
        by="total_gap",
        ascending=False
    )


# Test the engine
if __name__ == "__main__":

    print("\n========== SKILL GAP ANALYSIS ==========")

    print("\n1. SKILL SHORTAGES")

    print(identify_shortages().to_string(index=False))

    print("\n2. SKILL SURPLUSES")

    print(identify_surpluses().to_string(index=False))

    print("\n3. STATE-WISE ANALYSIS")

    print(state_wise_analysis().to_string(index=False))

    print("\n4. MOST DEMANDED SKILLS")

    print(most_demanded_skills().to_string())

    print("\n5. INDUSTRY-WISE ANALYSIS")

    print(industry_wise_analysis().to_string(index=False))