import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const checkBackend = async () => {
  const response = await API.get("/api/health");
  return response.data;
};

export const getStates = async () => {
  const response = await API.get("/api/states");
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

export default API;

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