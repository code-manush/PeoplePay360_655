import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient, { unwrapData } from '../api/client';

export type Role = 'ADMIN' | 'HR' | 'EMPLOYEE';

export interface AuthUser {
  id: string;
  email: string;
  status?: string;
}

export interface AuthEmployee {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email?: string;
  department_id?: string;
}

interface AuthContextType {
  role: Role | null;
  user: AuthUser | null;
  employee: AuthEmployee | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role | null>(() => localStorage.getItem('peoplepay_role') as Role | null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('peoplepay_token'));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem('peoplepay_user');
    return raw ? JSON.parse(raw) : null;
  });
  const [employee, setEmployee] = useState<AuthEmployee | null>(() => {
    const raw = localStorage.getItem('peoplepay_employee');
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    if (token) localStorage.setItem('peoplepay_token', token);
    else localStorage.removeItem('peoplepay_token');
    if (role) localStorage.setItem('peoplepay_role', role);
    else localStorage.removeItem('peoplepay_role');
    if (user) localStorage.setItem('peoplepay_user', JSON.stringify(user));
    else localStorage.removeItem('peoplepay_user');
    if (employee) localStorage.setItem('peoplepay_employee', JSON.stringify(employee));
    else localStorage.removeItem('peoplepay_employee');
  }, [token, role, user, employee]);

  useEffect(() => {
    if (!token) return;
    apiClient.get('/auth/me').then((response) => {
      const data = unwrapData<any>(response);
      if (data?.role) setRole(data.role);
      if (data?.user) setUser(data.user);
      if (data?.employee) setEmployee(data.employee);
    }).catch(() => undefined);
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    const data = unwrapData<any>(response);
    setToken(data.token);
    setRole(data.role);
    setUser(data.user);
    setEmployee(data.employee);
  };

  const logout = () => {
    setToken(null);
    setRole(null);
    setUser(null);
    setEmployee(null);
  };

  return (
    <AuthContext.Provider value={{ role, user, employee, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
