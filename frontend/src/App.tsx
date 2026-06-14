import { Navigate, Route, Routes } from 'react-router-dom';
import type { ReactElement } from 'react';

import { clearStoredTokens } from './api/client';
import { portalForRole, type SessionContext } from './api/auth';
import { AdminCreateUserPage } from './features/admin/AdminCreateUserPage';
import { AnalyticsReportsPage } from './features/analytics/AnalyticsPages';
import {
  AssignmentSubmissionPage,
  AssessmentAuthoringPage,
  StudentAssessmentAttemptPage
} from './features/assessments/AssessmentPages';
import {
  DashboardRedirect,
  LoginPage,
  NoAccessPage,
  OidcCallbackPage,
  ProtectedRoute
} from './features/auth/AuthPages';
import { useSessionContext } from './features/auth/session';
import { StudentCertificatesPage } from './features/certificates/CertificatePages';
import { ContentUploadPage } from './features/content/ContentPages';
import {
  CourseBuilderPage,
  CourseCatalogPage,
  CourseDetailPage,
  InstructorCourseManagementPage,
  StudentLearningPlayerPage
} from './features/courses/CoursePages';
import {
  AdminDashboardPage,
  InstructorDashboardPage,
  StudentDashboardPage
} from './features/dashboard/DashboardPages';
import { EnrollmentManagementPage } from './features/enrollment/EnrollmentPages';
import { GradingPage } from './features/grading/GradingPages';
import type { Portal } from './features/layout/PortalLayout';
import { NotificationCenterPage } from './features/notifications/NotificationPages';
import { StudentProgressPage } from './features/progress/ProgressPages';
import { LoadingState } from './features/shared/ui';

function portalHome(portal: Portal | 'none') {
  return portal === 'none' ? '/dashboard/no-access' : `/dashboard/${portal}`;
}

function PortalRoute({
  portal,
  children
}: {
  portal: Portal;
  children: (context: SessionContext) => ReactElement;
}) {
  const query = useSessionContext();
  if (query.isLoading) {
    return <LoadingState label="Loading session" />;
  }
  if (query.isError || !query.data) {
    clearStoredTokens();
    return <Navigate to="/login" replace />;
  }

  const allowedPortal = portalForRole(query.data.session.primary_role);
  if (allowedPortal !== portal) {
    return <Navigate to={portalHome(allowedPortal)} replace />;
  }

  return children(query.data);
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/oidc/callback" element={<OidcCallbackPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardRedirect />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard/student"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <StudentDashboardPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/courses"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <CourseCatalogPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/courses/:courseId"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <CourseDetailPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/courses/:courseId/learn"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <StudentLearningPlayerPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/progress"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <StudentProgressPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/assessments/:assessmentId/attempt"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <StudentAssessmentAttemptPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/assignments/:assignmentId/submit"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <AssignmentSubmissionPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/certificates"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <StudentCertificatesPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/student/notifications"
        element={<ProtectedRoute><PortalRoute portal="student">{(context) => <NotificationCenterPage context={context} />}</PortalRoute></ProtectedRoute>}
      />

      <Route
        path="/dashboard/instructor"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <InstructorDashboardPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/courses"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <InstructorCourseManagementPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/courses/:courseId/builder"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <CourseBuilderPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/content"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <ContentUploadPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/assessments"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <AssessmentAuthoringPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/grading"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <GradingPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/reports"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <AnalyticsReportsPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/instructor/notifications"
        element={<ProtectedRoute><PortalRoute portal="instructor">{(context) => <NotificationCenterPage context={context} />}</PortalRoute></ProtectedRoute>}
      />

      <Route
        path="/dashboard/admin"
        element={<ProtectedRoute><PortalRoute portal="admin">{(context) => <AdminDashboardPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/admin/users/new"
        element={<ProtectedRoute><PortalRoute portal="admin">{(context) => <AdminCreateUserPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/admin/enrollments"
        element={<ProtectedRoute><PortalRoute portal="admin">{(context) => <EnrollmentManagementPage context={context} />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/admin/reports"
        element={<ProtectedRoute><PortalRoute portal="admin">{(context) => <AnalyticsReportsPage context={context} activeNav="reports" />}</PortalRoute></ProtectedRoute>}
      />
      <Route
        path="/dashboard/admin/notifications"
        element={<ProtectedRoute><PortalRoute portal="admin">{(context) => <NotificationCenterPage context={context} />}</PortalRoute></ProtectedRoute>}
      />

      <Route path="/dashboard/no-access" element={<NoAccessPage />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
