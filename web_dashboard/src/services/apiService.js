// src/services/apiService.js
const API_BASE = 'http://localhost:8000/api';

// Helper function to handle API responses
const handleResponse = async (response, endpoint) => {
  console.log(`${endpoint} response status:`, response.status);
  console.log(`${endpoint} response headers:`, [...response.headers.entries()]);

  if (!response.ok) {
    let errorMessage;
    const contentType = response.headers.get('content-type');

    try {
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        console.error(`${endpoint} error JSON:`, errorData);
        errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
      } else {
        const text = await response.text();
        console.error(`${endpoint} error text:`, text);
        errorMessage = text;
      }
    } catch (parseError) {
      console.error(`${endpoint} error parsing response:`, parseError);
      errorMessage = `HTTP ${response.status}`;
    }

    // Provide specific error messages
    if (response.status === 401) {
      throw new Error(`Unauthorized: ${errorMessage}. Your session may have expired.`);
    } else if (response.status === 403) {
      throw new Error(`Forbidden: ${errorMessage}. You don't have permission to access this resource.`);
    } else if (response.status === 404) {
      throw new Error(`Not found: ${errorMessage}`);
    } else {
      throw new Error(`Failed to load ${endpoint} (HTTP ${response.status}): ${errorMessage}`);
    }
  }

  return response.json();
};

export const getPatients = async (token) => {
  console.log('=== FETCHING PATIENTS ===');
  console.log('Token (first 20 chars):', token?.substring(0, 20));
  console.log('Full Authorization header:', `Bearer ${token}`);

  try {
    const res = await fetch(`${API_BASE}/patients`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    return await handleResponse(res, 'getPatients');
  } catch (error) {
    console.error('getPatients caught error:', error);
    throw error;
  }
};

export const createPatient = async (token, patientData) => {
  const res = await fetch(`${API_BASE}/patients`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(patientData),
  });
  return await handleResponse(res, 'createPatient');
};

export const updatePatient = async (token, patientId, patientData) => {
  const res = await fetch(`${API_BASE}/patients/${patientId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(patientData),
  });
  return await handleResponse(res, 'updatePatient');
};

export const deletePatient = async (token, patientId) => {
  const res = await fetch(`${API_BASE}/patients/${patientId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return await handleResponse(res, 'deletePatient');
};

export const createTrial = async (token, trialData) => {
  const res = await fetch(`${API_BASE}/trials`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(trialData),
  });
  return await handleResponse(res, 'createTrial');
};

export const updateTrial = async (token, trialId, trialData) => {
  const res = await fetch(`${API_BASE}/trials/${trialId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(trialData),
  });
  return await handleResponse(res, 'updateTrial');
};

export const deleteTrial = async (token, trialId) => {
  const res = await fetch(`${API_BASE}/trials/${trialId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return await handleResponse(res, 'deleteTrial');
};

export const getTrials = async (token) => {
  console.log('=== FETCHING TRIALS ===');
  console.log('Token (first 20 chars):', token?.substring(0, 20));

  try {
    const res = await fetch(`${API_BASE}/trials`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    return await handleResponse(res, 'getTrials');
  } catch (error) {
    console.error('getTrials caught error:', error);
    throw error;
  }
};

export const getChecks = async (token) => {
  console.log('=== FETCHING CHECKS ===');
  console.log('Token (first 20 chars):', token?.substring(0, 20));

  try {
    const res = await fetch(`${API_BASE}/checks`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    return await handleResponse(res, 'getChecks');
  } catch (error) {
    console.error('getChecks caught error:', error);
    throw error;
  }
};

export const checkEligibility = async (token, formData) => {
  const response = await fetch(`${API_BASE}/eligibility/check`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  return await handleResponse(response, 'checkEligibility');
};

export const getCheckHistory = async (userId) => {
  const response = await fetch(`${API_BASE}/eligibility/history/${userId}`);

  if (!response.ok) {
    throw new Error('Failed to get history');
  }

  return response.json();
};

// Test function - you can call this from console to debug
window.testApiEndpoints = async () => {
  const token = localStorage.getItem('authToken');
  console.log('Testing with token:', token?.substring(0, 20));

  console.log('\n1. Testing /auth/me...');
  try {
    const meRes = await fetch('http://localhost:8000/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    console.log('✅ /auth/me status:', meRes.status);
    const meData = await meRes.json();
    console.log('✅ /auth/me data:', meData);
  } catch (e) {
    console.error('❌ /auth/me failed:', e);
  }

  console.log('\n2. Testing /patients...');
  try {
    const patientsRes = await fetch('http://localhost:8000/api/patients', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    console.log('✅ /patients status:', patientsRes.status);
    const patientsData = await patientsRes.json();
    console.log('✅ /patients data:', patientsData);
  } catch (e) {
    console.error('❌ /patients failed:', e);
  }

  console.log('\n3. Testing /trials...');
  try {
    const trialsRes = await fetch('http://localhost:8000/api/trials', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    console.log('✅ /trials status:', trialsRes.status);
    const trialsData = await trialsRes.json();
    console.log('✅ /trials data:', trialsData);
  } catch (e) {
    console.error('❌ /trials failed:', e);
  }

  console.log('\n4. Testing /checks...');
  try {
    const checksRes = await fetch('http://localhost:8000/api/checks', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    console.log('✅ /checks status:', checksRes.status);
    const checksData = await checksRes.json();
    console.log('✅ /checks data:', checksData);
  } catch (e) {
    console.error('❌ /checks failed:', e);
  }
};

console.log('🔍 Debug helper loaded! Run window.testApiEndpoints() in console to test all endpoints');