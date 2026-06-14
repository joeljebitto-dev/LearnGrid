import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type GradeRecord = Entity & {
  student_profile_id?: string;
  course_id?: string;
  assessment_id?: string | null;
  score?: string | number;
  max_score?: string | number;
};

export type Certificate = Entity & {
  student_profile_id?: string;
  course_id?: string;
  certificate_number?: string;
  certificate_asset_id?: string | null;
  revoked_at?: string | null;
  valid?: boolean;
};

export async function listGradingRules(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/grading/rules/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createGradingRule(payload: {
  course_id: string;
  assessment_id?: string | null;
  rule_type: string;
  configuration?: Record<string, unknown>;
  created_by_profile_id: string;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/grading/rules/', payload);
  return response.data;
}

export async function listGradeRecords(params?: QueryParams): Promise<ListResponse<GradeRecord>> {
  const response = await apiClient.get<ListResponse<GradeRecord>>('/grading/records/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function calculateGrade(payload: {
  submission_type: 'quiz_attempt';
  submission_id: string;
  rule_id?: string | null;
}): Promise<GradeRecord> {
  const response = await apiClient.post<GradeRecord>('/grading/records/calculate/', payload);
  return response.data;
}

export async function createManualReview(payload: {
  submission_type: 'quiz_attempt' | 'assignment_submission';
  submission_id: string;
  reviewer_profile_id?: string | null;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/grading/records/manual-reviews/', payload);
  return response.data;
}

export async function completeManualReview(
  reviewId: string,
  payload: { score: number; feedback?: string | null }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/grading/manual-reviews/${reviewId}/complete/`, payload);
  return response.data;
}

export async function overrideGrade(
  gradeRecordId: string,
  payload: { score: number; max_score?: number; change_reason: string }
): Promise<GradeRecord> {
  const response = await apiClient.post<GradeRecord>(
    `/grading/records/${gradeRecordId}/override/`,
    payload
  );
  return response.data;
}

export async function publishGrade(
  gradeRecordId: string,
  payload: { published_feedback?: string | null }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/grading/records/${gradeRecordId}/publish/`, payload);
  return response.data;
}

export async function listPublishedResults(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/grading/results/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function listCertificates(params?: QueryParams): Promise<ListResponse<Certificate>> {
  const response = await apiClient.get<ListResponse<Certificate>>('/grading/certificates/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function evaluateCertificateEligibility(payload: {
  student_profile_id: string;
  course_id: string;
  certificate_asset_id?: string | null;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>(
    '/grading/certificates/eligibility/evaluate/',
    payload
  );
  return response.data;
}

export async function updateCertificateAsset(
  certificateId: string,
  payload: { certificate_asset_id?: string | null }
): Promise<Certificate> {
  const response = await apiClient.patch<Certificate>(`/grading/certificates/${certificateId}/`, payload);
  return response.data;
}

export async function revokeCertificate(certificateId: string): Promise<Certificate> {
  const response = await apiClient.post<Certificate>(`/grading/certificates/${certificateId}/revoke/`, {});
  return response.data;
}
