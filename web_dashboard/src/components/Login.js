// src/components/Login.js — ClinSight Redesign
import { useState } from 'react';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const result = await onLogin({ email, password });
    if (!result.success) {
      setError(result.error || 'Authentication failed.');
      setLoading(false);
    }
  };

  const css = `
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

    .login-root {
      min-height: 100vh;
      background: #f7f6f4;
      display: flex;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      -webkit-font-smoothing: antialiased;
    }

    /* Left panel — decorative */
    .login-panel-left {
      flex: 1;
      background: #1a1916;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 56px 64px;
      position: relative;
      overflow: hidden;
    }
    .login-panel-left::before {
      content: '';
      position: absolute;
      inset: 0;
      background:
        repeating-linear-gradient(
          0deg,
          transparent,
          transparent 79px,
          rgba(255,255,255,0.04) 79px,
          rgba(255,255,255,0.04) 80px
        ),
        repeating-linear-gradient(
          90deg,
          transparent,
          transparent 79px,
          rgba(255,255,255,0.04) 79px,
          rgba(255,255,255,0.04) 80px
        );
      pointer-events: none;
    }
    .login-logo-mark {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 18px;
      letter-spacing: 0.02em;
      color: #ffffff;
    }
    .login-logo-sub {
      font-family: 'DM Mono', monospace;
      font-size: 10px;
      letter-spacing: 0.12em;
      color: rgba(255,255,255,0.35);
      margin-top: 4px;
    }
    .login-tagline {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: clamp(32px, 4vw, 52px);
      letter-spacing: -0.02em;
      color: #ffffff;
      line-height: 1.08;
    }
    .login-tagline span {
      color: rgba(255,255,255,0.25);
    }
    .login-caption {
      font-family: 'DM Mono', monospace;
      font-size: 12px;
      color: rgba(255,255,255,0.35);
      letter-spacing: 0.05em;
      line-height: 1.7;
      margin-top: 20px;
      max-width: 320px;
    }
    .login-version {
      font-family: 'DM Mono', monospace;
      font-size: 10px;
      color: rgba(255,255,255,0.2);
      letter-spacing: 0.1em;
    }

    /* Right panel — form */
    .login-panel-right {
      width: 480px;
      min-width: 380px;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 64px 56px;
      border-left: 1px solid #e2e0db;
    }
    .login-heading {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 28px;
      letter-spacing: -0.02em;
      color: #1a1916;
      margin-bottom: 6px;
    }
    .login-subheading {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      letter-spacing: 0.08em;
      color: #a09d98;
      margin-bottom: 40px;
    }

    .login-label {
      display: block;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #6b6760;
      margin-bottom: 8px;
    }
    .login-input {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid #e2e0db;
      border-radius: 4px;
      background: #f7f6f4;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      color: #1a1916;
      outline: none;
      transition: border-color 200ms ease, background 200ms ease;
      margin-bottom: 20px;
    }
    .login-input:focus {
      border-color: #1a1916;
      background: #ffffff;
    }
    .login-input::placeholder {
      color: #c8c5be;
    }

    .login-btn {
      width: 100%;
      padding: 14px;
      background: #1a1916;
      color: #ffffff;
      border: none;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 15px;
      letter-spacing: 0.04em;
      cursor: pointer;
      transition: background 200ms ease, transform 100ms ease;
      margin-top: 8px;
    }
    .login-btn:hover:not(:disabled) {
      background: #3d3a35;
    }
    .login-btn:active:not(:disabled) {
      transform: scale(0.99);
    }
    .login-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .login-error {
      font-family: 'DM Mono', monospace;
      font-size: 12px;
      color: #b94040;
      background: #fdf2f2;
      border: 1px solid #f0c8c8;
      border-radius: 4px;
      padding: 10px 14px;
      margin-bottom: 20px;
      letter-spacing: 0.02em;
    }

    .login-divider {
      border: none;
      border-top: 1px solid #e2e0db;
      margin: 32px 0;
    }

    .login-footer {
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      color: #c8c5be;
      letter-spacing: 0.04em;
      line-height: 1.6;
    }

    @media (max-width: 768px) {
      .login-panel-left { display: none; }
      .login-panel-right { width: 100%; padding: 48px 32px; }
    }
  `;

  return (
    <>
      <style>{css}</style>
      <div className="login-root">

        {/* Left decorative panel */}
        <div className="login-panel-left">
          <div>
            <div className="login-logo-mark">CLINSIGHT</div>
            <div className="login-logo-sub">CLINICAL DASHBOARD</div>
          </div>

          <div>
            <div className="login-tagline">
              Clinical<br />
              <span>Trial</span><br />
              Intelligence.
            </div>
            <div className="login-caption">
              Streamlined eligibility screening,<br />
              patient management, and trial matching<br />
              for clinical research teams.
            </div>
          </div>

          <div className="login-version">CLINSIGHT v2.0 — RESTRICTED ACCESS</div>
        </div>

        {/* Right form panel */}
        <div className="login-panel-right">
          <div className="login-heading">Sign in</div>
          <div className="login-subheading">AUTHORIZED PERSONNEL ONLY</div>

          <form onSubmit={handleSubmit} noValidate>
            {error && <div className="login-error">{error}</div>}

            <label className="login-label">Email address</label>
            <input
              className="login-input"
              type="email"
              placeholder="you@institution.edu"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              autoFocus
            />

            <label className="login-label">Password</label>
            <input
              className="login-input"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />

            <button className="login-btn" type="submit" disabled={loading}>
              {loading ? 'AUTHENTICATING...' : 'SIGN IN'}
            </button>
          </form>

          <hr className="login-divider" />

          <div className="login-footer">
            Access to this system is restricted to authorized<br />
            clinical research staff. All sessions are monitored<br />
            and logged for compliance purposes.
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;