import { useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";

const geoUrl = "/india-states.geojson";

// Temporary demo skill-gap data.
// We will connect this to the backend later.
const stateData: Record<string, number> = {
  Maharashtra: 72,
  "Uttar Pradesh": 65,
  Karnataka: 58,
  "Tamil Nadu": 48,
  "Madhya Pradesh": 62,
  Chhattisgarh: 90,
  Gujarat: 45,
  Rajasthan: 60,
  "West Bengal": 52,
  Bihar: 75,
};

function skillGapColor(value: number) {
  if (value < 30) return "#86EFAC";
  if (value < 45) return "#FDE047";
  if (value < 60) return "#FDBA74";
  return "#F87171";
}

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
};

function IndiaSkillMap() {
  const [selectedState, setSelectedState] = useState("Chhattisgarh");

  const skillGap = stateData[selectedState] ?? 40;

  return (
    <div className="india-map-container">

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

                return (
                  <Geography
                    key={`${stateName}-${index}`}
                    geography={geo}
                    className="india-state"
                    aria-label={stateName}
                    onClick={() => setSelectedState(stateName)}
                    fill={skillGapColor(stateData[stateName] ?? 40)}
                    stroke="#334155"
                    strokeWidth={0.8}
                  />
                );
              })
            }
          </Geographies>

          {Object.entries(stateCoordinates).map(
            ([state, coordinates]) => (
              <Marker key={state} coordinates={coordinates}>
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

      <div className="state-info">
        <span>SELECTED REGION</span>

        <h2>{selectedState}</h2>

        <p>Illustrative Skill Gap Index</p>

        <h1>{skillGap}%</h1>

        <div className="skill-progress">
          <div style={{ width: `${skillGap}%` }} />
        </div>

        <p>
          Hover over a state to highlight it, or click it to explore its
          skill-gap information.
        </p>
      </div>

    </div>
  );
}

export default IndiaSkillMap;