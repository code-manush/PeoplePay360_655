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
import Organization from './pages/Organization/Organization';
import ScheduleList from './pages/Schedules/ScheduleList';
import AuditLogs from './pages/Audit/AuditLogs';
import { AuthProvider, useAuth, type Role } from './contexts/AuthContext';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { role, token } = useAuth();
  if (!role || !token) {
    return <Navigate to="/landing" replace />;
  }
  return <>{children}</>;
}

function RoleRoute({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const { role } = useAuth();
  if (!role || !roles.includes(role)) {
    return <Navigate to="/" replace />;
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
            <Route path="/employees" element={<RoleRoute roles={['ADMIN', 'HR']}><EmployeeList /></RoleRoute>} />
            <Route path="/organization" element={<RoleRoute roles={['ADMIN', 'HR']}><Organization /></RoleRoute>} />
            <Route path="/contracts" element={<RoleRoute roles={['ADMIN', 'HR']}><ContractList /></RoleRoute>} />
            <Route path="/schedules" element={<RoleRoute roles={['ADMIN', 'HR']}><ScheduleList /></RoleRoute>} />
            <Route path="/attendance" element={<AttendanceList />} />
            <Route path="/leave" element={<LeaveList />} />
            <Route path="/payroll" element={<PayrollList />} />
            <Route path="/payroll-config" element={<RoleRoute roles={['ADMIN', 'HR']}><SalaryConfig /></RoleRoute>} />
            <Route path="/reports" element={<RoleRoute roles={['ADMIN', 'HR']}><Reports /></RoleRoute>} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/audit" element={<RoleRoute roles={['ADMIN', 'HR']}><AuditLogs /></RoleRoute>} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/ai-agent" element={<RoleRoute roles={['ADMIN', 'HR']}><AIAgent /></RoleRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
