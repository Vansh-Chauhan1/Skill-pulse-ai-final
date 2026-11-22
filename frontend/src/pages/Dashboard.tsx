import { useEffect, useState, type FormEvent } from "react";

import "./Dashboard.css";

import IndiaSkillMap from "../components/IndiaSkillMap";
import { getPrediction, getStates } from "../services/api";

// AI prediction response
type PredictionResult = {
  demand: number;
  available_workers: number;
  skill_gap: number;
  gap_percentage: number | null;
  predicted_status: string;
};

// State-wise backend response
type StateData = {
  state: string;
  total_demand: number;
  total_workers: number;
  total_gap: number;
  gap_percentage: number;
};

function Dashboard() {
  // ==========================================
  // NATIONAL STATISTICS
  // ==========================================

  const [nationalStats, setNationalStats] = useState({
    demand: 0,
    workers: 0,
    gap: 0,
  });

  const [stateRecords, setStateRecords] = useState<StateData[]>([]);

  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState("");

  // ==========================================
  // AI PREDICTION STATES
  // ==========================================

  const [demand, setDemand] = useState("10000");
  const [availableWorkers, setAvailableWorkers] = useState("7000");

  const [prediction, setPrediction] =
    useState<PredictionResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ==========================================
  // FETCH STATE-WISE DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchNationalStats = async () => {
      try {
        const data: StateData[] = await getStates();

        if (!isMounted) return;

        // Save state records for the comparison table
        setStateRecords(data);

        // Calculate national totals
        const totals = data.reduce(
          (acc, item) => ({
            demand:
              acc.demand + Number(item.total_demand || 0),

            workers:
              acc.workers + Number(item.total_workers || 0),

            gap:
              acc.gap + Number(item.total_gap || 0),
          }),
          {
            demand: 0,
            workers: 0,
            gap: 0,
          }
        );

        setNationalStats(totals);
        setStatsError("");
      } catch (err) {
        console.error(
          "Failed to fetch national statistics:",
          err
        );

        if (isMounted) {
          setStatsError(
            "Unable to load employment statistics. Check backend connection."
          );
        }
      } finally {
        if (isMounted) {
          setStatsLoading(false);
        }
      }
    };

    fetchNationalStats();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // AI SKILL GAP PREDICTION
  // ==========================================

  const handlePrediction = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    const demandValue = Number(demand);
    const workersValue = Number(availableWorkers);

    // Validate demand
    if (
      !Number.isFinite(demandValue) ||
      demandValue <= 0
    ) {
      setError("Enter a valid demand greater than zero.");
      return;
    }

    // Validate available workers
    if (
      !Number.isFinite(workersValue) ||
      workersValue < 0
    ) {
      setError("Enter a valid number of available workers.");
      return;
    }

    setLoading(true);
    setError("");
    setPrediction(null);

    try {
      const result = await getPrediction(
        demandValue,
        workersValue
      );

      setPrediction(result);
    } catch (err) {
      console.error("Prediction failed:", err);

      setError(
        "Prediction failed. Please check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // DETERMINE STATE STATUS
  // ==========================================

  const getStatus = (gap: number) => {
    if (gap > 0) return "Shortage";
    if (gap < 0) return "Surplus";
    return "Balanced";
  };

  // ==========================================
  // DASHBOARD UI
  // ==========================================

  return (
    <div className="dashboard">

      {/* NAVIGATION */}
      <nav className="dashboard-nav">

        <h2 className="dashboard-logo">
          SkillPulse AI
        </h2>

        <div className="nav-links">
          <a href="/">Home</a>
          <a href="/dashboard">Dashboard</a>
        </div>

      </nav>

      <main className="dashboard-content">

        {/* DASHBOARD HEADER */}
        <header className="dashboard-header">

          <h1>India Skill Gap Dashboard</h1>

          <p>
            Analyze workforce demand, employment availability
            and skill shortages across India.
          </p>

        </header>

        {/* ======================================
            NATIONAL STATISTICS
        ====================================== */}

        <section className="stats-grid">

          <div className="stat-card">

            <h3>Total Workforce Demand</h3>

            <h2>
              {statsLoading
                ? "Loading..."
                : nationalStats.demand.toLocaleString("en-IN")}
            </h2>

          </div>

          <div className="stat-card">

            <h3>Available Workers</h3>

            <h2>
              {statsLoading
                ? "Loading..."
                : nationalStats.workers.toLocaleString("en-IN")}
            </h2>

          </div>

          <div className="stat-card">

            <h3>Net National Skill Gap</h3>

            <h2>
              {statsLoading
                ? "Loading..."
                : nationalStats.gap.toLocaleString("en-IN")}
            </h2>

          </div>

        </section>

        {statsError && (
          <p className="prediction-error">
            {statsError}
          </p>
        )}

        {/* ======================================
            AI SKILL GAP PREDICTOR
        ====================================== */}

        <section className="prediction-section">

          <h2>AI Skill Gap Predictor</h2>

          <p>
            Enter workforce data to identify whether a
            skill shortage or surplus exists.
          </p>

          <form
            onSubmit={handlePrediction}
            className="prediction-form"
          >

            {/* Workforce Demand */}
            <div className="form-group">

              <label htmlFor="demand">
                Workforce Demand
              </label>

              <input
                id="demand"
                type="number"
                min="1"
                value={demand}
                onChange={(e) => setDemand(e.target.value)}
                required
              />

            </div>

            {/* Available Workers */}
            <div className="form-group">

              <label htmlFor="workers">
                Available Workers
              </label>

              <input
                id="workers"
                type="number"
                min="0"
                value={availableWorkers}
                onChange={(e) =>
                  setAvailableWorkers(e.target.value)
                }
                required
              />

            </div>

            {/* Prediction Button */}
            <button
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Analyzing..."
                : "Predict Skill Gap"}
            </button>

          </form>

          {/* Prediction Error */}
          {error && (
            <p className="prediction-error">
              {error}
            </p>
          )}

          {/* Prediction Results */}
          {prediction && (
            <div className="prediction-result">

              <h3>Prediction Results</h3>

              <p>
                <strong>Workforce Demand:</strong>{" "}
                {prediction.demand.toLocaleString("en-IN")}
              </p>

              <p>
                <strong>Available Workers:</strong>{" "}
                {prediction.available_workers.toLocaleString("en-IN")}
              </p>

              <p>
                <strong>Skill Gap:</strong>{" "}
                {prediction.skill_gap.toLocaleString("en-IN")} workers
              </p>

              <p>
                <strong>Gap Percentage:</strong>{" "}
                {prediction.gap_percentage === null
                  ? "N/A"
                  : `${prediction.gap_percentage.toFixed(2)}%`}
              </p>

              <p>
                <strong>Predicted Status:</strong>{" "}
                {prediction.predicted_status}
              </p>

            </div>
          )}

        </section>

        {/* ======================================
            INTERACTIVE INDIA SKILL GAP MAP
        ====================================== */}

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

        {/* ======================================
            STATE-WISE EMPLOYMENT TABLE
        ====================================== */}

        <section className="state-table-section">

          <div className="table-heading">

            <h2>State-wise Employment Analysis</h2>

            <p>
              Compare workforce demand, available workers
              and skill gaps across states.
            </p>

          </div>

          <div className="table-scroll">

            <table className="state-table">

              <thead>
                <tr>
                  <th>State</th>
                  <th>Workforce Demand</th>
                  <th>Available Workers</th>
                  <th>Net Skill Gap</th>
                  <th>Gap Percentage</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>

                {stateRecords.map((item) => {
                  const gap = Number(item.total_gap);
                  const percentage = Number(item.gap_percentage);

                  const status = getStatus(gap);

                  return (
                    <tr key={item.state}>

                      <td>{item.state}</td>

                      <td>
                        {Number(item.total_demand).toLocaleString("en-IN")}
                      </td>

                      <td>
                        {Number(item.total_workers).toLocaleString("en-IN")}
                      </td>

                      <td>
                        {gap > 0 ? "+" : ""}
                        {gap.toLocaleString("en-IN")}
                      </td>

                      <td>
                        {percentage.toFixed(2)}%
                      </td>

                      <td>
                        <span
                          className={`status-badge ${status.toLowerCase()}`}
                        >
                          {status}
                        </span>
                      </td>

                    </tr>
                  );
                })}

                {!statsLoading && stateRecords.length === 0 && (
                  <tr>
                    <td colSpan={6}>
                      {statsError
                        ? "Unable to load state data."
                        : "No state data available."}
                    </td>
                  </tr>
                )}

                {statsLoading && (
                  <tr>
                    <td colSpan={6}>
                      Loading state data...
                    </td>
                  </tr>
                )}

              </tbody>

            </table>

          </div>

          {/* Dataset Disclaimer */}
          <p className="data-disclaimer">
            Note: The current dashboard uses a synthetic
            demonstration dataset. Real employment data
            will be integrated in a later development phase.
          </p>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;