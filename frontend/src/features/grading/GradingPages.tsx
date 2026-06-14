import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import type { SessionContext } from '../../api/auth';
import {
  calculateGrade,
  completeManualReview,
  createGradingRule,
  createManualReview,
  evaluateCertificateEligibility,
  listCertificates,
  listGradeRecords,
  listGradingRules,
  listPublishedResults,
  overrideGrade,
  publishGrade,
  revokeCertificate,
  updateCertificateAsset
} from '../../api/grading';
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
  secondaryButtonClass
} from '../shared/ui';

type FormMutation = {
  mutate: (form: HTMLFormElement) => void;
  isPending: boolean;
  isError: boolean;
  error: unknown;
};

export function GradingPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const recordsQuery = useQuery({ queryKey: ['grading', 'records'], queryFn: () => listGradeRecords({ page_size: 20 }) });
  const rulesQuery = useQuery({ queryKey: ['grading', 'rules'], queryFn: () => listGradingRules({ page_size: 20 }) });
  const resultsQuery = useQuery({ queryKey: ['grading', 'results'], queryFn: () => listPublishedResults({ page_size: 20 }) });
  const certificatesQuery = useQuery({ queryKey: ['grading', 'certificates'], queryFn: () => listCertificates({ include_revoked: true, page_size: 20 }) });
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['grading'] });
  };
  const ruleMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createGradingRule({
        course_id: String(data.get('course_id') || ''),
        assessment_id: String(data.get('assessment_id') || '') || null,
        rule_type: String(data.get('rule_type') || 'weighted_total'),
        configuration: { certificate_min_percent: Number(data.get('certificate_min_percent') || 70) },
        created_by_profile_id: context.profile.id
      });
    },
    onSuccess: invalidate
  });
  const calculateMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return calculateGrade({
        submission_type: 'quiz_attempt',
        submission_id: String(data.get('submission_id') || ''),
        rule_id: String(data.get('rule_id') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const manualMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createManualReview({
        submission_type: String(data.get('submission_type') || 'assignment_submission') as 'quiz_attempt' | 'assignment_submission',
        submission_id: String(data.get('submission_id') || ''),
        reviewer_profile_id: context.profile.id
      });
    },
    onSuccess: invalidate
  });
  const completeMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return completeManualReview(String(data.get('review_id') || ''), {
        score: Number(data.get('score') || 0),
        feedback: String(data.get('feedback') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const overrideMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return overrideGrade(String(data.get('grade_record_id') || ''), {
        score: Number(data.get('score') || 0),
        max_score: Number(data.get('max_score') || 0),
        change_reason: String(data.get('change_reason') || '')
      });
    },
    onSuccess: invalidate
  });
  const publishMutation = useMutation({
    mutationFn: (gradeRecordId: string) => publishGrade(gradeRecordId, { published_feedback: null }),
    onSuccess: invalidate
  });
  const certificateMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return evaluateCertificateEligibility({
        student_profile_id: String(data.get('student_profile_id') || ''),
        course_id: String(data.get('course_id') || ''),
        certificate_asset_id: String(data.get('certificate_asset_id') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const certificateAssetMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return updateCertificateAsset(String(data.get('certificate_id') || ''), {
        certificate_asset_id: String(data.get('certificate_asset_id') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const revokeMutation = useMutation({ mutationFn: revokeCertificate, onSuccess: invalidate });

  return (
    <PortalLayout context={context} activeNav="grading">
      <PageHeader title="Grading And Manual Reviews" description="Manage rules, records, reviews, overrides, publication, and certificate workflows." />
      <div className="grid gap-5 xl:grid-cols-3">
        <GradingFormPanel title="Create rule" mutation={ruleMutation}>
          <Field htmlFor="rule-course" label="Course ID"><input id="rule-course" name="course_id" className={fieldClass} required /></Field>
          <Field htmlFor="rule-assessment" label="Assessment ID"><input id="rule-assessment" name="assessment_id" className={fieldClass} /></Field>
          <Field htmlFor="rule-type" label="Rule type"><input id="rule-type" name="rule_type" className={fieldClass} defaultValue="weighted_total" /></Field>
          <Field htmlFor="rule-certificate" label="Certificate min percent"><input id="rule-certificate" name="certificate_min_percent" className={fieldClass} type="number" defaultValue={70} /></Field>
        </GradingFormPanel>
        <GradingFormPanel title="Calculate quiz grade" mutation={calculateMutation}>
          <Field htmlFor="calc-submission" label="Quiz attempt ID"><input id="calc-submission" name="submission_id" className={fieldClass} required /></Field>
          <Field htmlFor="calc-rule" label="Rule ID"><input id="calc-rule" name="rule_id" className={fieldClass} /></Field>
        </GradingFormPanel>
        <GradingFormPanel title="Manual review" mutation={manualMutation}>
          <Field htmlFor="manual-submission-type" label="Submission type">
            <select id="manual-submission-type" name="submission_type" className={fieldClass}>
              <option value="assignment_submission">Assignment submission</option>
              <option value="quiz_attempt">Quiz attempt</option>
            </select>
          </Field>
          <Field htmlFor="manual-submission" label="Submission ID"><input id="manual-submission" name="submission_id" className={fieldClass} required /></Field>
        </GradingFormPanel>
        <GradingFormPanel title="Complete review" mutation={completeMutation}>
          <Field htmlFor="complete-review" label="Review ID"><input id="complete-review" name="review_id" className={fieldClass} required /></Field>
          <Field htmlFor="complete-score" label="Score"><input id="complete-score" name="score" className={fieldClass} type="number" min={0} required /></Field>
          <Field htmlFor="complete-feedback" label="Feedback"><textarea id="complete-feedback" name="feedback" className={fieldClass} rows={3} /></Field>
        </GradingFormPanel>
        <GradingFormPanel title="Override grade" mutation={overrideMutation}>
          <Field htmlFor="override-record" label="Grade record ID"><input id="override-record" name="grade_record_id" className={fieldClass} required /></Field>
          <Field htmlFor="override-score" label="Score"><input id="override-score" name="score" className={fieldClass} type="number" min={0} required /></Field>
          <Field htmlFor="override-max" label="Max score"><input id="override-max" name="max_score" className={fieldClass} type="number" min={0} /></Field>
          <Field htmlFor="override-reason" label="Change reason"><input id="override-reason" name="change_reason" className={fieldClass} required /></Field>
        </GradingFormPanel>
        <GradingFormPanel title="Evaluate certificate" mutation={certificateMutation}>
          <Field htmlFor="cert-student" label="Student profile ID"><input id="cert-student" name="student_profile_id" className={fieldClass} required /></Field>
          <Field htmlFor="cert-course" label="Course ID"><input id="cert-course" name="course_id" className={fieldClass} required /></Field>
          <Field htmlFor="cert-asset" label="Certificate asset ID"><input id="cert-asset" name="certificate_asset_id" className={fieldClass} /></Field>
        </GradingFormPanel>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        {recordsQuery.isLoading ? <LoadingState label="Loading grade records" /> : null}
        {recordsQuery.data ? (
          <EntityList
            title="Grade records"
            response={recordsQuery.data}
            detailKeys={['student_profile_id', 'course_id', 'score', 'status']}
            actions={(record) => (
              <button className={secondaryButtonClass} type="button" onClick={() => publishMutation.mutate(record.id)}>Publish</button>
            )}
          />
        ) : null}
        {rulesQuery.data ? <EntityList title="Rules" response={rulesQuery.data} detailKeys={['course_id', 'assessment_id', 'rule_type']} /> : null}
        {resultsQuery.data ? <EntityList title="Published results" response={resultsQuery.data} detailKeys={['student_profile_id', 'course_id', 'published_score']} /> : null}
        {certificatesQuery.data ? (
          <Panel title="Certificates">
            <form className="mb-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={(event) => { event.preventDefault(); certificateAssetMutation.mutate(event.currentTarget); }}>
              <Field htmlFor="cert-link-id" label="Certificate ID"><input id="cert-link-id" name="certificate_id" className={fieldClass} required /></Field>
              <Field htmlFor="cert-link-asset" label="Asset ID"><input id="cert-link-asset" name="certificate_asset_id" className={fieldClass} /></Field>
              <button className={`${buttonClass} self-end`} type="submit">Link asset</button>
            </form>
            <EntityList
              title="Issued certificates"
              response={certificatesQuery.data}
              detailKeys={['student_profile_id', 'course_id', 'certificate_number', 'revoked_at']}
              actions={(certificate) => (
                <button className={secondaryButtonClass} type="button" onClick={() => revokeMutation.mutate(certificate.id)}>Revoke</button>
              )}
            />
          </Panel>
        ) : null}
      </div>
    </PortalLayout>
  );
}

function GradingFormPanel({
  title,
  mutation,
  children
}: {
  title: string;
  mutation: FormMutation;
  children: ReactNode;
}) {
  return (
    <Panel title={title}>
      <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); mutation.mutate(event.currentTarget); }}>
        {children}
        {mutation.isError ? <ErrorState title={`${title} failed`} error={mutation.error} /> : null}
        <button className={buttonClass} type="submit" disabled={mutation.isPending}>Submit</button>
      </form>
    </Panel>
  );
}
