
import { useEffect, useState } from "react";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";

import {
  getOfficialPlfsStateWpr,
  getOfficialNcsSectorVacancies,
  sendAiChat,
} from "../services/api";

const geoUrl = "/india-states.geojson";

// ==========================================
// TYPES
// ==========================================

type WprRecord = {
  state_ut: string;
  survey_period: string;

  rural_person_wpr_pct: number | null;
  urban_person_wpr_pct: number | null;
  rural_urban_person_wpr_pct: number | null;

  rural_urban_male_wpr_pct: number | null;
  rural_urban_female_wpr_pct: number | null;
};

type NcsSectorRecord = {
  ncs_sector_as_published: string;
  vacancies_fy2022_23: number | string | null;
  vacancies_fy2023_24: number | string | null;
  reported_percent_change: number | string | null;
  source_report?: string;
  source_url?: string;
};

// ==========================================
// STATE NAME NORMALIZATION
// ==========================================

function normalizeStateName(name: string) {
  const normalized = name
    .replace(/&/g, " and ")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");

  const aliases: Record<string, string> = {
    nctofdelhi: "delhi",
    nationalcapitalterritoryofdelhi: "delhi",
    andamanandnicobarisland: "andamanandnicobarislands",
    orissa: "odisha",
    uttaranchal: "uttarakhand",
  };

  return aliases[normalized] ?? normalized;
}

// ==========================================
// WPR COLOUR CLASSIFICATION
// ==========================================

function getWprColor(value: number | null | undefined) {
  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(Number(value))
  ) {
    return "#334155";
  }

  const wpr = Number(value);

  if (wpr < 35) return "#7F1D1D";
  if (wpr < 40) return "#C2410C";
  if (wpr < 45) return "#CA8A04";
  if (wpr < 50) return "#0F766E";

  return "#15803D";
}

// ==========================================
// FORMATTERS
// ==========================================

function formatWpr(value: number | null | undefined) {
  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(Number(value))
  ) {
    return "Not reported";
  }

  return `${Number(value).toFixed(1)}%`;
}

function formatCount(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "—";
  return parsed.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function formatChange(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "—";
  return `${parsed > 0 ? "+" : ""}${parsed.toFixed(1)}%`;
}

// ==========================================
// STATE LABEL COORDINATES
// ==========================================

const stateCoordinates: Record<string, [number, number]> = {
  Maharashtra: [75.7, 19.5],
  "Uttar Pradesh": [80.9, 26.8],
  Karnataka: [76.5, 15.3],
  "Tamil Nadu": [78.5, 11],
  "Madhya Pradesh": [78.5, 23.5],
  Chhattisgarh: [82, 21],
  Gujarat: [71.5, 22],
  Rajasthan: [73.8, 26],
  "West Bengal": [87.8, 23],
  Bihar: [85.5, 25.8],
  Delhi: [77.1, 28.7],
};

// ==========================================
// INDIA SKILL MAP COMPONENT
// ==========================================

function IndiaSkillMap() {
  const [selectedState, setSelectedState] = useState("Chhattisgarh");

  const [stateData, setStateData] = useState<
    Record<string, WprRecord>
  >({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Official NCS sector vacancy data (national context only)
  const [ncsSectorRows, setNcsSectorRows] = useState<NcsSectorRecord[]>([]);
  const [ncsSectorLoading, setNcsSectorLoading] = useState(true);
  const [ncsSectorError, setNcsSectorError] = useState("");
  const [sectorPanelOpen, setSectorPanelOpen] = useState(false);

  // Shared SkillPulse AI intelligence
  const [aiInsight, setAiInsight] = useState("");
  const [aiInsightLoading, setAiInsightLoading] = useState(false);
  const [aiInsightError, setAiInsightError] = useState("");

  // ==========================================
  // FETCH OFFICIAL PLFS STATE DATA
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchStateData = async () => {
      try {
        const records: WprRecord[] =
          await getOfficialPlfsStateWpr();

        const lookup: Record<string, WprRecord> = {};

        records.forEach((record) => {
          if (
            record.state_ut.trim().toLowerCase() === "all india"
          ) {
            return;
          }

          lookup[normalizeStateName(record.state_ut)] = record;
        });

        if (isMounted) {
          setStateData(lookup);
          setError("");
        }
      } catch (err) {
        console.error(
          "Failed to load official PLFS map data:",
          err
        );

        if (isMounted) {
          setError("Unable to load official PLFS state data.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchStateData();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // FETCH OFFICIAL NCS SECTOR VACANCY DATA
  // These figures are national NCS platform signals, not state-level counts.
  // ==========================================

  useEffect(() => {
    let isMounted = true;

    const fetchNcsSectors = async () => {
      try {
        const records: NcsSectorRecord[] =
          await getOfficialNcsSectorVacancies();

        if (isMounted) {
          setNcsSectorRows(Array.isArray(records) ? records : []);
          setNcsSectorError("");
        }
      } catch (err) {
        console.error("Failed to load official NCS sector vacancies:", err);
        if (isMounted) {
          setNcsSectorError("Unable to load official NCS sector vacancy data.");
        }
      } finally {
        if (isMounted) setNcsSectorLoading(false);
      }
    };

    fetchNcsSectors();

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // SHARED AI INTELLIGENCE ENGINE
  // ==========================================

  useEffect(() => {
    let isActive = true;

    const loadStateIntelligence = async () => {
      setAiInsight("");
      setAiInsightError("");
      setAiInsightLoading(true);

      try {
        const question = `Analyze ${selectedState} using state-level PLFS WPR and national NCS sector vacancy data. Separate the state observation from national vacancy signals; explain supported patterns and limitations. Do not infer local vacancy demand or worker supply.`;

        const response = await sendAiChat(question, []);

        if (isActive) {
          setAiInsight(
            response.answer ||
              "No AI analysis was returned."
          );
        }
      } catch (err) {
        console.error(
          "SkillPulse AI state intelligence error:",
          err
        );

        if (isActive) {
          setAiInsightError(
            "Unable to generate AI insights. Check the backend connection and try again."
          );
        }
      } finally {
        if (isActive) {
          setAiInsightLoading(false);
        }
      }
    };

    loadStateIntelligence();

    return () => {
      isActive = false;
    };
  }, [selectedState]);

  // ==========================================
  // SELECTED STATE DATA
  // ==========================================

  const selectedData =
    stateData[normalizeStateName(selectedState)];

  const combinedWpr =
    selectedData?.rural_urban_person_wpr_pct ?? null;

  const selectedColor = getWprColor(combinedWpr);

  const progressWidth =
    combinedWpr !== null
      ? Math.min(Math.max(combinedWpr, 0), 100)
      : 0;

  const nationalNcsSectorRows = [...ncsSectorRows].sort(
    (a, b) =>
      (Number(b.vacancies_fy2023_24) || 0) -
      (Number(a.vacancies_fy2023_24) || 0)
  );

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <div className="india-map-container">
      {/* ======================================
          INDIA MAP
      ====================================== */}

      <div className="map-area">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            center: [82, 23],
            scale: 900,
          }}
        >
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo, index) => {
                const name =
                  geo.properties?.NAME_1 ||
                  geo.properties?.ST_NM ||
                  geo.properties?.name ||
                  geo.properties?.st_nm ||
                  "Unknown";

                const stateName = String(name);

                const normalizedName =
                  normalizeStateName(stateName);

                const data = stateData[normalizedName];

                const selected =
                  normalizeStateName(selectedState) ===
                  normalizedName;

                return (
                  <Geography
                    key={`${stateName}-${index}`}
                    geography={geo}
                    className="india-state"
                    aria-label={`Select ${stateName}`}
                    onClick={() => {
                      setSelectedState(stateName);
                      setSectorPanelOpen(true);
                    }}
                    fill={getWprColor(
                      data?.rural_urban_person_wpr_pct
                    )}
                    stroke={
                      selected ? "#38BDF8" : "#334155"
                    }
                    strokeWidth={selected ? 1.8 : 0.8}
                  />
                );
              })
            }
          </Geographies>

          {/* STATE LABELS */}

          {Object.entries(stateCoordinates).map(
            ([state, coordinates]) => (
              <Marker
                key={state}
                coordinates={coordinates}
              >
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  style={{
                    fontSize: "9px",
                    fontWeight: 700,
                    fill: "#172033",
                    stroke: "#ffffff",
                    strokeWidth: 2,
                    paintOrder: "stroke",
                    pointerEvents: "none",
                  }}
                >
                  {state}
                </text>
              </Marker>
            )
          )}
        </ComposableMap>

        {/* MAP LEGEND */}

        <div className="wpr-legend">
          <strong>Worker Population Ratio</strong>

          {[
            { color: "#7F1D1D", label: "Below 35%" },
            { color: "#C2410C", label: "35–40%" },
            { color: "#CA8A04", label: "40–45%" },
            { color: "#0F766E", label: "45–50%" },
            { color: "#15803D", label: "50% and above" },
            { color: "#334155", label: "No data" },
          ].map((item) => (
            <div
              className="wpr-legend-item"
              key={item.label}
            >
              <span
                className="wpr-legend-swatch"
                style={{
                  background: item.color,
                }}
              />

              <span>{item.label}</span>
            </div>
          ))}
        </div>

        {/* ======================================
            NATIONAL NCS SECTOR CONTEXT PANEL
        ====================================== */}

        {sectorPanelOpen && (
          <aside
            className="state-sector-panel"
            aria-labelledby="state-sector-panel-title"
          >
            <div className="state-sector-panel__header">
              <div>
                <span>NATIONAL NCS DATA · NOT STATE-SPECIFIC</span>
                <h3 id="state-sector-panel-title">
                  Sector vacancy context for {selectedState}
                </h3>
              </div>

              <button
                type="button"
                className="state-sector-panel__close"
                onClick={() => setSectorPanelOpen(false)}
                aria-label="Close sector details"
              >
                ×
              </button>
            </div>

            <p>
              The table below shows vacancies reported nationally through
              the National Career Service (NCS). These figures provide
              broader sector context; they are not vacancy counts for
              {` ${selectedState}`} or for the entire Indian labour market.
            </p>

            {ncsSectorLoading ? (
              <p>Loading official NCS sector trends...</p>
            ) : ncsSectorError ? (
              <p className="prediction-error">{ncsSectorError}</p>
            ) : nationalNcsSectorRows.length > 0 ? (
              <>
                <div className="state-sector-panel__table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Sector</th>
                        <th>FY 2022–23</th>
                        <th>FY 2023–24</th>
                        <th>Reported change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {nationalNcsSectorRows.map((row) => (
                        <tr key={row.ncs_sector_as_published}>
                          <td>{row.ncs_sector_as_published}</td>
                          <td>{formatCount(row.vacancies_fy2022_23)}</td>
                          <td>{formatCount(row.vacancies_fy2023_24)}</td>
                          <td>{formatChange(row.reported_percent_change)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p>
                  Source: National Career Service (NCS) published vacancy
                  data. Counts represent platform-reported vacancies for
                  the stated financial years.
                </p>
              </>
            ) : (
              <p>No NCS sector vacancy records were returned by the API.</p>
            )}
          </aside>
        )}
      </div>
      {/* ======================================
          SELECTED STATE INFORMATION
      ====================================== */}

      <div className="state-info">
        <span>OFFICIAL PLFS 2025</span>

        <h2>{selectedState}</h2>

        {loading ? (
          <p>Loading official data...</p>
        ) : error ? (
          <p className="prediction-error">
            {error}
          </p>
        ) : selectedData ? (
          <>
            <div className="wpr-primary">
              <p>
                Combined Worker Population Ratio
              </p>

              <h1
                style={{
                  color: selectedColor,
                }}
              >
                {formatWpr(combinedWpr)}
              </h1>
            </div>

            <div className="skill-progress">
              <div
                style={{
                  width: `${progressWidth}%`,
                  background: selectedColor,
                }}
              />
            </div>

            <div className="wpr-details">
              <div>
                <span>Rural WPR</span>

                <strong>
                  {formatWpr(
                    selectedData.rural_person_wpr_pct
                  )}
                </strong>
              </div>

              <div>
                <span>Urban WPR</span>

                <strong>
                  {formatWpr(
                    selectedData.urban_person_wpr_pct
                  )}
                </strong>
              </div>

              <div>
                <span>Male WPR</span>

                <strong>
                  {formatWpr(
                    selectedData.rural_urban_male_wpr_pct
                  )}
                </strong>
              </div>

              <div>
                <span>Female WPR</span>

                <strong>
                  {formatWpr(
                    selectedData.rural_urban_female_wpr_pct
                  )}
                </strong>
              </div>
            </div>

            <p>
              Reference period:{" "}
              {selectedData.survey_period}
            </p>

            <p>
              Indicator: Usual status (principal +
              subsidiary), all ages.
            </p>
          </>
        ) : (
          <p>
            Official PLFS data is unavailable for this
            geographical region.
          </p>
        )}

        {/* ======================================
            SKILLPULSE AI INTELLIGENCE PANEL
        ====================================== */}

        <div className="state-ai-intelligence">
          <span>SKILLPULSE AI INTELLIGENCE</span>

          <h3>
            AI-powered State Analysis
          </h3>

          {aiInsightLoading ? (
            <div>
              <p>
                Analyzing {selectedState}'s labour market...
              </p>

              <p>
                Retrieving employment indicators,
                sector demand and forecasting results.
              </p>
            </div>
          ) : aiInsightError ? (
            <p className="prediction-error">
              {aiInsightError}
            </p>
          ) : (
            <div
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: 1.7,
              }}
            >
              {aiInsight}
            </div>
          )}

          <p>
            AI analysis is based on available PLFS and
            NCS data. Forecasts are exploratory and
            must not be interpreted as official
            government projections.
          </p>
        </div>
      </div>
    </div>
  );
}

export default IndiaSkillMap;