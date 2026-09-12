export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function login(email, password) {
  const formData = new URLSearchParams();
  formData.append('username', email); // OAuth2 expects username
  formData.append('password', password);

  const res = await fetch(`${API_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString()
  });
  
  if (!res.ok) throw new Error('Login failed');
  const data = await res.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function register(email, password) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error('Registration failed');
  return res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_URL}/documents`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders()
    },
    body: formData
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function getTaskStatus(taskId) {
  const res = await fetch(`${API_URL}/tasks/${taskId}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch status');
  return res.json();
}

export async function askQuestion(docId, query) {
  const res = await fetch(`${API_URL}/documents/${docId}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({ query })
  });
  if (!res.ok) throw new Error('Failed to ask question');
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_URL}/documents`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}
