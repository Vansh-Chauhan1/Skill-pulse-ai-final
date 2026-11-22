import { useState, type FormEvent } from "react";
import "./Dashboard.css";
import IndiaSkillMap from "../components/IndiaSkillMap";
import { getPrediction } from "../services/api";

type PredictionResult = {
  demand: number;
  available_workers: number;
  skill_gap: number;
  gap_percentage: number;
  predicted_status: string;
};

function Dashboard() {
  const [demand, setDemand] = useState("10000");
  const [availableWorkers, setAvailableWorkers] = useState("7000");

  const [prediction, setPrediction] =
    useState<PredictionResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePrediction = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const demandValue = Number(demand);
    const workersValue = Number(availableWorkers);

    if (!Number.isFinite(demandValue) || demandValue <= 0) {
      setError("Enter a valid demand greater than zero.");
      return;
    }

    if (!Number.isFinite(workersValue) || workersValue < 0) {
      setError("Enter a valid number of available workers.");
      return;
    }

    setLoading(true);
    setError("");
    setPrediction(null);

    try {
      const result = await getPrediction(demandValue, workersValue);
      setPrediction(result);
    } catch {
      setError("Prediction failed. Check whether the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <nav className="dashboard-nav">
        <h2 className="dashboard-logo">SkillPulse AI</h2>

        <div className="nav-links">
          <a href="/">Home</a>
          <a href="/dashboard">Dashboard</a>
        </div>
      </nav>

      <main className="dashboard-content">
        <header className="dashboard-header">
          <h1>India Skill Gap Dashboard</h1>
          <p>
            Analyze workforce demand, employment availability
            and skill shortages across India.
          </p>
        </header>

        <section className="stats-grid">
          <div className="stat-card">
            <h3>Total Workforce Demand</h3>
            <h2>--</h2>
          </div>

          <div className="stat-card">
            <h3>Available Workers</h3>
            <h2>--</h2>
          </div>

          <div className="stat-card">
            <h3>National Skill Gap</h3>
            <h2>--</h2>
          </div>
        </section>

        {/* AI Prediction Panel */}
        <section className="prediction-section">
          <h2>AI Skill Gap Predictor</h2>
          <p>
            Enter workforce data to identify whether a skill shortage
            or surplus is likely.
          </p>

          <form onSubmit={handlePrediction} className="prediction-form">
            <div className="form-group">
              <label htmlFor="demand">Workforce Demand</label>
              <input
                id="demand"
                type="number"
                min="1"
                value={demand}
                onChange={(e) => setDemand(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="workers">Available Workers</label>
              <input
                id="workers"
                type="number"
                min="0"
                value={availableWorkers}
                onChange={(e) => setAvailableWorkers(e.target.value)}
                required
              />
            </div>

            <button type="submit" disabled={loading}>
              {loading ? "Analyzing..." : "Predict Skill Gap"}
            </button>
          </form>

          {error && <p className="prediction-error">{error}</p>}

          {prediction && (
            <div className="prediction-result">
              <h3>Prediction Results</h3>

              <p>
                <strong>Skill Gap:</strong>{" "}
                {prediction.skill_gap.toLocaleString("en-IN")} workers
              </p>

              <p>
                <strong>Gap Percentage:</strong>{" "}
                {prediction.gap_percentage.toFixed(2)}%
              </p>

              <p>
                <strong>AI Predicted Status:</strong>{" "}
                {prediction.predicted_status}
              </p>
            </div>
          )}
        </section>

        {/* India Map */}
        <section className="map-section">
          <div className="map-header">
            <h2>State-wise Skill Gap Analysis</h2>
            <p>
              Select a state to explore employment demand
              and workforce availability.
            </p>
          </div>

          <IndiaSkillMap />
        </section>
      </main>
    </div>
  );
}

export default Dashboard;