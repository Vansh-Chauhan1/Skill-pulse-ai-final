import { useEffect, useState } from "react";
import { checkBackend } from "../services/api";

function BackendStatus() {
  const [status, setStatus] = useState("Connecting...");

  useEffect(() => {
    checkBackend()
      .then((data) => {
        setStatus(data.status === "healthy" ? "Connected" : "Disconnected");
      })
      .catch(() => {
        setStatus("Disconnected");
      });
  }, []);

  return (
    <div style={{ padding: "10px", color: "#38bdf8" }}>
      Backend Status: {status}
    </div>
  );
}

export default BackendStatus;