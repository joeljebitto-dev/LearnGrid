import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import type { SessionContext } from '../../api/auth';
import {
  generateReport,
  listDashboardAggregates,
  listReportSnapshots,
  listUsageMetrics,
  searchResourceType,
  searchResources
} from '../../api/analytics';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import {
  buttonClass,
  EntityList,
  ErrorState,
  fieldClass,
  Field,
  JsonPreview,
  LoadingState,
  PageHeader,
  Panel
} from '../shared/ui';

export function AnalyticsReportsPage({
  context,
  activeNav = 'reports'
}: {
  context: SessionContext;
  activeNav?: string;
}) {
  const queryClient = useQueryClient();
  const [q, setQ] = useState('');
  const [resourceType, setResourceType] = useState('all');
  const institutionId =
    context.session.primary_role === 'institution_admin'
      ? adminInstitutionScope(context)
      : context.profile.institution_id;
  const searchQuery = useQuery({
    queryKey: ['analytics-search', resourceType, q, institutionId],
    queryFn: () =>
      resourceType === 'all'
        ? searchResources({ q, institution_id: institutionId ?? undefined, page_size: 20 })
        : searchResourceType(resourceType as 'courses' | 'users' | 'enrollments' | 'assessments' | 'submissions', {
            q,
            institution_id: institutionId ?? undefined,
            page_size: 20
          })
  });
  const snapshotsQuery = useQuery({
    queryKey: ['analytics-snapshots', institutionId],
    queryFn: () => listReportSnapshots({ institution_id: institutionId ?? undefined })
  });
  const aggregatesQuery = useQuery({
    queryKey: ['analytics-aggregates', institutionId],
    queryFn: () => listDashboardAggregates({ institution_id: institutionId ?? undefined })
  });
  const usageQuery = useQuery({
    queryKey: ['analytics-usage', institutionId],
    queryFn: () => listUsageMetrics({ scope_id: institutionId ?? undefined })
  });
  const reportMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return generateReport({
        institution_id: String(data.get('institution_id') || institutionId || '') || null,
        report_type: String(data.get('report_type') || 'active_users'),
        parameters: {}
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['analytics-snapshots'] });
    }
  });

  return (
    <PortalLayout context={context} activeNav={activeNav}>
      <PageHeader title="Analytics And Reporting" description="Search indexed resources, generate reports, and inspect dashboard aggregates and usage metrics." />
      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <section className="rounded border border-slate-200 bg-white p-4">
            <div className="grid gap-3 md:grid-cols-[1fr_220px]">
              <Field htmlFor="analytics-q" label="Search">
                <input id="analytics-q" className={fieldClass} value={q} onChange={(event) => setQ(event.target.value)} />
              </Field>
              <Field htmlFor="analytics-resource" label="Resource">
                <select id="analytics-resource" className={fieldClass} value={resourceType} onChange={(event) => setResourceType(event.target.value)}>
                  <option value="all">All permitted</option>
                  <option value="courses">Courses</option>
                  <option value="users">Users</option>
                  <option value="enrollments">Enrollments</option>
                  <option value="assessments">Assessments</option>
                  <option value="submissions">Submissions</option>
                </select>
              </Field>
            </div>
          </section>
          {searchQuery.isLoading ? <LoadingState label="Searching" /> : null}
          {searchQuery.isError ? <ErrorState error={searchQuery.error} onRetry={() => void searchQuery.refetch()} /> : null}
          {searchQuery.data ? <EntityList title="Search results" response={searchQuery.data} detailKeys={['resource_type', 'status', 'updated_at']} /> : null}
          {snapshotsQuery.data ? <EntityList title="Report snapshots" response={snapshotsQuery.data} detailKeys={['report_type', 'generated_at']} /> : null}
          {aggregatesQuery.data ? <EntityList title="Dashboard aggregates" response={aggregatesQuery.data} detailKeys={['scope_type', 'scope_id', 'metric_date']} /> : null}
          {usageQuery.data ? <EntityList title="Usage metrics" response={usageQuery.data} detailKeys={['metric_name', 'metric_value', 'bucket_start_at']} /> : null}
        </div>
        <Panel title="Generate report">
          <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); reportMutation.mutate(event.currentTarget); }}>
            <Field htmlFor="report-institution" label="Institution ID">
              <input id="report-institution" name="institution_id" className={fieldClass} defaultValue={institutionId ?? ''} />
            </Field>
            <Field htmlFor="report-type" label="Report type">
              <select id="report-type" name="report_type" className={fieldClass}>
                <option value="active_users">Active users</option>
                <option value="enrollments">Enrollments</option>
                <option value="completion_rates">Completion rates</option>
                <option value="assessment_results">Assessment results</option>
                <option value="system_usage">System usage</option>
              </select>
            </Field>
            {reportMutation.isError ? <ErrorState title="Report generation failed" error={reportMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={reportMutation.isPending}>Generate report</button>
          </form>
          {reportMutation.data ? <div className="mt-4"><JsonPreview value={reportMutation.data} /></div> : null}
        </Panel>
      </div>
    </PortalLayout>
  );
}
