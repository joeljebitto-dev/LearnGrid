import { useQuery } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import {
  getAdminDashboard,
  getInstructorDashboard,
  getStudentDashboard,
  type StudentDashboard
} from '../../api/dashboards';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import { ErrorState, ListBand, LoadingState, PageHeader, SummaryGrid } from '../shared/ui';

function DashboardHeader({
  title,
  aggregate
}: {
  title: string;
  aggregate: StudentDashboard['aggregate'];
}) {
  return (
    <PageHeader
      title={title}
      description={aggregate ? `Updated ${aggregate.computed_at}` : 'No aggregate computed yet'}
    />
  );
}

export function StudentDashboardPage({ context }: { context: SessionContext }) {
  const query = useQuery({ queryKey: ['dashboard', 'student'], queryFn: getStudentDashboard });

  return (
    <PortalLayout context={context} activeNav="student-dashboard">
      {query.isLoading ? <LoadingState label="Loading student dashboard" /> : null}
      {query.isError ? <ErrorState title="Unable to load dashboard" error={query.error} onRetry={() => void query.refetch()} /> : null}
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

export function InstructorDashboardPage({ context }: { context: SessionContext }) {
  const query = useQuery({
    queryKey: ['dashboard', 'instructor'],
    queryFn: getInstructorDashboard
  });

  return (
    <PortalLayout context={context} activeNav="instructor-dashboard">
      {query.isLoading ? <LoadingState label="Loading instructor dashboard" /> : null}
      {query.isError ? <ErrorState title="Unable to load dashboard" error={query.error} onRetry={() => void query.refetch()} /> : null}
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

export function AdminDashboardPage({ context }: { context: SessionContext }) {
  const institutionScope =
    context.session.primary_role === 'institution_admin' ? adminInstitutionScope(context) : null;
  const query = useQuery({
    queryKey: ['dashboard', 'admin', institutionScope ?? 'system'],
    queryFn: () => getAdminDashboard(institutionScope)
  });

  return (
    <PortalLayout context={context} activeNav="admin-dashboard">
      {query.isLoading ? <LoadingState label="Loading admin dashboard" /> : null}
      {query.isError ? <ErrorState title="Unable to load dashboard" error={query.error} onRetry={() => void query.refetch()} /> : null}
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
