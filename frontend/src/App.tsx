import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate
} from 'react-router-dom';
import { z } from 'zod';

import { getFrontendStatus } from './api/status';
import {
  getSessionContext,
  login,
  portalForRole,
  type SessionContext
} from './api/auth';
import { clearStoredTokens, hasStoredAccessToken } from './api/client';
import {
  getAdminDashboard,
  getInstructorDashboard,
  getStudentDashboard,
  type StudentDashboard
} from './api/dashboards';
import { createUserProfile, type CreateUserProfilePayload } from './api/users';

const phoneSchema = z
  .string()
  .trim()
  .regex(/^\+?[1-9][0-9]{7,14}$/, 'Invalid phone number')
  .optional()
  .or(z.literal(''));

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

const createUserSchema = z
  .object({
    email: z.string().email(),
    phone: phoneSchema,
    temporary_password: z.string().min(12),
    profile_type: z.enum(['student', 'instructor', 'admin']),
    institution_id: z.string().trim().optional(),
    first_name: z.string().trim().min(1),
    last_name: z.string().trim().min(1),
    display_name: z.string().trim().optional(),
    student_number: z.string().trim().optional(),
    batch_id: z.string().trim().optional(),
    department_id: z.string().trim().optional(),
    guardian_profile_id: z.string().trim().optional(),
    employee_number: z.string().trim().optional(),
    title: z.string().trim().optional(),
    bio: z.string().trim().optional(),
    admin_type: z.enum(['institution_admin', 'super_admin'])
  })
  .superRefine((value, context) => {
    if (value.profile_type === 'student' && !value.student_number) {
      context.addIssue({
        code: 'custom',
        path: ['student_number'],
        message: 'Student number is required.'
      });
    }
  });

type LoginForm = z.infer<typeof loginSchema>;
type CreateUserForm = z.infer<typeof createUserSchema>;
type Portal = 'student' | 'instructor' | 'admin';
type NavKey = Portal | 'admin-create-user';

function useSessionContext() {
  return useQuery({
    queryKey: ['session-context'],
    queryFn: getSessionContext,
    enabled: hasStoredAccessToken(),
    retry: false
  });
}

function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex min-h-[280px] items-center justify-center rounded border border-slate-200 bg-white text-sm font-medium text-slate-600">
      {label}
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded border border-rose-200 bg-rose-50 p-5">
      <h2 className="text-base font-semibold text-rose-950">Unable to load dashboard</h2>
      <p className="mt-1 text-sm text-rose-800">
        The service denied the request or could not be reached.
      </p>
      <button
        className="mt-4 rounded border border-rose-300 bg-white px-3 py-2 text-sm font-medium text-rose-900 hover:bg-rose-100"
        type="button"
        onClick={onRetry}
      >
        Retry
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-600">
      No dashboard data yet.
    </div>
  );
}

function displayName(context: SessionContext) {
  return (
    context.profile.display_name ||
    `${context.profile.first_name} ${context.profile.last_name}`.trim() ||
    context.session.email
  );
}

function emptyToNull(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function adminInstitutionScope(context: SessionContext) {
  return (
    context.session.role_assignments.find((assignment) => assignment.scope_type === 'institution')
      ?.scope_id ?? context.profile.institution_id
  );
}

function createUserDefaults(context: SessionContext): CreateUserForm {
  return {
    email: '',
    phone: '',
    temporary_password: '',
    profile_type: 'student',
    institution_id:
      context.session.primary_role === 'institution_admin'
        ? adminInstitutionScope(context) ?? ''
        : '',
    first_name: '',
    last_name: '',
    display_name: '',
    student_number: '',
    batch_id: '',
    department_id: '',
    guardian_profile_id: '',
    employee_number: '',
    title: '',
    bio: '',
    admin_type: 'institution_admin'
  };
}

function buildCreateUserPayload(
  values: CreateUserForm,
  context: SessionContext
): CreateUserProfilePayload {
  const institutionId =
    emptyToNull(values.institution_id) ??
    (context.session.primary_role === 'institution_admin' ? adminInstitutionScope(context) : null);
  const departmentId = emptyToNull(values.department_id);
  const payload: CreateUserProfilePayload = {
    email: values.email.trim(),
    phone: emptyToNull(values.phone),
    temporary_password: values.temporary_password,
    profile_type: values.profile_type,
    institution_id: institutionId,
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    display_name: emptyToNull(values.display_name)
  };

  if (values.profile_type === 'student') {
    payload.student = {
      student_number: values.student_number?.trim() ?? '',
      batch_id: emptyToNull(values.batch_id),
      department_id: departmentId,
      guardian_profile_id: emptyToNull(values.guardian_profile_id)
    };
  }

  if (values.profile_type === 'instructor') {
    payload.instructor = {
      employee_number: emptyToNull(values.employee_number),
      department_id: departmentId,
      title: emptyToNull(values.title),
      bio: emptyToNull(values.bio)
    };
  }

  if (values.profile_type === 'admin') {
    payload.admin = {
      admin_type: values.admin_type,
      department_id: departmentId
    };
  }

  return payload;
}

function apiErrorMessage(error: unknown) {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    error.response &&
    typeof error.response === 'object' &&
    'data' in error.response
  ) {
    const data = error.response.data;
    if (data && typeof data === 'object' && 'detail' in data) {
      return String(data.detail);
    }
  }
  return 'User creation failed.';
}

function DashboardRedirect() {
  const sessionQuery = useSessionContext();
  if (sessionQuery.isLoading) {
    return <LoadingState label="Loading session" />;
  }
  if (sessionQuery.isError || !sessionQuery.data) {
    clearStoredTokens();
    return <Navigate to="/login" replace />;
  }

  const portal = portalForRole(sessionQuery.data.session.primary_role);
  if (portal === 'none') {
    return <Navigate to="/dashboard/no-access" replace />;
  }
  return <Navigate to={`/dashboard/${portal}`} replace />;
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  if (!hasStoredAccessToken()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ['frontend-status'],
    queryFn: getFrontendStatus
  });
  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' }
  });
  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['session-context'] });
      navigate('/dashboard', { replace: true });
    }
  });

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-10">
      <section className="grid w-full gap-8 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col justify-center border-l-4 border-emerald-600 pl-6">
          <span className="text-sm font-semibold uppercase text-emerald-700">
            {statusQuery.data?.serviceId ?? 'SVC-011'}{' '}
            {statusQuery.data?.serviceName ?? 'frontend-service'}
          </span>
          <h1 className="mt-3 text-4xl font-semibold text-slate-950">LearnGrid LMS</h1>
          <p className="mt-3 max-w-2xl text-base text-slate-600">
            Student, instructor, and admin portal access.
          </p>
        </div>

        <form
          className="rounded border border-slate-200 bg-white p-5"
          onSubmit={form.handleSubmit((values) => loginMutation.mutate(values))}
        >
          <h2 className="text-xl font-semibold text-slate-950">Sign in</h2>
          <label className="mt-5 block text-sm font-medium text-slate-700" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
            type="email"
            autoComplete="email"
            {...form.register('email')}
          />
          {form.formState.errors.email ? (
            <p className="mt-1 text-xs text-rose-700">{form.formState.errors.email.message}</p>
          ) : null}

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
            type="password"
            autoComplete="current-password"
            {...form.register('password')}
          />
          {loginMutation.isError ? (
            <p className="mt-3 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              Sign in failed.
            </p>
          ) : null}
          <button
            className="mt-5 w-full rounded bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            type="submit"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? 'Signing in' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}

function PortalLayout({
  context,
  activeNav,
  children
}: {
  context: SessionContext;
  activeNav: NavKey;
  children: ReactNode;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const availablePortal = portalForRole(context.session.primary_role);
  const navItems =
    availablePortal === 'admin'
      ? [
          { key: 'admin' as const, label: 'Admin', to: '/dashboard/admin' },
          {
            key: 'admin-create-user' as const,
            label: 'Create User',
            to: '/dashboard/admin/users/new'
          }
        ]
      : [
          { key: 'student' as const, label: 'Student', to: '/dashboard/student' },
          { key: 'instructor' as const, label: 'Instructor', to: '/dashboard/instructor' }
        ].filter((item) => item.key === availablePortal);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <span className="text-xs font-semibold uppercase text-emerald-700">
              SVC-011 frontend-service
            </span>
            <h1 className="text-2xl font-semibold text-slate-950">LearnGrid LMS</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{displayName(context)}</span>
            <button
              className="rounded border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              type="button"
              onClick={() => {
                clearStoredTokens();
                queryClient.clear();
                navigate('/login', { replace: true });
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[220px_1fr]">
        <nav className="h-fit rounded border border-slate-200 bg-white p-3">
          {navItems.map((item) => (
            <Link
              key={item.key}
              className={`block rounded px-3 py-2 text-sm font-medium ${
                activeNav === item.key
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
              to={item.to}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <section>{children}</section>
      </div>
    </main>
  );
}

function SummaryGrid({ summary }: { summary: Record<string, number> }) {
  const entries = Object.entries(summary);
  if (!entries.length) {
    return <EmptyState />;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded border border-slate-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">
            {key.replaceAll('_', ' ')}
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-950">{value}</div>
        </div>
      ))}
    </div>
  );
}

function titleForItem(item: Record<string, unknown>, fallback: string) {
  const value = item.title || item.name || item.course_title || item.label || item.id || fallback;
  return String(value);
}

function ListBand({
  title,
  items
}: {
  title: string;
  items: Array<Record<string, unknown>>;
}) {
  return (
    <section className="rounded border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-base font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      {items.length ? (
        <ul className="mt-4 divide-y divide-slate-100">
          {items.slice(0, 6).map((item, index) => (
            <li className="py-3" key={`${title}-${index}`}>
              <div className="text-sm font-medium text-slate-900">
                {titleForItem(item, `${title} ${index + 1}`)}
              </div>
              <div className="mt-1 truncate text-xs text-slate-500">
                {Object.entries(item)
                  .slice(0, 3)
                  .map(([key, value]) => `${key}: ${String(value)}`)
                  .join(' · ')}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4">
          <EmptyState />
        </div>
      )}
    </section>
  );
}

function DashboardHeader({
  title,
  aggregate
}: {
  title: string;
  aggregate: StudentDashboard['aggregate'];
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">{title}</h2>
        <p className="mt-1 text-sm text-slate-600">
          {aggregate ? `Updated ${aggregate.computed_at}` : 'No aggregate computed yet'}
        </p>
      </div>
    </div>
  );
}

function StudentPortal({ context }: { context: SessionContext }) {
  const query = useQuery({ queryKey: ['dashboard', 'student'], queryFn: getStudentDashboard });

  return (
    <PortalLayout context={context} activeNav="student">
      {query.isLoading ? <LoadingState label="Loading student dashboard" /> : null}
      {query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <>
          <DashboardHeader title="Student Dashboard" aggregate={query.data.aggregate} />
          <SummaryGrid summary={query.data.summary} />
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <ListBand title="Active courses" items={query.data.active_courses} />
            <ListBand title="Completed lessons" items={query.data.completed_lessons} />
            <ListBand title="Pending assessments" items={query.data.pending_assessments} />
            <ListBand title="Grades" items={query.data.grades} />
            <ListBand title="Upcoming deadlines" items={query.data.upcoming_deadlines} />
          </div>
        </>
      ) : null}
    </PortalLayout>
  );
}

function InstructorPortal({ context }: { context: SessionContext }) {
  const query = useQuery({
    queryKey: ['dashboard', 'instructor'],
    queryFn: getInstructorDashboard
  });

  return (
    <PortalLayout context={context} activeNav="instructor">
      {query.isLoading ? <LoadingState label="Loading instructor dashboard" /> : null}
      {query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <>
          <DashboardHeader title="Instructor Dashboard" aggregate={query.data.aggregate} />
          <SummaryGrid summary={query.data.summary} />
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <ListBand title="Learner engagement" items={query.data.learner_engagement} />
            <ListBand title="Progress distribution" items={query.data.progress_distribution} />
            <ListBand title="Assessment status" items={query.data.assessment_status} />
            <ListBand title="Course summaries" items={query.data.course_summaries} />
          </div>
        </>
      ) : null}
    </PortalLayout>
  );
}

function AdminPortal({ context }: { context: SessionContext }) {
  const institutionScope =
    context.session.primary_role === 'institution_admin'
      ? context.session.role_assignments.find((assignment) => assignment.scope_type === 'institution')
          ?.scope_id ?? context.profile.institution_id
      : null;
  const query = useQuery({
    queryKey: ['dashboard', 'admin', institutionScope ?? 'system'],
    queryFn: () => getAdminDashboard(institutionScope)
  });

  return (
    <PortalLayout context={context} activeNav="admin">
      {query.isLoading ? <LoadingState label="Loading admin dashboard" /> : null}
      {query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <>
          <DashboardHeader title="Admin Dashboard" aggregate={query.data.aggregate} />
          <SummaryGrid summary={query.data.summary} />
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <ListBand title="Active users" items={query.data.active_users} />
            <ListBand title="Enrollments" items={query.data.enrollments} />
            <ListBand title="Completion rates" items={query.data.completion_rates} />
            <ListBand title="Assessment results" items={query.data.assessment_results} />
            <ListBand title="System usage" items={query.data.system_usage} />
          </div>
        </>
      ) : null}
    </PortalLayout>
  );
}

function AdminCreateUserPage({ context }: { context: SessionContext }) {
  const isSuperAdmin = context.session.primary_role === 'super_admin';
  const isInstitutionAdmin = context.session.primary_role === 'institution_admin';
  const form = useForm<CreateUserForm>({
    resolver: zodResolver(createUserSchema),
    defaultValues: createUserDefaults(context)
  });
  const profileType = useWatch({ control: form.control, name: 'profile_type' });
  const mutation = useMutation({
    mutationFn: (values: CreateUserForm) => createUserProfile(buildCreateUserPayload(values, context)),
    onSuccess: () => {
      form.reset(createUserDefaults(context));
    }
  });
  const fieldClass =
    'mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 disabled:bg-slate-100';

  return (
    <PortalLayout context={context} activeNav="admin-create-user">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold text-slate-950">Create User</h2>
      </div>

      <form
        className="rounded border border-slate-200 bg-white p-5"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700" htmlFor="new-email">
            Email
            <input id="new-email" className={fieldClass} type="email" {...form.register('email')} />
            {form.formState.errors.email ? (
              <span className="mt-1 block text-xs text-rose-700">
                {form.formState.errors.email.message}
              </span>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="new-phone">
            Phone
            <input id="new-phone" className={fieldClass} type="tel" {...form.register('phone')} />
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="new-password">
            Temporary password
            <input
              id="new-password"
              className={fieldClass}
              type="password"
              autoComplete="new-password"
              {...form.register('temporary_password')}
            />
            {form.formState.errors.temporary_password ? (
              <span className="mt-1 block text-xs text-rose-700">
                {form.formState.errors.temporary_password.message}
              </span>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="profile-type">
            Profile type
            <select id="profile-type" className={fieldClass} {...form.register('profile_type')}>
              <option value="student">Student</option>
              <option value="instructor">Instructor</option>
              <option value="admin">Admin</option>
            </select>
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="first-name">
            First name
            <input id="first-name" className={fieldClass} type="text" {...form.register('first_name')} />
            {form.formState.errors.first_name ? (
              <span className="mt-1 block text-xs text-rose-700">
                {form.formState.errors.first_name.message}
              </span>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="last-name">
            Last name
            <input id="last-name" className={fieldClass} type="text" {...form.register('last_name')} />
            {form.formState.errors.last_name ? (
              <span className="mt-1 block text-xs text-rose-700">
                {form.formState.errors.last_name.message}
              </span>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="display-name">
            Display name
            <input
              id="display-name"
              className={fieldClass}
              type="text"
              {...form.register('display_name')}
            />
          </label>

          <label className="block text-sm font-medium text-slate-700" htmlFor="institution-id">
            Institution ID
            <input
              id="institution-id"
              className={fieldClass}
              type="text"
              readOnly={isInstitutionAdmin}
              {...form.register('institution_id')}
            />
          </label>
        </div>

        {profileType === 'student' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Student details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700" htmlFor="student-number">
                Student number
                <input
                  id="student-number"
                  className={fieldClass}
                  type="text"
                  {...form.register('student_number')}
                />
                {form.formState.errors.student_number ? (
                  <span className="mt-1 block text-xs text-rose-700">
                    {form.formState.errors.student_number.message}
                  </span>
                ) : null}
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="batch-id">
                Batch ID
                <input id="batch-id" className={fieldClass} type="text" {...form.register('batch_id')} />
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="student-department-id">
                Department ID
                <input
                  id="student-department-id"
                  className={fieldClass}
                  type="text"
                  {...form.register('department_id')}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="guardian-profile-id">
                Guardian profile ID
                <input
                  id="guardian-profile-id"
                  className={fieldClass}
                  type="text"
                  {...form.register('guardian_profile_id')}
                />
              </label>
            </div>
          </section>
        ) : null}

        {profileType === 'instructor' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Instructor details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700" htmlFor="employee-number">
                Employee number
                <input
                  id="employee-number"
                  className={fieldClass}
                  type="text"
                  {...form.register('employee_number')}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="instructor-department-id">
                Department ID
                <input
                  id="instructor-department-id"
                  className={fieldClass}
                  type="text"
                  {...form.register('department_id')}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="instructor-title">
                Title
                <input id="instructor-title" className={fieldClass} type="text" {...form.register('title')} />
              </label>
              <label className="block text-sm font-medium text-slate-700 md:col-span-2" htmlFor="bio">
                Bio
                <textarea id="bio" className={fieldClass} rows={4} {...form.register('bio')} />
              </label>
            </div>
          </section>
        ) : null}

        {profileType === 'admin' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Admin details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700" htmlFor="admin-type">
                Admin type
                <select id="admin-type" className={fieldClass} {...form.register('admin_type')}>
                  <option value="institution_admin">Institution Admin</option>
                  {isSuperAdmin ? <option value="super_admin">Super Admin</option> : null}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700" htmlFor="admin-department-id">
                Department ID
                <input
                  id="admin-department-id"
                  className={fieldClass}
                  type="text"
                  {...form.register('department_id')}
                />
              </label>
            </div>
          </section>
        ) : null}

        {mutation.isError ? (
          <div className="mt-5 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800" role="alert">
            {apiErrorMessage(mutation.error)}
          </div>
        ) : null}

        {mutation.data ? (
          <div className="mt-5 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
            Created user: {mutation.data.display_name || `${mutation.data.first_name} ${mutation.data.last_name}`.trim()}
          </div>
        ) : null}

        <button
          className="mt-5 rounded bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? 'Creating user' : 'Create user'}
        </button>
      </form>
    </PortalLayout>
  );
}

function PortalRoute({ portal }: { portal: Portal }) {
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
    return <Navigate to={allowedPortal === 'none' ? '/dashboard/no-access' : `/dashboard/${allowedPortal}`} replace />;
  }

  if (portal === 'student') {
    return <StudentPortal context={query.data} />;
  }
  if (portal === 'instructor') {
    return <InstructorPortal context={query.data} />;
  }
  return <AdminPortal context={query.data} />;
}

function AdminCreateUserRoute() {
  const query = useSessionContext();
  if (query.isLoading) {
    return <LoadingState label="Loading session" />;
  }
  if (query.isError || !query.data) {
    clearStoredTokens();
    return <Navigate to="/login" replace />;
  }

  const allowedPortal = portalForRole(query.data.session.primary_role);
  if (allowedPortal !== 'admin') {
    return (
      <Navigate
        to={allowedPortal === 'none' ? '/dashboard/no-access' : `/dashboard/${allowedPortal}`}
        replace
      />
    );
  }

  return <AdminCreateUserPage context={query.data} />;
}

function NoAccessPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6">
      <section className="rounded border border-slate-200 bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-950">No portal access</h1>
        <p className="mt-2 text-sm text-slate-600">
          This account does not have a student, instructor, or admin portal role.
        </p>
        <Link className="mt-5 inline-flex text-sm font-medium text-emerald-700" to="/login">
          Back to sign in
        </Link>
      </section>
    </main>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
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
        element={
          <ProtectedRoute>
            <PortalRoute portal="student" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/instructor"
        element={
          <ProtectedRoute>
            <PortalRoute portal="instructor" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/admin"
        element={
          <ProtectedRoute>
            <PortalRoute portal="admin" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/admin/users/new"
        element={
          <ProtectedRoute>
            <AdminCreateUserRoute />
          </ProtectedRoute>
        }
      />
      <Route path="/dashboard/no-access" element={<NoAccessPage />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
