import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import type { SessionContext } from '../../api/auth';
import { createUserProfile, type CreateUserProfilePayload } from '../../api/users';
import { adminInstitutionScope } from '../auth/session';
import { PortalLayout } from '../layout/PortalLayout';
import { apiErrorMessage } from '../../api/types';
import { buttonClass, fieldClass, Field, PageHeader } from '../shared/ui';

const phoneSchema = z
  .string()
  .trim()
  .regex(/^\+?[1-9][0-9]{7,14}$/, 'Invalid phone number')
  .optional()
  .or(z.literal(''));

const createUserSchema = z
  .object({
    email: z.string().email(),
    phone: phoneSchema,
    temporary_password: z.string().min(12),
    profile_type: z.enum(['student', 'instructor', 'admin']),
    institution_id: z.string().trim().optional(),
    first_name: z.string().trim().min(1),
    last_name: z.string().trim().min(1),
    display_name: z.string().trim().optional(),
    student_number: z.string().trim().optional(),
    batch_id: z.string().trim().optional(),
    department_id: z.string().trim().optional(),
    guardian_profile_id: z.string().trim().optional(),
    employee_number: z.string().trim().optional(),
    title: z.string().trim().optional(),
    bio: z.string().trim().optional(),
    admin_type: z.enum(['institution_admin', 'super_admin'])
  })
  .superRefine((value, context) => {
    if (value.profile_type === 'student' && !value.student_number) {
      context.addIssue({
        code: 'custom',
        path: ['student_number'],
        message: 'Student number is required.'
      });
    }
  });

type CreateUserForm = z.infer<typeof createUserSchema>;

function emptyToNull(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function createUserDefaults(context: SessionContext): CreateUserForm {
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

function buildCreateUserPayload(
  values: CreateUserForm,
  context: SessionContext
): CreateUserProfilePayload {
  const institutionId =
    emptyToNull(values.institution_id) ??
    (context.session.primary_role === 'institution_admin' ? adminInstitutionScope(context) : null);
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
      student_number: values.student_number?.trim() ?? '',
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

export function AdminCreateUserPage({ context }: { context: SessionContext }) {
  const isSuperAdmin = context.session.primary_role === 'super_admin';
  const isInstitutionAdmin = context.session.primary_role === 'institution_admin';
  const form = useForm<CreateUserForm>({
    resolver: zodResolver(createUserSchema),
    defaultValues: createUserDefaults(context)
  });
  const profileType = useWatch({ control: form.control, name: 'profile_type' });
  const mutation = useMutation({
    mutationFn: (values: CreateUserForm) => createUserProfile(buildCreateUserPayload(values, context)),
    onSuccess: () => {
      form.reset(createUserDefaults(context));
    }
  });

  return (
    <PortalLayout context={context} activeNav="admin-create-user">
      <PageHeader title="Create User" />

      <form
        className="rounded border border-slate-200 bg-white p-5"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Field htmlFor="new-email" label="Email" error={form.formState.errors.email?.message}>
            <input id="new-email" className={fieldClass} type="email" {...form.register('email')} />
          </Field>

          <Field htmlFor="new-phone" label="Phone">
            <input id="new-phone" className={fieldClass} type="tel" {...form.register('phone')} />
          </Field>

          <Field
            htmlFor="new-password"
            label="Temporary password"
            error={form.formState.errors.temporary_password?.message}
          >
            <input
              id="new-password"
              className={fieldClass}
              type="password"
              autoComplete="new-password"
              {...form.register('temporary_password')}
            />
          </Field>

          <Field htmlFor="profile-type" label="Profile type">
            <select id="profile-type" className={fieldClass} {...form.register('profile_type')}>
              <option value="student">Student</option>
              <option value="instructor">Instructor</option>
              <option value="admin">Admin</option>
            </select>
          </Field>

          <Field htmlFor="first-name" label="First name" error={form.formState.errors.first_name?.message}>
            <input id="first-name" className={fieldClass} type="text" {...form.register('first_name')} />
          </Field>

          <Field htmlFor="last-name" label="Last name" error={form.formState.errors.last_name?.message}>
            <input id="last-name" className={fieldClass} type="text" {...form.register('last_name')} />
          </Field>

          <Field htmlFor="display-name" label="Display name">
            <input id="display-name" className={fieldClass} type="text" {...form.register('display_name')} />
          </Field>

          <Field htmlFor="institution-id" label="Institution ID">
            <input
              id="institution-id"
              className={fieldClass}
              type="text"
              readOnly={isInstitutionAdmin}
              {...form.register('institution_id')}
            />
          </Field>
        </div>

        {profileType === 'student' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Student details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Field
                htmlFor="student-number"
                label="Student number"
                error={form.formState.errors.student_number?.message}
              >
                <input id="student-number" className={fieldClass} type="text" {...form.register('student_number')} />
              </Field>
              <Field htmlFor="batch-id" label="Batch ID">
                <input id="batch-id" className={fieldClass} type="text" {...form.register('batch_id')} />
              </Field>
              <Field htmlFor="student-department-id" label="Department ID">
                <input id="student-department-id" className={fieldClass} type="text" {...form.register('department_id')} />
              </Field>
              <Field htmlFor="guardian-profile-id" label="Guardian profile ID">
                <input id="guardian-profile-id" className={fieldClass} type="text" {...form.register('guardian_profile_id')} />
              </Field>
            </div>
          </section>
        ) : null}

        {profileType === 'instructor' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Instructor details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Field htmlFor="employee-number" label="Employee number">
                <input id="employee-number" className={fieldClass} type="text" {...form.register('employee_number')} />
              </Field>
              <Field htmlFor="instructor-department-id" label="Department ID">
                <input id="instructor-department-id" className={fieldClass} type="text" {...form.register('department_id')} />
              </Field>
              <Field htmlFor="instructor-title" label="Title">
                <input id="instructor-title" className={fieldClass} type="text" {...form.register('title')} />
              </Field>
              <Field htmlFor="bio" label="Bio">
                <textarea id="bio" className={fieldClass} rows={4} {...form.register('bio')} />
              </Field>
            </div>
          </section>
        ) : null}

        {profileType === 'admin' ? (
          <section className="mt-6 border-t border-slate-200 pt-5">
            <h3 className="text-base font-semibold text-slate-950">Admin details</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Field htmlFor="admin-type" label="Admin type">
                <select id="admin-type" className={fieldClass} {...form.register('admin_type')}>
                  <option value="institution_admin">Institution Admin</option>
                  {isSuperAdmin ? <option value="super_admin">Super Admin</option> : null}
                </select>
              </Field>
              <Field htmlFor="admin-department-id" label="Department ID">
                <input id="admin-department-id" className={fieldClass} type="text" {...form.register('department_id')} />
              </Field>
            </div>
          </section>
        ) : null}

        {mutation.isError ? (
          <div className="mt-5 rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800" role="alert">
            {apiErrorMessage(mutation.error, 'User creation failed.')}
          </div>
        ) : null}

        {mutation.data ? (
          <div className="mt-5 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
            Created user:{' '}
            {mutation.data.display_name || `${mutation.data.first_name} ${mutation.data.last_name}`.trim()}
          </div>
        ) : null}

        <button className={`mt-5 ${buttonClass}`} type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Creating user' : 'Create user'}
        </button>
      </form>
    </PortalLayout>
  );
}
