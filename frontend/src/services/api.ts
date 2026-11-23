import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// ==========================================
// BACKEND HEALTH
// ==========================================

export const checkBackend = async () => {
  const response = await API.get("/api/health");
  return response.data;
};

// ==========================================
// EXISTING DEMONSTRATION APIs
// ==========================================

export const getStates = async () => {
  const response = await API.get("/api/states");
  return response.data;
};

export const getIndustries = async () => {
  const response = await API.get("/api/industries");
  return response.data;
};

export const getSkills = async () => {
  const response = await API.get("/api/skills");
  return response.data;
};

export const getSkillGaps = async () => {
  const response = await API.get("/api/skill-gaps");
  return response.data;
};

export const getShortages = async () => {
  const response = await API.get("/api/shortages");
  return response.data;
};

export const getSurpluses = async () => {
  const response = await API.get("/api/surpluses");
  return response.data;
};

// ==========================================
// PREDICTION API
// ==========================================

export const getPrediction = async (
  demand: number,
  available_workers: number
) => {
  const response = await API.get("/api/predict", {
    params: {
      demand,
      available_workers,
    },
  });

  return response.data;
};

// ==========================================
// OFFICIAL PLFS APIs
// ==========================================

export const getOfficialPlfsStateWpr = async () => {
  const response = await API.get(
    "/api/official/plfs/state-wpr"
  );

  return response.data;
};

export const getOfficialPlfsIndustryDistribution = async () => {
  const response = await API.get(
    "/api/official/plfs/industry-distribution"
  );

  return response.data;
};

// ==========================================
// OFFICIAL NCS APIs
// ==========================================

export const getOfficialNcsSectorVacancies = async () => {
  const response = await API.get(
    "/api/official/ncs/sector-vacancies"
  );

  return response.data;
};

export const getOfficialNcsQualificationVacancies = async () => {
  const response = await API.get(
    "/api/official/ncs/qualification-vacancies"
  );

  return response.data;
};

export const getOfficialNcsSummary = async () => {
  const response = await API.get(
    "/api/official/ncs/summary"
  );

  return response.data;
};

// ==========================================
// OFFICIAL PLFS WPR FORECAST API
// ==========================================

export const getOfficialPlfsWprForecast = async (
  horizon: number = 1
) => {
  const response = await API.get(
    "/api/official/plfs/wpr-forecast",
    {
      params: { horizon },
    }
  );

  return response.data;
};

export default API;