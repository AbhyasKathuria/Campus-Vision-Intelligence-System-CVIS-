import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { OpsLayout } from './layouts/OpsLayout';
import { StudentLayout } from './layouts/StudentLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { OpsDashboard } from './pages/ops/Dashboard';
import { OpsReviewQueue } from './pages/ops/ReviewQueue';
import { OpsTelemetryView } from './pages/ops/TelemetryView';
import { OpsEventPhotoManager } from './pages/ops/EventPhotoManager';
import { OpsCameraRegistry } from './pages/ops/CameraRegistry';
import { OpsAuditLogViewer } from './pages/ops/AuditLogViewer';
import { OpsSystemSettings } from './pages/ops/SystemSettings';
import { StudentSelfieSearch } from './pages/student/SelfieSearch';
import { StudentConsentManager } from './pages/student/ConsentManager';
import { StudentHistoryView } from './pages/student/StudentHistory';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Staff Ops Center Console (Dark Theme: #0B0F17) */}
        <Route path="/ops" element={<OpsLayout />}>
          <Route index element={<OpsDashboard />} />
          <Route path="reviews" element={<OpsReviewQueue />} />
          <Route path="telemetry" element={<OpsTelemetryView />} />
          <Route path="events" element={<OpsEventPhotoManager />} />
          <Route path="cameras" element={<OpsCameraRegistry />} />
          <Route path="audit" element={<OpsAuditLogViewer />} />
          <Route path="settings" element={<OpsSystemSettings />} />
        </Route>

        {/* Student Portal (Light Theme: #FAFAF8) */}
        <Route path="/student" element={<StudentLayout />}>
          <Route index element={<StudentSelfieSearch />} />
          <Route path="consent" element={<StudentConsentManager />} />
          <Route path="history" element={<StudentHistoryView />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
