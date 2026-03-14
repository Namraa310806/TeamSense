import axios from 'axios';
import { showToast } from '../utils/toast';

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
    localStorage.removeItem('demo_mode');
  } catch {
    // noop
  }
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

function isDemoMode() {
  try {
    return localStorage.getItem('demo_mode') === 'true';
  } catch {
    return false;
  }
}

api.interceptors.request.use((config) => {
  if (isDemoMode()) {
    return config;
  }
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
  (response) => {
    const showToastForRequest = response?.config?.meta?.showToast === true;
    if (showToastForRequest) {
      const successMessage =
        response?.data?.message
        || response?.data?.detail
        || 'Action completed successfully.';
      showToast(successMessage, 'success', 2000);
    }

    return response;
  },
  (error) => {
    const showToastForRequest = error?.config?.meta?.showToast === true;
    if (showToastForRequest) {
      const errorMessage =
        error?.response?.data?.error
        || error?.response?.data?.message
        || error?.response?.data?.detail
        || 'Something went wrong. Please try again.';
      showToast(errorMessage, 'error', 2000);
    }

    if (error?.response?.status === 401 && !isDemoMode()) {
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
export const createEmployee = (data) => api.post('/employees/', data, { meta: { showToast: true } });

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
    meta: { showToast: true },
  });
export const uploadMeetingRecording = (formData) =>
  api.post('/meetings/upload-recording/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    meta: { showToast: true },
  });
export const fetchMeetingAnalysis = (meetingId) => api.get(`/meetings/analysis/${meetingId}/`);
export const fetchMeetingInsights = (meetingId) => api.get(`/meetings/${meetingId}/insights/`);
export const mapMeetingSpeakers = (payload) => api.post('/meetings/map-speakers/', payload, { meta: { showToast: true } });
export const fetchEmployeeMeetingInsights = (employeeId) =>
  api.get(`/employees/${employeeId}/meeting-insights/`);

export const uploadCsvFeedback = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/ingestion/csv/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    meta: { showToast: true },
  });
};

export const ingestSlackData = (payload) => api.post('/ingestion/slack/', payload, { meta: { showToast: true } });

export const ingestGoogleFormsData = (payload) => api.post('/ingestion/forms/', payload, { meta: { showToast: true } });

export const uploadIngestionDocument = ({ file, employeeId, participants }) => {
  const formData = new FormData();
  formData.append('file', file);
  if (employeeId) formData.append('employee_id', String(employeeId));
  if (participants) formData.append('participants', participants);
  return api.post('/ingestion/document/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    meta: { showToast: true },
  });
};

export const fetchIngestionStats = () => api.get('/ingestion/stats/');
export const fetchIngestionOverview = () => api.get('/ingestion/overview/');
export const fetchIngestionJobs = () => api.get('/ingestion/jobs/');

export const fetchFeedback = () => api.get('/ingestion/feedback/');

// Insights
export const fetchInsights = (employeeId) => api.get(`/employee-insights/${employeeId}/`);

// Attrition
export const fetchAttrition = (employeeId) =>
  api.get('/analytics/attrition/', { params: { employee_id: employeeId } });

// AI Query
export const aiQuery = (query, employeeId = null) =>
  api.post('/ai/query/', { query, employee_id: employeeId });

// HR Assistant (OpenAI-backed)
export const hrAssistantQuery = (query, employeeId = null) =>
  api.post('/ai/hr-assistant/', { question: query, employee_id: employeeId });

// HR User Management (CHR only)
export const fetchHRUsers = () => api.get('/accounts/hr-users/');
export const addHRUser = (data) => api.post('/accounts/hr-users/', data, { meta: { showToast: true } });
export const deleteHRUser = (id) => api.delete(`/accounts/hr-users/${id}/`, { meta: { showToast: true } });

export default api;
