import { apiClient } from './client';
import type { UserProfile } from './auth';

export type ProfileType = 'student' | 'instructor' | 'admin';

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

export async function createUserProfile(payload: CreateUserProfilePayload): Promise<UserProfile> {
  const response = await apiClient.post<UserProfile>('/users/profiles/', payload);
  return response.data;
}
