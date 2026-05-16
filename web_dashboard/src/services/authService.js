// src/services/authService.js
const API_BASE = 'http://localhost:8000/api';

export const register = async (email, password, name, hospitalName) => {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name, hospital_name: hospitalName }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Registration failed');
  }
  return response.json();
};

export const login = async (email, password) => {
  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        accept: 'application/json',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });
    
    if (!response.ok) {
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || 'Login failed';
      } catch {
        errorMessage = await response.text();
      }
      
      // Provide user-friendly error messages
      if (response.status === 401) {
        throw new Error('Invalid email or password');
      } else if (response.status === 404) {
        throw new Error('User not found');
      } else if (response.status === 422) {
        throw new Error('Invalid email or password format');
      } else {
        throw new Error(errorMessage || `Login failed (HTTP ${response.status})`);
      }
    }
    
    return response.json(); // { access_token, token_type }
  } catch (error) {
    // Handle network errors
    if (error.message === 'Failed to fetch' || error instanceof TypeError) {
      throw new Error('Cannot connect to server. Please check if the backend is running on http://localhost:8000');
    }
    throw error;
  }
};

export const getCurrentUser = async (token) => {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to load current user (HTTP ${response.status})`);
  }
  return response.json(); // { id, email, name, ... }
};