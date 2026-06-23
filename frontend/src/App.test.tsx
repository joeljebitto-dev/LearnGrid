import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import { App } from './App';
import { storeTokens } from './api/client';
import {
  completeOidcCallback,
  createRoleAssignment,
  getOidcConfig,
  getSessionContext,
  listRoleAssignments,
  login,
  startOidcAuthorization,
  type SessionContext,
  type UserProfile
} from './api/auth';
import {
  getAdminDashboard,
  getInstructorDashboard,
  getStudentDashboard
} from './api/dashboards';
import {
  archiveInstitution,
  createInstitution,
  createUserProfile,
  deactivateUserProfile,
  getUserProfile,
  listInstitutions,
  listUserProfiles,
  updateInstitution,
  updateUserProfile,
  type Institution
} from './api/users';
import {
  archiveCourse,
  createCourse,
  createLesson,
  createModule,
  createTopic,
  deleteCourse,
  getCourse,
  getCourseStructure,
  listCourses,
  publishCourse,
  updateCourse
} from './api/courses';
import { createPresignedUpload, listContentAssets } from './api/content';
import {
  createEnrollment,
  listBatchEnrollments,
  listCohortEnrollments,
  listEnrollments
} from './api/enrollments';
import { listCourseProgress } from './api/progress';
import {
  closeAssessment,
  createAssessment,
  createQuestion,
  createQuestionBank,
  listAssessments,
  listQuestionBanks,
  listQuestions,
  publishAssessment,
  replaceAssessmentQuestions,
  updateAssessment
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
	    createRoleAssignment: vi.fn(),
	    getOidcConfig: vi.fn(),
	    listRoleAssignments: vi.fn(),
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
  archiveInstitution: vi.fn(),
  createInstitution: vi.fn(),
  createUserProfile: vi.fn(),
  deactivateUserProfile: vi.fn(),
  getUserProfile: vi.fn(),
  listInstitutions: vi.fn(),
  listUserProfiles: vi.fn(),
  updateInstitution: vi.fn(),
  updateUserProfile: vi.fn()
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

const baseInstitution: Institution = {
  id: baseProfile.institution_id,
  name: 'Acme University',
  code: 'ACME',
  status: 'active',
  settings: {},
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  deleted_at: null
};

const managedStudentProfile: UserProfile = {
  ...baseProfile,
  role_profile: {
    student_number: 'STU-100',
    batch_id: null,
    department_id: null,
    guardian_profile_id: null
  }
};

const managedInstructorProfile: UserProfile = {
  ...baseProfile,
  id: '77777777-7777-7777-7777-777777777777',
  auth_account_id: '88888888-8888-8888-8888-888888888888',
  first_name: 'Grace',
  last_name: 'Hopper',
  display_name: 'Grace Hopper',
  profile_type: 'instructor',
  role_profile: {
    employee_number: 'EMP-100',
    department_id: null,
    title: 'Instructor',
    bio: null
  }
};

const baseCourse = {
  id: 'course-1',
  institution_id: baseInstitution.id,
  owner_profile_id: managedInstructorProfile.id,
  title: 'Biology Basics',
  slug: 'biology-basics',
  description: 'Cells and systems',
  status: 'published' as const,
  difficulty_level: 'beginner' as const,
  categories: [],
  tags: [],
  prerequisite_course_ids: [],
  learning_outcomes: []
};

const baseCourseStructure = {
  ...baseCourse,
  modules: [
    {
      id: 'module-1',
      title: 'Foundations',
      status: 'published',
      lessons: [
        {
          id: 'lesson-1',
          title: 'Cell structure',
          summary: 'Cells up close',
          status: 'published',
          content_asset_id: 'asset-1',
          topics: [{ id: 'topic-1', title: 'Nucleus', status: 'published', content_asset_id: null }]
        }
      ]
    },
    {
      id: 'module-2',
      title: 'Advanced cells',
      status: 'published',
      lessons: [
        {
          id: 'lesson-2',
          title: 'Cell energy',
          summary: 'Energy flow',
          status: 'published',
          content_asset_id: null,
          topics: [{ id: 'topic-2', title: 'ATP cycle', status: 'published', content_asset_id: null }]
        }
      ]
    }
  ]
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
              scope_type:
                role === 'super_admin' ? 'platform' : role === 'instructor' ? 'course' : 'institution',
              scope_id:
                role === 'super_admin'
                  ? null
                  : role === 'instructor'
                    ? baseCourse.id
                    : baseProfile.institution_id,
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
    access_expires_at: '2026-12-31T00:05:00Z',
    refresh_expires_at: '2027-01-07T00:00:00Z'
  });
}

beforeEach(() => {
  window.localStorage.clear();
  vi.mocked(completeOidcCallback).mockReset();
  vi.mocked(createRoleAssignment).mockReset();
  vi.mocked(getOidcConfig).mockReset();
  vi.mocked(listRoleAssignments).mockReset();
  vi.mocked(login).mockReset();
  vi.mocked(startOidcAuthorization).mockReset();
  vi.mocked(getSessionContext).mockReset();
  vi.mocked(getStudentDashboard).mockReset();
  vi.mocked(getInstructorDashboard).mockReset();
  vi.mocked(getAdminDashboard).mockReset();
  vi.mocked(archiveInstitution).mockReset();
  vi.mocked(createInstitution).mockReset();
  vi.mocked(createUserProfile).mockReset();
  vi.mocked(deactivateUserProfile).mockReset();
  vi.mocked(getUserProfile).mockReset();
  vi.mocked(listInstitutions).mockReset();
  vi.mocked(listUserProfiles).mockReset();
  vi.mocked(updateInstitution).mockReset();
  vi.mocked(updateUserProfile).mockReset();
  vi.mocked(archiveCourse).mockReset();
  vi.mocked(createCourse).mockReset();
  vi.mocked(createLesson).mockReset();
  vi.mocked(createModule).mockReset();
  vi.mocked(createTopic).mockReset();
  vi.mocked(deleteCourse).mockReset();
  vi.mocked(getCourse).mockReset();
  vi.mocked(getCourseStructure).mockReset();
  vi.mocked(listCourses).mockReset();
  vi.mocked(publishCourse).mockReset();
  vi.mocked(updateCourse).mockReset();
  vi.mocked(listContentAssets).mockReset();
  vi.mocked(createPresignedUpload).mockReset();
  vi.mocked(listEnrollments).mockReset();
  vi.mocked(createEnrollment).mockReset();
  vi.mocked(listBatchEnrollments).mockReset();
  vi.mocked(listCohortEnrollments).mockReset();
  vi.mocked(listCourseProgress).mockReset();
  vi.mocked(listQuestionBanks).mockReset();
  vi.mocked(createQuestionBank).mockReset();
  vi.mocked(listQuestions).mockReset();
  vi.mocked(createQuestion).mockReset();
  vi.mocked(listAssessments).mockReset();
  vi.mocked(createAssessment).mockReset();
  vi.mocked(updateAssessment).mockReset();
  vi.mocked(replaceAssessmentQuestions).mockReset();
  vi.mocked(publishAssessment).mockReset();
  vi.mocked(closeAssessment).mockReset();
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
  vi.mocked(listUserProfiles).mockImplementation(async (params = {}) => {
    if (params.profile_type === 'instructor') {
      return {
        count: 1,
        next: null,
        previous: null,
        results: [managedInstructorProfile]
      };
    }
    return {
      count: 1,
      next: null,
      previous: null,
      results: [managedStudentProfile]
    };
  });
  vi.mocked(listInstitutions).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [baseInstitution]
  });
  vi.mocked(createInstitution).mockResolvedValue({
    ...baseInstitution,
    id: '66666666-6666-6666-6666-666666666666',
    name: 'North Campus',
    code: 'NORTH'
  });
  vi.mocked(updateInstitution).mockResolvedValue({
    ...baseInstitution,
    name: 'Acme Learning',
    code: 'ACU'
  });
  vi.mocked(archiveInstitution).mockResolvedValue({
    ...baseInstitution,
    status: 'archived',
    deleted_at: '2026-01-01T00:05:00Z'
  });
  vi.mocked(createUserProfile).mockResolvedValue({
    ...baseProfile,
    id: '55555555-5555-5555-5555-555555555555',
    first_name: 'New',
    last_name: 'User',
    display_name: 'New User',
    profile_type: 'student'
  });
  vi.mocked(getUserProfile).mockResolvedValue(managedStudentProfile);
  vi.mocked(updateUserProfile).mockResolvedValue({
    ...managedStudentProfile,
    first_name: 'Ada Updated'
  });
  vi.mocked(deactivateUserProfile).mockResolvedValue({
    ...managedStudentProfile,
    status: 'deactivated',
    deleted_at: '2026-01-01T00:05:00Z'
  });
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
    results: [baseCourse]
  });
  vi.mocked(getCourse).mockResolvedValue(baseCourse);
  vi.mocked(createCourse).mockResolvedValue({
    ...baseCourse,
    id: 'course-2',
    title: 'Computer Science 101',
    slug: 'computer-science-101',
    status: 'draft'
  });
  vi.mocked(updateCourse).mockResolvedValue({
    ...baseCourse,
    title: 'Biology Updated'
  });
  vi.mocked(publishCourse).mockResolvedValue(baseCourse);
  vi.mocked(archiveCourse).mockResolvedValue({
    ...baseCourse,
    status: 'archived'
  });
  vi.mocked(deleteCourse).mockResolvedValue({
    ...baseCourse,
    status: 'deleted',
    deleted_at: '2026-01-01T00:05:00Z'
  });
  vi.mocked(getCourseStructure).mockResolvedValue(baseCourseStructure);
  vi.mocked(createModule).mockResolvedValue({ id: 'module-2', title: 'New module' });
  vi.mocked(createLesson).mockResolvedValue({ id: 'lesson-2', title: 'New lesson' });
  vi.mocked(createTopic).mockResolvedValue({ id: 'topic-2', title: 'New topic' });
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
  vi.mocked(createRoleAssignment).mockResolvedValue({
    id: 'role-assignment-1',
    role_code: 'instructor',
    role_name: 'instructor',
    scope_type: 'course',
    scope_id: baseCourse.id,
    assigned_at: '2026-01-01T00:00:00Z'
  });
  vi.mocked(listRoleAssignments).mockResolvedValue([]);
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
  vi.mocked(listQuestions).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(createQuestion).mockResolvedValue({ id: 'question-1', prompt: 'What is a cell?' });
  vi.mocked(listAssessments).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.mocked(createAssessment).mockResolvedValue({ id: 'assessment-1', title: 'Chapter quiz', status: 'draft' });
  vi.mocked(updateAssessment).mockResolvedValue({ id: 'assessment-1', title: 'Chapter quiz updated', status: 'draft' });
  vi.mocked(replaceAssessmentQuestions).mockResolvedValue({ id: 'assessment-1', title: 'Chapter quiz' });
  vi.mocked(publishAssessment).mockResolvedValue({ id: 'assessment-1', title: 'Chapter quiz', status: 'published' });
  vi.mocked(closeAssessment).mockResolvedValue({ id: 'assessment-1', title: 'Chapter quiz', status: 'closed' });
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
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(/Instructor/i);
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
  expect(screen.getByRole('link', { name: /^Institutions$/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Users$/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Courses$/i })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /^Create User$/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /^Student$/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /^Instructor$/i })).not.toBeInTheDocument();
});

test('super admin can manage institutions', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/institutions');

  expect(await screen.findByRole('heading', { name: /^institutions$/i })).toBeInTheDocument();
  expect(await screen.findByText(/Acme University/i)).toBeInTheDocument();
  expect(listInstitutions).toHaveBeenCalledWith({
    q: undefined,
    status: undefined,
    sort: 'name',
    page: 1,
    page_size: 10
  });

  await userEvent.type(screen.getByLabelText(/^Name/i), 'North Campus');
  await userEvent.type(screen.getByLabelText(/^Code/i), 'north');
  await userEvent.click(screen.getByRole('button', { name: /^Create institution$/i }));

  await waitFor(() => expect(createInstitution).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createInstitution).mock.calls[0][0]).toEqual({
    name: 'North Campus',
    code: 'north',
    status: 'active'
  });

  await userEvent.click(screen.getByRole('button', { name: /edit acme university/i }));
  expect(screen.getByLabelText(/^Name/i)).toHaveValue('Acme University');
  await userEvent.clear(screen.getByLabelText(/^Name/i));
  await userEvent.type(screen.getByLabelText(/^Name/i), 'Acme Learning');
  await userEvent.clear(screen.getByLabelText(/^Code/i));
  await userEvent.type(screen.getByLabelText(/^Code/i), 'acu');
  await userEvent.selectOptions(screen.getAllByLabelText(/^Status$/i)[1], 'suspended');
  await userEvent.click(screen.getByRole('button', { name: /^Update institution$/i }));

  await waitFor(() => expect(updateInstitution).toHaveBeenCalledTimes(1));
  expect(vi.mocked(updateInstitution).mock.calls[0]).toEqual([
    baseInstitution.id,
    { name: 'Acme Learning', code: 'acu', status: 'suspended' }
  ]);

  await userEvent.click(screen.getByRole('button', { name: /archive acme university/i }));
  await waitFor(() => expect(archiveInstitution).toHaveBeenCalledWith(baseInstitution.id));
});

test('institution admin cannot call platform institution CRUD', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin/institutions');

  expect(await screen.findByRole('heading', { name: /^institutions$/i })).toBeInTheDocument();
  expect(await screen.findByText(/Super Admin access required/i)).toBeInTheDocument();
  expect(listInstitutions).not.toHaveBeenCalled();
  expect(createInstitution).not.toHaveBeenCalled();
  expect(updateInstitution).not.toHaveBeenCalled();
  expect(archiveInstitution).not.toHaveBeenCalled();
  expect(screen.queryByRole('button', { name: /^Create institution$/i })).not.toBeInTheDocument();
});

test('non-admin roles cannot access institution management route', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/admin/institutions');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /^institutions$/i })).not.toBeInTheDocument();
  expect(listInstitutions).not.toHaveBeenCalled();
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

test('super admin can create a user by selecting institution name', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/users');

  expect(await screen.findByRole('heading', { name: /^users$/i })).toBeInTheDocument();
  expect(await screen.findByText(/Ada Lovelace/i)).toBeInTheDocument();
  expect(await screen.findByRole('option', { name: /Acme University \(ACME\)/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/^Institution/i), baseInstitution.id);
  await userEvent.type(screen.getByLabelText(/^Email/i), 'new-student@example.com');
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
    institution_id: baseInstitution.id,
    first_name: 'New',
    last_name: 'Student',
    student: { student_number: 'STU-200' }
  });
  expect(await screen.findByText(/User created/i)).toBeInTheDocument();
});

test('admin users route updates and deactivates users', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/users');

  await userEvent.click(await screen.findByRole('button', { name: /edit ada lovelace/i }));
  await userEvent.clear(screen.getByLabelText(/first name/i));
  await userEvent.type(screen.getByLabelText(/first name/i), 'Ada Updated');
  await userEvent.click(screen.getByRole('button', { name: /^Update user$/i }));

  await waitFor(() => expect(updateUserProfile).toHaveBeenCalledTimes(1));
  expect(vi.mocked(updateUserProfile).mock.calls[0][0]).toBe(baseProfile.id);
  expect(vi.mocked(updateUserProfile).mock.calls[0][1]).toMatchObject({
    first_name: 'Ada Updated',
    last_name: 'Lovelace',
    status: 'active'
  });

  await userEvent.click(screen.getByRole('button', { name: /deactivate ada lovelace/i }));
  await waitFor(() => expect(deactivateUserProfile).toHaveBeenCalledWith(baseProfile.id));
});

test('institution admin creates users only in their institution', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin/users');

  expect(await screen.findByRole('heading', { name: /^users$/i })).toBeInTheDocument();
  await waitFor(() =>
    expect(listUserProfiles).toHaveBeenCalledWith(
      expect.objectContaining({ institution_id: baseProfile.institution_id })
    )
  );
  await userEvent.selectOptions(screen.getByLabelText(/^Profile type$/i), 'admin');
  expect(screen.queryByRole('option', { name: /super admin/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/^Institution$/i)).not.toBeInTheDocument();

  await userEvent.type(screen.getByLabelText(/^Email/i), 'new-admin@example.com');
  await userEvent.type(screen.getByLabelText(/temporary password/i), 'Temporary123!');
  await userEvent.type(screen.getByLabelText(/first name/i), 'New');
  await userEvent.type(screen.getByLabelText(/last name/i), 'Admin');
  expect(screen.getByLabelText(/admin type/i)).toHaveValue('institution_admin');
  await userEvent.click(screen.getByRole('button', { name: /^Create user$/i }));

  await waitFor(() => expect(createUserProfile).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createUserProfile).mock.calls[0][0]).toMatchObject({
    email: 'new-admin@example.com',
    profile_type: 'admin',
    institution_id: baseProfile.institution_id,
    admin: { admin_type: 'institution_admin' }
  });
});

test('create user API failure displays an error state', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));
  vi.mocked(createUserProfile).mockRejectedValueOnce({
    response: { data: { detail: 'Email already exists.' } }
  });

  renderApp('/dashboard/admin/users');

  expect(await screen.findByRole('heading', { name: /^users$/i })).toBeInTheDocument();
  expect(await screen.findByRole('option', { name: /Acme University \(ACME\)/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/^Institution/i), baseInstitution.id);
  await userEvent.type(screen.getByLabelText(/^Email/i), 'duplicate@example.com');
  await userEvent.type(screen.getByLabelText(/temporary password/i), 'Temporary123!');
  await userEvent.type(screen.getByLabelText(/first name/i), 'Duplicate');
  await userEvent.type(screen.getByLabelText(/last name/i), 'Student');
  await userEvent.type(screen.getByLabelText(/student number/i), 'STU-DUP');
  await userEvent.click(screen.getByRole('button', { name: /^Create user$/i }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Email already exists.');
});

test('non-admin roles cannot access users route', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/admin/users');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /^users$/i })).not.toBeInTheDocument();
  expect(listUserProfiles).not.toHaveBeenCalled();
});

test('super admin creates a course by selecting institution and instructor names', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByRole('heading', { name: /^courses$/i })).toBeInTheDocument();
  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  expect(await screen.findAllByRole('option', { name: /Acme University \(ACME\)/i })).not.toHaveLength(0);
  await userEvent.selectOptions(screen.getAllByLabelText(/^Institution/i)[1], baseInstitution.id);
  expect(await screen.findByRole('option', { name: /Grace Hopper/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/owner instructor/i), managedInstructorProfile.id);
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Computer Science 101');
  await userEvent.click(screen.getByRole('button', { name: /^Create course$/i }));

  await waitFor(() => expect(createCourse).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createCourse).mock.calls[0][0]).toMatchObject({
    institution_id: baseInstitution.id,
    owner_profile_id: managedInstructorProfile.id,
    title: 'Computer Science 101',
    description: null,
    difficulty_level: null
  });
  expect(vi.mocked(createCourse).mock.calls[0][0]).not.toHaveProperty('slug');
});

test('institution admin creates courses only in their institution', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByRole('heading', { name: /^courses$/i })).toBeInTheDocument();
  await waitFor(() =>
    expect(listCourses).toHaveBeenCalledWith(
      expect.objectContaining({ institution_id: baseProfile.institution_id })
    )
  );
  expect(screen.queryByLabelText(/^Institution$/i)).not.toBeInTheDocument();
  expect(await screen.findByRole('option', { name: /Grace Hopper/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/owner instructor/i), managedInstructorProfile.id);
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Institution Course');
  await userEvent.click(screen.getByRole('button', { name: /^Create course$/i }));

  await waitFor(() => expect(createCourse).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createCourse).mock.calls[0][0]).toMatchObject({
    institution_id: baseProfile.institution_id,
    owner_profile_id: managedInstructorProfile.id,
    title: 'Institution Course'
  });
});

test('admin courses route edits and updates lifecycle actions', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));
  vi.mocked(listCourses).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ ...baseCourse, status: 'draft' }]
  });

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /edit biology basics/i }));
  await userEvent.clear(screen.getByLabelText(/^Title/i));
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Biology Updated');
  await userEvent.click(screen.getByRole('button', { name: /^Update course$/i }));

  await waitFor(() => expect(updateCourse).toHaveBeenCalledTimes(1));
  expect(vi.mocked(updateCourse).mock.calls[0]).toEqual([
    baseCourse.id,
    expect.objectContaining({
      owner_profile_id: managedInstructorProfile.id,
      title: 'Biology Updated'
    })
  ]);

  await userEvent.click(screen.getByRole('button', { name: /publish biology basics/i }));
  await waitFor(() => expect(publishCourse).toHaveBeenCalledWith(baseCourse.id));
  await userEvent.click(screen.getByRole('button', { name: /archive biology basics/i }));
  await waitFor(() => expect(archiveCourse).toHaveBeenCalledWith(baseCourse.id));
  await userEvent.click(screen.getByRole('button', { name: /delete biology basics/i }));
  await waitFor(() => expect(deleteCourse).toHaveBeenCalledWith(baseCourse.id));
});

test('admin courses route adds students and instructors by name', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('super_admin', 'admin'));

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /add people to biology basics/i }));

  expect(await screen.findByRole('option', { name: /Ada Lovelace/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/^Student$/i), managedStudentProfile.id);
  await userEvent.click(screen.getByRole('button', { name: /^Add student$/i }));

  await waitFor(() => expect(createEnrollment).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createEnrollment).mock.calls[0][0]).toMatchObject({
    student_profile_id: managedStudentProfile.id,
    course_id: baseCourse.id,
    institution_id: baseInstitution.id,
    enrolled_by_profile_id: baseProfile.id
  });

  expect(await screen.findByRole('option', { name: /Grace Hopper/i })).toBeInTheDocument();
  await userEvent.selectOptions(
    screen.getByLabelText(/^Instructor$/i),
    managedInstructorProfile.id
  );
  await userEvent.click(screen.getByRole('button', { name: /^Add instructor$/i }));

  await waitFor(() => expect(createRoleAssignment).toHaveBeenCalledTimes(1));
  expect(vi.mocked(createRoleAssignment).mock.calls[0][0]).toEqual({
    account_id: managedInstructorProfile.auth_account_id,
    role_code: 'instructor',
    scope_type: 'course',
    scope_id: baseCourse.id
  });
});

test('institution admin course people pickers are scoped to their institution', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(
    sessionContext('institution_admin', 'admin')
  );

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /add people to biology basics/i }));
  expect(await screen.findByRole('option', { name: /Ada Lovelace/i })).toBeInTheDocument();

  await waitFor(() =>
    expect(listUserProfiles).toHaveBeenCalledWith(
      expect.objectContaining({
        institution_id: baseProfile.institution_id,
        profile_type: 'student'
      })
    )
  );
  expect(listUserProfiles).toHaveBeenCalledWith(
    expect.objectContaining({
      institution_id: baseProfile.institution_id,
      profile_type: 'instructor'
    })
  );
});

test('instructor course list is open-only for assigned courses', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/courses');

  expect(await screen.findByRole('heading', { name: /course management/i })).toBeInTheDocument();
  expect(await screen.findByText(/Biology Basics/i)).toBeInTheDocument();
  expect(getCourse).toHaveBeenCalledWith(baseCourse.id);
  expect(screen.getByRole('link', { name: /^Open$/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}`
  );
  expect(screen.queryByRole('button', { name: /create/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /^Publish$/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /^Archive$/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /^Delete$/i })).not.toBeInTheDocument();
});

test('assigned instructor opens course overview with course-local links', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}`);

  expect(await screen.findByRole('heading', { name: /course overview/i })).toBeInTheDocument();
  expect((await screen.findAllByText(/Biology Basics/i)).length).toBeGreaterThan(0);
  expect(getCourse).toHaveBeenCalledWith(baseCourse.id);
  expect(screen.getByRole('navigation', { name: /^Course$/i })).toBeInTheDocument();
  expect(screen.queryByRole('navigation', { name: /^Portal$/i })).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Overview$/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}`
  );
  expect(screen.getAllByRole('link', { name: /Builder/i })[0]).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/builder`
  );
  expect(screen.getByRole('link', { name: /Question banks/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/question-banks`
  );
  expect(screen.getByRole('link', { name: /Participants/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/participants`
  );
  expect(screen.getByRole('link', { name: /Assessments/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/assessments`
  );
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Instructor.*Courses.*Biology Basics/i
  );
});

test('assigned instructor navigates from course overview to builder', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}`);

  expect(await screen.findByRole('heading', { name: /course overview/i })).toBeInTheDocument();
  await userEvent.click(screen.getAllByRole('link', { name: /Builder/i })[0]);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  expect(getCourseStructure).toHaveBeenCalledWith(baseCourse.id);
  expect(screen.getByRole('navigation', { name: /^Course$/i })).toBeInTheDocument();
  expect(screen.queryByRole('navigation', { name: /^Portal$/i })).not.toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Instructor.*Courses.*Biology Basics.*Builder/i
  );
});

test('instructor builder opens add structure modal with course-local navigation only', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/builder`);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  expect(screen.queryByRole('navigation', { name: /^Portal$/i })).not.toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /^Course$/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Overview$/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}`
  );
  expect(screen.getByRole('link', { name: /^Builder$/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/builder`
  );
  expect(screen.getByRole('link', { name: /Question banks/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Participants/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^Assessments$/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Manage assessments/i })).toHaveAttribute(
    'href',
    `/dashboard/instructor/courses/${baseCourse.id}/assessments`
  );

  await userEvent.click(screen.getByRole('button', { name: /^Add structure$/i }));

  expect(await screen.findByRole('dialog', { name: /^Add structure$/i })).toBeInTheDocument();
  expect(screen.queryByLabelText(/module id/i)).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/lesson id/i)).not.toBeInTheDocument();
});

test('instructor builder creates a module from the add structure modal', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/builder`);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /^Add structure$/i }));
  await userEvent.type(screen.getByLabelText(/^Title/i), 'New module');
  await userEvent.clear(screen.getByLabelText(/^Position$/i));
  await userEvent.type(screen.getByLabelText(/^Position$/i), '2');
  await userEvent.type(screen.getByLabelText(/^Description$/i), 'New module description');
  await userEvent.click(screen.getByRole('button', { name: /^Save item$/i }));

  await waitFor(() => expect(createModule).toHaveBeenCalledTimes(1));
  expect(createModule).toHaveBeenCalledWith(baseCourse.id, {
    title: 'New module',
    description: 'New module description',
    position: 2
  });
});

test('instructor builder creates a lesson by selecting a module title', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/builder`);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /^Add structure$/i }));
  await userEvent.selectOptions(screen.getByLabelText(/^Item type/i), 'lesson');
  expect(await screen.findByRole('option', { name: /^Foundations$/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/^Module/i), 'module-1');
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Photosynthesis');
  await userEvent.type(screen.getByLabelText(/^Summary$/i), 'Light and plants');
  await userEvent.click(screen.getByRole('button', { name: /^Save item$/i }));

  await waitFor(() => expect(createLesson).toHaveBeenCalledTimes(1));
  expect(createLesson).toHaveBeenCalledWith('module-1', {
    title: 'Photosynthesis',
    summary: 'Light and plants',
    position: 1,
    content_asset_id: null
  });
});

test('instructor builder creates a topic by selecting a lesson title', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/builder`);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /^Add structure$/i }));
  await userEvent.selectOptions(screen.getByLabelText(/^Item type/i), 'topic');
  expect(await screen.findByRole('option', { name: /^Foundations \/ Cell structure$/i })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText(/^Lesson/i), 'lesson-1');
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Nucleus details');
  await userEvent.click(screen.getByRole('button', { name: /^Save item$/i }));

  await waitFor(() => expect(createTopic).toHaveBeenCalledTimes(1));
  expect(createTopic).toHaveBeenCalledWith('lesson-1', {
    title: 'Nucleus details',
    position: 1,
    content_asset_id: null
  });
});

test('instructor builder blocks lesson save when no parent module exists', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  vi.mocked(getCourseStructure).mockResolvedValue({ ...baseCourse, modules: [] });

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/builder`);

  expect(await screen.findByRole('heading', { name: /course builder/i })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /^Add structure$/i }));
  await userEvent.selectOptions(screen.getByLabelText(/^Item type/i), 'lesson');
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Blocked lesson');

  expect(screen.getByLabelText(/^Module/i)).toBeDisabled();
  expect(screen.getByText(/Create a module before adding lessons/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /^Save item$/i })).toBeDisabled();
  expect(createLesson).not.toHaveBeenCalled();
});

test('instructor overview blocks unassigned courses before loading course details', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/courses/not-assigned');

  expect(await screen.findByText(/Course access required/i)).toBeInTheDocument();
  expect(getCourse).not.toHaveBeenCalled();
  expect(getCourseStructure).not.toHaveBeenCalled();
});

test('instructor builder blocks unassigned courses before loading structure', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/courses/not-assigned/builder');

  expect(await screen.findByText(/Course access required/i)).toBeInTheDocument();
  expect(getCourse).not.toHaveBeenCalled();
  expect(getCourseStructure).not.toHaveBeenCalled();
});

test('unassigned instructor cannot access course-local tools or trigger their APIs', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/courses/not-assigned/question-banks');

  expect(await screen.findByText(/Course access required/i)).toBeInTheDocument();
  expect(getCourse).not.toHaveBeenCalled();
  expect(listQuestionBanks).not.toHaveBeenCalled();
  expect(listQuestions).not.toHaveBeenCalled();

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  renderApp('/dashboard/instructor/courses/not-assigned/participants');

  expect(await screen.findByText(/Course access required/i)).toBeInTheDocument();
  expect(listEnrollments).not.toHaveBeenCalled();
  expect(listRoleAssignments).not.toHaveBeenCalled();

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  renderApp('/dashboard/instructor/courses/not-assigned/assessments');

  expect(await screen.findByText(/Course access required/i)).toBeInTheDocument();
  expect(listAssessments).not.toHaveBeenCalled();
  expect(listQuestionBanks).not.toHaveBeenCalled();
});

test('course question banks create banks and questions by title selection', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  vi.mocked(listQuestionBanks).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'bank-1', title: 'Cells bank', description: 'Course questions' }]
  });
  vi.mocked(listQuestions).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'question-1', prompt: 'What is a nucleus?', question_type: 'short_answer', points: 2 }]
  });

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/question-banks`);

  expect(await screen.findByRole('heading', { name: /question banks/i })).toBeInTheDocument();
  await waitFor(() =>
    expect(listQuestionBanks).toHaveBeenCalledWith(
      expect.objectContaining({
        institution_id: baseInstitution.id,
        owner_profile_id: baseProfile.id
      })
    )
  );
  expect(screen.getByRole('navigation', { name: /^Course$/i })).toHaveTextContent(/Question banks/i);

  await userEvent.type(await screen.findByLabelText(/^Title/i), 'Module bank');
  await userEvent.type(screen.getByLabelText(/^Description/i), 'Module questions');
  await userEvent.click(screen.getByRole('button', { name: /^Create bank$/i }));

  await waitFor(() => expect(createQuestionBank).toHaveBeenCalledTimes(1));
  expect(createQuestionBank).toHaveBeenCalledWith({
    institution_id: baseInstitution.id,
    owner_profile_id: baseProfile.id,
    title: 'Module bank',
    description: 'Module questions'
  });

  await userEvent.selectOptions(screen.getByLabelText(/^Question bank/i), 'bank-1');
  expect(await screen.findByText(/What is a nucleus/i)).toBeInTheDocument();
  await userEvent.type(screen.getByLabelText(/^Prompt/i), 'What powers a cell?');
  await userEvent.selectOptions(screen.getByLabelText(/^Question type$/i), 'short_answer');
  await userEvent.click(screen.getByRole('button', { name: /^Create question$/i }));

  await waitFor(() => expect(createQuestion).toHaveBeenCalledTimes(1));
  expect(createQuestion).toHaveBeenCalledWith(
    'bank-1',
    expect.objectContaining({
      question_type: 'short_answer',
      prompt: 'What powers a cell?',
      points: 1,
      status: 'draft'
    })
  );
});

test('course participants list students and course staff groups', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  vi.mocked(listEnrollments).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 'enrollment-1',
        student_profile_id: managedStudentProfile.id,
        course_id: baseCourse.id,
        institution_id: baseInstitution.id,
        status: 'active',
        enrolled_at: '2026-01-01T00:00:00Z'
      }
    ]
  });
  vi.mocked(listRoleAssignments).mockResolvedValue([
    {
      id: 'staff-1',
      account_id: managedInstructorProfile.auth_account_id,
      role_code: 'instructor',
      role_name: 'Instructor',
      scope_type: 'course',
      scope_id: baseCourse.id,
      assigned_at: '2026-01-01T00:00:00Z'
    },
    {
      id: 'staff-2',
      account_id: '99999999-9999-9999-9999-999999999999',
      role_code: 'teaching_assistant',
      role_name: 'Teaching Assistant',
      scope_type: 'course',
      scope_id: baseCourse.id,
      assigned_at: '2026-01-02T00:00:00Z'
    }
  ]);

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/participants`);

  expect(await screen.findByRole('heading', { name: /participants/i })).toBeInTheDocument();
  expect(await screen.findByText(managedStudentProfile.id)).toBeInTheDocument();
  expect(await screen.findByText(managedInstructorProfile.auth_account_id)).toBeInTheDocument();
  expect(screen.getByText(/Teaching Assistant/i)).toBeInTheDocument();
  expect(listEnrollments).toHaveBeenCalledWith(expect.objectContaining({ course_id: baseCourse.id }));
  expect(listRoleAssignments).toHaveBeenCalledWith({
    scope_type: 'course',
    scope_id: baseCourse.id,
    role_code: 'instructor,teaching_assistant'
  });
});

test('course assessments create, update, attach questions, publish, and close', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));
  vi.mocked(listAssessments).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 'assessment-1',
        title: 'Cell quiz',
        assessment_type: 'quiz',
        status: 'draft',
        course_id: baseCourse.id,
        institution_id: baseInstitution.id,
        instructions: 'Answer every item',
        quiz: { max_attempts: 1 }
      }
    ]
  });
  vi.mocked(listQuestionBanks).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'bank-1', title: 'Cells bank' }]
  });
  vi.mocked(listQuestions).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 'question-1', prompt: 'What is a nucleus?', question_type: 'short_answer', points: 2 }]
  });

  renderApp(`/dashboard/instructor/courses/${baseCourse.id}/assessments`);

  expect(await screen.findByRole('heading', { name: /^assessments$/i })).toBeInTheDocument();
  expect(screen.queryByLabelText(/^Course ID$/i)).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/^Institution ID$/i)).not.toBeInTheDocument();

  await userEvent.type(await screen.findByLabelText(/^Title/i), 'Chapter quiz');
  await userEvent.click(screen.getByRole('button', { name: /^Create assessment$/i }));

  await waitFor(() => expect(createAssessment).toHaveBeenCalledTimes(1));
  expect(createAssessment).toHaveBeenCalledWith(
    expect.objectContaining({
      course_id: baseCourse.id,
      institution_id: baseInstitution.id,
      owner_profile_id: baseProfile.id,
      title: 'Chapter quiz',
      assessment_type: 'quiz'
    })
  );

  await userEvent.click(await screen.findByRole('button', { name: /^Edit$/i }));
  await userEvent.clear(screen.getByLabelText(/^Title/i));
  await userEvent.type(screen.getByLabelText(/^Title/i), 'Cell quiz updated');
  await userEvent.click(screen.getByRole('button', { name: /^Update assessment$/i }));

  await waitFor(() => expect(updateAssessment).toHaveBeenCalledTimes(1));
  expect(updateAssessment).toHaveBeenCalledWith(
    'assessment-1',
    expect.objectContaining({ title: 'Cell quiz updated' })
  );

  await userEvent.selectOptions(screen.getByLabelText(/^Assessment/i), 'assessment-1');
  await userEvent.selectOptions(screen.getByLabelText(/^Question bank/i), 'bank-1');
  await userEvent.click(await screen.findByLabelText(/What is a nucleus/i));
  await userEvent.click(screen.getByRole('button', { name: /^Replace attached questions$/i }));

  await waitFor(() => expect(replaceAssessmentQuestions).toHaveBeenCalledTimes(1));
  expect(replaceAssessmentQuestions).toHaveBeenCalledWith('assessment-1', [
    { question_id: 'question-1', position: 1 }
  ]);

  await userEvent.click(screen.getByRole('button', { name: /^Publish$/i }));
  await waitFor(() => expect(publishAssessment).toHaveBeenCalledWith('assessment-1'));
  await userEvent.click(screen.getByRole('button', { name: /^Close$/i }));
  await waitFor(() => expect(closeAssessment).toHaveBeenCalledWith('assessment-1'));
});

test('non-admin roles cannot access courses route', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/admin/courses');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /^courses$/i })).not.toBeInTheDocument();
  expect(createCourse).not.toHaveBeenCalled();
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

test('student pages render breadcrumbs and learn page shows the full published outline', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));

  renderApp('/dashboard/student');

  expect(await screen.findByRole('heading', { name: /student dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(/Student/i);

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/courses');

  expect(await screen.findByRole('heading', { name: /course catalog/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(/Student.*Courses/i);

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp(`/dashboard/student/courses/${baseCourse.id}`);

  expect(await screen.findByRole('heading', { name: /course overview/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Student.*Courses.*Biology Basics/i
  );

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp(`/dashboard/student/courses/${baseCourse.id}/learn`);

  expect(await screen.findByRole('heading', { name: /learning player/i })).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
      /Student.*Courses.*Biology Basics.*Learn/i
    )
  );
  expect(screen.getAllByText(/Foundations/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Cell structure/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Nucleus/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Advanced cells/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Cell energy/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/ATP cycle/i).length).toBeGreaterThan(0);

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/assessments/assessment-1/attempt');

  expect(await screen.findByRole('heading', { name: /assessment attempt/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Student.*Assessments.*Attempt/i
  );

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/assignments/assignment-1/submit');

  expect(await screen.findByRole('heading', { name: /assignment submission/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Student.*Assignments.*Submit/i
  );

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/certificates');

  expect(await screen.findByRole('heading', { name: /^certificates$/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(/Student.*Certificates/i);

  cleanup();
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('student'));
  renderApp('/dashboard/student/notifications');

  expect(await screen.findByRole('heading', { name: /notification center/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(/Student.*Notifications/i);
});

test('instructor content route submits presigned upload metadata', async () => {
  storeTestTokens();
  vi.mocked(getSessionContext).mockResolvedValue(sessionContext('instructor', 'instructor'));

  renderApp('/dashboard/instructor/content');

  expect(await screen.findByRole('heading', { name: /content upload/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Instructor.*Content/i
  );
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
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Instructor.*Assessments/i
  );
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
  expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent(
    /Instructor.*Grading/i
  );
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
