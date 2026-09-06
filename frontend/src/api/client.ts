import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

let authToken = localStorage.getItem('peoplepay_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) localStorage.setItem('peoplepay_token', token);
  else localStorage.removeItem('peoplepay_token');
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = authToken || localStorage.getItem('peoplepay_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function extractErrorMessage(error: any): string {
  const data = error.response?.data;
  return (
    data?.error?.message ||
    data?.detail?.error?.message ||
    (typeof data?.detail === 'string' ? data.detail : null) ||
    data?.message ||
    (!error.response ? 'Cannot reach the API. Confirm the backend is running on port 8000, then refresh.' : null) ||
    error.message ||
    'An unexpected error occurred'
  );
}

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      setAuthToken(null);
      localStorage.removeItem('peoplepay_role');
      localStorage.removeItem('peoplepay_user');
      localStorage.removeItem('peoplepay_employee');
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(new Error(extractErrorMessage(error)));
  }
);

export function unwrapList<T = any>(response: any): T[] {
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.data)) return response.data;
  if (Array.isArray(response?.data?.items)) return response.data.items;
  if (Array.isArray(response?.items)) return response.items;
  return [];
}

export function unwrapData<T = any>(response: any): T {
  return (response?.data ?? response) as T;
}

export async function downloadPayslipPdf(payslipId: string, filename?: string) {
  const token = authToken || localStorage.getItem('peoplepay_token');
  const res = await axios.get(`${API_BASE_URL}/payroll/payslips/${payslipId}/pdf`, {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const url = window.URL.createObjectURL(res.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || `payslip-${payslipId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export default apiClient;
