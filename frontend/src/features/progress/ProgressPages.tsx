import { useQuery } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import { listCourseProgress } from '../../api/progress';
import { PortalLayout } from '../layout/PortalLayout';
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Panel,
  StatusBadge
} from '../shared/ui';

export function StudentProgressPage({ context }: { context: SessionContext }) {
  const query = useQuery({
    queryKey: ['progress', 'courses', context.profile.id],
    queryFn: () => listCourseProgress({ student_profile_id: context.profile.id })
  });
  const records = Array.isArray(query.data) ? query.data : query.data?.results ?? [];

  return (
    <PortalLayout context={context} activeNav="student-progress">
      <PageHeader
        title="Learning Progress"
        description="Track lesson, video, assessment, and course completion across active learning."
      />
      {query.isLoading ? <LoadingState label="Loading progress" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {records.length ? (
            records.map((record) => {
              const percent = Number(record.completion_percent ?? 0);
              return (
                <Panel key={record.id} title={`Course ${record.course_id ?? record.id}`}>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Status</span>
                      <StatusBadge value={record.status} />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between text-xs text-slate-500">
                        <span>Completion</span>
                        <span>{percent}%</span>
                      </div>
                      <div className="h-2 rounded bg-slate-100">
                        <div
                          className="h-2 rounded bg-emerald-600"
                          style={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
                        />
                      </div>
                    </div>
                    <dl className="grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded bg-slate-50 p-3">
                        <dt className="text-xs text-slate-500">Lessons</dt>
                        <dd className="font-semibold text-slate-950">{record.lessons_completed ?? 0}</dd>
                      </div>
                      <div className="rounded bg-slate-50 p-3">
                        <dt className="text-xs text-slate-500">Assessments</dt>
                        <dd className="font-semibold text-slate-950">{record.assessments_completed ?? 0}</dd>
                      </div>
                    </dl>
                  </div>
                </Panel>
              );
            })
          ) : (
            <div className="lg:col-span-2">
              <EmptyState message="No course progress has been recorded yet." />
            </div>
          )}
        </div>
      ) : null}
    </PortalLayout>
  );
}
