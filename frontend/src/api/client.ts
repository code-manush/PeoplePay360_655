import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('peoplepay_token');
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
    error.message ||
    'An unexpected error occurred'
  );
}

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('peoplepay_token');
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
  return [];
}

export function unwrapData<T = any>(response: any): T {
  return (response?.data ?? response) as T;
}

export default apiClient;
