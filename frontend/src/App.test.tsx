import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import { App } from './App';
import { storeTokens } from './api/client';
import {
  completeOidcCallback,
  getOidcConfig,
  getSessionContext,
  login,
  startOidcAuthorization,
  type SessionContext
} from './api/auth';
import {
  getAdminDashboard,
  getInstructorDashboard,
  getStudentDashboard
} from './api/dashboards';
import { createUserProfile } from './api/users';
import { listCourses } from './api/courses';
import { createPresignedUpload, listContentAssets } from './api/content';
import {
  createEnrollment,
  listBatchEnrollments,
  listCohortEnrollments,
  listEnrollments
} from './api/enrollments';
import { listCourseProgress } from './api/progress';
import {
  createQuestionBank,
  listAssessments,
  listQuestionBanks
} from './api/assessments';
import {
  listCertificates,
  listGradeRecords,
  listGradingRules,
  listPublishedResults,
  publishGrade
} from './api/grading';
import {
  listNotificationPreferences,
  listNotifications,
  markAllNotificationsRead
} from './api/notifications';
import {
  generateReport,
  listDashboardAggregates,
  listReportSnapshots,
  listUsageMetrics,
  searchResources
} from './api/analytics';

vi.mock('./api/auth', async () => {
  const actual = await vi.importActual<typeof import('./api/auth')>('./api/auth');
  return {
    ...actual,
    completeOidcCallback: vi.fn(),
    getOidcConfig: vi.fn(),
    login: vi.fn(),
    startOidcAuthorization: vi.fn(),
    getSessionContext: vi.fn()
  };
});

vi.mock('./api/dashboards', () => ({
  getStudentDashboard: vi.fn(),
  getInstructorDashboard: vi.fn(),
  getAdminDashboard: vi.fn()
}));

vi.mock('./api/users', () => ({
  createUserProfile: vi.fn()
}));

vi.mock('./api/courses', () => ({
  listCourses: vi.fn(),
  getCourse: vi.fn(),
  createCourse: vi.fn(),
  updateCourse: vi.fn(),
  publishCourse: vi.fn(),
  archiveCourse: vi.fn(),
  deleteCourse: vi.fn(),
  getCourseStructure: vi.fn(),
  listCategories: vi.fn(),
  listTags: vi.fn(),
  createModule: vi.fn(),
  createLesson: vi.fn(),
  publishLesson: vi.fn(),
  createTopic: vi.fn()
}));

vi.mock('./api/content', () => ({
  listContentAssets: vi.fn(),
  createPresignedUpload: vi.fn(),
  completePresignedUpload: vi.fn(),
  proxyUploadAsset: vi.fn(),
  createSignedAccess: vi.fn()
}));

vi.mock('./api/enrollments', () => ({
  listEnrollments: vi.fn(),
  createEnrollment: vi.fn(),
  transitionEnrollment: vi.fn(),
  getEnrollmentHistory: vi.fn(),
  checkEnrollmentAccess: vi.fn(),
  listBatchEnrollments: vi.fn(),
  createBatchEnrollment: vi.fn(),
  listCohortEnrollments: vi.fn(),
  createCohortEnrollment: vi.fn()
}));

vi.mock('./api/progress', () => ({
  listCourseProgress: vi.fn(),
  updateLessonProgress: vi.fn(),
  updateVideoProgress: vi.fn(),
  updateAssessmentProgress: vi.fn()
}));

vi.mock('./api/assessments', () => ({
  listQuestionBanks: vi.fn(),
  createQuestionBank: vi.fn(),
  listQuestions: vi.fn(),
  createQuestion: vi.fn(),
  listAssessments: vi.fn(),
  createAssessment: vi.fn(),
  updateAssessment: vi.fn(),
  replaceAssessmentQuestions: vi.fn(),
  publishAssessment: vi.fn(),
  closeAssessment: vi.fn(),
  startQuizAttempt: vi.fn(),
  getQuizAttempt: vi.fn(),
  saveQuizAnswers: vi.fn(),
  submitQuizAttempt: vi.fn(),
  autoSubmitQuizAttempt: vi.fn(),
  listAssignmentSubmissions: vi.fn(),
  createAssignmentSubmission: vi.fn(),
  updateAssignmentSubmission: vi.fn(),
  submitAssignmentSubmission: vi.fn()
}));

vi.mock('./api/grading', () => ({
  listGradingRules: vi.fn(),
  createGradingRule: vi.fn(),
  listGradeRecords: vi.fn(),
  calculateGrade: vi.fn(),
  createManualReview: vi.fn(),
  completeManualReview: vi.fn(),
  overrideGrade: vi.fn(),
  publishGrade: vi.fn(),
  listPublishedResults: vi.fn(),
  listCertificates: vi.fn(),
  evaluateCertificateEligibility: vi.fn(),
  updateCertificateAsset: vi.fn(),
  revokeCertificate: vi.fn()
}));

vi.mock('./api/notifications', () => ({
  listNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markNotificationUnread: vi.fn(),
  markAllNotificationsRead: vi.fn(),
  listNotificationPreferences: vi.fn(),
  upsertNotificationPreference: vi.fn(),
  listNotificationTemplates: vi.fn()
}));

vi.mock('./api/analytics', () => ({
  searchResources: vi.fn(),
  searchResourceType: vi.fn(),
  listReportSnapshots: vi.fn(),
  createReportSnapshot: vi.fn(),
  generateReport: vi.fn(),
  listDashboardAggregates: vi.fn(),
  listUsageMetrics: vi.fn()
}));

const baseProfile = {
  id: '22222222-2222-2222-2222-222222222222',
  auth_account_id: '11111111-1111-1111-1111-111111111111',
  institution_id: '33333333-3333-3333-3333-333333333333',
  first_name: 'Ada',
  last_name: 'Lovelace',
  display_name: 'Ada Lovelace',
  avatar_url: null,
  status: 'active',
  metadata: {},
  profile_type: 'student' as const,
  role_profile: {},
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  deleted_at: null
};

function sessionContext(role: string | null, profileType = 'student'): SessionContext {
  return {
    session: {
      account_id: '11111111-1111-1111-1111-111111111111',
      email: 'ada@example.com',
      status: 'active',
      primary_role: role,
      role_assignments: role
        ? [
            {
              id: '44444444-4444-4444-4444-444444444444',
              role_code: role,
              role_name: role,
              scope_type: role === 'super_admin' ? 'platform' : 'institution',
              scope_id: role === 'super_admin' ? null : baseProfile.institution_id,
              assigned_at: '2026-01-01T00:00:00Z'
            }
          ]
        : []
    },
    profile: {
      ...baseProfile,
      profile_type: profileType as SessionContext['profile']['profile_type']
    }
  };
}

const studentDashboard = {
  portal: 'student' as const,
  profile: baseProfile,
  institution_id: baseProfile.institution_id,
  aggregate: null,
  active_courses: [{ title: 'Algebra' }],
  completed_lessons: [],
  pending_assessments: [],
  grades: [],
  upcoming_deadlines: [],
  summary: {
    active_course_count: 1,
    completed_lesson_count: 0,
    pending_assessment_count: 0,
    grade_count: 0,
    upcoming_deadline_count: 0
  }
};

const instructorDashboard = {
  portal: 'instructor' as const,
  profile: baseProfile,
  institution_id: baseProfile.institution_id,
  aggregate: null,
  learner_engagement: [],
  progress_distribution: [],
  assessment_status: [],
  course_summaries: [{ title: 'Physics' }],
  summary: {
    assigned_course_count: 1,
    active_learner_count: 0,
    pending_assessment_count: 0,
    average_progress_percent: 0
  }
};

const adminDashboard = {
  portal: 'admin' as const,
  profile: baseProfile,
  institution_id: baseProfile.institution_id,
  aggregate: null,
  active_users: [],
  enrollments: [],
  completion_rates: [],
  assessment_results: [],
  system_usage: [{ name: 'Logins' }],
  summary: {
    active_user_count: 0,
    enrollment_count: 0,
    average_completion_percent: 0,
    assessment_result_count: 0,
    system_event_count: 1
  }
};

function renderApp(route = '/') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function storeTestTokens() {
  storeTokens({
    access: 'access-token',
    refresh: 'refresh-token',
    access_expires_at: '2026-01-01T00:05:00Z',
    refresh_expires_at: '2026-01-08T00:00:00Z'
  });
}

beforeEach(() => {
  window.localStorage.clear();
  vi.mocked(completeOidcCallback).mockReset();
  vi.mocked(getOidcConfig).mockReset();
  vi.mocked(login).mockReset();
  vi.mocked(startOidcAuthorization).mockReset();
  vi.mocked(getSessionContext).mockReset();
  vi.mocked(getStudentDashboard).mockReset();
  vi.mocked(getInstructorDashboard).mockReset();
  vi.mocked(getAdminDashboard).mockReset();
  vi.mocked(createUserProfile).mockReset();
  vi.mocked(listCourses).mockReset();
  vi.mocked(listContentAssets).mockReset();
  vi.mocked(createPresignedUpload).mockReset();
  vi.mocked(listEnrollments).mockReset();
  vi.mocked(createEnrollment).mockReset();
  vi.mocked(listBatchEnrollments).mockReset();
  vi.mocked(listCohortEnrollments).mockReset();
  vi.mocked(listCourseProgress).mockReset();
  vi.mocked(listQuestionBanks).mockReset();
  vi.mocked(createQuestionBank).mockReset();
  vi.mocked(listAssessments).mockReset();
  vi.mocked(listGradeRecords).mockReset();
  vi.mocked(listGradingRules).mockReset();
  vi.mocked(listPublishedResults).mockReset();
  vi.mocked(publishGrade).mockReset();
  vi.mocked(listCertificates).mockReset();
  vi.mocked(listNotifications).mockReset();
  vi.mocked(markAllNotificationsRead).mockReset();
  vi.mocked(listNotificationPreferences).mockReset();
  vi.mocked(searchResources).mockReset();
  vi.mocked(listReportSnapshots).mockReset();
  vi.mocked(listDashboardAggregates).mockReset();
  vi.mocked(listUsageMetrics).mockReset();
  vi.mocked(generateReport).mockReset();
  vi.mocked(getStudentDashboard).mockResolvedValue(studentDashboard);
  vi.mocked(getInstructorDashboard).mockResolvedValue(instructorDashboard);
  vi.mocked(getAdminDashboard).mockResolvedValue(adminDashboard);
  vi.mocked(createUserProfile).mockResolvedValue({
    ...baseProfile,
    id: '55555555-5555-5555-5555-555555555555',
    email: undefined,
    first_name: 'New',
    last_name: 'User',
    display_name: 'New User',
    profile_type: 'student'
  } as never);
  vi.mocked(getOidcConfig).mockResolvedValue({
    enabled: false,
    provider: 'oidc',
    provider_label: 'SSO',
    scopes: ['openid', 'email', 'profile']
  });
  vi.mocked(listCourses).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 'course-1',
        title: 'Biology Basics',
        description: 'Cells and systems',
        status: 'published',
        difficulty_level: 'beginner',
        categories: [],
        tags: [],
        prerequisite_course_ids: [],
        learning_outcomes: []
      }
    ]
  });
  vi.mocked(listContentAssets).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(createPresignedUpload).mockResolvedValue({
    asset: { id: 'asset-1', title: 'Slides', status: 'draft' },
    object_key: 'objects/slides.pdf',
    upload_url: 'http://minio/upload',
    upload_headers: {},
    expires_at: '2026-01-01T00:15:00Z'
  });
  vi.mocked(listEnrollments).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listBatchEnrollments).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listCohortEnrollments).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(createEnrollment).mockResolvedValue({
    id: 'enrollment-1',
    student_profile_id: baseProfile.id,
    course_id: 'course-1',
    institution_id: baseProfile.institution_id,
    status: 'active'
  });
  vi.mocked(listCourseProgress).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 'progress-1',
        course_id: 'course-1',
        status: 'in_progress',
        completion_percent: 45,
        lessons_completed: 3,
        assessments_completed: 1
      }
    ]
  });
  vi.mocked(listQuestionBanks).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(createQuestionBank).mockResolvedValue({ id: 'bank-1', title: 'Midterm bank' });
  vi.mocked(listAssessments).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listGradeRecords).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'grade-1', title: 'Quiz 1', status: 'calculated', score: 90 }]
  });
  vi.mocked(listGradingRules).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listPublishedResults).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(publishGrade).mockResolvedValue({ id: 'result-1', title: 'Published' });
  vi.mocked(listCertificates).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'certificate-1', certificate_number: 'LG-20260101-ABCDEF1234', valid: true }]
  });
  vi.mocked(listNotifications).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'notification-1', title: 'Grade published', event_type: 'GradePublished', read_at: null }]
  });
  vi.mocked(markAllNotificationsRead).mockResolvedValue({ status: 'ok' });
  vi.mocked(listNotificationPreferences).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(searchResources).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'search-1', title: 'Biology Basics', resource_type: 'course' }]
  });
  vi.mocked(listReportSnapshots).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listDashboardAggregates).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(listUsageMetrics).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(generateReport).mockResolvedValue({ id: 'report-1', report_type: 'active_users' });
});

test('unauthenticated users redirect to login', async () => {
  renderApp('/dashboard');

  expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument();
});

test('login stores tokens and redirects by role', async () => {
  vi.mocked(login).mockImplementation(async () => {
    const tokens = {
      access: 'access-token',
      refresh: 'refresh-token',
      access_expires_at: '2026-01-01T00:05:00Z',
      refresh_expires_at: '2026-01-08T00:00:00Z'
    };
    storeTokens(tokens);
    return tokens;
  });
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/login');
  await userEvent.type(screen.getByLabelText(/email/i), 'student@example.com');
  await userEvent.type(screen.getByLabelText(/password/i), 'temporary-pass');
  await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(window.localStorage.getItem('learngrid.tokens')).toContain('access-token');
});

test('OIDC sign in button follows enabled config', async () => {
  vi.mocked(getOidcConfig).mockResolvedValue({
    enabled: true,
    provider: 'oidc',
    provider_label: 'Campus SSO',
    scopes: ['openid', 'email', 'profile']
  });

  renderApp('/login');

  expect(await screen.findByRole('button', { name: /continue with campus sso/i })).toBeInTheDocument();
});

test('OIDC callback stores tokens and redirects by role', async () => {
  vi.mocked(completeOidcCallback).mockImplementation(async () => {
    const tokens = {
      access: 'oidc-access-token',
      refresh: 'oidc-refresh-token',
      access_expires_at: '2026-01-01T00:05:00Z',
      refresh_expires_at: '2026-01-08T00:00:00Z'
    };
    storeTokens(tokens);
    return tokens;
  });
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/auth/oidc/callback?code=auth-code&state=state-token');

  await waitFor(() => expect(completeOidcCallback).toHaveBeenCalledTimes(1));
  expect(vi.mocked(completeOidcCallback).mock.calls[0][0]).toEqual({
    code: 'auth-code',
    state: 'state-token'
  });
  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(window.localStorage.getItem('learngrid.tokens')).toContain('oidc-access-token');
});

test('OIDC callback errors show controlled failure state', async () => {
  vi.mocked(completeOidcCallback).mockRejectedValueOnce(new Error('invalid state'));

  renderApp('/auth/oidc/callback?code=auth-code&state=state-token');

  expect(await screen.findByRole('alert')).toHaveTextContent('SSO sign in failed.');
});

test('student portal renders populated dashboard state', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.getAllByText(/Algebra/i).length).toBeGreaterThan(0);
});

test('instructor role redirects to instructor portal', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard');

  expect(await screen.findByRole('heading', { name: /instructor dashboard/i })).toBeInTheDocument();
  expect(screen.getAllByText(/Physics/i).length).toBeGreaterThan(0);
});

test('admin navigation hides unrelated portals', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin');

  expect(await screen.findByRole('heading', { name: /admin dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Admin$/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Create User$/i })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /^Student$/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /^Instructor$/i })).not.toBeInTheDocument();
});

test('dashboard error state exposes retry action', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  vi.mocked(getStudentDashboard)
    .mockRejectedValueOnce(new Error('network'))
    .mockResolvedValueOnce(studentDashboard);

  renderApp('/dashboard/student');

  expect(await screen.findByText(/Unable to load dashboard/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /retry/i }));
  await waitFor(() => expect(screen.getAllByText(/Algebra/i).length).toBeGreaterThan(0));
});

test('admin can create a student user', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/users/new');

  expect(await screen.findByRole('heading', { name: /create user/i })).toBeInTheDocument();
  await userEvent.type(screen.getByLabelText(/^Email$/i), 'new-student@example.com');
  await userEvent.type(screen.getByLabelText(/temporary password/i), 'Temporary123!');
  await userEvent.type(screen.getByLabelText(/first name/i), 'New');
  await userEvent.type(screen.getByLabelText(/last name/i), 'Student');
  await userEvent.type(screen.getByLabelText(/student number/i), 'STU-200');
  await userEvent.click(screen.getByRole('button', { name: /^Create user$/i }));

  await waitFor(() => expect(createUserProfile).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createUserProfile).mock.calls[0][0]).toMatchObject({
    email: 'new-student@example.com',
    temporary_password: 'Temporary123!',
    profile_type: 'student',
    first_name: 'New',
    last_name: 'Student',
    student: { student_number: 'STU-200' }
  });
  expect(await screen.findByText(/Created user: New User/i)).toBeInTheDocument();
});

test('admin can create an instructor user with optional fields', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/users/new');

  expect(await screen.findByRole('heading', { name: /create user/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/profile type/i), 'instructor');
  await userEvent.type(screen.getByLabelText(/^Email$/i), 'new-instructor@example.com');
  await userEvent.type(screen.getByLabelText(/temporary password/i), 'Temporary123!');
  await userEvent.type(screen.getByLabelText(/first name/i), 'New');
  await userEvent.type(screen.getByLabelText(/last name/i), 'Instructor');
  await userEvent.type(screen.getByLabelText(/employee number/i), 'EMP-200');
  await userEvent.type(screen.getByLabelText(/title/i), 'Professor');
  await userEvent.click(screen.getByRole('button', { name: /^Create user$/i }));

  await waitFor(() => expect(createUserProfile).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createUserProfile).mock.calls[0][0]).toMatchObject({
    email: 'new-instructor@example.com',
    profile_type: 'instructor',
    instructor: {
      employee_number: 'EMP-200',
      title: 'Professor'
    }
  });
  expect(vi.mocked(createUserProfile).mock.calls[0][0]).not.toHaveProperty('student');
});

test('institution admin cannot select super admin', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin/users/new');

  expect(await screen.findByRole('heading', { name: /create user/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/profile type/i), 'admin');

  expect(screen.getByLabelText(/institution id/i)).toHaveValue(baseProfile.institution_id);
  expect(screen.getByLabelText(/institution id/i)).toHaveAttribute('readonly');
  expect(screen.getByLabelText(/admin type/i)).toHaveValue('institution_admin');
  expect(screen.queryByRole('option', { name: /super admin/i })).not.toBeInTheDocument();
});

test('create user API failure displays an error state', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));
  vi.mocked(createUserProfile).mockRejectedValueOnce({
    response: { data: { detail: 'Email already exists.' } }
  });

  renderApp('/dashboard/admin/users/new');

  expect(await screen.findByRole('heading', { name: /create user/i })).toBeInTheDocument();
  await userEvent.type(screen.getByLabelText(/^Email$/i), 'duplicate@example.com');
  await userEvent.type(screen.getByLabelText(/temporary password/i), 'Temporary123!');
  await userEvent.type(screen.getByLabelText(/first name/i), 'Duplicate');
  await userEvent.type(screen.getByLabelText(/last name/i), 'Student');
  await userEvent.type(screen.getByLabelText(/student number/i), 'STU-DUP');
  await userEvent.click(screen.getByRole('button', { name: /^Create user$/i }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Email already exists.');
});

test('non-admin roles cannot access create user route', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/admin/users/new');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /create user/i })).not.toBeInTheDocument();
});

test('student catalog route renders API-backed courses and progress route renders completion state', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/student/courses');

  expect(await screen.findByRole('heading', { name: /course catalog/i })).toBeInTheDocument();
  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /catalog/i })).toBeInTheDocument();

  cleanup();
  renderApp('/dashboard/student/progress');
  expect(await screen.findByRole('heading', { name: /learning progress/i })).toBeInTheDocument();
  expect(await screen.findByText(/45%/i)).toBeInTheDocument();
});

test('instructor content route submits presigned upload metadata', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/content');

  expect(await screen.findByRole('heading', { name: /content upload/i })).toBeInTheDocument();
  await userEvent.type(screen.getAllByLabelText(/^Title$/i)[0], 'Slides');
  await userEvent.type(screen.getByLabelText(/file name/i), 'slides.pdf');
  await userEvent.clear(screen.getByLabelText(/file size bytes/i));
  await userEvent.type(screen.getByLabelText(/file size bytes/i), '1200');
  await userEvent.click(screen.getByRole('button', { name: /create upload url/i }));

  await waitFor(() => expect(createPresignedUpload).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createPresignedUpload).mock.calls[0][0]).toMatchObject({
    title: 'Slides',
    file_name: 'slides.pdf',
    file_size_bytes: 1200
  });
});

test('admin enrollment route creates an individual enrollment', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('institution_admin', 'admin'));

  renderApp('/dashboard/admin/enrollments');

  expect(await screen.findByRole('heading', { name: /enrollment management/i })).toBeInTheDocument();
  await userEvent.type(screen.getAllByLabelText(/student profile id/i)[0], baseProfile.id);
  await userEvent.type(screen.getAllByLabelText(/^Course ID$/i)[0], '99999999-9999-9999-9999-999999999999');
  await userEvent.click(screen.getByRole('button', { name: /^Save$/i }));

  await waitFor(() => expect(createEnrollment).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createEnrollment).mock.calls[0][0]).toMatchObject({
    student_profile_id: baseProfile.id,
    institution_id: baseProfile.institution_id
  });
});

test('instructor assessment authoring creates a question bank', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/assessments');

  expect(await screen.findByRole('heading', { name: /assessment authoring/i })).toBeInTheDocument();
  await userEvent.type(screen.getAllByLabelText(/^Title$/i)[0], 'Midterm bank');
  await userEvent.click(screen.getAllByRole('button', { name: /^Save$/i })[0]);

  await waitFor(() => expect(createQuestionBank).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createQuestionBank).mock.calls[0][0]).toMatchObject({
    title: 'Midterm bank',
    owner_profile_id: baseProfile.id
  });
});

test('instructor grading route publishes a grade and student certificates route renders issued certificate', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/grading');

  expect(await screen.findByRole('heading', { name: /grading and manual reviews/i })).toBeInTheDocument();
  await userEvent.click(await screen.findByRole('button', { name: /publish/i }));
  await waitFor(() =>
    expect(publishGrade).toHaveBeenCalledWith('grade-1', { published_feedback: null })
  );

  cleanup();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/certificates');
  expect(await screen.findByRole('heading', { name: /^certificates$/i })).toBeInTheDocument();
  expect((await screen.findAllByText(/LG-20260101-ABCDEF1234/i)).length).toBeGreaterThan(0);
});

test('notification center and reports routes render API-backed operational data', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('institution_admin', 'admin'));

  renderApp('/dashboard/admin/notifications');

  expect(await screen.findByRole('heading', { name: /notification center/i })).toBeInTheDocument();
  expect(await screen.findByText(/Grade published/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /mark all read/i }));
  await waitFor(() => expect(markAllNotificationsRead).toHaveBeenCalledTimes(1));

  renderApp('/dashboard/admin/reports');
  expect(await screen.findByRole('heading', { name: /analytics and reporting/i })).toBeInTheDocument();
  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /generate report/i }));
  await waitFor(() => expect(generateReport).toHaveBeenCalledTimes(1));
});
