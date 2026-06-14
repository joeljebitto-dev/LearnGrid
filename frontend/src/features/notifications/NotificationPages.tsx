import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { SessionContext } from '../../api/auth';
import {
  listNotificationPreferences,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  markNotificationUnread,
  upsertNotificationPreference
} from '../../api/notifications';
import { PortalLayout } from '../layout/PortalLayout';
import {
  buttonClass,
  EntityList,
  ErrorState,
  fieldClass,
  Field,
  LoadingState,
  PageHeader,
  Panel,
  secondaryButtonClass
} from '../shared/ui';

export function NotificationCenterPage({
  context,
  activeNav = 'notifications'
}: {
  context: SessionContext;
  activeNav?: string;
}) {
  const queryClient = useQueryClient();
  const notificationsQuery = useQuery({
    queryKey: ['notifications', context.profile.id],
    queryFn: () => listNotifications({ recipient_profile_id: context.profile.id, sort: '-created_at' })
  });
  const preferencesQuery = useQuery({
    queryKey: ['notification-preferences', context.profile.id],
    queryFn: () => listNotificationPreferences({ profile_id: context.profile.id })
  });
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['notifications'] });
    await queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
  };
  const readMutation = useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate });
  const unreadMutation = useMutation({ mutationFn: markNotificationUnread, onSuccess: invalidate });
  const readAllMutation = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate });
  const preferenceMutation = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form);
      return upsertNotificationPreference({
        profile_id: context.profile.id,
        event_type: String(data.get('event_type') || ''),
        channel: String(data.get('channel') || 'in_app'),
        enabled: data.get('enabled') === 'true'
      });
    },
    onSuccess: invalidate
  });

  return (
    <PortalLayout context={context} activeNav={activeNav}>
      <PageHeader title="Notification Center" description="Review in-app notifications and manage notification preferences.">
        <button className={secondaryButtonClass} type="button" onClick={() => readAllMutation.mutate()}>
          Mark all read
        </button>
      </PageHeader>
      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div>
          {notificationsQuery.isLoading ? <LoadingState label="Loading notifications" /> : null}
          {notificationsQuery.isError ? <ErrorState error={notificationsQuery.error} onRetry={() => void notificationsQuery.refetch()} /> : null}
          {notificationsQuery.data ? (
            <EntityList
              title="Notifications"
              response={notificationsQuery.data}
              detailKeys={['event_type', 'read_at', 'created_at']}
              emptyMessage="No notifications yet."
              actions={(notification) => (
                <>
                  <button className={secondaryButtonClass} type="button" onClick={() => readMutation.mutate(notification.id)}>Read</button>
                  <button className={secondaryButtonClass} type="button" onClick={() => unreadMutation.mutate(notification.id)}>Unread</button>
                </>
              )}
            />
          ) : null}
        </div>
        <Panel title="Preference">
          <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); preferenceMutation.mutate(event.currentTarget); }}>
            <Field htmlFor="pref-event" label="Event type">
              <input id="pref-event" name="event_type" className={fieldClass} defaultValue="GradePublished" required />
            </Field>
            <Field htmlFor="pref-channel" label="Channel">
              <select id="pref-channel" name="channel" className={fieldClass}>
                <option value="in_app">In app</option>
                <option value="email">Email</option>
              </select>
            </Field>
            <Field htmlFor="pref-enabled" label="Enabled">
              <select id="pref-enabled" name="enabled" className={fieldClass}>
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </Field>
            {preferenceMutation.isError ? <ErrorState title="Preference update failed" error={preferenceMutation.error} /> : null}
            <button className={buttonClass} type="submit" disabled={preferenceMutation.isPending}>Save preference</button>
          </form>
          <div className="mt-5">
            {preferencesQuery.data ? (
              <EntityList title="Preferences" response={preferencesQuery.data} detailKeys={['event_type', 'channel', 'enabled']} />
            ) : null}
          </div>
        </Panel>
      </div>
    </PortalLayout>
  );
}
