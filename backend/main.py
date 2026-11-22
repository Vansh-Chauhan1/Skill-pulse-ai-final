from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["http://localhost:5173"],
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