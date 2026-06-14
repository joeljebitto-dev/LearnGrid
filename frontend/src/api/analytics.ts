import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export async function searchResources(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/analytics/search/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function searchResourceType(
  resourceType: 'courses' | 'users' | 'enrollments' | 'assessments' | 'submissions',
  params?: QueryParams
): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>(`/analytics/search/${resourceType}/`, {
    params: cleanParams(params)
  });
  return response.data;
}

export async function listReportSnapshots(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/analytics/reports/snapshots/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function createReportSnapshot(payload: {
  institution_id?: string | null;
  report_type: string;
  parameters?: Record<string, unknown>;
  result_payload?: Record<string, unknown>;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/analytics/reports/snapshots/', payload);
  return response.data;
}

export async function generateReport(payload: {
  institution_id?: string | null;
  report_type: string;
  parameters?: Record<string, unknown>;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/analytics/reports/generate/', payload);
  return response.data;
}

export async function listDashboardAggregates(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/analytics/dashboards/aggregates/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function listUsageMetrics(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/analytics/usage-metrics/', {
    params: cleanParams(params)
  });
  return response.data;
}
