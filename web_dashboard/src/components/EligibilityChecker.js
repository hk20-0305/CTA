// src/components/EligibilityChecker.js — ClinSight Redesign
import { AlertCircle, CheckCircle, Upload, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../services/apiService';

// Lightweight markdown-to-HTML renderer (avoids ESM-only react-markdown v9 crash in CRA)
const renderMarkdown = (md) => {
  if (!md || typeof md !== 'string') return '';
  let html = md
    // Escape HTML entities
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Horizontal rules
    .replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:16px 0"/>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3 style="font-size:14px;font-weight:700;margin:14px 0 6px;color:var(--text)">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:16px;font-weight:700;margin:18px 0 8px;color:var(--text)">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:18px;font-weight:700;margin:20px 0 10px;color:var(--text)">$1</h1>')
    // Bold + italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--text)">$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Unordered list items
    .replace(/^- (.+)$/gm, '<li style="margin-left:20px;margin-bottom:4px;list-style:disc">$1</li>')
    // Numbered list items
    .replace(/^\d+\.\s+(.+)$/gm, '<li style="margin-left:20px;margin-bottom:4px;list-style:decimal">$1</li>')
    // Line breaks → paragraphs (double newline)
    .replace(/\n\n+/g, '</p><p style="margin-bottom:10px">')
    // Single newlines → <br>
    .replace(/\n/g, '<br/>');
  return '<p style="margin-bottom:10px">' + html + '</p>';
};


const EligibilityChecker = ({ token }) => {
  const [patients, setPatients] = useState([]);
  const [trials, setTrials] = useState([]);

  const [patientMode, setPatientMode] = useState('dropdown');
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [patientText, setPatientText] = useState('');
  const [patientFile, setPatientFile] = useState(null);

  const [trialMode, setTrialMode] = useState('dropdown');
  const [selectedTrialId, setSelectedTrialId] = useState('');
  const [trialText, setTrialText] = useState('');
  const [trialFile, setTrialFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { loadData(); }, [token]);

  const loadData = async () => {
    try {
      const [pd, td] = await Promise.all([
        api.getPatients(token),
        api.getTrials(token)
      ]);
      setPatients(Array.isArray(pd) ? pd : []);
      setTrials(Array.isArray(td) ? td : []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCheck = async () => {
    setError(''); setLoading(true); setResult(null);
    try {
      const fd = new FormData();
      if (patientMode === 'dropdown') { if (!selectedPatientId) throw new Error('Please select a patient'); fd.append('patient_id', selectedPatientId); }
      else if (patientMode === 'text') { if (!patientText) throw new Error('Please enter patient information'); fd.append('patient_text', patientText); }
      else { if (!patientFile) throw new Error('Please upload patient PDF'); fd.append('patient_pdf', patientFile); }

      if (trialMode === 'dropdown') { if (!selectedTrialId) throw new Error('Please select a trial'); fd.append('trial_id', selectedTrialId); }
      else if (trialMode === 'text') { if (!trialText) throw new Error('Please enter trial criteria'); fd.append('trial_text', trialText); }
      else { if (!trialFile) throw new Error('Please upload trial PDF'); fd.append('trial_pdf', trialFile); }

      const data = await api.checkEligibility(token, fd);
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const statusMeta = (s) => ({
    eligible: { icon: CheckCircle, color: 'var(--ok)', bg: 'var(--ok-bg)', border: '#c3e6d4' },
    not_eligible: { icon: XCircle, color: 'var(--danger)', bg: 'var(--danger-bg)', border: '#f0c8c8' },
  }[s] || { icon: AlertCircle, color: '#92400e', bg: '#fffbeb', border: '#fde68a' });

  // ── Shared field styles ────────────────────────────────────────────────
  const inputBase = {
    width: '100%', padding: '10px 12px',
    border: '1px solid var(--border)', borderRadius: '4px',
    background: 'var(--bg)', fontFamily: 'var(--mono)', fontSize: '14px',
    color: 'var(--text)', outline: 'none', transition: 'border-color 180ms',
  };
  const labelStyle = {
    display: 'block', fontFamily: 'var(--mono)', fontSize: '12px',
    letterSpacing: '0.08em', textTransform: 'uppercase',
    color: 'var(--text-dim)', marginBottom: '6px',
  };
  const modePillContainer = { display: 'flex', gap: '6px', marginBottom: '20px' };
  const modePill = (active) => ({
    padding: '6px 16px', border: `1px solid ${active ? 'var(--text)' : 'var(--border)'}`,
    borderRadius: '3px', background: active ? 'var(--text)' : 'transparent',
    color: active ? '#fff' : 'var(--text-mid)',
    fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.04em',
    cursor: 'pointer', transition: 'all 180ms',
  });

  const SectionPanel = ({ title, index }) => {
    const isPatient = index === 0;
    const mode = isPatient ? patientMode : trialMode;
    const setMode = isPatient ? setPatientMode : setTrialMode;

    return (
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '28px' }}>
        {/* Panel header */}
        <div style={{ paddingBottom: '18px', marginBottom: '22px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.08em', color: 'var(--text-dim)', marginBottom: '4px' }}>
            0{index + 1} / {isPatient ? 'PATIENT' : 'TRIAL'}
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '16px', color: 'var(--text)' }}>
            {isPatient ? 'Patient Information' : 'Trial Protocol'}
          </div>
        </div>

        {/* Mode switcher */}
        <div style={modePillContainer}>
          {['dropdown', 'text', 'pdf'].map(m => (
            <button key={m} style={modePill(mode === m)} onClick={() => setMode(m)}>
              {m === 'dropdown' ? 'Select' : m === 'text' ? 'Text' : 'PDF'}
            </button>
          ))}
        </div>

        {/* Dropdown */}
        {mode === 'dropdown' && (
          <div>
            <label style={labelStyle}>{isPatient ? 'Select patient' : 'Select trial'}</label>
            <select
              style={{ ...inputBase, cursor: 'pointer', appearance: 'none' }}
              value={isPatient ? selectedPatientId : selectedTrialId}
              onChange={e => isPatient ? setSelectedPatientId(e.target.value) : setSelectedTrialId(e.target.value)}
              onFocus={e => e.target.style.borderColor = 'var(--text)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            >
              <option value="">{isPatient ? '— Choose a patient —' : '— Choose a trial —'}</option>
              {isPatient
                ? patients.map(p => <option key={p.id} value={p.id}>{p.name} ({p.age}y, {p.gender})</option>)
                : trials.map(t => <option key={t.id} value={t.id}>{t.title} — {t.condition}</option>)
              }
            </select>
          </div>
        )}

        {/* Text */}
        {mode === 'text' && (
          <div>
            <label style={labelStyle}>{isPatient ? 'Patient data' : 'Trial criteria'}</label>
            <textarea
              style={{ ...inputBase, minHeight: '180px', resize: 'vertical', lineHeight: 1.7 }}
              placeholder={isPatient
                ? 'Name: John Doe\nAge: 45\nGender: Male\nConditions: Diabetes, Hypertension\nMedications: Metformin'
                : 'Inclusion Criteria:\n- Age 18–75\n- Type 2 Diabetes\n\nExclusion Criteria:\n- Pregnant\n- Severe kidney disease'
              }
              value={isPatient ? patientText : trialText}
              onChange={e => isPatient ? setPatientText(e.target.value) : setTrialText(e.target.value)}
              onFocus={e => e.target.style.borderColor = 'var(--text)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
        )}

        {/* PDF */}
        {mode === 'pdf' && (
          <div>
            <label style={labelStyle}>Upload PDF</label>
            <label htmlFor={isPatient ? 'patient-pdf' : 'trial-pdf'} style={{ cursor: 'pointer' }}>
              <div style={{
                border: `1px dashed ${(isPatient ? patientFile : trialFile) ? 'var(--text)' : 'var(--border)'}`,
                borderRadius: '4px', padding: '32px 20px', textAlign: 'center',
                background: (isPatient ? patientFile : trialFile) ? 'var(--bg)' : 'transparent',
                transition: 'all 180ms',
              }}>
                <Upload size={20} color="var(--text-dim)" style={{ margin: '0 auto 10px', display: 'block' }} />
                <div style={{ fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-mid)' }}>
                  {(isPatient ? patientFile : trialFile)?.name || 'Click to upload PDF'}
                </div>
                {!(isPatient ? patientFile : trialFile) && (
                  <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                    .pdf files only
                  </div>
                )}
              </div>
            </label>
            <input
              id={isPatient ? 'patient-pdf' : 'trial-pdf'}
              type="file" accept=".pdf" style={{ display: 'none' }}
              onChange={e => {
                const f = e.target.files[0];
                if (isPatient) setPatientFile(f); else setTrialFile(f);
              }}
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: '48px 56px', maxWidth: '1100px', animation: 'fadeUp 280ms ease both' }}>

      {/* Page header */}
      <div style={{ marginBottom: '40px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.08em', color: 'var(--text-dim)', marginBottom: '8px' }}>
          02 / ELIGIBILITY
        </div>
        <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '28px', letterSpacing: '-0.02em', color: 'var(--text)' }}>
          Check Eligibility
        </h1>
      </div>

      {/* Two panel input grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        <SectionPanel title="Patient" index={0} />
        <SectionPanel title="Trial" index={1} />
      </div>

      {/* Error */}
      {error && (
        <div style={{
          fontFamily: 'var(--mono)', fontSize: '12px', padding: '12px 16px',
          background: 'var(--danger-bg)', color: 'var(--danger)',
          border: '1px solid #f0c8c8', borderRadius: '4px', marginBottom: '20px',
        }}>
          {error}
        </div>
      )}

      {/* CTA */}
      <button
        onClick={handleCheck}
        disabled={loading}
        style={{
          width: '100%', padding: '14px',
          background: loading ? 'var(--border-mid)' : 'var(--text)',
          color: '#fff', border: 'none', borderRadius: '4px',
          fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '14px',
          letterSpacing: '0.04em', cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'background 180ms',
        }}
        onMouseEnter={e => { if (!loading) e.target.style.background = 'var(--accent-h)'; }}
        onMouseLeave={e => { if (!loading) e.target.style.background = 'var(--text)'; }}
      >
        {loading ? 'RUNNING CHECK...' : 'RUN ELIGIBILITY CHECK'}
      </button>

      {/* Result */}
      {result && (() => {
        const { icon: Icon, color, bg, border } = statusMeta(result.status);
        return (
          <div style={{ marginTop: '32px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '32px', animation: 'fadeUp 280ms ease both' }}>

            {/* Status banner */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '18px 22px', background: bg, border: `1px solid ${border}`, borderRadius: '6px', marginBottom: '28px' }}>
              <Icon size={22} color={color} strokeWidth={2} />
              <div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.08em', color, textTransform: 'uppercase', marginBottom: '2px' }}>
                  Result
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '22px', letterSpacing: '-0.02em', color }}>
                  {result.status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </div>
              </div>
            </div>

            {/* Score row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '28px' }}>
              {[
                { label: 'Overall Score', value: `${(result.overall_score * 100).toFixed(1)}%` },
                { label: 'Confidence', value: `${result.confidence_score.toFixed(1)}%` },
              ].map(({ label, value }) => (
                <div key={label} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', padding: '20px' }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '8px' }}>
                    {label}
                  </div>
                  <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '32px', letterSpacing: '-0.02em', color: 'var(--text)' }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>

            {/* Explanation */}
            <div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>
                ML-Generated Explanation
              </div>
              <div className="markdown-body" style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', padding: '20px', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-mid)', lineHeight: 1.8 }}
                dangerouslySetInnerHTML={{ __html: renderMarkdown(result.explanation) }}
              />
            </div>
          </div>
        );
      })()}

      <style>{`@keyframes fadeUp { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:translateY(0) } }`}</style>
    </div>
  );
};

export default EligibilityChecker;