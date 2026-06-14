import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type Assessment = Entity & {
  course_id?: string;
  institution_id?: string;
  assessment_type?: string;
  available_from?: string | null;
  available_until?: string | null;
};

export type Question = Entity & {
  question_type?: string;
  prompt?: string;
  choices?: unknown;
  points?: string | number;
};

export type QuizAttempt = Entity & {
  assessment_id?: string;
  student_profile_id?: string;
  questions?: Question[];
  answers?: unknown[];
  status?: string;
};

export async function listQuestionBanks(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/assessments/question-banks/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createQuestionBank(payload: {
  institution_id: string;
  owner_profile_id: string;
  title: string;
  description?: string | null;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/assessments/question-banks/', payload);
  return response.data;
}

export async function listQuestions(
  questionBankId: string,
  params?: QueryParams
): Promise<ListResponse<Question>> {
  const response = await apiClient.get<ListResponse<Question>>(
    `/assessments/question-banks/${questionBankId}/questions/`,
    { params: cleanParams(params) }
  );
  return response.data;
}

export async function createQuestion(
  questionBankId: string,
  payload: {
    question_type: string;
    prompt: string;
    choices?: unknown;
    correct_answer?: unknown;
    points?: number;
    status?: string;
  }
): Promise<Question> {
  const response = await apiClient.post<Question>(
    `/assessments/question-banks/${questionBankId}/questions/`,
    payload
  );
  return response.data;
}

export async function listAssessments(params?: QueryParams): Promise<ListResponse<Assessment>> {
  const response = await apiClient.get<ListResponse<Assessment>>('/assessments/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createAssessment(payload: {
  course_id: string;
  institution_id: string;
  owner_profile_id: string;
  title: string;
  assessment_type: string;
  instructions?: string | null;
  available_from?: string | null;
  available_until?: string | null;
  quiz?: Record<string, unknown>;
  assignment?: Record<string, unknown>;
}): Promise<Assessment> {
  const response = await apiClient.post<Assessment>('/assessments/', payload);
  return response.data;
}

export async function updateAssessment(
  assessmentId: string,
  payload: Partial<Assessment>
): Promise<Assessment> {
  const response = await apiClient.patch<Assessment>(`/assessments/${assessmentId}/`, payload);
  return response.data;
}

export async function replaceAssessmentQuestions(
  assessmentId: string,
  questions: Array<{ question_id: string; position?: number; points_override?: number | null }>
): Promise<Assessment> {
  const response = await apiClient.put<Assessment>(`/assessments/${assessmentId}/questions/`, {
    questions
  });
  return response.data;
}

export async function publishAssessment(assessmentId: string): Promise<Assessment> {
  const response = await apiClient.post<Assessment>(`/assessments/${assessmentId}/publish/`, {});
  return response.data;
}

export async function closeAssessment(assessmentId: string): Promise<Assessment> {
  const response = await apiClient.post<Assessment>(`/assessments/${assessmentId}/close/`, {});
  return response.data;
}

export async function startQuizAttempt(assessmentId: string): Promise<QuizAttempt> {
  const response = await apiClient.post<QuizAttempt>(
    `/assessments/${assessmentId}/attempts/start/`,
    {}
  );
  return response.data;
}

export async function getQuizAttempt(attemptId: string): Promise<QuizAttempt> {
  const response = await apiClient.get<QuizAttempt>(`/assessments/attempts/${attemptId}/`);
  return response.data;
}

export async function saveQuizAnswers(
  attemptId: string,
  answers: Array<{ question_id: string; answer_payload: unknown }>
): Promise<QuizAttempt> {
  const response = await apiClient.put<QuizAttempt>(`/assessments/attempts/${attemptId}/answers/`, {
    answers
  });
  return response.data;
}

export async function submitQuizAttempt(attemptId: string): Promise<QuizAttempt> {
  const response = await apiClient.post<QuizAttempt>(`/assessments/attempts/${attemptId}/submit/`, {});
  return response.data;
}

export async function autoSubmitQuizAttempt(attemptId: string): Promise<QuizAttempt> {
  const response = await apiClient.post<QuizAttempt>(
    `/assessments/attempts/${attemptId}/auto-submit/`,
    {}
  );
  return response.data;
}

export async function listAssignmentSubmissions(
  assignmentId: string,
  params?: QueryParams
): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>(
    `/assessments/assignments/${assignmentId}/submissions/`,
    { params: cleanParams(params) }
  );
  return response.data;
}

export async function createAssignmentSubmission(
  assignmentId: string,
  payload: {
    student_profile_id: string;
    text_response?: string | null;
    attachment_asset_id?: string | null;
    submit?: boolean;
  }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(
    `/assessments/assignments/${assignmentId}/submissions/`,
    payload
  );
  return response.data;
}

export async function updateAssignmentSubmission(
  submissionId: string,
  payload: { text_response?: string | null; attachment_asset_id?: string | null }
): Promise<Entity> {
  const response = await apiClient.patch<Entity>(`/assessments/submissions/${submissionId}/`, payload);
  return response.data;
}

export async function submitAssignmentSubmission(submissionId: string): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/assessments/submissions/${submissionId}/submit/`, {});
  return response.data;
}
