import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type Enrollment = Entity & {
  student_profile_id?: string;
  course_id?: string;
  institution_id?: string;
};

export async function listEnrollments(params?: QueryParams): Promise<ListResponse<Enrollment>> {
  const response = await apiClient.get<ListResponse<Enrollment>>('/enrollments/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createEnrollment(payload: {
  student_profile_id: string;
  course_id: string;
  institution_id: string;
  enrolled_by_profile_id?: string | null;
  expires_at?: string | null;
}): Promise<Enrollment> {
  const response = await apiClient.post<Enrollment>('/enrollments/', payload);
  return response.data;
}

export async function transitionEnrollment(
  enrollmentId: string,
  payload: { status: string; changed_by_profile_id?: string | null; reason?: string | null }
): Promise<Enrollment> {
  const response = await apiClient.post<Enrollment>(
    `/enrollments/${enrollmentId}/transition/`,
    payload
  );
  return response.data;
}

export async function getEnrollmentHistory(enrollmentId: string): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>(
    `/enrollments/${enrollmentId}/history/`
  );
  return response.data;
}

export async function checkEnrollmentAccess(payload: {
  student_profile_id: string;
  course_id: string;
}): Promise<Record<string, unknown>> {
  const response = await apiClient.get<Record<string, unknown>>('/enrollments/access/check/', {
    params: payload
  });
  return response.data;
}

export async function listBatchEnrollments(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/enrollments/batch-enrollments/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createBatchEnrollment(payload: {
  batch_id: string;
  course_id: string;
  institution_id: string;
  requested_by_profile_id: string;
  student_profile_ids: string[];
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/enrollments/batch-enrollments/', payload);
  return response.data;
}

export async function listCohortEnrollments(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/enrollments/cohort-enrollments/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createCohortEnrollment(payload: {
  cohort_id: string;
  course_id: string;
  institution_id: string;
  requested_by_profile_id: string;
  student_profile_ids: string[];
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/enrollments/cohort-enrollments/', payload);
  return response.data;
}
