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
import { toList } from '../../api/types';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import { ReportingFilters, ReportInsightPanel } from '../lms/LmsProductComponents';
import { useUnsavedChangesWarning } from '../shared/quality';
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
  const [hasUnsavedReport, setHasUnsavedReport] = useState(false);
  useUnsavedChangesWarning(hasUnsavedReport, 'Report generation form has unsaved parameters.');
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
      setHasUnsavedReport(false);
      await queryClient.invalidateQueries({ queryKey: ['analytics-snapshots'] });
    }
  });

  return (
    <PortalLayout context={context} activeNav={activeNav}>
      <PageHeader title="Analytics And Reporting" description="Search indexed resources, generate reports, and inspect dashboard aggregates and usage metrics." />
      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <ReportingFilters
            q={q}
            resourceType={resourceType}
            onQChange={setQ}
            onResourceTypeChange={setResourceType}
          />
          {searchQuery.isLoading ? <LoadingState label="Searching" /> : null}
          {searchQuery.isError ? <ErrorState error={searchQuery.error} onRetry={() => void searchQuery.refetch()} /> : null}
          {searchQuery.data ? <EntityList title="Search results" response={searchQuery.data} detailKeys={['resource_type', 'status', 'updated_at']} /> : null}
          {snapshotsQuery.data ? <ReportInsightPanel title="Report snapshots" items={toList(snapshotsQuery.data)} /> : null}
          {aggregatesQuery.data ? <ReportInsightPanel title="Dashboard aggregates" items={toList(aggregatesQuery.data)} /> : null}
          {usageQuery.data ? <ReportInsightPanel title="Usage metrics" items={toList(usageQuery.data)} /> : null}
        </div>
        <Panel title="Generate report">
          <form className="space-y-4" onChange={() => setHasUnsavedReport(true)} onSubmit={(event) => { event.preventDefault(); reportMutation.mutate(event.currentTarget); }}>
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
