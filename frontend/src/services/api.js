import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
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
export const uploadMeeting = (data) => api.post('/meetings/upload/', data);

// Insights
export const fetchInsights = (employeeId) => api.get(`/employee-insights/${employeeId}/`);

// Attrition
export const fetchAttrition = (employeeId) => api.get(`/attrition/${employeeId}/`);

// AI Query
export const aiQuery = (query, employeeId = null) =>
  api.post('/ai/query/', { query, employee_id: employeeId });

export default api;
