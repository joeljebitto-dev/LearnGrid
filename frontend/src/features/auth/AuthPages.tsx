import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, type ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import {
  completeOidcCallback,
  getOidcConfig,
  login,
  portalForRole
} from '../../api/auth';
import { clearStoredTokens, hasStoredAccessToken } from '../../api/client';
import { getFrontendStatus } from '../../api/status';
import { buttonClass, fieldClass, LoadingState } from '../shared/ui';
import { useSessionContext } from './session';
import { startOidcAuthorization } from '../../api/auth';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

type LoginForm = z.infer<typeof loginSchema>;

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  if (!hasStoredAccessToken()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

export function DashboardRedirect() {
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

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ['frontend-status'],
    queryFn: getFrontendStatus
  });
  const oidcConfigQuery = useQuery({
    queryKey: ['oidc-config'],
    queryFn: getOidcConfig,
    retry: false
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
  const oidcAuthorizeMutation = useMutation({
    mutationFn: startOidcAuthorization,
    onSuccess: (result) => {
      window.location.assign(result.authorization_url);
    }
  });
  const oidcEnabled = oidcConfigQuery.data?.enabled === true;
  const oidcProviderLabel = oidcConfigQuery.data?.provider_label || 'SSO';

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
            <input
              id="email"
              className={fieldClass}
              type="email"
              autoComplete="email"
              {...form.register('email')}
            />
          </label>
          {form.formState.errors.email ? (
            <p className="mt-1 text-xs text-rose-700">{form.formState.errors.email.message}</p>
          ) : null}

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="password">
            Password
            <input
              id="password"
              className={fieldClass}
              type="password"
              autoComplete="current-password"
              {...form.register('password')}
            />
          </label>
          {loginMutation.isError ? (
            <p className="mt-3 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              Sign in failed.
            </p>
          ) : null}
          {oidcAuthorizeMutation.isError ? (
            <p className="mt-3 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              SSO sign in could not be started.
            </p>
          ) : null}
          <button className={`mt-5 w-full ${buttonClass}`} type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? 'Signing in' : 'Sign in'}
          </button>
          {oidcEnabled ? (
            <button
              className="mt-3 w-full rounded border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500"
              type="button"
              disabled={oidcAuthorizeMutation.isPending}
              onClick={() => oidcAuthorizeMutation.mutate()}
            >
              {oidcAuthorizeMutation.isPending
                ? 'Opening SSO'
                : `Continue with ${oidcProviderLabel}`}
            </button>
          ) : null}
        </form>
      </section>
    </main>
  );
}

export function OidcCallbackPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const submittedRef = useRef(false);
  const params = new URLSearchParams(location.search);
  const code = params.get('code');
  const state = params.get('state');
  const callbackMutation = useMutation({
    mutationFn: completeOidcCallback,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['session-context'] });
      navigate('/dashboard', { replace: true });
    }
  });
  const missingParams = !code || !state;

  useEffect(() => {
    if (submittedRef.current || !code || !state) {
      return;
    }
    submittedRef.current = true;
    callbackMutation.mutate({ code, state });
  }, [callbackMutation, code, state]);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6">
      <section className="w-full rounded border border-slate-200 bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-950">Completing SSO sign in</h1>
        {callbackMutation.isPending ? (
          <p className="mt-2 text-sm text-slate-600">Validating identity provider response.</p>
        ) : null}
        {missingParams || callbackMutation.isError ? (
          <div
            className="mt-4 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"
            role="alert"
          >
            SSO sign in failed.
          </div>
        ) : null}
      </section>
    </main>
  );
}

export function NoAccessPage() {
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
