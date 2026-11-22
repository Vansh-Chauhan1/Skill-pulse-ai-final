import "./App.css";
import EmploymentDashboard from "./components/EmploymentDashboard";
import BackendStatus from "./components/BackendStatus";

function App() {
  return (
    <div className="app">

      {/* Navbar */}
      <nav className="navbar">
        <div className="logo">
          SkillPulse <span>AI</span>
        </div>

        <div className="nav-links">
          <a href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </div>

        <button className="nav-button">
          Explore Dashboard →
        </button>
        <BackendStatus />
      </nav>

      {/* Hero Section */}
      <section className="hero" id="home">

        <div className="hero-content">

          <div className="badge">
            AI-Powered Employment Intelligence
          </div>

          <h1>
            Bridging India's
            <span> Skill Gap </span>
            with Artificial Intelligence
          </h1>

          <p>
            SkillPulse AI analyses employment trends, identifies
            skill shortages and predicts future workforce demands
            to help students, institutions and policymakers make
            smarter career decisions.
          </p>

          <div className="hero-buttons">
            <button className="primary-btn">
              Explore Dashboard →
            </button>

            <button className="secondary-btn">
              Discover More
            </button>
          </div>

        </div>

        <div className="hero-visual">
          <div className="visual-card">
            <div className="visual-heading">
              India's Workforce Intelligence
            </div>

            <div className="visual-number">
              AI <span>+</span>
            </div>

            <p>Understanding India's Future Workforce</p>

            <div className="visual-stats">
              <div>
                <h3>28+</h3>
                <p>States & UTs</p>
              </div>

              <div>
                <h3>AI</h3>
                <p>Predictions</p>
              </div>
            </div>
          </div>
        </div>

      </section>

      {/* Features */}
      <section className="features" id="features">

        <div className="section-heading">
          <span>OUR CAPABILITIES</span>
          <h2>Making Workforce Data Intelligent</h2>
          <p>
            Transforming employment data into actionable insights.
          </p>
        </div>

        <div className="feature-grid">

          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Skill Gap Analysis</h3>
            <p>
              Identify differences between industry skill demand
              and the available workforce.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🗺️</div>
            <h3>State-wise Insights</h3>
            <p>
              Explore employment opportunities and skill gaps
              across different Indian states.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI Predictions</h3>
            <p>
              Predict emerging employment trends and
              future skill requirements using machine learning.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Career Recommendations</h3>
            <p>
              Help students identify relevant skills and
              learning paths for future opportunities.
            </p>
          </div>

        </div>
        <EmploymentDashboard />

      </section>

      {/* Footer */}
      <footer id="about">
        <h2>SkillPulse AI</h2>
        <p>Empowering India's workforce through intelligent insights.</p>
        <p>© 2026 SkillPulse AI. All rights reserved.</p>
      </footer>

    </div>
  );
}

export default App;