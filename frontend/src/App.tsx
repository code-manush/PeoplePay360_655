import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import Dashboard from './pages/Dashboard';
import EmployeeList from './pages/Employees/EmployeeList';
import PayrollList from './pages/Payroll/PayrollList';
import SalaryConfig from './pages/Payroll/SalaryConfig';
import AttendanceList from './pages/Attendance/AttendanceList';
import LeaveList from './pages/Leave/LeaveList';
import ContractList from './pages/Contracts/ContractList';
import Reports from './pages/Reports/Reports';
import Notifications from './pages/Notifications/Notifications';
import Settings from './pages/Settings/Settings';
import Login from './pages/Login';
import Landing from './pages/Landing/Landing';
import Register from './pages/Register/Register';
import AIAgent from './pages/AIAgent/AIAgent';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { role, token } = useAuth();
  if (!role || !token) {
    return <Navigate to="/landing" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/landing" element={<Landing />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<EmployeeList />} />
            <Route path="/contracts" element={<ContractList />} />
            <Route path="/attendance" element={<AttendanceList />} />
            <Route path="/leave" element={<LeaveList />} />
            <Route path="/payroll" element={<PayrollList />} />
            <Route path="/payroll-config" element={<SalaryConfig />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/ai-agent" element={<AIAgent />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
