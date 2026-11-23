import json

from services.official_data import (
    load_plfs_state_wpr,
    load_plfs_industry_distribution,
    load_ncs_sector_vacancies,
    load_ncs_qualification_vacancies,
    load_ncs_summary,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.predictor import predict_skill_gap

from services.skill_gap import (
    calculate_skill_gaps,
    identify_shortages,
    identify_surpluses,
    state_wise_analysis,
    most_demanded_skills,
    industry_wise_analysis
)

app = FastAPI(
    title="SkillPulse AI",
    description="Indian Employment and Skill Gap Intelligence Platform",
    version="1.0.0"
)

# Frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175"
],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "project": "SkillPulse AI",
        "status": "Operational"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "backend": "connected",
        "project": "SkillPulse AI"
    }


# Overall skill gap data
@app.get("/api/skill-gaps")
def get_skill_gaps():

    df = calculate_skill_gaps()

    return df.to_dict(orient="records")


# State-wise analysis
@app.get("/api/states")
def get_states():

    df = state_wise_analysis()

    return df.to_dict(orient="records")


# Industry-wise analysis
@app.get("/api/industries")
def get_industries():

    df = industry_wise_analysis()

    return df.to_dict(orient="records")


# Most demanded skills
@app.get("/api/skills")
def get_skills():

    df = most_demanded_skills()

    result = df.reset_index()

    result.columns = ["skill", "total_demand"]

    return result.to_dict(orient="records")


# Skill shortages
@app.get("/api/shortages")
def get_shortages():

    df = identify_shortages()

    return df.to_dict(orient="records")


# Skill surpluses
@app.get("/api/surpluses")
def get_surpluses():

    df = identify_surpluses()

    return df.to_dict(orient="records")

@app.get("/api/predict")
def predict(
    demand: float,
    available_workers: float
):
    return predict_skill_gap(
        demand=demand,
        available_workers=available_workers
    )
# ==========================================
# OFFICIAL PLFS AND NCS DATA API
# ==========================================

def dataframe_to_records(df):
    return json.loads(
        df.to_json(orient="records")
    )


# PLFS: State-wise Worker Population Ratio

@app.get("/api/official/plfs/state-wpr")
def official_plfs_state_wpr():

    df = load_plfs_state_wpr()

    return dataframe_to_records(df)


# PLFS: Industry-wise Employment Distribution

@app.get("/api/official/plfs/industry-distribution")
def official_plfs_industry_distribution():

    df = load_plfs_industry_distribution()

    return dataframe_to_records(df)


# NCS: Sector-wise Vacancies

@app.get("/api/official/ncs/sector-vacancies")
def official_ncs_sector_vacancies():

    df = load_ncs_sector_vacancies()

    return dataframe_to_records(df)


# NCS: Qualification-wise Vacancies

@app.get("/api/official/ncs/qualification-vacancies")
def official_ncs_qualification_vacancies():

    df = load_ncs_qualification_vacancies()

    return dataframe_to_records(df)


# NCS: Summary Statistics

@app.get("/api/official/ncs/summary")
def official_ncs_summary():

    df = load_ncs_summary()

    return dataframe_to_records(df)