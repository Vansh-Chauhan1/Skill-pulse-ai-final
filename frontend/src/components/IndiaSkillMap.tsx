import { useEffect, useState } from "react";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";

import { getStates } from "../services/api";

const geoUrl = "/india-states.geojson";

type StateData = {
  state: string;
  total_demand: number;
  total_workers: number;
  total_gap: number;
  gap_percentage: number;
};

// Normalize state names for matching GeoJSON with backend data
function normalizeStateName(name: string) {
  const normalized = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");

  const aliases: Record<string, string> = {
    nctofdelhi: "delhi",
    nationalcapitalterritoryofdelhi: "delhi",
  };

  return aliases[normalized] ?? normalized;
}

// Determine map color from actual skill-gap data
function skillGapColor(data?: StateData) {
  if (!data) return "#334155";

  const gap = Number(data.total_gap);

  if (gap === 0) return "#86EFAC";

  if (gap < 0) return "#38BDF8";

  const percentage = Math.abs(Number(data.gap_percentage));

  if (percentage < 15) return "#FDE047";

  if (percentage < 30) return "#FDBA74";

  return "#F87171";
}

// State label coordinates
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

function IndiaSkillMap() {
  const [selectedState, setSelectedState] =
    useState("Chhattisgarh");

  const [stateData, setStateData] =
    useState<Record<string, StateData>>({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch state-wise data from FastAPI
  useEffect(() => {
    let isMounted = true;

    const fetchStateData = async () => {
      try {
        const records: StateData[] = await getStates();

        const lookup: Record<string, StateData> = {};

        records.forEach((record) => {
          lookup[normalizeStateName(record.state)] = record;
        });

        if (isMounted) {
          setStateData(lookup);
          setError("");
        }
      } catch (err) {
        console.error("Failed to load map data:", err);

        if (isMounted) {
          setError("Unable to load state-wise data.");
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

  // Get selected state's information
  const selectedData =
    stateData[normalizeStateName(selectedState)];

  const gapPercentage = selectedData
    ? Number(selectedData.gap_percentage)
    : 0;

  const status = !selectedData
    ? "No Data Available"
    : selectedData.total_gap > 0
    ? "Shortage"
    : selectedData.total_gap < 0
    ? "Surplus"
    : "Balanced";

  const statusColor =
    status === "Shortage"
      ? "#F87171"
      : status === "Surplus"
      ? "#38BDF8"
      : status === "Balanced"
      ? "#86EFAC"
      : "#94A3B8";

  const progressWidth = Math.min(
    Math.abs(gapPercentage),
    100
  );

  return (
    <div className="india-map-container">

      {/* India Map */}
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

                return (
                  <Geography
                    key={`${stateName}-${index}`}
                    geography={geo}
                    className="india-state"
                    aria-label={stateName}
                    onClick={() =>
                      setSelectedState(stateName)
                    }
                    fill={skillGapColor(data)}
                    stroke={
                      selectedState === stateName
                        ? "#38BDF8"
                        : "#334155"
                    }
                    strokeWidth={
                      selectedState === stateName
                        ? 1.8
                        : 0.8
                    }
                  />
                );
              })
            }
          </Geographies>

          {/* State Labels */}
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

      </div>

      {/* Selected State Information */}
      <div className="state-info">

        <span>SELECTED REGION</span>

        <h2>{selectedState}</h2>

        {loading ? (
          <p>Loading state data...</p>
        ) : error ? (
          <p>{error}</p>
        ) : selectedData ? (
          <>
            <p>Skill Gap Percentage</p>

            <h1 style={{ color: statusColor }}>
              {gapPercentage > 0 ? "+" : ""}
              {gapPercentage.toFixed(2)}%
            </h1>

            <h3 style={{ color: statusColor }}>
              {status}
            </h3>

            <div className="skill-progress">
              <div
                style={{
                  width: `${progressWidth}%`,
                  background: statusColor,
                }}
              />
            </div>

            <p>
              Total Demand:{" "}
              {selectedData.total_demand.toLocaleString("en-IN")}
            </p>

            <p>
              Available Workers:{" "}
              {selectedData.total_workers.toLocaleString("en-IN")}
            </p>

            <p>
              Net Skill Gap:{" "}
              {selectedData.total_gap.toLocaleString("en-IN")}
            </p>
          </>
        ) : (
          <p>
            No employment dataset is currently available
            for this state.
          </p>
        )}

      </div>

    </div>
  );
}

export default IndiaSkillMap;