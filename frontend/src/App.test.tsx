import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
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
