// src/theme.js — ClinSight Design System
// Import this in any component for consistent styles and helpers

// ─── CSS Variables (injected by App.js) ──────────────────────────────────
// --bg        #f7f6f4   warm off-white background
// --surface   #ffffff   card/panel surfaces
// --border    #e2e0db   hairline borders
// --border-mid #c8c5be  slightly stronger borders (hover states)
// --text      #1a1916   primary text (near-black, warm)
// --text-mid  #6b6760   secondary text
// --text-dim  #a09d98   tertiary / placeholder
// --accent    #1a1916   same as text for flat mono look
// --danger    #b94040   error red
// --danger-bg #fdf2f2
// --ok        #2e7d52   success green
// --ok-bg     #f0f7f3
// --mono      'DM Mono', monospace
// --sans      'Syne', sans-serif
// --radius    4px
// --radius-md 8px

// ─── Reusable style objects ───────────────────────────────────────────────
export const t = {
  // Layout
  pageWrapper: {
    padding: '48px 56px',
    maxWidth: '1100px',
    animation: 'fadeUp 280ms ease both',
  },

  // Page header block
  pageHeader: {
    marginBottom: '40px',
    paddingBottom: '24px',
    borderBottom: '1px solid var(--border)',
  },
  pageLabel: {
    fontFamily: 'var(--mono)',
    fontSize: '11px',
    letterSpacing: '0.12em',
    color: 'var(--text-dim)',
    marginBottom: '8px',
    textTransform: 'uppercase',
  },
  pageTitle: {
    fontFamily: 'var(--sans)',
    fontWeight: 800,
    fontSize: '36px',
    letterSpacing: '-0.04em',
    color: 'var(--text)',
    lineHeight: 1.1,
  },

  // Cards
  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '24px',
  },
  cardLabel: {
    fontFamily: 'var(--mono)',
    fontSize: '10px',
    letterSpacing: '0.12em',
    color: 'var(--text-dim)',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  cardValue: {
    fontFamily: 'var(--sans)',
    fontWeight: 800,
    fontSize: '32px',
    letterSpacing: '-0.04em',
    color: 'var(--text)',
    lineHeight: 1,
  },
  cardValueSub: {
    fontFamily: 'var(--mono)',
    fontSize: '12px',
    color: 'var(--text-mid)',
    marginTop: '6px',
  },

  // Inputs
  label: {
    display: 'block',
    fontFamily: 'var(--mono)',
    fontSize: '10px',
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: 'var(--text-mid)',
    marginBottom: '8px',
  },
  input: {
    width: '100%',
    padding: '11px 13px',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    background: 'var(--bg)',
    fontFamily: 'var(--mono)',
    fontSize: '13px',
    color: 'var(--text)',
    outline: 'none',
    transition: 'border-color 200ms ease',
  },
  select: {
    width: '100%',
    padding: '11px 13px',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    background: 'var(--bg)',
    fontFamily: 'var(--mono)',
    fontSize: '13px',
    color: 'var(--text)',
    outline: 'none',
    cursor: 'pointer',
    appearance: 'none',
  },
  textarea: {
    width: '100%',
    padding: '11px 13px',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    background: 'var(--bg)',
    fontFamily: 'var(--mono)',
    fontSize: '13px',
    color: 'var(--text)',
    outline: 'none',
    resize: 'vertical',
    minHeight: '100px',
    lineHeight: 1.6,
  },

  // Buttons
  btnPrimary: {
    padding: '11px 22px',
    background: 'var(--text)',
    color: '#ffffff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--sans)',
    fontWeight: 700,
    fontSize: '13px',
    letterSpacing: '0.03em',
    cursor: 'pointer',
    transition: 'background 200ms ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },
  btnSecondary: {
    padding: '11px 22px',
    background: 'transparent',
    color: 'var(--text)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--sans)',
    fontWeight: 600,
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'border-color 200ms ease, background 200ms ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },
  btnDanger: {
    padding: '11px 22px',
    background: 'var(--danger-bg)',
    color: 'var(--danger)',
    border: '1px solid #f0c8c8',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--sans)',
    fontWeight: 600,
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'background 200ms ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },

  // Status badges
  badge: (status) => ({
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--mono)',
    fontSize: '11px',
    fontWeight: 500,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    ...(status === 'eligible' || status === 'active' || status === 'ok' ? {
      background: 'var(--ok-bg)',
      color: 'var(--ok)',
      border: '1px solid #c3e6d4',
    } : status === 'ineligible' || status === 'error' || status === 'closed' ? {
      background: 'var(--danger-bg)',
      color: 'var(--danger)',
      border: '1px solid #f0c8c8',
    } : {
      background: '#f4f3f1',
      color: 'var(--text-mid)',
      border: '1px solid var(--border)',
    }),
  }),

  // Table
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    fontFamily: 'var(--mono)',
    fontSize: '10px',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: 'var(--text-dim)',
    padding: '10px 16px',
    textAlign: 'left',
    borderBottom: '2px solid var(--border)',
    fontWeight: 400,
  },
  td: {
    fontFamily: 'var(--mono)',
    fontSize: '13px',
    color: 'var(--text)',
    padding: '14px 16px',
    borderBottom: '1px solid var(--border)',
    verticalAlign: 'middle',
  },

  // Inline mono detail
  mono: {
    fontFamily: 'var(--mono)',
    fontSize: '12px',
    color: 'var(--text-mid)',
  },

  // Section divider
  divider: {
    border: 'none',
    borderTop: '1px solid var(--border)',
    margin: '32px 0',
  },

  // Error / info alerts
  alert: (type = 'error') => ({
    fontFamily: 'var(--mono)',
    fontSize: '12px',
    padding: '12px 16px',
    borderRadius: 'var(--radius)',
    letterSpacing: '0.02em',
    lineHeight: 1.6,
    marginBottom: '20px',
    ...(type === 'error' ? {
      background: 'var(--danger-bg)',
      color: 'var(--danger)',
      border: '1px solid #f0c8c8',
    } : type === 'success' ? {
      background: 'var(--ok-bg)',
      color: 'var(--ok)',
      border: '1px solid #c3e6d4',
    } : {
      background: '#f4f3f1',
      color: 'var(--text-mid)',
      border: '1px solid var(--border)',
    }),
  }),

  // Skeleton / loading shimmer (apply as className)
  loadingText: {
    fontFamily: 'var(--mono)',
    fontSize: '13px',
    color: 'var(--text-dim)',
    letterSpacing: '0.04em',
  },
};

// ─── Helper: Page header shorthand ───────────────────────────────────────
export const PageHeader = ({ index, label, title, subtitle }) => (
  <div style={t.pageHeader}>
    <div style={t.pageLabel}>
      {String(index).padStart(2, '0')} / {label}
    </div>
    <h1 style={t.pageTitle}>{title}</h1>
    {subtitle && (
      <p style={{ ...t.mono, marginTop: '10px', color: 'var(--text-mid)' }}>
        {subtitle}
      </p>
    )}
  </div>
);

export default t;