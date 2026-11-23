import { useEffect, useMemo, useState } from "react";

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
  getOfficialPlfsStateWpr,
  getOfficialPlfsIndustryDistribution,
  getOfficialNcsSectorVacancies,
  getOfficialNcsQualificationVacancies,
  getOfficialNcsSummary,
} from "../services/api";

// ======================================================
// TYPES
// ======================================================

type NumericValue = number | string | null | undefined;

type PlfsStateWpr = {
  state_ut: string;
  survey_period: string;
  age_group: string;
  status_approach: string;

  rural_male_wpr_pct: NumericValue;
  rural_female_wpr_pct: NumericValue;
  rural_person_wpr_pct: NumericValue;

  urban_male_wpr_pct: NumericValue;
  urban_female_wpr_pct: NumericValue;
  urban_person_wpr_pct: NumericValue;

  rural_urban_male_wpr_pct: NumericValue;
  rural_urban_female_wpr_pct: NumericValue;
  rural_urban_person_wpr_pct: NumericValue;

  source_table?: string;
  source_page?: string;
  source_url?: string;
};

type PlfsIndustry = {
  survey_period: string;
  industry_broad_division_nic08: string;

  rural_male_pct: NumericValue;
  rural_female_pct: NumericValue;
  rural_person_pct: NumericValue;

  urban_male_pct: NumericValue;
  urban_female_pct: NumericValue;
  urban_person_pct: NumericValue;

  rural_urban_male_pct: NumericValue;
  rural_urban_female_pct: NumericValue;
  rural_urban_person_pct: NumericValue;

  indicator?: string;
  source_statement?: string;
  source_page?: string;
  source_url?: string;
};

type NcsSector = {
  ncs_sector_as_published: string;
  vacancies_fy2022_23: NumericValue;
  vacancies_fy2023_24: NumericValue;
  reported_percent_change: NumericValue;
  source_report?: string;
  source_url?: string;
};

type NcsQualification = {
  qualification_as_published: string;
  vacancies_fy2022_23: NumericValue;
  vacancies_fy2023_24: NumericValue;
  reported_percent_change: NumericValue;
  source_report?: string;
  source_url?: string;
};

type NcsSummary = {
  metric_as_published: string;
  value_fy2022_23: NumericValue;
  value_fy2023_24: NumericValue;
  reported_percent_change: NumericValue;
  source_report?: string;
  source_url?: string;
};

type StateSortOption = "wpr_desc" | "wpr_asc" | "name";

// ======================================================
// HELPER FUNCTIONS
// ======================================================

function toNumber(value: NumericValue): number | null {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value: NumericValue): string {
  const parsed = toNumber(value);

  if (parsed === null) {
    return "—";
  }

  return parsed.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
}

function formatPercentage(value: NumericValue): string {
  const parsed = toNumber(value);

  if (parsed === null) {
    return "—";
  }

  return `${parsed.toFixed(1)}%`;
}

function formatChange(value: NumericValue): string {
  const parsed = toNumber(value);

  if (parsed === null) {
    return "—";
  }

  return `${parsed > 0 ? "+" : ""}${parsed}%`;
}

function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "")
    .trim();
}

function isAllIndiaRecord(stateName: string): boolean {
  const normalized = normalizeText(stateName);

  return (
    normalized === "allindia" ||
    normalized === "india" ||
    normalized === "allindiatotal"
  );
}

// ======================================================
// DASHBOARD COMPONENT
// ======================================================

function Dashboard() {
  // ----------------------------------------------------
  // PLFS STATE WPR DATA
  // ----------------------------------------------------

  const [plfsStateRows, setPlfsStateRows] = useState<
    PlfsStateWpr[]
  >([]);

  const [plfsStateLoading, setPlfsStateLoading] =
    useState(true);

  const [plfsStateError, setPlfsStateError] =
    useState("");

  // ----------------------------------------------------
  // PLFS INDUSTRY DATA
  // ----------------------------------------------------

  const [industryRows, setIndustryRows] = useState<
    PlfsIndustry[]
  >([]);

  const [industryLoading, setIndustryLoading] =
    useState(true);

  const [industryError, setIndustryError] =
    useState("");

  const [selectedIndustryPeriod, setSelectedIndustryPeriod] =
    useState("2023-24");

  // ----------------------------------------------------
  // NCS SECTOR VACANCY DATA
  // ----------------------------------------------------

  const [sectorRows, setSectorRows] = useState<
    NcsSector[]
  >([]);

  const [sectorLoading, setSectorLoading] =
    useState(true);

  const [sectorError, setSectorError] =
    useState("");

  // ----------------------------------------------------
  // NCS QUALIFICATION VACANCY DATA
  // ----------------------------------------------------

  const [qualificationRows, setQualificationRows] =
    useState<NcsQualification[]>([]);

  const [qualificationLoading, setQualificationLoading] =
    useState(true);

  const [qualificationError, setQualificationError] =
    useState("");

  // ----------------------------------------------------
  // NCS SUMMARY DATA
  // ----------------------------------------------------

  const [ncsSummaryRows, setNcsSummaryRows] = useState<
    NcsSummary[]
  >([]);

  const [ncsSummaryLoading, setNcsSummaryLoading] =
    useState(true);

  const [ncsSummaryError, setNcsSummaryError] =
    useState("");

  // ----------------------------------------------------
  // STATE TABLE SEARCH AND SORTING
  // ----------------------------------------------------

  const [stateSearch, setStateSearch] = useState("");

  const [stateSortBy, setStateSortBy] =
    useState<StateSortOption>("wpr_desc");

  // ====================================================
  // FETCH OFFICIAL DATA
  // ====================================================

  useEffect(() => {
    let isMounted = true;

    const fetchOfficialData = async () => {
      const results = await Promise.allSettled([
        getOfficialPlfsStateWpr(),
        getOfficialPlfsIndustryDistribution(),
        getOfficialNcsSectorVacancies(),
        getOfficialNcsQualificationVacancies(),
        getOfficialNcsSummary(),
      ]);

      if (!isMounted) return;

      // -----------------------------------------------
      // 1. PLFS STATE-WISE WPR
      // -----------------------------------------------

      const stateResult = results[0];

      if (stateResult.status === "fulfilled") {
        setPlfsStateRows(
          Array.isArray(stateResult.value)
            ? (stateResult.value as PlfsStateWpr[])
            : []
        );

        setPlfsStateError("");
      } else {
        console.error(
          "Failed to load PLFS state WPR:",
          stateResult.reason
        );

        setPlfsStateError(
          "Unable to load PLFS state-wise WPR data."
        );
      }

      setPlfsStateLoading(false);

      // -----------------------------------------------
      // 2. PLFS INDUSTRY DISTRIBUTION
      // -----------------------------------------------

      const industryResult = results[1];

      if (industryResult.status === "fulfilled") {
        setIndustryRows(
          Array.isArray(industryResult.value)
            ? (industryResult.value as PlfsIndustry[])
            : []
        );

        setIndustryError("");
      } else {
        console.error(
          "Failed to load PLFS industry data:",
          industryResult.reason
        );

        setIndustryError(
          "Unable to load PLFS industry distribution."
        );
      }

      setIndustryLoading(false);

      // -----------------------------------------------
      // 3. NCS SECTOR VACANCIES
      // -----------------------------------------------

      const sectorResult = results[2];

      if (sectorResult.status === "fulfilled") {
        setSectorRows(
          Array.isArray(sectorResult.value)
            ? (sectorResult.value as NcsSector[])
            : []
        );

        setSectorError("");
      } else {
        console.error(
          "Failed to load NCS sector vacancies:",
          sectorResult.reason
        );

        setSectorError(
          "Unable to load NCS sector vacancy data."
        );
      }

      setSectorLoading(false);

      // -----------------------------------------------
      // 4. NCS QUALIFICATION VACANCIES
      // -----------------------------------------------

      const qualificationResult = results[3];

      if (qualificationResult.status === "fulfilled") {
        setQualificationRows(
          Array.isArray(qualificationResult.value)
            ? (qualificationResult.value as NcsQualification[])
            : []
        );

        setQualificationError("");
      } else {
        console.error(
          "Failed to load NCS qualification vacancies:",
          qualificationResult.reason
        );

        setQualificationError(
          "Unable to load NCS qualification vacancy data."
        );
      }

      setQualificationLoading(false);

      // -----------------------------------------------
      // 5. NCS SUMMARY
      // -----------------------------------------------

      const summaryResult = results[4];

      if (summaryResult.status === "fulfilled") {
        setNcsSummaryRows(
          Array.isArray(summaryResult.value)
            ? (summaryResult.value as NcsSummary[])
            : []
        );

        setNcsSummaryError("");
      } else {
        console.error(
          "Failed to load NCS summary:",
          summaryResult.reason
        );

        setNcsSummaryError(
          "Unable to load NCS summary statistics."
        );
      }

      setNcsSummaryLoading(false);
    };

    fetchOfficialData();

    return () => {
      isMounted = false;
    };
  }, []);

  // ====================================================
  // PLFS NATIONAL RECORD
  // ====================================================

  const allIndiaRecord = useMemo(() => {
    return plfsStateRows.find((row) =>
      isAllIndiaRecord(row.state_ut)
    );
  }, [plfsStateRows]);

  // ====================================================
  // PLFS STATE RECORDS
  // ====================================================

  const stateRecords = useMemo(() => {
    return plfsStateRows.filter(
      (row) => !isAllIndiaRecord(row.state_ut)
    );
  }, [plfsStateRows]);

  // ====================================================
  // FILTERED AND SORTED STATE RECORDS
  // ====================================================

  const filteredStateRecords = useMemo(() => {
    const searchValue = stateSearch
      .trim()
      .toLowerCase();

    const filtered = stateRecords.filter((row) =>
      row.state_ut.toLowerCase().includes(searchValue)
    );

    return [...filtered].sort((a, b) => {
      const aWpr =
        toNumber(a.rural_urban_person_wpr_pct) ?? -Infinity;

      const bWpr =
        toNumber(b.rural_urban_person_wpr_pct) ?? -Infinity;

      switch (stateSortBy) {
        case "wpr_desc":
          return bWpr - aWpr;

        case "wpr_asc":
          return aWpr - bWpr;

        case "name":
          return a.state_ut.localeCompare(b.state_ut);

        default:
          return 0;
      }
    });
  }, [stateRecords, stateSearch, stateSortBy]);

  // ====================================================
  // PLFS INDUSTRY PERIODS
  // ====================================================

  const industryPeriods = useMemo(() => {
    return [
      ...new Set(
        industryRows.map((row) => row.survey_period)
      ),
    ].sort();
  }, [industryRows]);

  // ====================================================
  // PLFS INDUSTRY CHART DATA
  // ====================================================

  const industryChartData = useMemo(() => {
    return industryRows
      .filter(
        (row) =>
          row.survey_period === selectedIndustryPeriod
      )
      .map((row) => ({
        industry: row.industry_broad_division_nic08,
        employmentShare:
          toNumber(row.rural_urban_person_pct),
      }))
      .sort(
        (a, b) =>
          (b.employmentShare ?? -Infinity) -
          (a.employmentShare ?? -Infinity)
      );
  }, [industryRows, selectedIndustryPeriod]);

  // ====================================================
  // NCS SECTOR CHART DATA
  // ====================================================

  const sectorChartData = useMemo(() => {
    return sectorRows
      .map((row) => ({
        sector: row.ncs_sector_as_published,
        fy2022_23: toNumber(row.vacancies_fy2022_23),
        fy2023_24: toNumber(row.vacancies_fy2023_24),
      }))
      .sort(
        (a, b) =>
          (b.fy2023_24 ?? -Infinity) -
          (a.fy2023_24 ?? -Infinity)
      );
  }, [sectorRows]);

  // ====================================================
  // NCS QUALIFICATION CHART DATA
  // ====================================================

  const qualificationChartData = useMemo(() => {
    return qualificationRows
      .map((row) => ({
        qualification: row.qualification_as_published,
        fy2022_23: toNumber(row.vacancies_fy2022_23),
        fy2023_24: toNumber(row.vacancies_fy2023_24),
      }))
      .sort(
        (a, b) =>
          (b.fy2023_24 ?? -Infinity) -
          (a.fy2023_24 ?? -Infinity)
      );
  }, [qualificationRows]);

  // ====================================================
  // NCS SUMMARY CARDS
  // ====================================================

  const ncsSummaryCards = useMemo(() => {
    return ncsSummaryRows.map((row) => ({
      label: row.metric_as_published,
      previous: toNumber(row.value_fy2022_23),
      current: toNumber(row.value_fy2023_24),
      change: toNumber(row.reported_percent_change),
    }));
  }, [ncsSummaryRows]);

  // ====================================================
  // RENDER DASHBOARD
  // ====================================================

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
        {/* HEADER */}

        <header className="dashboard-header">
          <span className="dashboard-eyebrow">
            OFFICIAL EMPLOYMENT DATA INTELLIGENCE
          </span>

          <h1>India Skill Gap Dashboard</h1>

          <p>
            Explore workforce participation, industry-wise
            employment distribution and vacancies reported
            through the National Career Service.
          </p>
        </header>

        {/* =================================================
            PLFS NATIONAL WPR STATISTICS
        ================================================= */}

        <section className="stats-grid">
          <div className="stat-card">
            <h3>All India WPR</h3>

            <h2>
              {plfsStateLoading
                ? "Loading..."
                : formatPercentage(
                    allIndiaRecord?.rural_urban_person_wpr_pct
                  )}
            </h2>

            <p>Rural + Urban</p>
          </div>

          <div className="stat-card">
            <h3>Rural WPR</h3>

            <h2>
              {plfsStateLoading
                ? "Loading..."
                : formatPercentage(
                    allIndiaRecord?.rural_person_wpr_pct
                  )}
            </h2>

            <p>Rural population</p>
          </div>

          <div className="stat-card">
            <h3>Urban WPR</h3>

            <h2>
              {plfsStateLoading
                ? "Loading..."
                : formatPercentage(
                    allIndiaRecord?.urban_person_wpr_pct
                  )}
            </h2>

            <p>Urban population</p>
          </div>
        </section>

        {/* IMPORTANT: PLFS DATA DISCLAIMER */}

        <p className="data-disclaimer">
          Source: MoSPI, PLFS Annual Report 2025. These are
          annual usual-status estimates (ps+ss) for all ages.
          They should not be directly compared with monthly
          PLFS Current Weekly Status (CWS) estimates, which
          use a different reference period and may use a
          different age group.
        </p>

        {plfsStateError && (
          <p className="prediction-error">
            {plfsStateError}
          </p>
        )}

        {/* =================================================
            INDIA WPR MAP
        ================================================= */}

        <section className="map-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                GEOGRAPHIC EMPLOYMENT DATA
              </span>

              <h2>India Worker Population Ratio Map</h2>

              <p>
                Select a state or union territory to explore
                its reported Worker Population Ratio.
              </p>
            </div>
          </div>

          <IndiaSkillMap />

          <p className="data-disclaimer">
            Source: MoSPI, PLFS Annual Report 2025,
            state-wise Worker Population Ratio data.
            WPR is an employment indicator; it is not a
            direct measurement of skill demand or skill shortage.
          </p>
        </section>

        {/* =================================================
            STATE-WISE PLFS TABLE
        ================================================= */}

        <section className="state-table-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                STATE-WISE PLFS DATA
              </span>

              <h2>Worker Population Ratio by State</h2>

              <p>
                State and union territory estimates from
                the PLFS annual dataset.
              </p>
            </div>

            <span className="record-count">
              {stateRecords.length} regions
            </span>
          </div>

          <div className="table-controls">
            <input
              type="text"
              placeholder="Search state or union territory..."
              value={stateSearch}
              onChange={(event) =>
                setStateSearch(event.target.value)
              }
            />

            <select
              value={stateSortBy}
              onChange={(event) =>
                setStateSortBy(
                  event.target.value as StateSortOption
                )
              }
            >
              <option value="wpr_desc">
                Highest WPR first
              </option>

              <option value="wpr_asc">
                Lowest WPR first
              </option>

              <option value="name">
                Sort alphabetically
              </option>
            </select>
          </div>

          {plfsStateLoading ? (
            <p className="loading-message">
              Loading state-wise PLFS data...
            </p>
          ) : plfsStateError ? (
            <p className="prediction-error">
              {plfsStateError}
            </p>
          ) : (
            <div className="table-scroll">
              <table className="state-table">
                <thead>
                  <tr>
                    <th>State / UT</th>
                    <th>Combined WPR</th>
                    <th>Rural WPR</th>
                    <th>Urban WPR</th>
                    <th>Male WPR</th>
                    <th>Female WPR</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredStateRecords.length > 0 ? (
                    filteredStateRecords.map((row) => (
                      <tr key={row.state_ut}>
                        <td className="state-name">
                          {row.state_ut}
                        </td>

                        <td>
                          {formatPercentage(
                            row.rural_urban_person_wpr_pct
                          )}
                        </td>

                        <td>
                          {formatPercentage(
                            row.rural_person_wpr_pct
                          )}
                        </td>

                        <td>
                          {formatPercentage(
                            row.urban_person_wpr_pct
                          )}
                        </td>

                        <td>
                          {formatPercentage(
                            row.rural_urban_male_wpr_pct
                          )}
                        </td>

                        <td>
                          {formatPercentage(
                            row.rural_urban_female_wpr_pct
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={6}
                        className="empty-state"
                      >
                        No matching state found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          <p className="data-disclaimer">
            WPR represents the percentage of employed
            persons in the relevant population group.
            It should not be interpreted as the percentage
            of vacancies filled.
          </p>
        </section>

        {/* =================================================
            PLFS INDUSTRY DISTRIBUTION
        ================================================= */}

        <section className="industry-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                PLFS INDUSTRY ANALYSIS
              </span>

              <h2>Employment Distribution by Industry</h2>

              <p>
                Percentage distribution of workers across
                broad industry divisions.
              </p>
            </div>
          </div>

          <div className="industry-filter">
            <label htmlFor="industry-period">
              Survey period
            </label>

            <select
              id="industry-period"
              value={selectedIndustryPeriod}
              onChange={(event) =>
                setSelectedIndustryPeriod(event.target.value)
              }
              disabled={industryLoading}
            >
              {industryPeriods.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </select>
          </div>

          {industryLoading ? (
            <p className="loading-message">
              Loading industry distribution...
            </p>
          ) : industryError ? (
            <p className="prediction-error">
              {industryError}
            </p>
          ) : industryChartData.length === 0 ? (
            <p className="empty-state">
              No industry data available for this period.
            </p>
          ) : (
            <div className="industry-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={industryChartData}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 65,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    dataKey="industry"
                    angle={-25}
                    textAnchor="end"
                    interval={0}
                    height={90}
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 11,
                    }}
                  />

                  <YAxis
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                    tickFormatter={(value) => `${value}%`}
                  />

                  <Tooltip
                    formatter={(value) =>
                      `${Number(value).toFixed(1)}%`
                    }
                    contentStyle={{
                      background: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Bar
                    dataKey="employmentShare"
                    name="Employment share"
                    fill="#38bdf8"
                    radius={[5, 5, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="data-disclaimer">
            Source: MoSPI, PLFS Annual Report 2023–24,
            Statement 7. These are historical annual
            employment-distribution estimates, not forecasts.
          </p>
        </section>

        {/* =================================================
            NCS SUMMARY STATISTICS
        ================================================= */}

        <section className="industry-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                NATIONAL CAREER SERVICE
              </span>

              <h2>NCS Summary Statistics</h2>

              <p>
                Published National Career Service platform
                statistics for FY 2022–23 and FY 2023–24.
              </p>
            </div>
          </div>

          {ncsSummaryLoading ? (
            <p className="loading-message">
              Loading NCS summary...
            </p>
          ) : ncsSummaryError ? (
            <p className="prediction-error">
              {ncsSummaryError}
            </p>
          ) : ncsSummaryCards.length === 0 ? (
            <p className="empty-state">
              No NCS summary data available.
            </p>
          ) : (
            <div className="industry-gap-list">
              {ncsSummaryCards.map((item) => (
                <div
                  className="industry-gap-card"
                  key={item.label}
                >
                  <h3>{item.label}</h3>

                  <p>
                    FY 2023–24
                    <strong>
                      {" "}
                      {formatNumber(item.current)}
                    </strong>
                  </p>

                  <p>
                    FY 2022–23
                    <strong>
                      {" "}
                      {formatNumber(item.previous)}
                    </strong>
                  </p>

                  <p>
                    Reported change
                    <strong>
                      {" "}
                      {formatChange(item.change)}
                    </strong>
                  </p>
                </div>
              ))}
            </div>
          )}

          <p className="data-disclaimer">
            Source: National Career Service,
            Comparative NCS Statistics for FY 2022–23
            and FY 2023–24. These figures describe activity
            reported on the NCS platform; they are not a
            census of all vacancies in India.
          </p>
        </section>

        {/* =================================================
            NCS SECTOR-WISE VACANCIES
        ================================================= */}

        <section className="industry-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                NCS VACANCY ANALYSIS
              </span>

              <h2>Vacancies by Sector</h2>

              <p>
                Comparison of vacancies mobilised through
                NCS across the two reported financial years.
              </p>
            </div>
          </div>

          {sectorLoading ? (
            <p className="loading-message">
              Loading sector vacancy data...
            </p>
          ) : sectorError ? (
            <p className="prediction-error">
              {sectorError}
            </p>
          ) : sectorChartData.length === 0 ? (
            <p className="empty-state">
              No sector vacancy data available.
            </p>
          ) : (
            <div className="industry-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={sectorChartData}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 25,
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
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 11,
                    }}
                    tickFormatter={formatCompactNumber}
                  />

                  <YAxis
                    type="category"
                    dataKey="sector"
                    width={175}
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 11,
                    }}
                  />

                  <Tooltip
                    formatter={(value) =>
                      formatNumber(Number(value))
                    }
                    contentStyle={{
                      background: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="fy2022_23"
                    name="FY 2022–23"
                    fill="#0ea5e9"
                    radius={[0, 4, 4, 0]}
                  />

                  <Bar
                    dataKey="fy2023_24"
                    name="FY 2023–24"
                    fill="#22c55e"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="data-disclaimer">
            Source: NCS Comparative Statistics FY 2022–23
            and FY 2023–24. Sector figures represent
            vacancies mobilised through the NCS platform.
            They should not be treated as total national
            workforce demand.
          </p>
        </section>

        {/* =================================================
            NCS QUALIFICATION-WISE VACANCIES
        ================================================= */}

        <section className="industry-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                NCS QUALIFICATION ANALYSIS
              </span>

              <h2>Vacancies by Qualification</h2>

              <p>
                NCS-reported vacancies grouped by the
                qualification categories published in
                the source report.
              </p>
            </div>
          </div>

          {qualificationLoading ? (
            <p className="loading-message">
              Loading qualification vacancy data...
            </p>
          ) : qualificationError ? (
            <p className="prediction-error">
              {qualificationError}
            </p>
          ) : qualificationChartData.length === 0 ? (
            <p className="empty-state">
              No qualification vacancy data available.
            </p>
          ) : (
            <div className="industry-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={qualificationChartData}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 25,
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
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 11,
                    }}
                    tickFormatter={formatCompactNumber}
                  />

                  <YAxis
                    type="category"
                    dataKey="qualification"
                    width={190}
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 11,
                    }}
                  />

                  <Tooltip
                    formatter={(value) =>
                      formatNumber(Number(value))
                    }
                    contentStyle={{
                      background: "#0b1120",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="fy2022_23"
                    name="FY 2022–23"
                    fill="#0ea5e9"
                    radius={[0, 4, 4, 0]}
                  />

                  <Bar
                    dataKey="fy2023_24"
                    name="FY 2023–24"
                    fill="#a78bfa"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="data-disclaimer">
            Source: NCS Comparative Statistics FY 2022–23
            and FY 2023–24. Categories and values are
            reproduced from the published NCS report.
          </p>
        </section>

        {/* =================================================
            DATA SOURCES
        ================================================= */}

        <section className="industry-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                TRANSPARENCY
              </span>

              <h2>Data Sources and Methodology</h2>

              <p>
                Official sources used in the current
                dashboard.
              </p>
            </div>
          </div>

          <div className="industry-gap-list">
            <div className="industry-gap-card">
              <h3>PLFS Annual Report 2025</h3>

              <p>
                State-wise Worker Population Ratio.
              </p>

              <a
                href="https://www.mospi.gov.in/"
                target="_blank"
                rel="noreferrer"
              >
                MoSPI website
              </a>
            </div>

            <div className="industry-gap-card">
              <h3>PLFS Annual Report 2023–24</h3>

              <p>
                Industry-wise employment distribution,
                Statement 7.
              </p>

              <a
                href="https://mospi.gov.in/sites/default/files/publication_reports/AnnualReport_PLFS2023-24L2.pdf"
                target="_blank"
                rel="noreferrer"
              >
                Open PLFS report
              </a>
            </div>

            <div className="industry-gap-card">
              <h3>NCS Comparative Statistics</h3>

              <p>
                Vacancy statistics for FY 2022–23
                and FY 2023–24.
              </p>

              <a
                href="https://www.ncs.gov.in/Documents/NCS-Statistics-2022-23-24.pdf"
                target="_blank"
                rel="noreferrer"
              >
                Open NCS report
              </a>
            </div>
          </div>

          <p className="data-disclaimer">
            PLFS employment indicators and NCS platform
            vacancy statistics measure different concepts.
            They are presented separately and are not
            subtracted from one another to calculate a
            national skill gap.
          </p>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;