import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const login = (payload) => api.post('/auth/login/', payload);
export const register = (payload) => api.post('/auth/register/', payload);

function isLikelyJwt(token) {
  return typeof token === 'string' && token.split('.').length === 3;
}

function isJwtExpired(token) {
  try {
    const payloadBase64 = token.split('.')[1];
    const payloadJson = atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'));
    const payload = JSON.parse(payloadJson);
    if (!payload.exp) return false;
    return Date.now() >= Number(payload.exp) * 1000;
  } catch {
    return true;
  }
}

function clearSessionAndRedirect() {
  try {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
  } catch {
    // noop
  }
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token');
    if (token && isLikelyJwt(token) && !isJwtExpired(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    } else if (token) {
      clearSessionAndRedirect();
    }
  } catch {
    // Ignore localStorage access issues and continue unauthenticated.
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearSessionAndRedirect();
    }
    return Promise.reject(error);
  }
);

// Dashboard
export const fetchDashboard = () => api.get('/dashboard/');

// Employees
export const fetchEmployees = () => api.get('/employees/');
export const fetchEmployee = (id) => api.get(`/employees/${id}/`);
export const createEmployee = (data) => api.post('/employees/', data);

// Meetings
export const fetchMeetings = (employeeId) => {
  const params = employeeId ? { employee_id: employeeId } : {};
  return api.get('/meetings/', { params });
};
export const fetchMeeting = (id) => api.get(`/meetings/${id}/`);
export const fetchMeetingTranscript = (meetingId) =>
  api.get('/meetings/transcript/', { params: { meeting_id: meetingId } });
export const fetchMeetingSummary = (meetingId) =>
  api.get('/meetings/summary/', { params: { meeting_id: meetingId } });
export const uploadMeeting = (formData) =>
  api.post('/meetings/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const uploadMeetingRecording = (formData) =>
  api.post('/meetings/upload-recording/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const fetchMeetingAnalysis = (meetingId) => api.get(`/meetings/analysis/${meetingId}/`);
export const fetchMeetingInsights = (meetingId) => api.get(`/meetings/${meetingId}/insights/`);
export const mapMeetingSpeakers = (payload) => api.post('/meetings/map-speakers/', payload);
export const fetchEmployeeMeetingInsights = (employeeId) =>
  api.get(`/employees/${employeeId}/meeting-insights/`);

// Insights
export const fetchInsights = (employeeId) => api.get(`/employee-insights/${employeeId}/`);

// Attrition
export const fetchAttrition = (employeeId) =>
  api.get('/attrition/', { params: { employee_id: employeeId } });

// AI Query
export const aiQuery = (query, employeeId = null) =>
  api.post('/ai/query/', { query, employee_id: employeeId });

// HR User Management (CHR only)
export const fetchHRUsers = () => api.get('/accounts/hr-users/');
export const addHRUser = (data) => api.post('/accounts/hr-users/', data);
export const deleteHRUser = (id) => api.delete(`/accounts/hr-users/${id}/`);

export default api;
