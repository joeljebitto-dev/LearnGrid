import { useQuery } from '@tanstack/react-query';

import { getSessionContext } from '../../api/auth';
import { hasStoredAccessToken } from '../../api/client';

export function useSessionContext() {
  return useQuery({
    queryKey: ['session-context'],
    queryFn: getSessionContext,
    enabled: hasStoredAccessToken(),
    retry: false
  });
}

export function adminInstitutionScope(context: {
  session: {
    primary_role: string | null;
    role_assignments: Array<{ scope_type: string; scope_id: string | null }>;
  };
  profile: { institution_id: string | null };
}) {
  return (
    context.session.role_assignments.find((assignment) => assignment.scope_type === 'institution')
      ?.scope_id ?? context.profile.institution_id
  );
}
