import { useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { portalForRole, type SessionContext } from '../../api/auth';
import { clearStoredTokens } from '../../api/client';

export type Portal = 'student' | 'instructor' | 'admin';

export type NavItem = {
  key: string;
  label: string;
  to: string;
};

function displayName(context: SessionContext) {
  return (
    context.profile.display_name ||
    `${context.profile.first_name} ${context.profile.last_name}`.trim() ||
    context.session.email
  );
}

function navItemsFor(portal: Portal): NavItem[] {
  if (portal === 'student') {
    return [
      { key: 'student-dashboard', label: 'Student', to: '/dashboard/student' },
      { key: 'student-courses', label: 'Catalog', to: '/dashboard/student/courses' },
      { key: 'student-progress', label: 'Progress', to: '/dashboard/student/progress' },
      { key: 'student-certificates', label: 'Certificates', to: '/dashboard/student/certificates' },
      { key: 'notifications', label: 'Notifications', to: '/dashboard/student/notifications' }
    ];
  }
  if (portal === 'instructor') {
    return [
      { key: 'instructor-dashboard', label: 'Instructor', to: '/dashboard/instructor' },
      { key: 'instructor-courses', label: 'Courses', to: '/dashboard/instructor/courses' },
      { key: 'content-upload', label: 'Content', to: '/dashboard/instructor/content' },
      { key: 'assessment-authoring', label: 'Assessments', to: '/dashboard/instructor/assessments' },
      { key: 'grading', label: 'Grading', to: '/dashboard/instructor/grading' },
      { key: 'reports', label: 'Reports', to: '/dashboard/instructor/reports' },
      { key: 'notifications', label: 'Notifications', to: '/dashboard/instructor/notifications' }
    ];
  }
  return [
    { key: 'admin-dashboard', label: 'Admin', to: '/dashboard/admin' },
    { key: 'admin-create-user', label: 'Create User', to: '/dashboard/admin/users/new' },
    { key: 'admin-enrollments', label: 'Enrollments', to: '/dashboard/admin/enrollments' },
    { key: 'reports', label: 'Reports', to: '/dashboard/admin/reports' },
    { key: 'notifications', label: 'Notifications', to: '/dashboard/admin/notifications' }
  ];
}

export function PortalLayout({
  context,
  activeNav,
  children
}: {
  context: SessionContext;
  activeNav: string;
  children: ReactNode;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const portal = portalForRole(context.session.primary_role);
  const navItems = portal === 'none' ? [] : navItemsFor(portal);

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
        <nav className="h-fit rounded border border-slate-200 bg-white p-3" aria-label="Portal">
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
