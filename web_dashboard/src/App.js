// src/App.js — ClinSight Redesign: Surgical Minimalism
import { CheckSquare, ChevronRight, FlaskConical, History, LayoutDashboard, LogOut, Menu, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard';
import EligibilityChecker from './components/EligibilityChecker';
import Login from './components/Login';
import PatientsManager from './components/PatientsManager';
import TrialsManager from './components/TrialsManager';
import { getChecks } from './services/apiService';
import { login as apiLogin, getCurrentUser } from './services/authService';

// ─── Global styles injected once ───────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #f7f6f4;
    --surface:   #ffffff;
    --border:    #e2e0db;
    --border-mid:#c8c5be;
    --text:      #1a1916;
    --text-mid:  #6b6760;
    --text-dim:  #a09d98;
    --accent:    #1a1916;
    --accent-h:  #3d3a35;
    --danger:    #b94040;
    --danger-bg: #fdf2f2;
    --ok:        #2e7d52;
    --ok-bg:     #f0f7f3;
    --mono:      'JetBrains Mono', monospace;
    --sans:      'JetBrains Mono', monospace;
    --radius:    4px;
    --radius-md: 8px;
    --sidebar-w: 280px;
    --sidebar-c: 64px;
    --transition: 220ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  html, body, #root { height: 100%; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    font-size: 14px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border-mid); border-radius: 2px; }

  /* Sidebar nav button hover */
  .nav-btn { background: transparent; border: none; cursor: pointer; width: 100%; text-align: left; transition: background var(--transition); }
  .nav-btn:hover { background: rgba(26,25,22,0.06); }
  .nav-btn.active { background: var(--text); color: #fff; }
  .nav-btn.active svg { color: #fff; }

  /* Logout */
  .logout-btn { background: transparent; border: 1px solid var(--border); cursor: pointer; transition: all var(--transition); font-family: var(--mono); }
  .logout-btn:hover { border-color: var(--danger); color: var(--danger); background: var(--danger-bg); }

  /* Collapse toggle */
  .collapse-btn { background: var(--surface); border: 1px solid var(--border); cursor: pointer; transition: all var(--transition); }
  .collapse-btn:hover { border-color: var(--border-mid); background: var(--bg); }

  /* History card */
  .history-card { background: var(--surface); border: 1px solid var(--border); transition: border-color var(--transition); }
  .history-card:hover { border-color: var(--border-mid); }

  /* Fade-in animation */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .fade-up { animation: fadeUp 280ms ease both; }
`;

function injectStyles() {
  if (document.getElementById('clinsight-global')) return;
  const el = document.createElement('style');
  el.id = 'clinsight-global';
  el.textContent = GLOBAL_CSS;
  document.head.appendChild(el);
}

// ─── App ───────────────────────────────────────────────────────────────────
const App = () => {
  injectStyles();

  const [selectedIndex, setSelectedIndex] = useState(0);
  const [token, setToken] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  const [userName, setUserName] = useState('');
  const [collapsed, setCollapsed] = useState(false);

  const handleLogin = async ({ email, password }) => {
    try {
      const data = await apiLogin(email, password);
      setToken(data.access_token);
      setUserEmail(email);
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('userEmail', email);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message || 'Login failed' };
    }
  };

  const handleLogout = () => {
    setToken(null); setUserEmail(''); setUserName('');
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    setSelectedIndex(0);
  };

  useEffect(() => {
    const t = localStorage.getItem('authToken');
    const e = localStorage.getItem('userEmail');
    if (t) { setToken(t); if (e) setUserEmail(e); }
  }, []);

  useEffect(() => {
    if (!token) return;
    getCurrentUser(token)
      .then(u => { setUserEmail(u.email); setUserName(u.name); })
      .catch(e => { if (e.message.includes('401') || e.message.includes('Unauthorized')) handleLogout(); });
  }, [token]);

  if (!token) return <Login onLogin={handleLogin} />;

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', short: 'DB' },
    { icon: CheckSquare, label: 'Check Eligibility', short: 'CE' },
    { icon: Users, label: 'Patients', short: 'PT' },
    { icon: FlaskConical, label: 'Trials', short: 'TR' },
    { icon: History, label: 'History', short: 'HX' },
  ];

  const sidebarW = collapsed ? 'var(--sidebar-c)' : 'var(--sidebar-w)';

  const LeftNav = () => (
    <aside style={{
      width: sidebarW,
      minWidth: sidebarW,
      height: '100vh',
      position: 'sticky',
      top: 0,
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      transition: `width var(--transition), min-width var(--transition)`,
      overflow: 'hidden',
      zIndex: 20,
    }}>

      {/* Header */}
      <div style={{
        padding: collapsed ? '20px 0' : '28px 20px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between',
        minHeight: '72px',
      }}>
        {!collapsed && (
          <div>
            <div style={{
              fontFamily: 'var(--mono)',
              fontWeight: 700,
              fontSize: '16px',
              letterSpacing: '0.02em',
              color: 'var(--text)',
              lineHeight: 1,
            }}>
              CLINSIGHT
            </div>
            <div style={{
              fontFamily: 'var(--mono)',
              fontSize: '11px',
              color: 'var(--text-dim)',
              letterSpacing: '0.06em',
              marginTop: '5px',
            }}>
              CLINICAL DASHBOARD
            </div>
          </div>
        )}

        {collapsed && (
          <div style={{
            fontFamily: 'var(--mono)',
            fontWeight: 500,
            fontSize: '13px',
            letterSpacing: '0.05em',
            color: 'var(--text)',
          }}>CS</div>
        )}

        {!collapsed && (
          <button
            className="collapse-btn"
            onClick={() => setCollapsed(true)}
            style={{
              width: '28px', height: '28px',
              borderRadius: 'var(--radius)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Menu size={14} color="var(--text-mid)" />
          </button>
        )}
      </div>
      {collapsed && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0', borderTop: '1px solid var(--border)' }}>
          <button
            className="collapse-btn"
            onClick={() => setCollapsed(false)}
            style={{
              width: '32px', height: '32px',
              borderRadius: 'var(--radius)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Menu size={14} color="var(--text-mid)" />
          </button>
        </div>
      )}

      {/* Nav items */}
      <nav style={{ flex: 1, padding: collapsed ? '12px 0' : '12px 10px', overflowY: 'auto' }}>
        {navItems.map((item, i) => {
          const Icon = item.icon;
          const active = selectedIndex === i;
          return (
            <button
              key={i}
              className={`nav-btn${active ? ' active' : ''}`}
              onClick={() => { setSelectedIndex(i); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: collapsed ? '12px 0' : '10px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                borderRadius: 'var(--radius)',
                marginBottom: '2px',
                color: active ? '#fff' : 'var(--text-mid)',
                fontFamily: 'var(--mono)',
                fontWeight: active ? 700 : 400,
                fontSize: '14px',
                letterSpacing: '0.01em',
              }}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} strokeWidth={active ? 2.5 : 1.8} />
              {!collapsed && <span style={{ flex: 1 }}>{item.label}</span>}
              {!collapsed && active && <ChevronRight size={14} strokeWidth={2} />}
            </button>
          );
        })}
      </nav>

      {/* Expand button when collapsed */}
      

      {/* User + Logout */}
      <div style={{
        padding: collapsed ? '16px 0' : '16px 10px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: collapsed ? 'center' : 'stretch',
        gap: '10px',
      }}>
        {!collapsed && (
          <div style={{ padding: '0 4px' }}>
            <div style={{
              fontFamily: 'var(--mono)',
              fontWeight: 700,
              fontSize: '13px',
              color: 'var(--text)',
              marginBottom: '2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {userName || 'User'}
            </div>
            <div style={{
              fontFamily: 'var(--mono)',
              fontSize: '12px',
              color: 'var(--text-dim)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {userEmail}
            </div>
          </div>
        )}
        <button
          className="logout-btn"
          onClick={handleLogout}
          title={collapsed ? 'Logout' : undefined}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '8px',
            padding: collapsed ? '8px' : '8px 12px',
            borderRadius: 'var(--radius)',
            color: 'var(--text-mid)',
            fontSize: '12px',
            letterSpacing: '0.04em',
          }}
        >
          <LogOut size={14} strokeWidth={1.8} />
          {!collapsed && 'LOGOUT'}
        </button>
      </div>
    </aside>
  );

  // ── History Page ─────────────────────────────────────────────────────────
  const HistoryPage = () => {
    const [checks, setChecks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      getChecks(token)
        .then(data => { setChecks(data); setLoading(false); })
        .catch(() => setLoading(false));
    }, []);

    return (
      <div style={{ padding: '48px 56px', maxWidth: '900px' }} className="fade-up">
        {/* Page header */}
        <div style={{ marginBottom: '40px', borderBottom: '1px solid var(--border)', paddingBottom: '24px' }}>
          <div style={{
            fontFamily: 'var(--mono)',
            fontSize: '12px',
            letterSpacing: '0.08em',
            color: 'var(--text-dim)',
            marginBottom: '8px',
          }}>
            05 / ELIGIBILITY HISTORY
          </div>
          <h1 style={{
            fontFamily: 'var(--mono)',
            fontWeight: 700,
            fontSize: '28px',
            letterSpacing: '-0.02em',
            color: 'var(--text)',
          }}>
            Check History
          </h1>
        </div>

        {loading ? (
          <div style={{ fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-dim)' }}>
            Loading records...
          </div>
        ) : checks.length === 0 ? (
          <div style={{
            border: '1px dashed var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '64px 40px',
            textAlign: 'center',
          }}>
            <div style={{ fontFamily: 'var(--sans)', fontWeight: 700, fontSize: '16px', color: 'var(--text-mid)', marginBottom: '8px' }}>
              No records found
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>
              Run your first eligibility check to see results here.
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {checks.map((c, idx) => (
              <div
                key={c.id}
                className="history-card fade-up"
                style={{
                  borderRadius: 'var(--radius-md)',
                  padding: '18px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px',
                  animationDelay: `${idx * 40}ms`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  <div style={{
                    fontFamily: 'var(--mono)',
                    fontSize: '11px',
                    color: 'var(--text-dim)',
                    letterSpacing: '0.06em',
                    minWidth: '48px',
                  }}>
                    #{String(c.id).padStart(4, '0')}
                  </div>
                  <div>
                    <div style={{
                      display: 'flex',
                      gap: '16px',
                      fontFamily: 'var(--mono)',
                      fontSize: '14px',
                      color: 'var(--text-mid)',
                    }}>
                      <span>Score <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{(c.overall_score * 100).toFixed(1)}%</strong></span>
                      <span>Confidence <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{c.confidence_score.toFixed(1)}%</strong></span>
                    </div>
                  </div>
                </div>

                <div style={{
                  padding: '5px 12px',
                  borderRadius: 'var(--radius)',
                  fontFamily: 'var(--mono)',
                  fontSize: '11px',
                  fontWeight: 500,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  background: c.status === 'eligible' ? 'var(--ok-bg)' : 'var(--danger-bg)',
                  color: c.status === 'eligible' ? 'var(--ok)' : 'var(--danger)',
                  border: `1px solid ${c.status === 'eligible' ? '#c3e6d4' : '#f0c8c8'}`,
                }}>
                  {c.status}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const pages = [
    <Dashboard key="dashboard" token={token} />,
    <EligibilityChecker key="eligibility" token={token} />,
    <PatientsManager key="patients" token={token} />,
    <TrialsManager key="trials" token={token} />,
    <HistoryPage key="history" />,
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>
      <LeftNav />
      <main style={{ flex: 1, overflowY: 'auto' }}>
        {pages[selectedIndex]}
      </main>
    </div>
  );
};

export default App;