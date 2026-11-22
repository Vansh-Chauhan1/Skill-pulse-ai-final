import {
  ComposableMap,
  Geographies,
  Geography,
} from "react-simple-maps";

const geoUrl = "/india-states.geojson";

function IndiaSkillMap() {
  return (
    <div style={{ width: "100%", minHeight: "500px" }}>

      <ComposableMap
        projection="geoMercator"
        projectionConfig={{
          scale: 900,
          center: [82, 23],
        }}
        width={800}
        height={550}
        style={{
          width: "100%",
          height: "auto",
        }}
      >
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#1e3a5f"
                stroke="#38bdf8"
                strokeWidth={0.7}
                style={{
                  default: {
                    outline: "none",
                  },
                  hover: {
                    fill: "#0ea5e9",
                    outline: "none",
                  },
                  pressed: {
                    fill: "#0284c7",
                    outline: "none",
                  },
                }}
              />
            ))
          }
        </Geographies>
      </ComposableMap>

    </div>
  );
}

export default IndiaSkillMap;