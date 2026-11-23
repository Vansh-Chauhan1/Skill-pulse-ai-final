import { useEffect, useState } from "react";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";

import {
  getOfficialPlfsStateWpr,
  getSkillGaps,
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

type SkillGapRecord = {
  state: string;
  industry: string;
  demand: number;
  available_workers: number;
  skill_gap: number;
  gap_percentage: number;
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

    andamanandnicobarisland:
      "andamanandnicobarislands",

    orissa: "odisha",

    uttaranchal: "uttarakhand",

  };

  return aliases[normalized] ?? normalized;
}

// ==========================================
// WPR COLOUR CLASSIFICATION
// ==========================================

function getWprColor(
  value: number | null | undefined
) {

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
// NUMBER FORMATTER
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

function formatCount(value: number) {
  return Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });
}

// ==========================================
// STATE LABEL COORDINATES
// ==========================================

const stateCoordinates: Record<
  string,
  [number, number]
> = {

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

  const [selectedState, setSelectedState] =
    useState("Chhattisgarh");

  const [stateData, setStateData] =
    useState<Record<string, WprRecord>>({});

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [skillGapRows, setSkillGapRows] = useState<SkillGapRecord[]>([]);
  const [skillGapLoading, setSkillGapLoading] = useState(true);
  const [skillGapError, setSkillGapError] = useState("");
  const [sectorPanelOpen, setSectorPanelOpen] = useState(false);

  // ==========================================
  // FETCH OFFICIAL PLFS DATA
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
            record.state_ut.trim().toLowerCase() ===
            "all india"
          ) {
            return;
          }

          lookup[
            normalizeStateName(record.state_ut)
          ] = record;

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

          setError(
            "Unable to load official PLFS state data."
          );

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

  useEffect(() => {
    let isMounted = true;

    getSkillGaps()
      .then((records: SkillGapRecord[]) => {
        if (isMounted) {
          setSkillGapRows(records);
          setSkillGapError("");
        }
      })
      .catch((err: unknown) => {
        console.error("Failed to load state-sector sample data:", err);
        if (isMounted) {
          setSkillGapError("Unable to load state-sector sample data.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setSkillGapLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // SELECTED STATE DATA
  // ==========================================

  const selectedData =
    stateData[
      normalizeStateName(selectedState)
    ];

  const combinedWpr =
    selectedData?.rural_urban_person_wpr_pct ?? null;

  const selectedColor = getWprColor(combinedWpr);

  const progressWidth =
    combinedWpr !== null
      ? Math.min(Math.max(combinedWpr, 0), 100)
      : 0;

  const selectedSkillGapRows = skillGapRows.filter(
    (row) =>
      normalizeStateName(row.state) ===
      normalizeStateName(selectedState)
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
                      setSelectedState(stateName)
                      setSectorPanelOpen(true)
                    }}
                    fill={getWprColor(
                      data?.rural_urban_person_wpr_pct
                    )}
                    stroke={
                      selected
                        ? "#38BDF8"
                        : "#334155"
                    }
                    strokeWidth={
                      selected ? 1.8 : 0.8
                    }
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
            {
              color: "#7F1D1D",
              label: "Below 35%",
            },
            {
              color: "#C2410C",
              label: "35–40%",
            },
            {
              color: "#CA8A04",
              label: "40–45%",
            },
            {
              color: "#0F766E",
              label: "45–50%",
            },
            {
              color: "#15803D",
              label: "50% and above",
            },
            {
              color: "#334155",
              label: "No data",
            },
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

        {sectorPanelOpen && (
          <aside
            className="state-sector-panel"
            aria-labelledby="state-sector-panel-title"
          >
            <div className="state-sector-panel__header">
              <div>
                <span>ILLUSTRATIVE SAMPLE · NOT OFFICIAL</span>
                <h3 id="state-sector-panel-title">
                  {selectedState} sector gaps
                </h3>
              </div>
              <button
                type="button"
                className="state-sector-panel__close"
                onClick={() => setSectorPanelOpen(false)}
                aria-label="Close state sector details"
              >
                ×
              </button>
            </div>

            {skillGapLoading ? (
              <p>Loading sector details...</p>
            ) : skillGapError ? (
              <p className="prediction-error">{skillGapError}</p>
            ) : selectedSkillGapRows.length > 0 ? (
              <>
                <div className="state-sector-panel__table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Sector</th>
                        <th>Demand</th>
                        <th>Workers</th>
                        <th>Gap</th>
                        <th>Gap %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedSkillGapRows.map((row) => (
                        <tr key={`${row.state}-${row.industry}`}>
                          <td>{row.industry}</td>
                          <td>{formatCount(row.demand)}</td>
                          <td>{formatCount(row.available_workers)}</td>
                          <td>{formatCount(row.skill_gap)}</td>
                          <td>{Number(row.gap_percentage).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p>
                  Gap = demand minus available workers. These sample figures
                  are arithmetic estimates, not official data or a time-based
                  forecast.
                </p>
              </>
            ) : (
              <p>
                No illustrative sector records are available for this state.
                The current sample covers six states only.
              </p>
            )}
          </aside>
        )}

      </div>

      {/* ======================================
          SELECTED STATE INFORMATION
      ====================================== */}

      <div className="state-info">

        <span>
          OFFICIAL PLFS 2025
        </span>

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
              Reference period: {selectedData.survey_period}
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

      </div>

    </div>

  );

}

export default IndiaSkillMap;