import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { useForm, useWatch } from 'react-hook-form';
import { Link, Route, Routes } from 'react-router-dom';
import { z } from 'zod';

import { getFrontendStatus } from './api/status';

const roleSchema = z.object({
  role: z.enum(['student', 'instructor', 'admin'])
});

type RoleForm = z.infer<typeof roleSchema>;

function DashboardPreview() {
  const { data } = useQuery({
    queryKey: ['frontend-status'],
    queryFn: getFrontendStatus
  });

  const { control, register } = useForm<RoleForm>({
    resolver: zodResolver(roleSchema),
    defaultValues: { role: 'student' }
  });

  const role = useWatch({ control, name: 'role' });

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2 border-b border-slate-200 pb-6">
        <span className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
          {data?.serviceId} {data?.serviceName}
        </span>
        <h1 className="text-4xl font-semibold text-slate-950">LearnGrid LMS</h1>
        <p className="max-w-2xl text-base text-slate-600">
          React frontend baseline for student, instructor, and admin portals.
        </p>
      </header>

      <section className="grid gap-5 md:grid-cols-[240px_1fr]">
        <form className="rounded border border-slate-200 bg-white p-4">
          <label htmlFor="role" className="block text-sm font-medium text-slate-700">
            Portal preview
          </label>
          <select
            id="role"
            className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            {...register('role')}
          >
            <option value="student">Student</option>
            <option value="instructor">Instructor</option>
            <option value="admin">Admin</option>
          </select>
        </form>

        <div className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-xl font-semibold capitalize text-slate-900">{role} dashboard</h2>
          <p className="mt-2 text-sm text-slate-600">
            This shell verifies routing, query state, Tailwind styling, form handling, and schema
            validation are wired for the frontend service.
          </p>
          <Link className="mt-4 inline-flex text-sm font-medium text-emerald-700" to="/health">
            View frontend health
          </Link>
        </div>
      </section>
    </main>
  );
}

function HealthPage() {
  const { data } = useQuery({
    queryKey: ['frontend-status'],
    queryFn: getFrontendStatus
  });

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link className="text-sm font-medium text-emerald-700" to="/">
        Back to dashboard
      </Link>
      <pre className="mt-6 overflow-auto rounded bg-slate-950 p-4 text-sm text-white">
        {JSON.stringify(data, null, 2)}
      </pre>
    </main>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPreview />} />
      <Route path="/health" element={<HealthPage />} />
    </Routes>
  );
}
