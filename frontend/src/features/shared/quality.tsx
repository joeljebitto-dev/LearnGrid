/* eslint-disable react-refresh/only-export-components */
import type { ErrorInfo, ReactNode } from 'react';
import { Component, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import {
  isStoredAccessTokenExpired,
  subscribeToNetworkError,
  subscribeToSessionExpired
} from '../../api/client';
import { addFrontendBreadcrumb, captureFrontendException } from '../../observability';
import { Button, ErrorState, cx } from './ui';

export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
  return (
    <a
      className="sr-only z-50 rounded-control bg-slate-950 px-4 py-2 text-sm font-semibold text-white focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      href={`#${targetId}`}
    >
      Skip to main content
    </a>
  );
}

export function LiveRegion({
  message,
  politeness = 'polite'
}: {
  message?: string | null;
  politeness?: 'polite' | 'assertive';
}) {
  return (
    <div className="sr-only" aria-live={politeness} aria-atomic="true">
      {message}
    </div>
  );
}

function QualityBanner({
  tone,
  title,
  children,
  onDismiss
}: {
  tone: 'warning' | 'error' | 'info';
  title: string;
  children: ReactNode;
  onDismiss?: () => void;
}) {
  const toneClass = {
    warning: 'border-amber-200 bg-amber-50 text-amber-950',
    error: 'border-rose-200 bg-rose-50 text-rose-950',
    info: 'border-blue-200 bg-blue-50 text-blue-950'
  }[tone];
  return (
    <div className={cx('border-b px-6 py-3 text-sm', toneClass)} role="status">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
        <div>
          <span className="font-semibold">{title}</span>
          <span className="ml-2">{children}</span>
        </div>
        {onDismiss ? (
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Dismiss
          </Button>
        ) : null}
      </div>
    </div>
  );
}

type BoundaryProps = {
  route: string;
  children: ReactNode;
};

type BoundaryState = {
  error: Error | null;
};

export class RouteErrorBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    captureFrontendException(error, {
      route: this.props.route,
      componentStack: info.componentStack ? 'available' : 'missing'
    });
  }

  render() {
    if (this.state.error) {
      return (
        <main className="mx-auto max-w-3xl px-6 py-10" id="main-content">
          <ErrorState
            title="This page could not be rendered"
            error={this.state.error}
            onRetry={() => this.setState({ error: null })}
          />
        </main>
      );
    }
    return this.props.children;
  }
}

export function FrontendQualityShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [sessionExpired, setSessionExpired] = useState(() => isStoredAccessTokenExpired());
  const [networkMessage, setNetworkMessage] = useState<string | null>(null);
  const [offline, setOffline] = useState(() => typeof navigator !== 'undefined' && !navigator.onLine);

  useEffect(() => {
    addFrontendBreadcrumb('route_change', { route: location.pathname });
  }, [location.pathname]);

  useEffect(() => {
    const unsubscribeSession = subscribeToSessionExpired(() => setSessionExpired(true));
    const unsubscribeNetwork = subscribeToNetworkError((message) => setNetworkMessage(message));
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      unsubscribeSession();
      unsubscribeNetwork();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const liveMessage =
    sessionExpired
      ? 'Your session expired. Sign in again.'
      : offline
        ? 'You are offline. Some actions are disabled until the network returns.'
        : networkMessage;

  return (
    <>
      <SkipLink />
      <LiveRegion message={liveMessage} />
      {sessionExpired ? (
        <QualityBanner tone="warning" title="Session expired">
          <Link className="font-semibold text-amber-950 underline" to="/login">
            Sign in again
          </Link>
        </QualityBanner>
      ) : null}
      {offline ? (
        <QualityBanner tone="info" title="Offline">
          Network access is unavailable. Unsaved changes should be kept locally until reconnect.
        </QualityBanner>
      ) : null}
      {networkMessage && !offline ? (
        <QualityBanner tone="error" title="Network issue" onDismiss={() => setNetworkMessage(null)}>
          {networkMessage}
        </QualityBanner>
      ) : null}
      <RouteErrorBoundary key={location.pathname} route={location.pathname}>
        {children}
      </RouteErrorBoundary>
    </>
  );
}

export function useUnsavedChangesWarning(enabled: boolean, message = 'You have unsaved changes.') {
  useEffect(() => {
    if (!enabled) {
      return undefined;
    }
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = message;
      return message;
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [enabled, message]);
}
