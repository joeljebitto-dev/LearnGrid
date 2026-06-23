import { useQuery } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import { listCertificates } from '../../api/grading';
import { toList } from '../../api/types';
import { PortalLayout } from '../layout/PortalLayout';
import { CertificateCard } from '../lms/LmsProductComponents';
import { EmptyState, ErrorState, LoadingState, PageHeader } from '../shared/ui';

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
        breadcrumbs={[
          { label: 'Student', href: '/dashboard/student' },
          { label: 'Certificates' }
        ]}
      />
      {query.isLoading ? <LoadingState label="Loading certificates" /> : null}
      {query.isError ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : null}
      {query.data ? (
        <div className="grid gap-4 md:grid-cols-2">
          {toList(query.data).length ? (
            toList(query.data).map((certificate) => (
              <CertificateCard key={certificate.id} certificate={certificate} />
            ))
          ) : (
            <div className="md:col-span-2">
              <EmptyState message="No certificates have been issued yet." />
            </div>
          )}
        </div>
      ) : null}
    </PortalLayout>
  );
}
