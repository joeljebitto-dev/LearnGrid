import { apiClient } from './client';

export type DashboardAggregate = {
  id: string;
  metric_date: string;
  computed_at: string;
} | null;

export type DashboardProfile = {
  id: string;
  institution_id: string | null;
  display_name: string | null;
  first_name: string;
  last_name: string;
  profile_type: string | null;
} | null;

export type StudentDashboard = {
  portal: 'student';
  profile: DashboardProfile;
  institution_id: string | null;
  aggregate: DashboardAggregate;
  active_courses: Array<Record<string, unknown>>;
  completed_lessons: Array<Record<string, unknown>>;
  pending_assessments: Array<Record<string, unknown>>;
  grades: Array<Record<string, unknown>>;
  upcoming_deadlines: Array<Record<string, unknown>>;
  summary: Record<string, number>;
};

export type InstructorDashboard = {
  portal: 'instructor';
  profile: DashboardProfile;
  institution_id: string | null;
  aggregate: DashboardAggregate;
  learner_engagement: Array<Record<string, unknown>>;
  progress_distribution: Array<Record<string, unknown>>;
  assessment_status: Array<Record<string, unknown>>;
  course_summaries: Array<Record<string, unknown>>;
  summary: Record<string, number>;
};

export type AdminDashboard = {
  portal: 'admin';
  profile: DashboardProfile;
  institution_id: string | null;
  aggregate: DashboardAggregate;
  active_users: Array<Record<string, unknown>>;
  enrollments: Array<Record<string, unknown>>;
  completion_rates: Array<Record<string, unknown>>;
  assessment_results: Array<Record<string, unknown>>;
  system_usage: Array<Record<string, unknown>>;
  summary: Record<string, number>;
};

export async function getStudentDashboard(): Promise<StudentDashboard> {
  const response = await apiClient.get<StudentDashboard>('/analytics/dashboards/student/');
  return response.data;
}

export async function getInstructorDashboard(): Promise<InstructorDashboard> {
  const response = await apiClient.get<InstructorDashboard>('/analytics/dashboards/instructor/');
  return response.data;
}

export async function getAdminDashboard(institutionId?: string | null): Promise<AdminDashboard> {
  const path = institutionId
    ? `/analytics/dashboards/admin/?institution_id=${institutionId}`
    : '/analytics/dashboards/admin/system/';
  const response = await apiClient.get<AdminDashboard>(path);
  return response.data;
}
