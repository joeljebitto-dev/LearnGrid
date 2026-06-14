import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type CourseProgress = Entity & {
  student_profile_id?: string;
  course_id?: string;
  completion_percent?: string | number;
  lessons_completed?: number;
  assessments_completed?: number;
};

export async function listCourseProgress(params?: QueryParams): Promise<ListResponse<CourseProgress>> {
  const response = await apiClient.get<ListResponse<CourseProgress>>('/progress/courses/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function updateLessonProgress(payload: {
  student_profile_id: string;
  course_id: string;
  lesson_id: string;
  status?: string;
  view_increment?: number;
  total_lessons?: number;
  total_assessments?: number;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/progress/lessons/', payload);
  return response.data;
}

export async function updateVideoProgress(payload: {
  student_profile_id: string;
  content_asset_id: string;
  course_id: string;
  last_position_seconds?: number;
  duration_seconds?: number;
  percent_complete?: number;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/progress/videos/', payload);
  return response.data;
}

export async function updateAssessmentProgress(payload: {
  student_profile_id: string;
  assessment_id: string;
  course_id: string;
  status?: string;
  attempt_increment?: number;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/progress/assessments/', payload);
  return response.data;
}
