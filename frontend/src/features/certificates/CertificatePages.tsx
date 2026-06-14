import { useQuery } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import { listCertificates } from '../../api/grading';
import { PortalLayout } from '../layout/PortalLayout';
import { EntityList, ErrorState, LoadingState, PageHeader } from '../shared/ui';

export function StudentCertificatesPage({ context }: { context: SessionContext }) {
  const query = useQuery({
    queryKey: ['certificates', context.profile.id],
    queryFn: () => listCertificates({ student_profile_id: context.profile.id })
  });

  return (
    <PortalLayout context={context} activeNav="student-certificates">
      <PageHeader
        title="Certificates"
        description="View valid certificates and certificate asset references issued for completed courses."
      />
      {query.isLoading ? <LoadingState label="Loading certificates" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <EntityList
          title="My certificates"
          response={query.data}
          detailKeys={['course_id', 'certificate_number', 'certificate_asset_id', 'valid']}
          emptyMessage="No certificates have been issued yet."
        />
      ) : null}
    </PortalLayout>
  );
}
