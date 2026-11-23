import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

import "./Dashboard.css";

import IndiaSkillMap from "../components/IndiaSkillMap";

import {
  getPrediction,
  getStates,
  getIndustries,
  getSkills,
  getSkillGaps,
} from "../services/api";

// ==========================================
// TYPES
// ==========================================

type PredictionResult = {
  demand: number;
  available_workers: number;
  skill_gap: number;
  gap_percentage: number | null;
  predicted_status: string;
};

type StateData = {
  state: string;
  total_demand: number;
  total_workers: number;
  total_gap: number;
  gap_percentage: number;
};

type IndustryData = {
  industry: string;
  total_demand: number;
  total_workers: number;
  total_gap: number;
};

type SkillData = {
  skill: string;
  total_demand: number;
};

type SkillGapRecord = {
  state: string;
  industry: string;
  skill: string;
  demand: number;
  available_workers: number;
  skill_gap: number;
  gap_percentage: number;
};

type StateSortOption =
  | "total_gap"
  | "gap_percentage"
  | "total_demand"
  | "state";

// ==========================================
// DASHBOARD COMPONENT
// ==========================================

function Dashboard() {

  // ==========================================
  // NATIONAL STATISTICS
  // ==========================================

  const [nationalStats, setNationalStats] = useState({
    demand: 0,
    workers: 0,
    gap: 0,
  });

  const [stateRecords, setStateRecords] =
    useState<StateData[]>([]);

  const [statsLoading, setStatsLoading] =
    useState(true);

  const [statsError, setStatsError] =
    useState("");

  // ==========================================
  // STATE SEARCH AND SORTING
  // ==========================================

  const [stateSearch, setStateSearch] =
    useState("");

  const [stateSortBy, setStateSortBy] =
    useState<StateSortOption>("total_gap");

  // ==========================================
  // INDUSTRY DATA
  // ==========================================

  const [industryRecords, setIndustryRecords] =
    useState<IndustryData[]>([]);

  const [industryLoading, setIndustryLoading] =
    useState(true);

  const [industryError, setIndustryError] =
    useState("");

  const [selectedIndustry, setSelectedIndustry] =
    useState("all");

  // ==========================================
  // SKILL DATA
  // ==========================================

  const [skillRecords, setSkillRecords] =
    useState<SkillData[]>([]);

  const [skillsLoading, setSkillsLoading] =
    useState(true);

  const [skillsError, setSkillsError] =
    useState("");

  const [skillSearch, setSkillSearch] =
    useState("");

  // ==========================================
  // STATE-WISE INDUSTRY COMPARISON DATA
  // ==========================================

  const [gapRecords, setGapRecords] =
    useState<SkillGapRecord[]>([]);

  const [comparisonLoading, setComparisonLoading] =
    useState(true);

  const [comparisonError, setComparisonError] =
    useState("");

  const [selectedComparisonState, setSelectedComparisonState] =
    useState("");

  // ==========================================
  // AI PREDICTION
  // ==========================================

  const [demand, setDemand] =
    useState("10000");

  const [availableWorkers, setAvailableWorkers] =
    useState("7000");

  const [prediction, setPrediction] =
    useState<PredictionResult | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  // ==========================================
  // FETCH NATIONAL AND STATE DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchNationalStats = async () => {
      try {
        const data: StateData[] = await getStates();

        if (!isMounted) return;

        const formattedData = data.map((item) => ({
          state: item.state,
          total_demand: Number(item.total_demand || 0),
          total_workers: Number(item.total_workers || 0),
          total_gap: Number(item.total_gap || 0),
          gap_percentage: Number(item.gap_percentage || 0),
        }));

        setStateRecords(formattedData);

        const totals = formattedData.reduce(
          (acc, item) => ({
            demand: acc.demand + item.total_demand,
            workers: acc.workers + item.total_workers,
            gap: acc.gap + item.total_gap,
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
  // FETCH INDUSTRY DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchIndustryData = async () => {
      try {
        const data: IndustryData[] =
          await getIndustries();

        if (!isMounted) return;

        const formattedData = data.map((item) => ({
          industry: item.industry,
          total_demand: Number(item.total_demand || 0),
          total_workers: Number(item.total_workers || 0),
          total_gap: Number(item.total_gap || 0),
        }));

        setIndustryRecords(formattedData);
        setIndustryError("");

      } catch (err) {
        console.error(
          "Failed to fetch industry data:",
          err
        );

        if (isMounted) {
          setIndustryError(
            "Unable to load industry data."
          );
        }

      } finally {
        if (isMounted) {
          setIndustryLoading(false);
        }
      }
    };

    fetchIndustryData();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // FETCH SKILL DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchSkillData = async () => {
      try {
        const data: SkillData[] = await getSkills();

        if (!isMounted) return;

        const formattedData = data
          .map((item) => ({
            skill: item.skill,
            total_demand: Number(item.total_demand || 0),
          }))
          .sort(
            (a, b) =>
              b.total_demand - a.total_demand
          );

        setSkillRecords(formattedData);
        setSkillsError("");

      } catch (err) {
        console.error(
          "Failed to fetch skill data:",
          err
        );

        if (isMounted) {
          setSkillsError(
            "Unable to load skill demand data."
          );
        }

      } finally {
        if (isMounted) {
          setSkillsLoading(false);
        }
      }
    };

    fetchSkillData();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // FETCH STATE-WISE INDUSTRY DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchGapRecords = async () => {
      try {
        const data: SkillGapRecord[] =
          await getSkillGaps();

        if (!isMounted) return;

        const formattedData = data.map((item) => ({
          state: item.state,
          industry: item.industry,
          skill: item.skill,
          demand: Number(item.demand || 0),
          available_workers: Number(
            item.available_workers || 0
          ),
          skill_gap: Number(item.skill_gap || 0),
          gap_percentage: Number(
            item.gap_percentage || 0
          ),
        }));

        setGapRecords(formattedData);
        setComparisonError("");

      } catch (err) {
        console.error(
          "Failed to fetch state-wise industry data:",
          err
        );

        if (isMounted) {
          setComparisonError(
            "Unable to load state-wise industry data."
          );
        }

      } finally {
        if (isMounted) {
          setComparisonLoading(false);
        }
      }
    };

    fetchGapRecords();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // STATE TABLE FILTERING AND SORTING
  // ==========================================

  const filteredStateRecords = useMemo(() => {

    const searchValue = stateSearch
      .trim()
      .toLowerCase();

    const filtered = stateRecords.filter((item) =>
      item.state.toLowerCase().includes(searchValue)
    );

    return filtered.sort((a, b) => {

      switch (stateSortBy) {

        case "state":
          return a.state.localeCompare(b.state);

        case "total_gap":
          return b.total_gap - a.total_gap;

        case "gap_percentage":
          return b.gap_percentage - a.gap_percentage;

        case "total_demand":
          return b.total_demand - a.total_demand;

        default:
          return 0;
      }
    });

  }, [stateRecords, stateSearch, stateSortBy]);

  // ==========================================
  // INDUSTRY FILTERING
  // ==========================================

  const filteredIndustryRecords = useMemo(() => {

    if (selectedIndustry === "all") {
      return industryRecords;
    }

    return industryRecords.filter(
      (item) => item.industry === selectedIndustry
    );

  }, [industryRecords, selectedIndustry]);

  // ==========================================
  // SKILL SEARCH
  // ==========================================

  const filteredSkillRecords = useMemo(() => {

    const searchValue = skillSearch
      .trim()
      .toLowerCase();

    return skillRecords.filter((item) =>
      item.skill.toLowerCase().includes(searchValue)
    );

  }, [skillRecords, skillSearch]);

  // Display top 10 normally, all matches when searching
  const displayedSkillRecords = useMemo(() => {

    if (skillSearch.trim()) {
      return filteredSkillRecords;
    }

    return filteredSkillRecords.slice(0, 10);

  }, [filteredSkillRecords, skillSearch]);

  // ==========================================
  // TOP 10 SHORTAGE STATES
  // ==========================================

  const topShortageStates = useMemo(() => {

    return [...stateRecords]
      .filter((item) => item.total_gap > 0)
      .sort(
        (a, b) =>
          b.total_gap - a.total_gap
      )
      .slice(0, 10);

  }, [stateRecords]);

  // ==========================================
  // STATE-WISE INDUSTRY COMPARISON
  // ==========================================

  const comparisonStates = useMemo(() => {

    return [
      ...new Set(
        gapRecords.map((item) => item.state)
      ),
    ].sort();

  }, [gapRecords]);

  const activeComparisonState =
    selectedComparisonState ||
    comparisonStates[0] ||
    "";

  const stateIndustryComparison = useMemo(() => {

    const selectedRecords = gapRecords.filter(
      (item) => item.state === activeComparisonState
    );

    const industryMap = new Map<
      string,
      {
        industry: string;
        total_demand: number;
        total_workers: number;
        total_gap: number;
      }
    >();

    selectedRecords.forEach((item) => {

      const existing = industryMap.get(item.industry);

      if (existing) {

        existing.total_demand += item.demand;
        existing.total_workers += item.available_workers;
        existing.total_gap += item.skill_gap;

      } else {

        industryMap.set(item.industry, {
          industry: item.industry,
          total_demand: item.demand,
          total_workers: item.available_workers,
          total_gap: item.skill_gap,
        });

      }
    });

    return Array.from(industryMap.values());

  }, [gapRecords, activeComparisonState]);

  // ==========================================
  // AI SKILL GAP PREDICTION
  // ==========================================

  const handlePrediction = async (
    event: FormEvent<HTMLFormElement>
  ) => {

    event.preventDefault();

    const demandValue = Number(demand);
    const workersValue = Number(availableWorkers);

    if (
      !Number.isFinite(demandValue) ||
      demandValue <= 0
    ) {
      setError(
        "Enter a valid demand greater than zero."
      );
      return;
    }

    if (
      !Number.isFinite(workersValue) ||
      workersValue < 0
    ) {
      setError(
        "Enter a valid number of available workers."
      );
      return;
    }

    setLoading(true);
    setError("");
    setPrediction(null);

    try {

      const result: PredictionResult =
        await getPrediction(
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
  // STATUS CLASSIFICATION
  // ==========================================

  const getStatus = (gap: number) => {

    if (gap > 0) return "Shortage";

    if (gap < 0) return "Surplus";

    return "Balanced";
  };

  // ==========================================
  // NUMBER FORMATTING
  // ==========================================

  const formatNumber = (value: number) => {
    return value.toLocaleString("en-IN");
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

          <span className="dashboard-eyebrow">
            EMPLOYMENT INTELLIGENCE PLATFORM
          </span>

          <h1>
            India Skill Gap Dashboard
          </h1>

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
                : formatNumber(nationalStats.demand)}
            </h2>

          </div>

          <div className="stat-card">

            <h3>Available Workers</h3>

            <h2>
              {statsLoading
                ? "Loading..."
                : formatNumber(nationalStats.workers)}
            </h2>

          </div>

          <div className="stat-card">

            <h3>Net National Skill Gap</h3>

            <h2
              className={
                nationalStats.gap > 0
                  ? "shortage-value"
                  : nationalStats.gap < 0
                  ? "surplus-value"
                  : ""
              }
            >
              {statsLoading
                ? "Loading..."
                : formatNumber(nationalStats.gap)}
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

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                INTELLIGENCE ENGINE
              </span>

              <h2>AI Skill Gap Predictor</h2>

            </div>

          </div>

          <p className="section-description">
            Enter workforce demand and worker availability
            to calculate the current skill gap.
          </p>

          <form
            onSubmit={handlePrediction}
            className="prediction-form"
          >

            <div className="form-group">

              <label htmlFor="demand">
                Workforce Demand
              </label>

              <input
                id="demand"
                type="number"
                min="1"
                step="any"
                value={demand}
                onChange={(e) =>
                  setDemand(e.target.value)
                }
                required
              />

            </div>

            <div className="form-group">

              <label htmlFor="workers">
                Available Workers
              </label>

              <input
                id="workers"
                type="number"
                min="0"
                step="any"
                value={availableWorkers}
                onChange={(e) =>
                  setAvailableWorkers(e.target.value)
                }
                required
              />

            </div>

            <button
              type="submit"
              disabled={loading}
              className="primary-action"
            >
              {loading
                ? "Analyzing..."
                : "Predict Skill Gap"}
            </button>

          </form>

          {error && (
            <p className="prediction-error">
              {error}
            </p>
          )}

          {/* PREDICTION RESULTS */}

          {prediction && (

            <div className="prediction-result">

              <div className="result-header">

                <h3>Prediction Results</h3>

                <span
                  className={`status-badge ${prediction.predicted_status.toLowerCase()}`}
                >
                  {prediction.predicted_status}
                </span>

              </div>

              <div className="prediction-metrics">

                <div>
                  <span>Workforce Demand</span>

                  <strong>
                    {formatNumber(prediction.demand)}
                  </strong>
                </div>

                <div>
                  <span>Available Workers</span>

                  <strong>
                    {formatNumber(
                      prediction.available_workers
                    )}
                  </strong>
                </div>

                <div>
                  <span>Net Skill Gap</span>

                  <strong>
                    {formatNumber(prediction.skill_gap)}
                  </strong>
                </div>

                <div>
                  <span>Gap Percentage</span>

                  <strong>
                    {prediction.gap_percentage === null
                      ? "N/A"
                      : `${prediction.gap_percentage.toFixed(2)}%`}
                  </strong>
                </div>

              </div>

            </div>

          )}

          <p className="data-disclaimer">
            Current classification uses workforce demand
            minus available workers. It is not a future
            employment forecast.
          </p>

        </section>

        {/* ======================================
            INTERACTIVE INDIA MAP
        ====================================== */}

        <section className="map-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                GEOGRAPHICAL ANALYSIS
              </span>

              <h2>State-wise Skill Gap Analysis</h2>

              <p>
                Select a state to explore employment demand
                and workforce availability.
              </p>

            </div>

          </div>

          <IndiaSkillMap />

        </section>

        {/* ======================================
            STATE-WISE EMPLOYMENT TABLE
        ====================================== */}

        <section className="state-table-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                REGIONAL WORKFORCE DATA
              </span>

              <h2>State-wise Employment Analysis</h2>

              <p>
                Compare workforce demand, available workers
                and skill gaps across states.
              </p>

            </div>

            <span className="record-count">
              {filteredStateRecords.length} states
            </span>

          </div>

          {/* STATE SEARCH AND SORT */}

          <div className="table-controls">

            <input
              type="search"
              placeholder="Search for a state..."
              aria-label="Search states"
              value={stateSearch}
              onChange={(e) =>
                setStateSearch(e.target.value)
              }
            />

            <select
              aria-label="Sort states"
              value={stateSortBy}
              onChange={(e) =>
                setStateSortBy(
                  e.target.value as StateSortOption
                )
              }
            >

              <option value="total_gap">
                Sort by Skill Gap
              </option>

              <option value="gap_percentage">
                Sort by Gap Percentage
              </option>

              <option value="total_demand">
                Sort by Workforce Demand
              </option>

              <option value="state">
                Sort Alphabetically
              </option>

            </select>

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

                {statsLoading ? (

                  <tr>
                    <td colSpan={6}>
                      Loading state data...
                    </td>
                  </tr>

                ) : filteredStateRecords.length === 0 ? (

                  <tr>
                    <td colSpan={6} className="empty-state">
                      No matching states found.
                    </td>
                  </tr>

                ) : (

                  filteredStateRecords.map((item) => {

                    const gap = item.total_gap;
                    const status = getStatus(gap);

                    return (

                      <tr key={item.state}>

                        <td className="state-name">
                          {item.state}
                        </td>

                        <td>
                          {formatNumber(item.total_demand)}
                        </td>

                        <td>
                          {formatNumber(item.total_workers)}
                        </td>

                        <td>

                          <span
                            className={
                              gap > 0
                                ? "shortage-value"
                                : gap < 0
                                ? "surplus-value"
                                : ""
                            }
                          >
                            {gap > 0 ? "+" : ""}
                            {formatNumber(gap)}
                          </span>

                        </td>

                        <td>
                          {item.gap_percentage.toFixed(2)}%
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
                  })

                )}

              </tbody>

            </table>

          </div>

          <p className="data-disclaimer">
            State-wise analysis currently uses our synthetic
            demonstration dataset. Real employment data
            will be integrated later.
          </p>

        </section>

        {/* ======================================
            TOP 10 SHORTAGE STATES
        ====================================== */}

        <section className="top-shortage-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                REGIONAL SHORTAGE INTELLIGENCE
              </span>

              <h2>
                Top 10 States with Highest Skill Shortages
              </h2>

              <p>
                States ranked according to the number of
                additional workers required.
              </p>

            </div>

            <span className="record-count">
              Top {topShortageStates.length} states
            </span>

          </div>

          {statsLoading ? (

            <p className="loading-message">
              Loading shortage rankings...
            </p>

          ) : topShortageStates.length === 0 ? (

            <p className="empty-state">
              No workforce shortages found.
            </p>

          ) : (

            <div
              className="top-shortage-chart"
              style={{
                height: `${Math.max(
                  280,
                  topShortageStates.length * 55
                )}px`,
              }}
            >

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <BarChart
                  data={topShortageStates}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 35,
                    left: 35,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    type="number"
                    stroke="#94a3b8"
                  />

                  <YAxis
                    type="category"
                    dataKey="state"
                    width={130}
                    stroke="#94a3b8"
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                  />

                  <Tooltip
                    formatter={(value) =>
                      `${formatNumber(Number(value))} workers`
                    }
                    contentStyle={{
                      backgroundColor: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Bar
                    dataKey="total_gap"
                    name="Additional Workers Required"
                    fill="#f87171"
                    radius={[0, 6, 6, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          )}

          <p className="data-disclaimer">
            Rankings are based on net state-wise skill gaps.
            Only states with positive skill gaps are included.
          </p>

        </section>

        {/* ======================================
            STATE-WISE INDUSTRY COMPARISON
        ====================================== */}

        <section className="state-industry-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                REGIONAL INDUSTRY INTELLIGENCE
              </span>

              <h2>
                State-wise Industry Comparison
              </h2>

              <p>
                Compare workforce demand and availability
                across industries within a selected state.
              </p>

            </div>

          </div>

          {/* STATE SELECTION */}

          <div className="industry-filter">

            <label htmlFor="comparison-state">
              Select State
            </label>

            <select
              id="comparison-state"
              value={activeComparisonState}
              onChange={(e) =>
                setSelectedComparisonState(e.target.value)
              }
              disabled={comparisonStates.length === 0}
            >

              {comparisonStates.map((state) => (

                <option key={state} value={state}>
                  {state}
                </option>

              ))}

            </select>

          </div>

          {/* COMPARISON CHART */}

          {comparisonLoading ? (

            <p className="loading-message">
              Loading state-wise industry data...
            </p>

          ) : comparisonError ? (

            <p className="prediction-error">
              {comparisonError}
            </p>

          ) : stateIndustryComparison.length === 0 ? (

            <p className="empty-state">
              No industry records available for this state.
            </p>

          ) : (

            <div className="industry-chart">

              <ResponsiveContainer
                width="100%"
                height={360}
              >

                <BarChart
                  data={stateIndustryComparison}
                  margin={{
                    top: 20,
                    right: 25,
                    left: 10,
                    bottom: 15,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    dataKey="industry"
                    stroke="#94a3b8"
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                  />

                  <YAxis
                    stroke="#94a3b8"
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                  />

                  <Tooltip
                    formatter={(value) =>
                      formatNumber(Number(value))
                    }
                    contentStyle={{
                      backgroundColor: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="total_demand"
                    name="Workforce Demand"
                    fill="#38bdf8"
                    radius={[5, 5, 0, 0]}
                  />

                  <Bar
                    dataKey="total_workers"
                    name="Available Workers"
                    fill="#a78bfa"
                    radius={[5, 5, 0, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          )}

          {/* INDUSTRY GAP CARDS */}

          {!comparisonLoading &&
            !comparisonError &&
            stateIndustryComparison.length > 0 && (

              <div className="industry-gap-list">

                {stateIndustryComparison.map((item) => {

                  const status = getStatus(item.total_gap);

                  return (

                    <div
                      className="industry-gap-card"
                      key={item.industry}
                    >

                      <h3>{item.industry}</h3>

                      <p>
                        Workforce Demand:{" "}
                        {formatNumber(item.total_demand)}
                      </p>

                      <p>
                        Available Workers:{" "}
                        {formatNumber(item.total_workers)}
                      </p>

                      <p>
                        Net Skill Gap:{" "}
                        {item.total_gap > 0 ? "+" : ""}
                        {formatNumber(item.total_gap)}
                      </p>

                      <span
                        className={`status-badge ${status.toLowerCase()}`}
                      >
                        {status}
                      </span>

                    </div>

                  );
                })}

              </div>

            )}

          <p className="data-disclaimer">
            Industry comparisons are calculated from
            the selected state's employment records.
          </p>

        </section>

        {/* ======================================
            INDUSTRY-WISE ANALYSIS
        ====================================== */}

        <section className="industry-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                SECTORAL ANALYSIS
              </span>

              <h2>
                Industry-wise Skill Gap Analysis
              </h2>

              <p>
                Compare workforce demand and availability
                across different industries.
              </p>

            </div>

          </div>

          {/* INDUSTRY FILTER */}

          <div className="industry-filter">

            <label htmlFor="industry-select">
              Select Industry
            </label>

            <select
              id="industry-select"
              value={selectedIndustry}
              onChange={(e) =>
                setSelectedIndustry(e.target.value)
              }
            >

              <option value="all">
                All Industries
              </option>

              {industryRecords.map((item) => (

                <option
                  key={item.industry}
                  value={item.industry}
                >
                  {item.industry}
                </option>

              ))}

            </select>

          </div>

          {/* INDUSTRY CHART */}

          {industryLoading ? (

            <p className="loading-message">
              Loading industry data...
            </p>

          ) : industryError ? (

            <p className="prediction-error">
              {industryError}
            </p>

          ) : filteredIndustryRecords.length === 0 ? (

            <p className="empty-state">
              No industry data available.
            </p>

          ) : (

            <>

              <div className="industry-chart">

                <ResponsiveContainer
                  width="100%"
                  height={360}
                >

                  <BarChart
                    data={filteredIndustryRecords}
                    margin={{
                      top: 20,
                      right: 25,
                      left: 10,
                      bottom: 15,
                    }}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#334155"
                    />

                    <XAxis
                      dataKey="industry"
                      stroke="#94a3b8"
                      tick={{
                        fill: "#cbd5e1",
                        fontSize: 12,
                      }}
                    />

                    <YAxis
                      stroke="#94a3b8"
                      tick={{
                        fill: "#cbd5e1",
                        fontSize: 12,
                      }}
                    />

                    <Tooltip
                      formatter={(value) =>
                        formatNumber(Number(value))
                      }
                      contentStyle={{
                        backgroundColor: "#0b1120",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                        color: "#ffffff",
                      }}
                    />

                    <Legend />

                    <Bar
                      dataKey="total_demand"
                      name="Workforce Demand"
                      fill="#38bdf8"
                      radius={[5, 5, 0, 0]}
                    />

                    <Bar
                      dataKey="total_workers"
                      name="Available Workers"
                      fill="#a78bfa"
                      radius={[5, 5, 0, 0]}
                    />

                  </BarChart>

                </ResponsiveContainer>

              </div>

              {/* INDUSTRY SUMMARY CARDS */}

              <div className="industry-gap-list">

                {filteredIndustryRecords.map((item) => {

                  const status = getStatus(item.total_gap);

                  return (

                    <div
                      className="industry-gap-card"
                      key={item.industry}
                    >

                      <h3>{item.industry}</h3>

                      <p>
                        Total Demand:{" "}
                        {formatNumber(item.total_demand)}
                      </p>

                      <p>
                        Available Workers:{" "}
                        {formatNumber(item.total_workers)}
                      </p>

                      <p>
                        Net Skill Gap:{" "}
                        {item.total_gap > 0 ? "+" : ""}
                        {formatNumber(item.total_gap)}
                      </p>

                      <span
                        className={`status-badge ${status.toLowerCase()}`}
                      >
                        {status}
                      </span>

                    </div>

                  );
                })}

              </div>

            </>

          )}

          <p className="data-disclaimer">
            Industry analysis currently uses synthetic
            demonstration data.
          </p>

        </section>

        {/* ======================================
            MOST DEMANDED SKILLS
        ====================================== */}

        <section className="skills-section">

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                SKILL DEMAND INTELLIGENCE
              </span>

              <h2>
                Most Demanded Skills in India
              </h2>

              <p>
                Discover which skills have the highest workforce
                demand across the available employment dataset.
              </p>

            </div>

          </div>

          {/* SKILL SEARCH */}

          <div className="skills-controls">

            <input
              type="search"
              placeholder="Search skills (e.g. Python, Java)..."
              aria-label="Search skills"
              value={skillSearch}
              onChange={(e) =>
                setSkillSearch(e.target.value)
              }
            />

            <span>
              {filteredSkillRecords.length} skills found
            </span>

          </div>

          {/* SKILL CHART */}

          {skillsLoading ? (

            <p className="loading-message">
              Loading skill demand data...
            </p>

          ) : skillsError ? (

            <p className="prediction-error">
              {skillsError}
            </p>

          ) : skillRecords.length === 0 ? (

            <p className="empty-state">
              No skill data available.
            </p>

          ) : displayedSkillRecords.length === 0 ? (

            <p className="empty-state">
              No matching skills found.
            </p>

          ) : (

            <div
              className="skills-chart"
              style={{
                height: `${Math.max(
                  300,
                  displayedSkillRecords.length * 45
                )}px`,
              }}
            >

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <BarChart
                  data={displayedSkillRecords}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 30,
                    left: 30,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    type="number"
                    stroke="#94a3b8"
                  />

                  <YAxis
                    type="category"
                    dataKey="skill"
                    width={150}
                    stroke="#94a3b8"
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                  />

                  <Tooltip
                    formatter={(value) =>
                      formatNumber(Number(value))
                    }
                    contentStyle={{
                      backgroundColor: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Bar
                    dataKey="total_demand"
                    name="Total Workforce Demand"
                    fill="#38bdf8"
                    radius={[0, 5, 5, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          )}

          <p className="data-disclaimer">
            {skillSearch.trim()
              ? "Search results include all matching skills in the dataset."
              : "Showing the top 10 skills by demand. Skill demand is aggregated from the synthetic demonstration dataset."}
          </p>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;