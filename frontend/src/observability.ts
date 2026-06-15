import * as Sentry from '@sentry/react';

type FrontendContext = Record<string, string | number | boolean | null | undefined>;

export function initFrontendObservability() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) {
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0
  });
}

export function addFrontendBreadcrumb(message: string, data?: FrontendContext) {
  Sentry.addBreadcrumb({
    category: 'frontend',
    level: 'info',
    message,
    data
  });
}

export function captureFrontendException(error: unknown, context?: FrontendContext) {
  Sentry.withScope((scope) => {
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        scope.setTag(key, value === undefined || value === null ? 'unknown' : String(value));
      });
    }
    Sentry.captureException(error);
  });
}
