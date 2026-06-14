import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import {
  createBatchEnrollment,
  createCohortEnrollment,
  createEnrollment,
  listBatchEnrollments,
  listCohortEnrollments,
  listEnrollments,
  transitionEnrollment
} from '../../api/enrollments';
import { PortalLayout } from '../layout/PortalLayout';
import {
  buttonClass,
  EntityList,
  ErrorState,
  fieldClass,
  Field,
  LoadingState,
  PageHeader,
  Panel,
  parseCsv
} from '../shared/ui';

type FormMutation = {
  mutate: (form: HTMLFormElement) => void;
  isPending: boolean;
  isError: boolean;
  error: unknown;
};

export function EnrollmentManagementPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const enrollmentsQuery = useQuery({
    queryKey: ['enrollments', context.profile.institution_id],
    queryFn: () =>
      listEnrollments({
        institution_id: context.profile.institution_id ?? undefined,
        page_size: 20,
        sort: '-updated_at'
      })
  });
  const batchQuery = useQuery({
    queryKey: ['batch-enrollments'],
    queryFn: () => listBatchEnrollments({ page_size: 10 })
  });
  const cohortQuery = useQuery({
    queryKey: ['cohort-enrollments'],
    queryFn: () => listCohortEnrollments({ page_size: 10 })
  });
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['enrollments'] });
    await queryClient.invalidateQueries({ queryKey: ['batch-enrollments'] });
    await queryClient.invalidateQueries({ queryKey: ['cohort-enrollments'] });
  };
  const individualMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createEnrollment({
        student_profile_id: String(data.get('student_profile_id') || ''),
        course_id: String(data.get('course_id') || ''),
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        enrolled_by_profile_id: context.profile.id,
        expires_at: String(data.get('expires_at') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const transitionMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return transitionEnrollment(String(data.get('enrollment_id') || ''), {
        status: String(data.get('status') || 'active'),
        changed_by_profile_id: context.profile.id,
        reason: String(data.get('reason') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const batchMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createBatchEnrollment({
        batch_id: String(data.get('batch_id') || ''),
        course_id: String(data.get('course_id') || ''),
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        requested_by_profile_id: context.profile.id,
        student_profile_ids: parseCsv(String(data.get('student_profile_ids') || ''))
      });
    },
    onSuccess: invalidate
  });
  const cohortMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createCohortEnrollment({
        cohort_id: String(data.get('cohort_id') || ''),
        course_id: String(data.get('course_id') || ''),
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        requested_by_profile_id: context.profile.id,
        student_profile_ids: parseCsv(String(data.get('student_profile_ids') || ''))
      });
    },
    onSuccess: invalidate
  });

  return (
    <PortalLayout context={context} activeNav="admin-enrollments">
      <PageHeader title="Enrollment Management" description="Manage individual, batch, cohort, history, and access-grant workflows." />
      <div className="grid gap-5 xl:grid-cols-4">
        <EnrollmentForm title="Individual enrollment" mutation={individualMutation} context={context} />
        <TransitionForm mutation={transitionMutation} />
        <BatchForm title="Batch enrollment" mutation={batchMutation} context={context} idName="batch_id" label="Batch ID" />
        <BatchForm title="Cohort enrollment" mutation={cohortMutation} context={context} idName="cohort_id" label="Cohort ID" />
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        {enrollmentsQuery.isLoading ? <LoadingState label="Loading enrollments" /> : null}
        {enrollmentsQuery.isError ? <ErrorState error={enrollmentsQuery.error} onRetry={() => void enrollmentsQuery.refetch()} /> : null}
        {enrollmentsQuery.data ? <EntityList title="Enrollments" response={enrollmentsQuery.data} detailKeys={['student_profile_id', 'course_id', 'status']} /> : null}
        {batchQuery.data ? <EntityList title="Batch jobs" response={batchQuery.data} detailKeys={['batch_id', 'course_id', 'status']} /> : null}
        {cohortQuery.data ? <EntityList title="Cohort jobs" response={cohortQuery.data} detailKeys={['cohort_id', 'course_id', 'status']} /> : null}
      </div>
    </PortalLayout>
  );
}

function EnrollmentForm({
  title,
  mutation,
  context
}: {
  title: string;
  mutation: FormMutation;
  context: SessionContext;
}) {
  return (
    <Panel title={title}>
      <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); mutation.mutate(event.currentTarget); }}>
        <Field htmlFor="enroll-student" label="Student profile ID">
          <input id="enroll-student" name="student_profile_id" className={fieldClass} required />
        </Field>
        <Field htmlFor="enroll-course" label="Course ID">
          <input id="enroll-course" name="course_id" className={fieldClass} required />
        </Field>
        <Field htmlFor="enroll-institution" label="Institution ID">
          <input id="enroll-institution" name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required />
        </Field>
        <Field htmlFor="enroll-expires" label="Expires at">
          <input id="enroll-expires" name="expires_at" className={fieldClass} type="datetime-local" />
        </Field>
        {mutation.isError ? <ErrorState title="Enrollment failed" error={mutation.error} /> : null}
        <button className={buttonClass} type="submit" disabled={mutation.isPending}>Save</button>
      </form>
    </Panel>
  );
}

function TransitionForm({ mutation }: { mutation: FormMutation }) {
  return (
    <Panel title="Transition status">
      <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); mutation.mutate(event.currentTarget); }}>
        <Field htmlFor="transition-id" label="Enrollment ID">
          <input id="transition-id" name="enrollment_id" className={fieldClass} required />
        </Field>
        <Field htmlFor="transition-status" label="Status">
          <select id="transition-status" name="status" className={fieldClass}>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </Field>
        <Field htmlFor="transition-reason" label="Reason">
          <input id="transition-reason" name="reason" className={fieldClass} />
        </Field>
        {mutation.isError ? <ErrorState title="Transition failed" error={mutation.error} /> : null}
        <button className={buttonClass} type="submit" disabled={mutation.isPending}>Transition</button>
      </form>
    </Panel>
  );
}

function BatchForm({
  title,
  mutation,
  context,
  idName,
  label
}: {
  title: string;
  mutation: FormMutation;
  context: SessionContext;
  idName: string;
  label: string;
}) {
  return (
    <Panel title={title}>
      <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); mutation.mutate(event.currentTarget); }}>
        <Field htmlFor={`${idName}-field`} label={label}>
          <input id={`${idName}-field`} name={idName} className={fieldClass} required />
        </Field>
        <Field htmlFor={`${idName}-course`} label="Course ID">
          <input id={`${idName}-course`} name="course_id" className={fieldClass} required />
        </Field>
        <Field htmlFor={`${idName}-institution`} label="Institution ID">
          <input id={`${idName}-institution`} name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required />
        </Field>
        <Field htmlFor={`${idName}-students`} label="Student profile IDs">
          <textarea id={`${idName}-students`} name="student_profile_ids" className={fieldClass} rows={3} placeholder="Comma-separated UUIDs" />
        </Field>
        {mutation.isError ? <ErrorState title={`${title} failed`} error={mutation.error} /> : null}
        <button className={buttonClass} type="submit" disabled={mutation.isPending}>Create job</button>
      </form>
    </Panel>
  );
}
