import { apiClient } from './client';
import { cleanParams, type Entity, type ListResponse, type QueryParams } from './types';

export type NotificationItem = Entity & {
  recipient_profile_id?: string;
  event_type?: string;
  title?: string;
  body?: string;
  read_at?: string | null;
};

export async function listNotifications(params?: QueryParams): Promise<ListResponse<NotificationItem>> {
  const response = await apiClient.get<ListResponse<NotificationItem>>('/notifications/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function markNotificationRead(notificationId: string): Promise<NotificationItem> {
  const response = await apiClient.post<NotificationItem>(`/notifications/${notificationId}/read/`, {});
  return response.data;
}

export async function markNotificationUnread(notificationId: string): Promise<NotificationItem> {
  const response = await apiClient.post<NotificationItem>(`/notifications/${notificationId}/unread/`, {});
  return response.data;
}

export async function markAllNotificationsRead(): Promise<Record<string, unknown>> {
  const response = await apiClient.post<Record<string, unknown>>('/notifications/read-all/', {});
  return response.data;
}

export async function listNotificationPreferences(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/notifications/preferences/', {
    params: cleanParams(params)
  });
  return response.data;
}

export async function upsertNotificationPreference(payload: {
  profile_id?: string;
  event_type: string;
  channel: string;
  enabled: boolean;
}): Promise<Entity> {
  const response = await apiClient.post<Entity>('/notifications/preferences/', payload);
  return response.data;
}

export async function listNotificationTemplates(params?: QueryParams): Promise<ListResponse<Entity>> {
  const response = await apiClient.get<ListResponse<Entity>>('/notifications/templates/', {
    params: cleanParams(params)
  });
  return response.data;
}
