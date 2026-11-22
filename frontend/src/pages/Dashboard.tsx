import "./Dashboard.css";
import IndiaSkillMap from "../components/IndiaSkillMap";

function Dashboard() {
  return (
    <div className="dashboard">

      {/* Navigation */}
      <nav className="dashboard-nav">
        <h2 className="dashboard-logo">SkillPulse AI</h2>

        <div className="nav-links">
          <a href="/">Home</a>
          <a href="/dashboard">Dashboard</a>
        </div>
      </nav>

      {/* Dashboard Header */}
      <main className="dashboard-content">

        <header className="dashboard-header">
          <h1>India Skill Gap Dashboard</h1>
          <p>
            Analyze workforce demand, employment availability
            and skill shortages across India.
          </p>
        </header>

        {/* Statistics */}
        <section className="stats-grid">

          <div className="stat-card">
            <h3>Total Workforce Demand</h3>
            <h2>--</h2>
          </div>

          <div className="stat-card">
            <h3>Available Workers</h3>
            <h2>--</h2>
          </div>

          <div className="stat-card">
            <h3>National Skill Gap</h3>
            <h2>--</h2>
          </div>

        </section>

        {/* India Map */}
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

      </main>
    </div>
  );
}

export default Dashboard;