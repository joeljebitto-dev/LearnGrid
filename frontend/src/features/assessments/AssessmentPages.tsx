import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import type { SessionContext } from '../../api/auth';
import {
  autoSubmitQuizAttempt,
  closeAssessment,
  createAssessment,
  createAssignmentSubmission,
  createQuestion,
  createQuestionBank,
  listAssessments,
  listQuestionBanks,
  publishAssessment,
  replaceAssessmentQuestions,
  saveQuizAnswers,
  startQuizAttempt,
  submitAssignmentSubmission,
  submitQuizAttempt,
  type QuizAttempt
} from '../../api/assessments';
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
  Panel,
  parseCsv,
  secondaryButtonClass
} from '../shared/ui';

type FormMutation = {
  mutate: (form: HTMLFormElement) => void;
  isPending: boolean;
  isError: boolean;
  error: unknown;
};

export function AssessmentAuthoringPage({ context }: { context: SessionContext }) {
  const queryClient = useQueryClient();
  const banksQuery = useQuery({ queryKey: ['question-banks'], queryFn: () => listQuestionBanks({ page_size: 20 }) });
  const assessmentsQuery = useQuery({ queryKey: ['assessments'], queryFn: () => listAssessments({ page_size: 20, sort: '-created_at' }) });
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['question-banks'] });
    await queryClient.invalidateQueries({ queryKey: ['assessments'] });
  };
  const bankMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createQuestionBank({
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        owner_profile_id: context.profile.id,
        title: String(data.get('title') || ''),
        description: String(data.get('description') || '') || null
      });
    },
    onSuccess: invalidate
  });
  const questionMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      const questionType = String(data.get('question_type') || 'multiple_choice');
      const choices = questionType.includes('multiple')
        ? [
            { id: 'A', text: String(data.get('choice_a') || 'A') },
            { id: 'B', text: String(data.get('choice_b') || 'B') }
          ]
        : undefined;
      return createQuestion(String(data.get('question_bank_id') || ''), {
        question_type: questionType,
        prompt: String(data.get('prompt') || ''),
        choices,
        correct_answer: questionType === 'multiple_choice' ? { choice_id: 'A' } : { value: true },
        points: Number(data.get('points') || 1),
        status: String(data.get('status') || 'draft')
      });
    },
    onSuccess: invalidate
  });
  const assessmentMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      const assessmentType = String(data.get('assessment_type') || 'quiz');
      return createAssessment({
        course_id: String(data.get('course_id') || ''),
        institution_id: String(data.get('institution_id') || context.profile.institution_id || ''),
        owner_profile_id: context.profile.id,
        title: String(data.get('title') || ''),
        assessment_type: assessmentType,
        instructions: String(data.get('instructions') || '') || null,
        quiz:
          assessmentType === 'quiz' || assessmentType === 'exam'
            ? { max_attempts: Number(data.get('max_attempts') || 1), randomize_questions: false }
            : undefined,
        assignment:
          assessmentType === 'assignment'
            ? { max_points: Number(data.get('max_points') || 100), allow_late_submission: true }
            : undefined
      });
    },
    onSuccess: invalidate
  });
  const attachMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return replaceAssessmentQuestions(
        String(data.get('assessment_id') || ''),
        parseCsv(String(data.get('question_ids') || '')).map((questionId, index) => ({
          question_id: questionId,
          position: index + 1
        }))
      );
    },
    onSuccess: invalidate
  });
  const lifecycleMutation = useMutation({
    mutationFn: ({ assessmentId, action }: { assessmentId: string; action: 'publish' | 'close' }) =>
      action === 'publish' ? publishAssessment(assessmentId) : closeAssessment(assessmentId),
    onSuccess: invalidate
  });

  return (
    <PortalLayout context={context} activeNav="assessment-authoring">
      <PageHeader title="Assessment Authoring" description="Build question banks, questions, quizzes, exams, and assignments." />
      <div className="grid gap-5 xl:grid-cols-4">
        <AssessmentFormPanel title="Question bank" mutation={bankMutation}>
          <Field htmlFor="bank-title" label="Title"><input id="bank-title" name="title" className={fieldClass} required /></Field>
          <Field htmlFor="bank-institution" label="Institution ID"><input id="bank-institution" name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required /></Field>
          <Field htmlFor="bank-description" label="Description"><textarea id="bank-description" name="description" className={fieldClass} rows={3} /></Field>
        </AssessmentFormPanel>

        <AssessmentFormPanel title="Question" mutation={questionMutation}>
          <Field htmlFor="question-bank-id" label="Question bank ID"><input id="question-bank-id" name="question_bank_id" className={fieldClass} required /></Field>
          <Field htmlFor="question-type" label="Question type">
            <select id="question-type" name="question_type" className={fieldClass}>
              <option value="multiple_choice">Multiple choice</option>
              <option value="true_false">True/false</option>
              <option value="short_answer">Short answer</option>
              <option value="essay">Essay</option>
              <option value="file_upload">File upload</option>
            </select>
          </Field>
          <Field htmlFor="question-prompt" label="Prompt"><textarea id="question-prompt" name="prompt" className={fieldClass} rows={3} required /></Field>
          <Field htmlFor="choice-a" label="Choice A"><input id="choice-a" name="choice_a" className={fieldClass} /></Field>
          <Field htmlFor="choice-b" label="Choice B"><input id="choice-b" name="choice_b" className={fieldClass} /></Field>
          <Field htmlFor="question-points" label="Points"><input id="question-points" name="points" className={fieldClass} type="number" min={0} defaultValue={1} /></Field>
        </AssessmentFormPanel>

        <AssessmentFormPanel title="Assessment" mutation={assessmentMutation}>
          <Field htmlFor="assessment-title" label="Title"><input id="assessment-title" name="title" className={fieldClass} required /></Field>
          <Field htmlFor="assessment-course" label="Course ID"><input id="assessment-course" name="course_id" className={fieldClass} required /></Field>
          <Field htmlFor="assessment-institution" label="Institution ID"><input id="assessment-institution" name="institution_id" className={fieldClass} defaultValue={context.profile.institution_id ?? ''} required /></Field>
          <Field htmlFor="assessment-type" label="Type">
            <select id="assessment-type" name="assessment_type" className={fieldClass}>
              <option value="quiz">Quiz</option>
              <option value="exam">Exam</option>
              <option value="assignment">Assignment</option>
            </select>
          </Field>
          <Field htmlFor="assessment-instructions" label="Instructions"><textarea id="assessment-instructions" name="instructions" className={fieldClass} rows={3} /></Field>
          <Field htmlFor="max-attempts" label="Max attempts"><input id="max-attempts" name="max_attempts" className={fieldClass} type="number" min={1} defaultValue={1} /></Field>
          <Field htmlFor="max-points" label="Assignment max points"><input id="max-points" name="max_points" className={fieldClass} type="number" min={0} defaultValue={100} /></Field>
        </AssessmentFormPanel>

        <AssessmentFormPanel title="Attach questions" mutation={attachMutation}>
          <Field htmlFor="attach-assessment" label="Assessment ID"><input id="attach-assessment" name="assessment_id" className={fieldClass} required /></Field>
          <Field htmlFor="attach-questions" label="Question IDs"><textarea id="attach-questions" name="question_ids" className={fieldClass} rows={4} placeholder="Comma-separated UUIDs" required /></Field>
        </AssessmentFormPanel>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        {banksQuery.isLoading ? <LoadingState label="Loading question banks" /> : null}
        {banksQuery.data ? <EntityList title="Question banks" response={banksQuery.data} detailKeys={['institution_id', 'owner_profile_id']} /> : null}
        {assessmentsQuery.data ? (
          <EntityList
            title="Assessments"
            response={assessmentsQuery.data}
            detailKeys={['course_id', 'assessment_type', 'status']}
            actions={(assessment) => (
              <>
                <button className={secondaryButtonClass} type="button" onClick={() => lifecycleMutation.mutate({ assessmentId: assessment.id, action: 'publish' })}>Publish</button>
                <button className={secondaryButtonClass} type="button" onClick={() => lifecycleMutation.mutate({ assessmentId: assessment.id, action: 'close' })}>Close</button>
              </>
            )}
          />
        ) : null}
      </div>
    </PortalLayout>
  );
}

function AssessmentFormPanel({
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
        <button className={buttonClass} type="submit" disabled={mutation.isPending}>Save</button>
      </form>
    </Panel>
  );
}

export function StudentAssessmentAttemptPage({ context }: { context: SessionContext }) {
  const { assessmentId = '' } = useParams();
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const startMutation = useMutation({
    mutationFn: () => startQuizAttempt(assessmentId),
    onSuccess: setAttempt
  });
  const saveMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return saveQuizAnswers(String(attempt?.id), [
        {
          question_id: String(data.get('question_id') || ''),
          answer_payload: { value: String(data.get('answer') || '') }
        }
      ]);
    },
    onSuccess: setAttempt
  });
  const submitMutation = useMutation({ mutationFn: () => submitQuizAttempt(String(attempt?.id)), onSuccess: setAttempt });
  const autoMutation = useMutation({ mutationFn: () => autoSubmitQuizAttempt(String(attempt?.id)), onSuccess: setAttempt });

  return (
    <PortalLayout context={context} activeNav="student-courses">
      <PageHeader title="Assessment Attempt" description="Start, save draft answers, submit, or auto-submit a quiz/exam attempt." />
      <Panel title="Attempt workflow">
        <div className="space-y-4">
          <button className={buttonClass} type="button" onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>Start attempt</button>
          {startMutation.isError ? <ErrorState title="Attempt start failed" error={startMutation.error} /> : null}
          {attempt ? (
            <>
              <JsonPreview value={attempt} />
              <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={(event) => { event.preventDefault(); saveMutation.mutate(event.currentTarget); }}>
                <Field htmlFor="attempt-question-id" label="Question ID"><input id="attempt-question-id" name="question_id" className={fieldClass} required /></Field>
                <Field htmlFor="attempt-answer" label="Answer"><input id="attempt-answer" name="answer" className={fieldClass} required /></Field>
                <button className={`${buttonClass} self-end`} type="submit">Save draft</button>
              </form>
              <div className="flex flex-wrap gap-2">
                <button className={secondaryButtonClass} type="button" onClick={() => submitMutation.mutate()}>Submit</button>
                <button className={secondaryButtonClass} type="button" onClick={() => autoMutation.mutate()}>Auto-submit</button>
              </div>
            </>
          ) : null}
        </div>
      </Panel>
    </PortalLayout>
  );
}

export function AssignmentSubmissionPage({ context }: { context: SessionContext }) {
  const { assignmentId = '' } = useParams();
  const [submissionId, setSubmissionId] = useState('');
  const draftMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return createAssignmentSubmission(assignmentId, {
        student_profile_id: context.profile.id,
        text_response: String(data.get('text_response') || '') || null,
        attachment_asset_id: String(data.get('attachment_asset_id') || '') || null,
        submit: false
      });
    },
    onSuccess: (submission) => setSubmissionId(submission.id)
  });
  const submitMutation = useMutation({ mutationFn: () => submitAssignmentSubmission(submissionId) });

  return (
    <PortalLayout context={context} activeNav="student-courses">
      <PageHeader title="Assignment Submission" description="Save draft work, attach content assets, and submit final assignment responses." />
      <Panel title="Submission editor">
        <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); draftMutation.mutate(event.currentTarget); }}>
          <Field htmlFor="assignment-text" label="Text response">
            <textarea id="assignment-text" name="text_response" className={fieldClass} rows={8} />
          </Field>
          <Field htmlFor="assignment-asset" label="Attachment asset ID">
            <input id="assignment-asset" name="attachment_asset_id" className={fieldClass} />
          </Field>
          {draftMutation.isError ? <ErrorState title="Draft save failed" error={draftMutation.error} /> : null}
          <button className={buttonClass} type="submit" disabled={draftMutation.isPending}>Save draft</button>
        </form>
        {submissionId ? (
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className="text-sm text-slate-600">Draft ID: {submissionId}</span>
            <button className={secondaryButtonClass} type="button" onClick={() => submitMutation.mutate()}>Submit final</button>
          </div>
        ) : null}
        {submitMutation.isError ? <div className="mt-4"><ErrorState title="Submission failed" error={submitMutation.error} /></div> : null}
      </Panel>
    </PortalLayout>
  );
}
