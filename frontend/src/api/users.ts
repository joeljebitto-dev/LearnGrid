import { apiClient } from './client';
import type { UserProfile } from './auth';
import { cleanParams, type PaginatedResponse, type QueryParams } from './types';

export type ProfileType = 'student' | 'instructor' | 'admin';
export type UserProfileStatus = 'active' | 'inactive' | 'deactivated';
export type InstitutionStatus = 'active' | 'suspended' | 'archived';

export type Institution = {
  id: string;
  name: string;
  code: string;
  status: InstitutionStatus;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type InstitutionListParams = QueryParams & {
  q?: string;
  status?: InstitutionStatus;
  sort?: string;
  page?: number;
  page_size?: number;
};

export type InstitutionPayload = {
  name: string;
  code: string;
  status?: InstitutionStatus;
};

export type UserProfileListParams = QueryParams & {
  institution_id?: string | null;
  q?: string;
  profile_type?: ProfileType;
  status?: UserProfileStatus;
  department_id?: string;
  batch_id?: string;
  sort?: string;
  page?: number;
  page_size?: number;
};

export type CreateUserProfilePayload = {
  email: string;
  phone?: string | null;
  temporary_password: string;
  profile_type: ProfileType;
  role_code?: string | null;
  institution_id?: string | null;
  first_name: string;
  last_name: string;
  display_name?: string | null;
  student?: {
    student_number: string;
    batch_id?: string | null;
    department_id?: string | null;
    guardian_profile_id?: string | null;
  };
  instructor?: {
    employee_number?: string | null;
    department_id?: string | null;
    title?: string | null;
    bio?: string | null;
  };
  admin?: {
    admin_type: 'super_admin' | 'institution_admin';
    department_id?: string | null;
  };
};

export type UpdateUserProfilePayload = {
  email?: string;
  phone?: string | null;
  first_name?: string;
  last_name?: string;
  display_name?: string | null;
  avatar_url?: string | null;
  status?: UserProfileStatus;
  metadata?: Record<string, unknown>;
  student?: {
    student_number?: string;
    batch_id?: string | null;
    department_id?: string | null;
    guardian_profile_id?: string | null;
  };
  instructor?: {
    employee_number?: string | null;
    department_id?: string | null;
    title?: string | null;
    bio?: string | null;
  };
  admin?: {
    admin_type?: 'super_admin' | 'institution_admin';
    department_id?: string | null;
  };
};

export async function listUserProfiles(
  params: UserProfileListParams = {}
): Promise<PaginatedResponse<UserProfile>> {
  const response = await apiClient.get<PaginatedResponse<UserProfile>>('/users/profiles/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createUserProfile(payload: CreateUserProfilePayload): Promise<UserProfile> {
  const response = await apiClient.post<UserProfile>('/users/profiles/', payload);
  return response.data;
}

export async function getUserProfile(profileId: string): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>(`/users/profiles/${profileId}/`);
  return response.data;
}

export async function updateUserProfile(
  profileId: string,
  payload: UpdateUserProfilePayload
): Promise<UserProfile> {
  const response = await apiClient.patch<UserProfile>(`/users/profiles/${profileId}/`, payload);
  return response.data;
}

export async function deactivateUserProfile(profileId: string): Promise<UserProfile> {
  const response = await apiClient.post<UserProfile>(`/users/profiles/${profileId}/deactivate/`, {});
  return response.data;
}

export async function listInstitutions(
  params: InstitutionListParams = {}
): Promise<PaginatedResponse<Institution>> {
  const response = await apiClient.get<PaginatedResponse<Institution>>('/users/institutions/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createInstitution(payload: InstitutionPayload): Promise<Institution> {
  const response = await apiClient.post<Institution>('/users/institutions/', payload);
  return response.data;
}

export async function updateInstitution(
  institutionId: string,
  payload: InstitutionPayload
): Promise<Institution> {
  const response = await apiClient.patch<Institution>(`/users/institutions/${institutionId}/`, payload);
  return response.data;
}

export async function archiveInstitution(institutionId: string): Promise<Institution> {
  const response = await apiClient.delete<Institution>(`/users/institutions/${institutionId}/`);
  return response.data;
}
