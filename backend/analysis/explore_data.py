import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "processed_employment_data.csv"


def explore_data():

    print("\n========== SKILLPULSE DATA ANALYSIS ==========\n")

    df = pd.read_csv(DATA_FILE)

    # 1. Dataset overview
    print("1. DATASET OVERVIEW")
    print("-------------------")

    print("Total records:", len(df))
    print("Total states:", df["state"].nunique())
    print("Total industries:", df["industry"].nunique())
    print("Total skills:", df["skill"].nunique())

    # 2. Overall employment statistics
    print("\n2. EMPLOYMENT STATISTICS")
    print("------------------------")

    print("Total demand:", df["demand"].sum())
    print("Available workers:", df["available_workers"].sum())
    print("Total skill gap:", df["skill_gap"].sum())

    # 3. State-wise skill gap
    print("\n3. STATE-WISE SKILL GAP")
    print("-----------------------")

    state_analysis = df.groupby("state").agg(
        total_demand=("demand", "sum"),
        total_workers=("available_workers", "sum"),
        total_gap=("skill_gap", "sum")
    )

    state_analysis["gap_percentage"] = (
        state_analysis["total_gap"] /
        state_analysis["total_demand"].replace(0, pd.NA)
    ) * 100

    print(state_analysis.sort_values(
        by="total_gap",
        ascending=False
    ).to_string())

    # 4. Industry-wise analysis
    print("\n4. INDUSTRY-WISE ANALYSIS")
    print("-------------------------")

    industry_analysis = df.groupby("industry").agg(
        demand=("demand", "sum"),
        workers=("available_workers", "sum"),
        skill_gap=("skill_gap", "sum")
    )

    print(industry_analysis.sort_values(
        by="skill_gap",
        ascending=False
    ).to_string())

    # 5. Most demanded skills
    print("\n5. MOST DEMANDED SKILLS")
    print("-----------------------")

    skill_analysis = df.groupby("skill")["demand"].sum()

    print(skill_analysis.sort_values(
        ascending=False
    ).head(10).to_string())

    # 6. Skill shortage and surplus
    print("\n6. SHORTAGE VS SURPLUS")
    print("----------------------")

    print(df["gap_status"].value_counts().to_string())

    print("\n========== ANALYSIS COMPLETE ==========")


if __name__ == "__main__":
    explore_data()