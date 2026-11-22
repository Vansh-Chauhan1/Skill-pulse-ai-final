import { useEffect, useState } from "react";
import { getStates } from "../services/api";
import type { StateData } from "../types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function EmploymentDashboard() {
  const [states, setStates] = useState<StateData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getStates()
      .then((data) => {
        setStates(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Unable to load employment data.");
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading employment statistics...</p>;

  if (error) return <p>{error}</p>;

  const totalDemand = states.reduce(
    (sum, item) => sum + item.total_demand, 0
  );

  const totalWorkers = states.reduce(
    (sum, item) => sum + item.total_workers, 0
  );

  const totalGap = states.reduce(
    (sum, item) => sum + item.total_gap, 0
  );

  const gapPercentage =
    totalDemand > 0 ? (totalGap / totalDemand) * 100 : 0;

  const formatNumber = (value: number) =>
    new Intl.NumberFormat("en-IN").format(value);

  return (
    <section className="employment-dashboard">

      <div className="dashboard-heading">
        <span>LIVE BACKEND DATA</span>
        <h2>India Employment Intelligence</h2>
        <p>
          Employment demand and workforce availability
          across the currently available states.
        </p>
      </div>

      <div className="stats-grid">

        <div className="stat-card">
          <p>Total Employment Demand</p>
          <h2>{formatNumber(totalDemand)}</h2>
        </div>

        <div className="stat-card">
          <p>Available Workforce</p>
          <h2>{formatNumber(totalWorkers)}</h2>
        </div>

        <div className="stat-card">
          <p>Total Skill Shortage</p>
          <h2>{formatNumber(totalGap)}</h2>
        </div>

        <div className="stat-card">
          <p>Demand Gap</p>
          <h2>{gapPercentage.toFixed(2)}%</h2>
        </div>

      </div>

      <div className="chart-container">

        <h3>State-wise Skill Gap Analysis</h3>

        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={states}>
            <CartesianGrid strokeDasharray="3 3" stroke="#26364d" />

            <XAxis
              dataKey="state"
              stroke="#94a3b8"
              tick={{ fontSize: 11 }}
              angle={-15}
              textAnchor="end"
              height={65}
            />

            <YAxis stroke="#94a3b8" />

            <Tooltip />

            <Bar
              dataKey="total_gap"
              fill="#38bdf8"
              name="Skill Gap"
            />
          </BarChart>
        </ResponsiveContainer>

      </div>

      <div className="state-table-container">

        <h3>State-wise Employment Data</h3>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>State</th>
                <th>Demand</th>
                <th>Available</th>
                <th>Skill Gap</th>
                <th>Gap %</th>
              </tr>
            </thead>

            <tbody>
              {states.map((item) => (
                <tr key={item.state}>
                  <td>{item.state}</td>
                  <td>{formatNumber(item.total_demand)}</td>
                  <td>{formatNumber(item.total_workers)}</td>
                  <td>{formatNumber(item.total_gap)}</td>
                  <td>{item.gap_percentage.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

      <p className="data-disclaimer">
        Demonstration dataset: figures are synthetic and
        should not be interpreted as actual employment statistics.
      </p>

    </section>
  );
}

export default EmploymentDashboard;