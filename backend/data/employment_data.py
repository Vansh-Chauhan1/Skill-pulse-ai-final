import pandas as pd
from pathlib import Path


def generate_employment_data():

    data = {
        "state": [
            "Maharashtra",
            "Maharashtra",
            "Karnataka",
            "Karnataka",
            "Tamil Nadu",
            "Tamil Nadu",
            "Chhattisgarh",
            "Chhattisgarh",
            "Delhi",
            "Delhi",
            "Uttar Pradesh",
            "Uttar Pradesh"
        ],

        "industry": [
            "IT",
            "Manufacturing",
            "IT",
            "Healthcare",
            "Manufacturing",
            "IT",
            "Mining",
            "IT",
            "IT",
            "Finance",
            "Agriculture",
            "Manufacturing"
        ],

        "skill": [
            "Python",
            "Machine Operation",
            "Java",
            "Nursing",
            "Machine Operation",
            "Data Science",
            "Mining Technology",
            "Python",
            "Cybersecurity",
            "Financial Analysis",
            "Agricultural Technology",
            "Quality Control"
        ],

        "demand": [
            15000,
            12000,
            18000,
            9000,
            11000,
            14000,
            7000,
            5000,
            13000,
            8000,
            10000,
            9000
        ],

        "available_workers": [
            10000,
            14000,
            12000,
            6000,
            8000,
            9000,
            4000,
            2000,
            7000,
            7500,
            6000,
            11000
        ]
    }

    df = pd.DataFrame(data)

    df["skill_gap"] = (
        df["demand"] - df["available_workers"]
    )

    df["gap_percentage"] = (
        df["skill_gap"] / df["demand"]
    ) * 100

    output_path = Path(__file__).parent / "employment_data.csv"

    df.to_csv(output_path, index=False)

    print("Employment dataset generated successfully!")
    print(f"Dataset saved at: {output_path}")

    print("\nDataset Preview:")
    print(df.head(12))


if __name__ == "__main__":
    generate_employment_data()