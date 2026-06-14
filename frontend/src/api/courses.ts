import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type Course = Entity & {
  institution_id?: string;
  owner_profile_id?: string;
  description?: string | null;
  difficulty_level?: string | null;
  slug?: string;
  categories?: Entity[];
  tags?: Entity[];
  prerequisite_course_ids?: string[];
  learning_outcomes?: Entity[];
};

export type CourseStructure = Course & {
  modules?: Array<
    Entity & {
      lessons?: Array<
        Entity & {
          summary?: string | null;
          content_asset_id?: string | null;
          topics?: Array<Entity & { content_asset_id?: string | null }>;
        }
      >;
    }
  >;
};

export type CoursePayload = {
  institution_id: string;
  owner_profile_id: string;
  title: string;
  slug?: string | null;
  description?: string | null;
  difficulty_level?: string | null;
  thumbnail_asset_id?: string | null;
  category_ids?: string[];
  tag_ids?: string[];
  prerequisite_course_ids?: string[];
  learning_outcomes?: Array<{ description: string; position?: number }>;
};

export async function listCourses(params?: QueryParams): Promise<ListResponse<Course>> {
  const response = await apiClient.get<ListResponse<Course>>('/courses/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function getCourse(courseId: string): Promise<Course> {
  const response = await apiClient.get<Course>(`/courses/${courseId}/`);
  return response.data;
}

export async function createCourse(payload: CoursePayload): Promise<Course> {
  const response = await apiClient.post<Course>('/courses/', payload);
  return response.data;
}

export async function updateCourse(courseId: string, payload: Partial<CoursePayload>): Promise<Course> {
  const response = await apiClient.patch<Course>(`/courses/${courseId}/`, payload);
  return response.data;
}

export async function publishCourse(courseId: string): Promise<Course> {
  const response = await apiClient.post<Course>(`/courses/${courseId}/publish/`, {});
  return response.data;
}

export async function archiveCourse(courseId: string): Promise<Course> {
  const response = await apiClient.post<Course>(`/courses/${courseId}/archive/`, {});
  return response.data;
}

export async function deleteCourse(courseId: string): Promise<Course> {
  const response = await apiClient.delete<Course>(`/courses/${courseId}/`);
  return response.data;
}

export async function getCourseStructure(courseId: string): Promise<CourseStructure> {
  const response = await apiClient.get<CourseStructure>(`/courses/${courseId}/structure/`);
  return response.data;
}

export async function listCategories(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/courses/categories/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function listTags(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/courses/tags/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createModule(
  courseId: string,
  payload: { title: string; description?: string | null; position?: number }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/courses/${courseId}/modules/`, payload);
  return response.data;
}

export async function createLesson(
  moduleId: string,
  payload: {
    title: string;
    summary?: string | null;
    position?: number;
    content_asset_id?: string | null;
  }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/courses/modules/${moduleId}/lessons/`, payload);
  return response.data;
}

export async function publishLesson(lessonId: string): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/courses/lessons/${lessonId}/publish/`, {});
  return response.data;
}

export async function createTopic(
  lessonId: string,
  payload: { title: string; position?: number; content_asset_id?: string | null }
): Promise<Entity> {
  const response = await apiClient.post<Entity>(`/courses/lessons/${lessonId}/topics/`, payload);
  return response.data;
}
