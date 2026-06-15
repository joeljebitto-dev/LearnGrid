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
import { Button, ErrorState, Field, Input, LoadingState } from '../shared/ui';
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
    <main className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-10" id="main-content">
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
          className="rounded-panel border border-slate-200 bg-white p-5 shadow-panel"
          aria-describedby="login-form-description"
          onSubmit={form.handleSubmit((values) => loginMutation.mutate(values))}
        >
          <h2 className="text-xl font-semibold text-slate-950">Sign in</h2>
          <p id="login-form-description" className="mt-1 text-sm text-slate-600">
            Use your LearnGrid account or the configured SSO provider.
          </p>
          <div className="mt-5">
            <Field htmlFor="email" label="Email" error={form.formState.errors.email?.message} required>
              <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(form.formState.errors.email)}
              {...form.register('email')}
            />
            </Field>
          </div>

          <div className="mt-4">
            <Field htmlFor="password" label="Password" error={form.formState.errors.password?.message} required>
              <Input
              id="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(form.formState.errors.password)}
              {...form.register('password')}
            />
            </Field>
          </div>
          {loginMutation.isError ? <div className="mt-3"><ErrorState title="Sign in failed" error={loginMutation.error} /></div> : null}
          {oidcAuthorizeMutation.isError ? <div className="mt-3"><ErrorState title="SSO sign in could not be started" error={oidcAuthorizeMutation.error} /></div> : null}
          <Button className="mt-5 w-full" type="submit" loading={loginMutation.isPending} loadingLabel="Signing in">
            Sign in
          </Button>
          {oidcEnabled ? (
            <Button
              className="mt-3 w-full"
              variant="secondary"
              type="button"
              loading={oidcAuthorizeMutation.isPending}
              loadingLabel="Opening SSO"
              onClick={() => oidcAuthorizeMutation.mutate()}
            >
              Continue with {oidcProviderLabel}
            </Button>
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
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6" id="main-content">
      <section className="w-full rounded-panel border border-slate-200 bg-white p-6 shadow-panel">
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
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6" id="main-content">
      <section className="rounded-panel border border-slate-200 bg-white p-6 shadow-panel">
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
