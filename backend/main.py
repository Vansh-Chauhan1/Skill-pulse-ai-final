from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SkillPulse AI",
    description="AI-powered Indian Employment and Skill Gap Intelligence Platform",
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
        "message": "Welcome to SkillPulse AI Backend",
        "status": "Operational"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "backend": "connected",
        "project": "SkillPulse AI"
    }