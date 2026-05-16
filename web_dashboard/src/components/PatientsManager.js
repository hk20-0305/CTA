import { ArrowLeft, Edit2, FileText, Plus, Save, Trash2, Upload, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../services/apiService';


const PatientsManager = ({ token }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingPatient, setEditingPatient] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [formData, setFormData] = useState({ name: '', age: '', gender: 'Male', conditions: '', medications: '' });

  useEffect(() => { loadPatients(); }, [token]);

  const loadPatients = async () => {
    try {
      const d = await api.getPatients(token);
      setPatients(Array.isArray(d) ? d : []);
    } catch (e) {
      console.error(e);
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const toArr = (str, sep = ',') => str.split(sep).map(s => s.trim()).filter(Boolean);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        age: parseInt(formData.age),
        gender: formData.gender,
        comorbidities: toArr(formData.conditions),
        medications: toArr(formData.medications)
      };
      await api.createPatient(token, payload);
      await loadPatients();
      closeModal();
    } catch (e) {
      console.error(e);
      alert(e.message || 'Failed to create patient');
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        age: parseInt(formData.age),
        gender: formData.gender,
        comorbidities: toArr(formData.conditions),
        medications: toArr(formData.medications)
      };
      const u = await api.updatePatient(token, editingPatient.id, payload);
      await loadPatients();
      closeModal();
      setSelectedPatient(u);
    } catch (e) {
      console.error(e);
      alert(e.message || 'Failed to update');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this patient?')) return;
    try {
      await api.deletePatient(token, id);
      await loadPatients();
      setSelectedPatient(null);
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
      // Directly call fetch for upload as it's multipart
      const r = await fetch('http://localhost:8000/api/patients/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd
      });
      if (r.ok) await loadPatients();
    } catch (e) {
      console.error(e);
    }
  };

  const openEditModal = (p) => {
    setEditingPatient(p);
    setFormData({ name: p.name || '', age: p.age || '', gender: p.gender || 'Male', conditions: p.comorbidities?.join(', ') || '', medications: p.medications?.join(', ') || '' });
    setSelectedPatient(null); setShowModal(true);
  };
  const openCreateModal = () => { setEditingPatient(null); setFormData({ name: '', age: '', gender: 'Male', conditions: '', medications: '' }); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditingPatient(null); };

  // ─── Shared styles ──────────────────────────────────────────────────────
  const inputStyle = {
    width: '100%', padding: '10px 12px', border: '1px solid var(--border)', borderRadius: '4px',
    background: 'var(--bg)', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text)', outline: 'none',
    transition: 'border-color 180ms', marginBottom: '16px',
  };
  const labelStyle = {
    display: 'block', fontFamily: 'var(--mono)', fontSize: '12px', letterSpacing: '0.08em',
    textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '6px',
  };
  const btnPrimary = {
    padding: '10px 20px', background: 'var(--text)', color: '#fff', border: 'none', borderRadius: '4px',
    fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '14px', letterSpacing: '0.04em',
    cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px', transition: 'background 180ms',
  };
  const btnOutline = {
    padding: '10px 20px', background: 'transparent', color: 'var(--text)', border: '1px solid var(--border)',
    borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '14px',
    cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px', transition: 'all 180ms',
  };
  const btnDanger = {
    padding: '10px 20px', background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #f0c8c8',
    borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '14px',
    cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '7px',
  };
  const chip = {
    display: 'inline-block', padding: '4px 10px', background: 'var(--bg)',
    border: '1px solid var(--border)', borderRadius: '3px', fontFamily: 'var(--mono)',
    fontSize: '13px', color: 'var(--text-mid)', marginRight: '6px', marginBottom: '6px',
  };

  if (loading) return (
    <div style={{ padding: '48px 56px', fontFamily: 'var(--mono)', fontSize: '14px', color: 'var(--text-dim)' }}>
      Loading patients...
    </div>
  );

  // ── Detail View ──────────────────────────────────────────────────────────
  if (selectedPatient) {
    return (
      <div style={{ padding: '48px 56px', maxWidth: '860px', animation: 'fadeUp 280ms ease both' }}>
        <button style={{ ...btnOutline, marginBottom: '28px' }} onClick={() => setSelectedPatient(null)}>
          <ArrowLeft size={13} /> Back to patients
        </button>

        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '36px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', color: 'var(--text-dim)', marginBottom: '6px' }}>
                MRN: {selectedPatient.mrn}
              </div>
              <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '28px', letterSpacing: '-0.04em', color: 'var(--text)' }}>
                {selectedPatient.name || 'Unknown Patient'}
              </h1>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button style={btnOutline} onClick={() => openEditModal(selectedPatient)}>
                <Edit2 size={13} /> Edit
              </button>
              <button style={btnDanger} onClick={() => handleDelete(selectedPatient.id)}>
                <Trash2 size={13} /> Delete
              </button>
            </div>
          </div>

          {/* Meta row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '24px', marginBottom: '32px' }}>
            {[
              { label: 'Age', value: `${selectedPatient.age || '—'} years` },
              { label: 'Gender', value: selectedPatient.gender || '—' },
              { label: 'Created', value: new Date(selectedPatient.created_at).toLocaleDateString() },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontFamily: 'var(--mono)', fontWeight: 400, fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '6px' }}>{label}</div>
                <div style={{ fontFamily: 'var(--mono)', fontWeight: 500, fontSize: '16px', color: 'var(--text)' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Conditions */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>Medical Conditions</div>
            {selectedPatient.comorbidities?.length > 0
              ? selectedPatient.comorbidities.map((c, i) => <span key={i} style={chip}>{c}</span>)
              : <span style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>No conditions recorded</span>}
          </div>

          {/* Medications */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>Medications</div>
            {selectedPatient.medications?.length > 0
              ? selectedPatient.medications.map((m, i) => <span key={i} style={chip}>{m}</span>)
              : <span style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>No medications recorded</span>}
          </div>

          {/* Lab values */}
          {selectedPatient.lab_values && Object.keys(selectedPatient.lab_values).length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>Lab Values</div>
              <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '4px', padding: '16px' }}>
                {Object.entries(selectedPatient.lab_values).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', gap: '12px', fontFamily: 'var(--mono)', fontSize: '12px', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-dim)', minWidth: '140px' }}>{k}</span>
                    <span style={{ color: 'var(--text)' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ML extraction summary */}
          <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '6px', padding: '18px', marginTop: '8px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '12px' }}>
              Extraction Summary
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {[
                selectedPatient.comorbidities?.length > 0 && `${selectedPatient.comorbidities.length} condition(s) identified via BioBERT NER`,
                selectedPatient.medications?.length > 0 && `${selectedPatient.medications.length} medication(s) extracted`,
                selectedPatient.lab_values && Object.keys(selectedPatient.lab_values).length > 0 && `${Object.keys(selectedPatient.lab_values).length} lab value(s) parsed`,
                selectedPatient.age && selectedPatient.gender && `Demographics: Age ${selectedPatient.age}, ${selectedPatient.gender}`,
              ].filter(Boolean).map((line, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-mid)' }}>
                  <span style={{ color: 'var(--ok)' }}>✓</span> {line}
                </div>
              ))}
              {!selectedPatient.comorbidities?.length && !selectedPatient.medications?.length && (
                <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                  Manually entered — no PDF extraction
                </div>
              )}
            </div>
          </div>
        </div>
        <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }`}</style>
      </div>
    );
  }

  // ── List View ────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '48px 56px', maxWidth: '1000px', animation: 'fadeUp 280ms ease both' }}>

      {/* Page header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '40px', paddingBottom: '24px', borderBottom: '1px solid var(--border)' }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', letterSpacing: '0.12em', color: 'var(--text-dim)', marginBottom: '8px' }}>03 / PATIENTS</div>
          <h1 style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '36px', letterSpacing: '-0.04em', color: 'var(--text)' }}>Patients</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <label htmlFor="upload-patient" style={{ ...btnOutline, cursor: 'pointer' }}>
            <Upload size={13} /> Upload PDF
          </label>
          <input id="upload-patient" type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          <button style={btnPrimary} onClick={openCreateModal}>
            <Plus size={13} /> Add Patient
          </button>
        </div>
      </div>

      {/* Table or empty */}
      {patients.length === 0 ? (
        <div style={{ border: '1px dashed var(--border)', borderRadius: '8px', padding: '64px 40px', textAlign: 'center' }}>
          <FileText size={28} color="var(--text-dim)" style={{ margin: '0 auto 12px', display: 'block' }} />
          <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '15px', color: 'var(--text-mid)', marginBottom: '6px' }}>No patients yet</div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>Upload a PDF or add a patient manually.</div>
        </div>
      ) : (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 80px 100px 160px auto', gap: '16px', padding: '12px 20px', borderBottom: '2px solid var(--border)', background: 'var(--bg)' }}>
            {['Name', 'Age', 'Gender', 'MRN', ''].map(h => (
              <div key={h} style={{ fontFamily: 'var(--mono)', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-dim)' }}>{h}</div>
            ))}
          </div>
          {patients.map((p, idx) => (
            <div key={p.id} style={{
              display: 'grid', gridTemplateColumns: '1fr 80px 100px 160px auto',
              gap: '16px', padding: '14px 20px', alignItems: 'center',
              borderBottom: idx < patients.length - 1 ? '1px solid var(--border)' : 'none',
              transition: 'background 150ms', cursor: 'pointer',
            }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              onClick={() => setSelectedPatient(p)}
            >
              <div style={{ fontFamily: 'var(--mono)', fontWeight: 400, fontSize: '14px', color: 'var(--text)' }}>{p.name || '—'}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-mid)' }}>{p.age || '—'}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-mid)' }}>{p.gender || '—'}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)' }}>{p.mrn}</div>
              <div style={{ display: 'flex', gap: '6px' }} onClick={e => e.stopPropagation()}>
                <button style={{ ...btnOutline, padding: '6px 10px' }} onClick={() => openEditModal(p)}><Edit2 size={12} /></button>
                <button style={{ ...btnDanger, padding: '6px 10px' }} onClick={() => handleDelete(p.id)}><Trash2 size={12} /></button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(26,25,22,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          onClick={closeModal}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', width: '600px', maxWidth: '95vw', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
            onClick={e => e.stopPropagation()}>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px 32px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '20px', letterSpacing: '-0.02em', color: 'var(--text)' }}>
                {editingPatient ? 'Edit Patient' : 'Add Patient'}
              </div>
              <button onClick={closeModal} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', display: 'flex' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
              <form onSubmit={editingPatient ? handleUpdate : handleCreate}>
                {[
                  { label: 'Full Name', key: 'name', type: 'text', placeholder: 'Jane Doe' },
                  { label: 'Age', key: 'age', type: 'number', placeholder: '45' },
                ].map(({ label, key, type, placeholder }) => (
                  <div key={key}>
                    <label style={labelStyle}>{label}</label>
                    <input type={type} value={formData[key]} placeholder={placeholder} required
                      style={inputStyle}
                      onChange={e => setFormData({ ...formData, [key]: e.target.value })}
                      onFocus={e => e.target.style.borderColor = 'var(--text)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border)'}
                    />
                  </div>
                ))}

                <label style={labelStyle}>Gender</label>
                <select value={formData.gender} style={{ ...inputStyle, cursor: 'pointer', appearance: 'none' }}
                  onChange={e => setFormData({ ...formData, gender: e.target.value })}>
                  {['Male', 'Female', 'Other'].map(g => <option key={g}>{g}</option>)}
                </select>

                {[
                  { label: 'Conditions (comma-separated)', key: 'conditions', placeholder: 'Diabetes, Hypertension' },
                  { label: 'Medications (comma-separated)', key: 'medications', placeholder: 'Metformin, Amlodipine' },
                ].map(({ label, key, placeholder }) => (
                  <div key={key}>
                    <label style={labelStyle}>{label}</label>
                    <input type="text" value={formData[key]} placeholder={placeholder}
                      style={inputStyle}
                      onChange={e => setFormData({ ...formData, [key]: e.target.value })}
                      onFocus={e => e.target.style.borderColor = 'var(--text)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border)'}
                    />
                  </div>
                ))}

                <div style={{ position: 'sticky', bottom: 0, background: 'var(--surface)', paddingTop: '16px', marginTop: '16px' }}>
                  <button type="submit" style={{ ...btnPrimary, width: '100%', justifyContent: 'center' }}>
                    <Save size={13} /> {editingPatient ? 'Update Patient' : 'Create Patient'}
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

export default PatientsManager;