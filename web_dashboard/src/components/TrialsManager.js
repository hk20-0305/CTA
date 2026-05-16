import { ArrowLeft, Edit2, FlaskConical, Plus, Save, Trash2, Upload, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../services/apiService';


const TrialsManager = ({ token }) => {
  const [trials, setTrials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTrial, setEditingTrial] = useState(null);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [formData, setFormData] = useState({ title: '', condition: '', phase: '', inclusion_criteria: '', exclusion_criteria: '' });

  useEffect(() => { loadTrials(); }, [token]);

  const loadTrials = async () => {
    try {
      const d = await api.getTrials(token);
      setTrials(Array.isArray(d) ? d : []);
    } catch (e) {
      console.error(e);
      setTrials([]);
    } finally {
      setLoading(false);
    }
  };

  const toArr = (str) => str.split('\n').map(s => s.trim()).filter(Boolean);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title: formData.title,
        condition: formData.condition,
        phase: formData.phase,
        inclusion_criteria: toArr(formData.inclusion_criteria),
        exclusion_criteria: toArr(formData.exclusion_criteria)
      };
      await api.createTrial(token, payload);
      await loadTrials();
      closeModal();
    } catch (e) {
      console.error(e);
      alert(e.message || 'Failed to create trial');
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title: formData.title,
        condition: formData.condition,
        phase: formData.phase,
        inclusion_criteria: toArr(formData.inclusion_criteria),
        exclusion_criteria: toArr(formData.exclusion_criteria)
      };
      const u = await api.updateTrial(token, editingTrial.id, payload);
      await loadTrials();
      closeModal();
      setSelectedTrial(u);
    } catch (e) {
      console.error(e);
      alert(e.message || 'Failed to update');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this trial?')) return;
    try {
      await api.deleteTrial(token, id);
      await loadTrials();
      setSelectedTrial(null);
    } catch (e) {
      console.error(e);
      alert(e.message || 'Failed to delete');
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await fetch('http://localhost:8000/api/trials/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd
      });
      if (r.ok) await loadTrials();
    } catch (e) {
      console.error(e);
    }
  };

  const openEditModal = (t) => {
    setEditingTrial(t);
    setFormData({ title: t.title || '', condition: t.condition || '', phase: t.phase || '', inclusion_criteria: t.inclusion_criteria?.join('\n') || '', exclusion_criteria: t.exclusion_criteria?.join('\n') || '' });
    setSelectedTrial(null); setShowModal(true);
  };
  const openCreateModal = () => { setEditingTrial(null); setFormData({ title: '', condition: '', phase: '', inclusion_criteria: '', exclusion_criteria: '' }); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditingTrial(null); };

  // ─── Shared styles ───────────────────────────────────────────────────────
  const inputStyle = { width: '100%', padding: '10px 12px', border: '1px solid var(--border)', borderRadius: '4px', background: 'var(--bg)', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text)', outline: 'none', transition: 'border-color 180ms', marginBottom: '16px' };
  const labelStyle = { display: 'block', fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '6px' };
  const btnPrimary = { padding: '10px 20px', background: 'var(--text)', color: '#fff', border: 'none', borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '14px', letterSpacing: '0.04em', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px', transition: 'background 180ms' };
  const btnOutline = { padding: '10px 20px', background: 'transparent', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '14px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px', transition: 'all 180ms' };
  const btnDanger = { padding: '10px 20px', background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #f0c8c8', borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '14px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px' };

  const phaseBadge = (phase) => ({
    display: 'inline-block', padding: '3px 10px',
    background: 'var(--bg)', border: '1px solid var(--border)',
    borderRadius: '3px', fontFamily: 'var(--mono)', fontSize: '10px',
    letterSpacing: '0.08em', color: 'var(--text-mid)', textTransform: 'uppercase',
  });

  if (loading) return (
    <div style={{ padding: '48px 56px', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-dim)' }}>
      Loading trials...
    </div>
  );

  // ── Detail View ──────────────────────────────────────────────────────────
  if (selectedTrial) {
    return (
      <div style={{ padding: '48px 56px', maxWidth: '860px', animation: 'fadeUp 280ms ease both' }}>
        <button style={{ ...btnOutline, marginBottom: '28px' }} onClick={() => setSelectedTrial(null)}>
          <ArrowLeft size={13} /> Back to trials
        </button>

        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '36px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', color: 'var(--text-dim)', marginBottom: '6px' }}>
                ID: {selectedTrial.trial_id}
              </div>
              <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '24px', letterSpacing: '-0.04em', color: 'var(--text)', maxWidth: '540px', lineHeight: 1.2 }}>
                {selectedTrial.title}
              </h1>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
              <button style={btnOutline} onClick={() => openEditModal(selectedTrial)}><Edit2 size={13} /> Edit</button>
              <button style={btnDanger} onClick={() => handleDelete(selectedTrial.id)}><Trash2 size={13} /> Delete</button>
            </div>
          </div>

          {/* Meta */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
            {[
              { label: 'Condition', value: selectedTrial.condition || '—' },
              { label: 'Phase', value: selectedTrial.phase || '—' },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '6px' }}>{label}</div>
                <div style={{ fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '16px', color: 'var(--text)' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Inclusion criteria */}
          <div style={{ marginBottom: '28px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--ok)', marginBottom: '12px' }}>
              ↳ Inclusion Criteria
            </div>
            {selectedTrial.inclusion_criteria?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {selectedTrial.inclusion_criteria.map((c, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px', padding: '10px 14px', background: 'var(--ok-bg)', border: '1px solid #c3e6d4', borderRadius: '4px' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--ok)', minWidth: '20px' }}>{i + 1}.</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text)', lineHeight: 1.6 }}>{c}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>None specified</div>
            )}
          </div>

          {/* Exclusion criteria */}
          <div style={{ marginBottom: '28px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--danger)', marginBottom: '12px' }}>
              ✕ Exclusion Criteria
            </div>
            {selectedTrial.exclusion_criteria?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {selectedTrial.exclusion_criteria.map((c, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px', padding: '10px 14px', background: 'var(--danger-bg)', border: '1px solid #f0c8c8', borderRadius: '4px' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--danger)', minWidth: '20px' }}>{i + 1}.</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text)', lineHeight: 1.6 }}>{c}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>None specified</div>
            )}
          </div>

          {/* ML extraction summary */}
          <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', padding: '18px', marginTop: '8px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '12px' }}>
              Extraction Summary
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {[
                selectedTrial.condition && `Primary condition: ${selectedTrial.condition}`,
                selectedTrial.inclusion_criteria?.length > 0 && `${selectedTrial.inclusion_criteria.length} inclusion criteria parsed`,
                selectedTrial.exclusion_criteria?.length > 0 && `${selectedTrial.exclusion_criteria.length} exclusion criteria parsed`,
                selectedTrial.phase && `Trial phase: ${selectedTrial.phase}`,
              ].filter(Boolean).map((line, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-mid)' }}>
                  <span style={{ color: 'var(--ok)' }}>✓</span> {line}
                </div>
              ))}
            </div>
          </div>
        </div>
        <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}`}</style>
      </div>
    );
  }

  // ── List View ────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '48px 56px', maxWidth: '1000px', animation: 'fadeUp 280ms ease both' }}>

      {/* Page header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '40px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.12em', color: 'var(--text-dim)', marginBottom: '8px' }}>04 / TRIALS</div>
          <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '36px', letterSpacing: '-0.04em', color: 'var(--text)' }}>Clinical Trials</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <label htmlFor="upload-trial" style={{ ...btnOutline, cursor: 'pointer' }}>
            <Upload size={13} /> Upload PDF
          </label>
          <input id="upload-trial" type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          <button style={btnPrimary} onClick={openCreateModal}><Plus size={13} /> Add Trial</button>
        </div>
      </div>

      {/* Empty or grid */}
      {trials.length === 0 ? (
        <div style={{ border: '1px dashed var(--border)', borderRadius: '8px', padding: '64px 40px', textAlign: 'center' }}>
          <FlaskConical size={28} color="var(--text-dim)" style={{ margin: '0 auto 12px', display: 'block' }} />
          <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '15px', color: 'var(--text-mid)', marginBottom: '6px' }}>No trials yet</div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>Upload a protocol PDF or add a trial manually.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
          {trials.map(trial => (
            <div key={trial.id}
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '22px', cursor: 'pointer', transition: 'border-color 180ms' }}
              onClick={() => setSelectedTrial(trial)}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-mid)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                <FlaskConical size={16} color="var(--text-dim)" strokeWidth={1.5} />
                {trial.phase && <span style={phaseBadge(trial.phase)}>{trial.phase}</span>}
              </div>
              <div style={{ fontFamily: 'var(--mono)', fontWeight: 400, fontSize: '15px', color: 'var(--text)', marginBottom: '6px', lineHeight: 1.3 }}>
                {trial.title}
              </div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)', marginBottom: '16px' }}>
                {trial.condition || 'No condition specified'}
              </div>
              <div style={{ display: 'flex', gap: '12px', fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--text-dim)', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
                <span>{trial.inclusion_criteria?.length || 0} inclusion</span>
                <span>{trial.exclusion_criteria?.length || 0} exclusion</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(26,25,22,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          onClick={closeModal}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', width: '800px', maxWidth: '95vw', maxHeight: '92vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
            onClick={e => e.stopPropagation()}>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px 32px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '20px', letterSpacing: '-0.02em', color: 'var(--text)' }}>
                {editingTrial ? 'Edit Trial' : 'Add Trial'}
              </div>
              <button onClick={closeModal} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', display: 'flex' }}><X size={20} /></button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
              <form onSubmit={editingTrial ? handleUpdate : handleCreate}>
                {[
                  { label: 'Trial Title', key: 'title', type: 'text', placeholder: 'Phase 2 Diabetes Intervention Study' },
                  { label: 'Condition', key: 'condition', type: 'text', placeholder: 'Type 2 Diabetes Mellitus' },
                ].map(({ label, key, type, placeholder }) => (
                  <div key={key}>
                    <label style={labelStyle}>{label}</label>
                    <input type={type} value={formData[key]} placeholder={placeholder} required style={inputStyle}
                      onChange={e => setFormData({ ...formData, [key]: e.target.value })}
                      onFocus={e => e.target.style.borderColor = 'var(--text)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border)'}
                    />
                  </div>
                ))}

                <label style={labelStyle}>Phase</label>
                <select value={formData.phase} style={{ ...inputStyle, cursor: 'pointer', appearance: 'none' }}
                  onChange={e => setFormData({ ...formData, phase: e.target.value })}>
                  <option value="">— Select phase —</option>
                  {['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'].map(p => <option key={p}>{p}</option>)}
                </select>

                {[
                  { label: 'Inclusion Criteria (one per line)', key: 'inclusion_criteria', placeholder: 'Age 18–75 years\nDiagnosed with Type 2 Diabetes\nHbA1c between 7.0–10.5%' },
                  { label: 'Exclusion Criteria (one per line)', key: 'exclusion_criteria', placeholder: 'Pregnant or breastfeeding\nSevere kidney disease\nRecent hospitalization' },
                ].map(({ label, key, placeholder }) => (
                  <div key={key}>
                    <label style={labelStyle}>{label}</label>
                    <textarea value={formData[key]} placeholder={placeholder}
                      style={{ ...inputStyle, minHeight: '110px', resize: 'vertical', lineHeight: 1.7 }}
                      onChange={e => setFormData({ ...formData, [key]: e.target.value })}
                      onFocus={e => e.target.style.borderColor = 'var(--text)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border)'}
                    />
                  </div>
                ))}

                <div style={{ position: 'sticky', bottom: 0, background: 'var(--surface)', paddingTop: '16px', marginTop: '16px' }}>
                  <button type="submit" style={{ ...btnPrimary, width: '100%', justifyContent: 'center' }}>
                    <Save size={13} /> {editingTrial ? 'Update Trial' : 'Create Trial'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}`}</style>
    </div>
  );
};

export default TrialsManager;