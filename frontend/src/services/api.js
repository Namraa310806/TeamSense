import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // Ignore localStorage access issues and continue unauthenticated.
  }
  return config;
});

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
export const fetchAttrition = (employeeId) => api.get(`/attrition/${employeeId}/`);

// AI Query
export const aiQuery = (query, employeeId = null) =>
  api.post('/ai/query/', { query, employee_id: employeeId });

export default api;
