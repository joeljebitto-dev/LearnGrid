import { Pencil, Plus, RotateCcw, Search, UserMinus } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState, type FormEvent } from 'react';

import type { SessionContext, UserProfile } from '../../api/auth';
import {
  createUserProfile,
  deactivateUserProfile,
  listInstitutions,
  listUserProfiles,
  updateUserProfile,
  type CreateUserProfilePayload,
  type Institution,
  type ProfileType,
  type UpdateUserProfilePayload,
  type UserProfileStatus
} from '../../api/users';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import {
  Badge,
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
  Textarea,
  Toolbar,
  Toast
} from '../shared/ui';

type AdminType = 'institution_admin' | 'super_admin';

type UserFormValues = {
  email: string;
  phone: string;
  temporary_password: string;
  profile_type: ProfileType;
  institution_id: string;
  first_name: string;
  last_name: string;
  display_name: string;
  status: UserProfileStatus;
  student_number: string;
  batch_id: string;
  department_id: string;
  guardian_profile_id: string;
  employee_number: string;
  title: string;
  bio: string;
  admin_type: AdminType;
};

const platformScopeValue = '__platform__';
const profileTypes: ProfileType[] = ['student', 'instructor', 'admin'];
const profileStatuses: UserProfileStatus[] = ['active', 'inactive', 'deactivated'];

function emptyToNull(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function stringValue(value: unknown) {
  return typeof value === 'string' ? value : '';
}

function profileTitle(profile: UserProfile) {
  return (
    profile.display_name ||
    `${profile.first_name} ${profile.last_name}`.trim() ||
    profile.auth_account_id
  );
}

function emptyUserForm(context: SessionContext): UserFormValues {
  return {
    email: '',
    phone: '',
    temporary_password: '',
    profile_type: 'student',
    institution_id:
      context.session.primary_role === 'institution_admin'
        ? adminInstitutionScope(context) ?? ''
        : '',
    first_name: '',
    last_name: '',
    display_name: '',
    status: 'active',
    student_number: '',
    batch_id: '',
    department_id: '',
    guardian_profile_id: '',
    employee_number: '',
    title: '',
    bio: '',
    admin_type: 'institution_admin'
  };
}

function formFromProfile(profile: UserProfile): UserFormValues {
  const roleProfile = profile.role_profile ?? {};
  return {
    email: '',
    phone: '',
    temporary_password: '',
    profile_type: profile.profile_type ?? 'student',
    institution_id: profile.institution_id ?? '',
    first_name: profile.first_name,
    last_name: profile.last_name,
    display_name: profile.display_name ?? '',
    status: profile.status as UserProfileStatus,
    student_number: stringValue(roleProfile.student_number),
    batch_id: stringValue(roleProfile.batch_id),
    department_id: stringValue(roleProfile.department_id),
    guardian_profile_id: stringValue(roleProfile.guardian_profile_id),
    employee_number: stringValue(roleProfile.employee_number),
    title: stringValue(roleProfile.title),
    bio: stringValue(roleProfile.bio),
    admin_type:
      stringValue(roleProfile.admin_type) === 'super_admin'
        ? 'super_admin'
        : 'institution_admin'
  };
}

function institutionLabel(institution: Institution) {
  return `${institution.name} (${institution.code})`;
}

function institutionName(
  institutionId: string | null,
  institutionsById: Map<string, Institution>
) {
  if (!institutionId) {
    return 'Platform';
  }
  const institution = institutionsById.get(institutionId);
  return institution ? institutionLabel(institution) : 'Institution unavailable';
}

function createPayload(
  values: UserFormValues,
  context: SessionContext
): CreateUserProfilePayload {
  const isInstitutionAdmin = context.session.primary_role === 'institution_admin';
  const lockedInstitutionId = isInstitutionAdmin ? adminInstitutionScope(context) : null;
  const institutionId =
    lockedInstitutionId ??
    (values.institution_id === platformScopeValue ? null : emptyToNull(values.institution_id));
  const departmentId = emptyToNull(values.department_id);
  const payload: CreateUserProfilePayload = {
    email: values.email.trim(),
    phone: emptyToNull(values.phone),
    temporary_password: values.temporary_password,
    profile_type: values.profile_type,
    institution_id: institutionId,
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    display_name: emptyToNull(values.display_name)
  };

  if (values.profile_type === 'student') {
    payload.student = {
      student_number: values.student_number.trim(),
      batch_id: emptyToNull(values.batch_id),
      department_id: departmentId,
      guardian_profile_id: emptyToNull(values.guardian_profile_id)
    };
  }

  if (values.profile_type === 'instructor') {
    payload.instructor = {
      employee_number: emptyToNull(values.employee_number),
      department_id: departmentId,
      title: emptyToNull(values.title),
      bio: emptyToNull(values.bio)
    };
  }

  if (values.profile_type === 'admin') {
    payload.admin = {
      admin_type: values.admin_type,
      department_id: departmentId
    };
  }

  return payload;
}

function updatePayload(values: UserFormValues, profile: UserProfile): UpdateUserProfilePayload {
  const departmentId = emptyToNull(values.department_id);
  const payload: UpdateUserProfilePayload = {
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    display_name: emptyToNull(values.display_name),
    status: values.status
  };
  const email = emptyToNull(values.email);
  const phone = emptyToNull(values.phone);
  if (email) {
    payload.email = email;
  }
  if (phone) {
    payload.phone = phone;
  }
  if (profile.profile_type === 'student') {
    payload.student = {
      batch_id: emptyToNull(values.batch_id),
      department_id: departmentId,
      guardian_profile_id: emptyToNull(values.guardian_profile_id)
    };
    if (values.student_number.trim()) {
      payload.student.student_number = values.student_number.trim();
    }
  }
  if (profile.profile_type === 'instructor') {
    payload.instructor = {
      employee_number: emptyToNull(values.employee_number),
      department_id: departmentId,
      title: emptyToNull(values.title),
      bio: emptyToNull(values.bio)
    };
  }
  if (profile.profile_type === 'admin') {
    payload.admin = {
      admin_type: values.admin_type,
      department_id: departmentId
    };
  }
  return payload;
}

export function AdminUsersPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const isSuperAdmin = context.session.primary_role === 'super_admin';
  const institutionScope =
    context.session.primary_role === 'institution_admin' ? adminInstitutionScope(context) : null;
  const [page, setPage] = useState(1);
  const [searchDraft, setSearchDraft] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [profileTypeFilter, setProfileTypeFilter] = useState<ProfileType | ''>('');
  const [statusFilter, setStatusFilter] = useState<UserProfileStatus | ''>('');
  const [institutionSearch, setInstitutionSearch] = useState('');
  const [editingProfile, setEditingProfile] = useState<UserProfile | null>(null);
  const [formValues, setFormValues] = useState<UserFormValues>(() => emptyUserForm(context));

  const usersQuery = useQuery({
    queryKey: [
      'admin-users',
      institutionScope ?? 'all',
      activeSearch,
      profileTypeFilter,
      statusFilter,
      page
    ],
    queryFn: () =>
      listUserProfiles({
        institution_id: institutionScope ?? undefined,
        q: activeSearch || undefined,
        profile_type: profileTypeFilter || undefined,
        status: statusFilter || undefined,
        sort: 'last_name',
        page,
        page_size: 10
      })
  });

  const institutionsQuery = useQuery({
    queryKey: ['admin-user-institutions', institutionSearch],
    queryFn: () =>
      listInstitutions({
        q: institutionSearch.trim() || undefined,
        status: 'active',
        sort: 'name',
        page_size: 100
      }),
    enabled: isSuperAdmin
  });

  const institutions = useMemo(
    () => institutionsQuery.data?.results ?? [],
    [institutionsQuery.data]
  );
  const institutionsById = useMemo(
    () =>
      new Map<string, Institution>(
        institutions.map((institution) => [institution.id, institution] as const)
      ),
    [institutions]
  );

  const invalidateUsers = async () => {
    await queryClient.invalidateQueries({ queryKey: ['admin-users'] });
  };

  const saveMutation = useMutation({
    mutationFn: (values: UserFormValues) =>
      editingProfile
        ? updateUserProfile(editingProfile.id, updatePayload(values, editingProfile))
        : createUserProfile(createPayload(values, context)),
    onSuccess: async () => {
      setEditingProfile(null);
      setFormValues(emptyUserForm(context));
      await invalidateUsers();
    }
  });

  const deactivateMutation = useMutation({
    mutationFn: (profileId: string) => deactivateUserProfile(profileId),
    onSuccess: invalidateUsers
  });

  const users = usersQuery.data?.results ?? [];
  const isEditing = Boolean(editingProfile);
  const isPlatformSuperAdminCreate =
    !isEditing &&
    isSuperAdmin &&
    formValues.profile_type === 'admin' &&
    formValues.admin_type === 'super_admin';
  const selectedInstitutionId =
    formValues.institution_id === platformScopeValue ? null : emptyToNull(formValues.institution_id);
  const hasInstitutionForCreate =
    Boolean(institutionScope) ||
    isPlatformSuperAdminCreate ||
    Boolean(selectedInstitutionId);
  const canSave =
    Boolean(formValues.first_name.trim() && formValues.last_name.trim()) &&
    (isEditing ||
      Boolean(
        formValues.email.trim() &&
          formValues.temporary_password.length >= 12 &&
          hasInstitutionForCreate &&
          (formValues.profile_type !== 'student' || formValues.student_number.trim())
      ));

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActiveSearch(searchDraft.trim());
    setPage(1);
  }

  function clearSearch() {
    setSearchDraft('');
    setActiveSearch('');
    setProfileTypeFilter('');
    setStatusFilter('');
    setPage(1);
  }

  function resetForm() {
    saveMutation.reset();
    setEditingProfile(null);
    setFormValues(emptyUserForm(context));
    setInstitutionSearch('');
  }

  function startEdit(profile: UserProfile) {
    saveMutation.reset();
    setEditingProfile(profile);
    setFormValues(formFromProfile(profile));
    setInstitutionSearch('');
  }

  function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSave) {
      saveMutation.mutate(formValues);
    }
  }

  function setProfileType(profileType: ProfileType) {
    setFormValues((current) => ({
      ...current,
      profile_type: profileType,
      institution_id:
        profileType === 'admin' && current.admin_type === 'super_admin'
          ? platformScopeValue
          : current.institution_id === platformScopeValue
            ? ''
            : current.institution_id
    }));
  }

  function setAdminType(adminType: AdminType) {
    setFormValues((current) => ({
      ...current,
      admin_type: adminType,
      institution_id:
        adminType === 'super_admin'
          ? platformScopeValue
          : current.institution_id === platformScopeValue
            ? ''
            : current.institution_id
    }));
  }

  return (
    <PortalLayout context={context} activeNav="admin-users">
      <PageHeader title="Users" />

      <form onSubmit={submitSearch}>
        <Toolbar className="mb-5">
          <Field htmlFor="user-search" label="Search">
            <Input
              id="user-search"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
            />
          </Field>
          <Field htmlFor="user-profile-type-filter" label="Filter profile type">
            <Select
              id="user-profile-type-filter"
              value={profileTypeFilter}
              onChange={(event) => {
                setProfileTypeFilter(event.target.value as ProfileType | '');
                setPage(1);
              }}
            >
              <option value="">Any type</option>
              {profileTypes.map((profileType) => (
                <option key={profileType} value={profileType}>
                  {profileType}
                </option>
              ))}
            </Select>
          </Field>
          <Field htmlFor="user-status-filter" label="Filter status">
            <Select
              id="user-status-filter"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as UserProfileStatus | '');
                setPage(1);
              }}
            >
              <option value="">Any status</option>
              {profileStatuses.map((status) => (
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

      <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
        <Panel title={isEditing ? 'Edit user' : 'Create user'}>
          <form className="space-y-4" onSubmit={submitForm}>
            {!isEditing ? (
              <>
                <Field htmlFor="user-email" label="Email" required>
                  <Input
                    id="user-email"
                    type="email"
                    value={formValues.email}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, email: event.target.value }))
                    }
                    required
                  />
                </Field>
                <Field htmlFor="user-password" label="Temporary password" required>
                  <Input
                    id="user-password"
                    type="password"
                    autoComplete="new-password"
                    value={formValues.temporary_password}
                    onChange={(event) =>
                      setFormValues((current) => ({
                        ...current,
                        temporary_password: event.target.value
                      }))
                    }
                    required
                  />
                </Field>
              </>
            ) : (
              <>
                <Field htmlFor="user-email" label="Email">
                  <Input
                    id="user-email"
                    type="email"
                    value={formValues.email}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, email: event.target.value }))
                    }
                  />
                </Field>
              </>
            )}

            <Field htmlFor="user-phone" label="Phone">
              <Input
                id="user-phone"
                type="tel"
                value={formValues.phone}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, phone: event.target.value }))
                }
              />
            </Field>

            <Field htmlFor="user-profile-type" label="Profile type">
              <Select
                id="user-profile-type"
                value={formValues.profile_type}
                disabled={isEditing}
                onChange={(event) => setProfileType(event.target.value as ProfileType)}
              >
                {profileTypes.map((profileType) => (
                  <option key={profileType} value={profileType}>
                    {profileType}
                  </option>
                ))}
              </Select>
            </Field>

            {!isEditing && isSuperAdmin && !isPlatformSuperAdminCreate ? (
              <>
                <Field htmlFor="institution-search" label="Find institution">
                  <Input
                    id="institution-search"
                    value={institutionSearch}
                    onChange={(event) => setInstitutionSearch(event.target.value)}
                  />
                </Field>
                <Field htmlFor="user-institution" label="Institution" required>
                  <Select
                    id="user-institution"
                    value={formValues.institution_id}
                    onChange={(event) =>
                      setFormValues((current) => ({
                        ...current,
                        institution_id: event.target.value
                      }))
                    }
                    required
                  >
                    <option value="">Select institution</option>
                    {institutions.map((institution) => (
                      <option key={institution.id} value={institution.id}>
                        {institutionLabel(institution)}
                      </option>
                    ))}
                  </Select>
                </Field>
                {institutionsQuery.isError ? (
                  <ErrorState title="Unable to load institutions" error={institutionsQuery.error} />
                ) : null}
              </>
            ) : null}

            {!isEditing && isSuperAdmin && isPlatformSuperAdminCreate ? (
              <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium text-slate-900">Institution</span>
                <div className="mt-1">Platform</div>
              </div>
            ) : null}

            {!isEditing && !isSuperAdmin ? (
              <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium text-slate-900">Institution</span>
                <div className="mt-1">Current institution</div>
              </div>
            ) : null}

            {isEditing ? (
              <div className="rounded-panel border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium text-slate-900">Institution</span>
                  <div className="mt-1">
                    {!isSuperAdmin && editingProfile?.institution_id === institutionScope
                      ? 'Current institution'
                      : institutionName(editingProfile?.institution_id ?? null, institutionsById)}
                  </div>
              </div>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              <Field htmlFor="user-first-name" label="First name" required>
                <Input
                  id="user-first-name"
                  value={formValues.first_name}
                  onChange={(event) =>
                    setFormValues((current) => ({ ...current, first_name: event.target.value }))
                  }
                  required
                />
              </Field>
              <Field htmlFor="user-last-name" label="Last name" required>
                <Input
                  id="user-last-name"
                  value={formValues.last_name}
                  onChange={(event) =>
                    setFormValues((current) => ({ ...current, last_name: event.target.value }))
                  }
                  required
                />
              </Field>
            </div>

            <Field htmlFor="user-display-name" label="Display name">
              <Input
                id="user-display-name"
                value={formValues.display_name}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, display_name: event.target.value }))
                }
              />
            </Field>

            {isEditing ? (
              <Field htmlFor="user-status" label="Status">
                <Select
                  id="user-status"
                  value={formValues.status}
                  onChange={(event) =>
                    setFormValues((current) => ({
                      ...current,
                      status: event.target.value as UserProfileStatus
                    }))
                  }
                >
                  {profileStatuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </Select>
              </Field>
            ) : null}

            {formValues.profile_type === 'student' ? (
              <div className="space-y-4 border-t border-slate-200 pt-4">
                <h3 className="text-base font-semibold text-slate-950">Student details</h3>
                <Field htmlFor="user-student-number" label="Student number" required={!isEditing}>
                  <Input
                    id="user-student-number"
                    value={formValues.student_number}
                    onChange={(event) =>
                      setFormValues((current) => ({
                        ...current,
                        student_number: event.target.value
                      }))
                    }
                    required={!isEditing}
                  />
                </Field>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field htmlFor="user-batch-id" label="Batch ID">
                    <Input
                      id="user-batch-id"
                      value={formValues.batch_id}
                      onChange={(event) =>
                        setFormValues((current) => ({ ...current, batch_id: event.target.value }))
                      }
                    />
                  </Field>
                  <Field htmlFor="user-student-department-id" label="Department ID">
                    <Input
                      id="user-student-department-id"
                      value={formValues.department_id}
                      onChange={(event) =>
                        setFormValues((current) => ({
                          ...current,
                          department_id: event.target.value
                        }))
                      }
                    />
                  </Field>
                </div>
                <Field htmlFor="user-guardian-profile-id" label="Guardian profile ID">
                  <Input
                    id="user-guardian-profile-id"
                    value={formValues.guardian_profile_id}
                    onChange={(event) =>
                      setFormValues((current) => ({
                        ...current,
                        guardian_profile_id: event.target.value
                      }))
                    }
                  />
                </Field>
              </div>
            ) : null}

            {formValues.profile_type === 'instructor' ? (
              <div className="space-y-4 border-t border-slate-200 pt-4">
                <h3 className="text-base font-semibold text-slate-950">Instructor details</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field htmlFor="user-employee-number" label="Employee number">
                    <Input
                      id="user-employee-number"
                      value={formValues.employee_number}
                      onChange={(event) =>
                        setFormValues((current) => ({
                          ...current,
                          employee_number: event.target.value
                        }))
                      }
                    />
                  </Field>
                  <Field htmlFor="user-instructor-department-id" label="Department ID">
                    <Input
                      id="user-instructor-department-id"
                      value={formValues.department_id}
                      onChange={(event) =>
                        setFormValues((current) => ({
                          ...current,
                          department_id: event.target.value
                        }))
                      }
                    />
                  </Field>
                </div>
                <Field htmlFor="user-title" label="Title">
                  <Input
                    id="user-title"
                    value={formValues.title}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, title: event.target.value }))
                    }
                  />
                </Field>
                <Field htmlFor="user-bio" label="Bio">
                  <Textarea
                    id="user-bio"
                    rows={4}
                    value={formValues.bio}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, bio: event.target.value }))
                    }
                  />
                </Field>
              </div>
            ) : null}

            {formValues.profile_type === 'admin' ? (
              <div className="space-y-4 border-t border-slate-200 pt-4">
                <h3 className="text-base font-semibold text-slate-950">Admin details</h3>
                <Field htmlFor="user-admin-type" label="Admin type">
                  <Select
                    id="user-admin-type"
                    value={formValues.admin_type}
                    onChange={(event) => setAdminType(event.target.value as AdminType)}
                  >
                    <option value="institution_admin">Institution Admin</option>
                    {isSuperAdmin ? <option value="super_admin">Super Admin</option> : null}
                  </Select>
                </Field>
                <Field htmlFor="user-admin-department-id" label="Department ID">
                  <Input
                    id="user-admin-department-id"
                    value={formValues.department_id}
                    onChange={(event) =>
                      setFormValues((current) => ({
                        ...current,
                        department_id: event.target.value
                      }))
                    }
                  />
                </Field>
              </div>
            ) : null}

            {saveMutation.isError ? (
              <ErrorState
                title={isEditing ? 'Unable to update user' : 'Unable to create user'}
                error={saveMutation.error}
              />
            ) : null}
            {saveMutation.isSuccess ? (
              <Toast title={isEditing ? 'User updated' : 'User created'} tone="success" />
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button
                type="submit"
                disabled={!canSave}
                loading={saveMutation.isPending}
                loadingLabel={isEditing ? 'Updating' : 'Creating'}
              >
                <Plus className="h-4 w-4" aria-hidden />
                {isEditing ? 'Update user' : 'Create user'}
              </Button>
              {isEditing ? (
                <Button type="button" variant="secondary" onClick={resetForm}>
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Cancel edit
                </Button>
              ) : null}
            </div>
          </form>
        </Panel>

        <Panel
          title="User directory"
          actions={
            <PaginationControls
              page={page}
              hasNext={Boolean(usersQuery.data?.next)}
              onPrevious={() => setPage((current) => Math.max(1, current - 1))}
              onNext={() => setPage((current) => current + 1)}
            />
          }
        >
          {usersQuery.isLoading ? <LoadingState label="Loading users" /> : null}
          {usersQuery.isError ? (
            <ErrorState
              title="Unable to load users"
              error={usersQuery.error}
              onRetry={() => void usersQuery.refetch()}
            />
          ) : null}
          {deactivateMutation.isError ? (
            <div className="mb-4">
              <ErrorState title="Unable to deactivate user" error={deactivateMutation.error} />
            </div>
          ) : null}
          {usersQuery.data && !users.length ? <EmptyState message="No users found." /> : null}
          {users.length ? (
            <div className="overflow-x-auto rounded-panel border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <caption className="sr-only">Users</caption>
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3" scope="col">Name</th>
                    <th className="px-4 py-3" scope="col">Profile type</th>
                    <th className="px-4 py-3" scope="col">Institution</th>
                    <th className="px-4 py-3" scope="col">Status</th>
                    <th className="px-4 py-3" scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((profile) => (
                    <tr key={profile.id}>
                      <td className="px-4 py-3 font-medium text-slate-950">
                        {profileTitle(profile)}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        <Badge>{profile.profile_type ?? 'none'}</Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {!isSuperAdmin && profile.institution_id === institutionScope
                          ? 'Current institution'
                          : institutionName(profile.institution_id, institutionsById)}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge value={profile.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            aria-label={`Edit ${profileTitle(profile)}`}
                            onClick={() => startEdit(profile)}
                          >
                            <Pencil className="h-4 w-4" aria-hidden />
                            Edit
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            aria-label={`Deactivate ${profileTitle(profile)}`}
                            loading={
                              deactivateMutation.isPending &&
                              deactivateMutation.variables === profile.id
                            }
                            loadingLabel="Deactivating"
                            onClick={() => deactivateMutation.mutate(profile.id)}
                            disabled={profile.status === 'deactivated'}
                          >
                            <UserMinus className="h-4 w-4" aria-hidden />
                            Deactivate
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
