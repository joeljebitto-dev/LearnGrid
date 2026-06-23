import { Archive, Pencil, Plus, RotateCcw, Save, Search } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';

import type { SessionContext } from '../../api/auth';
import {
  archiveInstitution,
  createInstitution,
  listInstitutions,
  updateInstitution,
  type Institution,
  type InstitutionPayload,
  type InstitutionStatus
} from '../../api/users';
import { PortalLayout } from '../layout/PortalLayout';
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  LoadingState,
  PageHeader,
  PaginationControls,
  Panel,
  Select,
  StatusBadge,
  Toolbar,
  Toast
} from '../shared/ui';

type InstitutionFormValues = {
  name: string;
  code: string;
  status: InstitutionStatus;
};

const institutionStatuses: InstitutionStatus[] = ['active', 'suspended', 'archived'];

function emptyInstitutionForm(): InstitutionFormValues {
  return {
    name: '',
    code: '',
    status: 'active'
  };
}

function formPayload(values: InstitutionFormValues): InstitutionPayload {
  return {
    name: values.name.trim(),
    code: values.code.trim(),
    status: values.status
  };
}

export function AdminInstitutionsPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const isSuperAdmin = context.session.primary_role === 'super_admin';
  const [page, setPage] = useState(1);
  const [searchDraft, setSearchDraft] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<InstitutionStatus | ''>('');
  const [editingInstitution, setEditingInstitution] = useState<Institution | null>(null);
  const [formValues, setFormValues] = useState<InstitutionFormValues>(emptyInstitutionForm);

  const institutionsQuery = useQuery({
    queryKey: ['institutions', activeSearch, statusFilter, page],
    queryFn: () =>
      listInstitutions({
        q: activeSearch || undefined,
        status: statusFilter || undefined,
        sort: 'name',
        page,
        page_size: 10
      }),
    enabled: isSuperAdmin
  });

  const invalidateInstitutions = async () => {
    await queryClient.invalidateQueries({ queryKey: ['institutions'] });
  };

  const saveMutation = useMutation({
    mutationFn: (payload: InstitutionPayload) =>
      editingInstitution
        ? updateInstitution(editingInstitution.id, payload)
        : createInstitution(payload),
    onSuccess: async () => {
      setEditingInstitution(null);
      setFormValues(emptyInstitutionForm());
      await invalidateInstitutions();
    }
  });

  const archiveMutation = useMutation({
    mutationFn: (institutionId: string) => archiveInstitution(institutionId),
    onSuccess: invalidateInstitutions
  });

  const institutions = institutionsQuery.data?.results ?? [];
  const canSave = Boolean(formValues.name.trim() && formValues.code.trim());

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActiveSearch(searchDraft.trim());
    setPage(1);
  }

  function clearSearch() {
    setSearchDraft('');
    setActiveSearch('');
    setStatusFilter('');
    setPage(1);
  }

  function startEdit(institution: Institution) {
    saveMutation.reset();
    setEditingInstitution(institution);
    setFormValues({
      name: institution.name,
      code: institution.code,
      status: institution.status
    });
  }

  function resetForm() {
    saveMutation.reset();
    setEditingInstitution(null);
    setFormValues(emptyInstitutionForm());
  }

  function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) {
      return;
    }
    saveMutation.mutate(formPayload(formValues));
  }

  if (!isSuperAdmin) {
    return (
      <PortalLayout context={context} activeNav="admin-institutions">
        <PageHeader title="Institutions" />
        <ErrorState
          title="Super Admin access required"
          error={new Error('Institution management requires platform-level institution.manage permission.')}
        />
      </PortalLayout>
    );
  }

  return (
    <PortalLayout context={context} activeNav="admin-institutions">
      <PageHeader title="Institutions" />

      <form onSubmit={submitSearch}>
        <Toolbar className="mb-5">
          <Field htmlFor="institution-search" label="Search">
            <Input
              id="institution-search"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
            />
          </Field>
          <Field htmlFor="institution-status-filter" label="Status">
            <Select
              id="institution-status-filter"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as InstitutionStatus | '');
                setPage(1);
              }}
            >
              <option value="">Any status</option>
              {institutionStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
          </Field>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="secondary">
              <Search className="h-4 w-4" aria-hidden />
              Search
            </Button>
            <Button type="button" variant="ghost" onClick={clearSearch}>
              <RotateCcw className="h-4 w-4" aria-hidden />
              Reset
            </Button>
          </div>
        </Toolbar>
      </form>

      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <Panel title={editingInstitution ? 'Edit institution' : 'Create institution'}>
          <form className="space-y-4" onSubmit={submitForm}>
            <Field htmlFor="institution-name" label="Name" required>
              <Input
                id="institution-name"
                value={formValues.name}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, name: event.target.value }))
                }
                required
              />
            </Field>
            <Field htmlFor="institution-code" label="Code" required>
              <Input
                id="institution-code"
                value={formValues.code}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, code: event.target.value }))
                }
                required
              />
            </Field>
            <Field htmlFor="institution-status" label="Status">
              <Select
                id="institution-status"
                value={formValues.status}
                onChange={(event) =>
                  setFormValues((current) => ({
                    ...current,
                    status: event.target.value as InstitutionStatus
                  }))
                }
              >
                {institutionStatuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </Select>
            </Field>

            {saveMutation.isError ? (
              <ErrorState title="Unable to save institution" error={saveMutation.error} />
            ) : null}
            {saveMutation.isSuccess ? (
              <Toast title="Institution saved" tone="success" />
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button
                type="submit"
                disabled={!canSave}
                loading={saveMutation.isPending}
                loadingLabel={editingInstitution ? 'Updating' : 'Creating'}
              >
                {editingInstitution ? (
                  <Save className="h-4 w-4" aria-hidden />
                ) : (
                  <Plus className="h-4 w-4" aria-hidden />
                )}
                {editingInstitution ? 'Update institution' : 'Create institution'}
              </Button>
              {editingInstitution ? (
                <Button type="button" variant="secondary" onClick={resetForm}>
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Cancel edit
                </Button>
              ) : null}
            </div>
          </form>
        </Panel>

        <Panel
          title="Institution directory"
          actions={
            <PaginationControls
              page={page}
              hasNext={Boolean(institutionsQuery.data?.next)}
              onPrevious={() => setPage((current) => Math.max(1, current - 1))}
              onNext={() => setPage((current) => current + 1)}
            />
          }
        >
          {institutionsQuery.isLoading ? <LoadingState label="Loading institutions" /> : null}
          {institutionsQuery.isError ? (
            <ErrorState
              title="Unable to load institutions"
              error={institutionsQuery.error}
              onRetry={() => void institutionsQuery.refetch()}
            />
          ) : null}
          {archiveMutation.isError ? (
            <div className="mb-4">
              <ErrorState title="Unable to archive institution" error={archiveMutation.error} />
            </div>
          ) : null}
          {institutionsQuery.data && !institutions.length ? (
            <EmptyState message="No institutions found." />
          ) : null}
          {institutions.length ? (
            <div className="overflow-x-auto rounded-panel border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <caption className="sr-only">Institutions</caption>
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3" scope="col">Name</th>
                    <th className="px-4 py-3" scope="col">Code</th>
                    <th className="px-4 py-3" scope="col">Status</th>
                    <th className="px-4 py-3" scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {institutions.map((institution) => (
                    <tr key={institution.id}>
                      <td className="px-4 py-3 font-medium text-slate-950">{institution.name}</td>
                      <td className="px-4 py-3 text-slate-700">{institution.code}</td>
                      <td className="px-4 py-3">
                        <StatusBadge value={institution.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Edit ${institution.name}`}
                            onClick={() => startEdit(institution)}
                          >
                            <Pencil className="h-4 w-4" aria-hidden />
                            Edit
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            aria-label={`Archive ${institution.name}`}
                            loading={
                              archiveMutation.isPending &&
                              archiveMutation.variables === institution.id
                            }
                            loadingLabel="Archiving"
                            onClick={() => archiveMutation.mutate(institution.id)}
                          >
                            <Archive className="h-4 w-4" aria-hidden />
                            Archive
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </Panel>
      </div>
    </PortalLayout>
  );
}
