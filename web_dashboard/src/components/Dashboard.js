import { Activity, BarChart3, CheckCircle, FlaskConical, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../services/apiService';


const Dashboard = ({ token }) => {
  const [stats, setStats] = useState({
    totalPatients: 0,
    totalTrials: 0,
    totalChecks: 0,
    eligibleCount: 0,
    recentActivity: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDashboardData(); }, [token]);

  const loadDashboardData = async () => {
    try {
      const [pA, tA, cA] = await Promise.all([
        api.getPatients(token),
        api.getTrials(token),
        api.getChecks(token)
      ]);
      setStats({
        totalPatients: pA.length,
        totalTrials: tA.length,
        totalChecks: cA.length,
        eligibleCount: cA.filter(c => c.status === 'eligible').length,
        recentActivity: cA.slice(0, 5)
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { label: 'Total Patients', value: stats.totalPatients, sub: 'Active records', icon: Users },
    { label: 'Clinical Trials', value: stats.totalTrials, sub: 'Available trials', icon: FlaskConical },
    { label: 'Checks Run', value: stats.totalChecks, sub: 'Total predictions', icon: Activity },
    {
      label: 'Eligible Patients',
      value: stats.eligibleCount,
      sub: stats.totalChecks > 0 ? `${((stats.eligibleCount / stats.totalChecks) * 100).toFixed(1)}% success rate` : 'No data',
      icon: CheckCircle
    },
  ];

  const avgConf = stats.recentActivity.length > 0
    ? (stats.recentActivity.reduce((s, c) => s + c.confidence_score, 0) / stats.recentActivity.length).toFixed(1)
    : '0.0';
  const successRate = stats.totalChecks > 0
    ? ((stats.eligibleCount / stats.totalChecks) * 100).toFixed(1)
    : '0.0';

  if (loading) return (
    <div style={{ padding: '48px 56px', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-dim)' }}>
      Loading dashboard...
    </div>
  );

  return (
    <div style={{ padding: '48px 56px', maxWidth: '1200px', animation: 'fadeUp 280ms ease both' }}>

      {/* Page header */}
      <div style={{ marginBottom: '40px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.08em', color: 'var(--text-dim)', marginBottom: '8px' }}>
          01 / OVERVIEW
        </div>
        <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '28px', letterSpacing: '-0.02em', color: 'var(--text)', lineHeight: 1.1 }}>
          Dashboard
        </h1>
        <p style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-mid)', marginTop: '8px' }}>
          Platform summary and recent activity
        </p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '40px' }}>
        {statCards.map(({ label, value, sub, icon: Icon }, i) => (
          <div key={i} style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '24px',
            transition: 'border-color 200ms ease',
          }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-mid)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.08em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                {label}
              </div>
              <Icon size={14} color="var(--text-dim)" strokeWidth={1.5} />
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '40px', letterSpacing: '-0.04em', color: 'var(--text)', lineHeight: 1, marginBottom: '8px' }}>
              {value}
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
              {sub}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>

        {/* Recent predictions */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
            <BarChart3 size={14} color="var(--text-dim)" strokeWidth={1.5} />
            <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '14px', color: 'var(--text)' }}>
              Recent Eligibility Checks
            </span>
          </div>

          {stats.recentActivity.length === 0 ? (
            <div style={{
              border: '1px dashed var(--border)',
              borderRadius: '4px',
              padding: '40px',
              textAlign: 'center',
              fontFamily: 'var(--mono)',
              fontSize: '12px',
              color: 'var(--text-dim)',
            }}>
              No predictions yet. Run your first eligibility check.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {/* Table header */}
              <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 1fr auto', gap: '12px', padding: '0 12px 10px', borderBottom: '1px solid var(--border)' }}>
                {['Check', 'Score', 'Confidence', 'Status'].map(h => (
                  <div key={h} style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-dim)' }}>{h}</div>
                ))}
              </div>
              {stats.recentActivity.map((check, idx) => (
                <div key={idx} style={{
                  display: 'grid',
                  gridTemplateColumns: '80px 1fr 1fr auto',
                  gap: '12px',
                  padding: '12px',
                  borderRadius: '4px',
                  transition: 'background 150ms ease',
                }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontFamily: 'var(--mono)', fontWeight: 400, fontSize: '12px', color: 'var(--text-dim)' }}>
                    #{String(check.id).padStart(4, '0')}
                  </div>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text)' }}>
                    {(check.overall_score * 100).toFixed(1)}%
                  </div>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text)' }}>
                    {check.confidence_score.toFixed(1)}%
                  </div>
                  <div style={{
                    display: 'inline-block',
                    padding: '3px 10px',
                    borderRadius: '3px',
                    fontFamily: 'var(--mono)',
                    fontSize: '10px',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    fontWeight: 500,
                    ...(check.status === 'eligible'
                      ? { background: 'var(--ok-bg)', color: 'var(--ok)', border: '1px solid #c3e6d4' }
                      : { background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #f0c8c8' })
                  }}>
                    {check.status.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick stats */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
            <Activity size={14} color="var(--text-dim)" strokeWidth={1.5} />
            <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '14px', color: 'var(--text)' }}>
              Quick Stats
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {[
              { label: 'Avg. Confidence', value: `${avgConf}%` },
              { label: 'Success Rate', value: `${successRate}%` },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '6px' }}>
                  {label}
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '32px', letterSpacing: '-0.04em', color: 'var(--text)' }}>
                  {value}
                </div>
              </div>
            ))}

            <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border)' }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>
                Platform Status
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--ok)' }} />
                <span style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--ok)', fontWeight: 500 }}>
                  All systems operational
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeUp { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:translateY(0) } }
      `}</style>
    </div>
  );
};

export default Dashboard;