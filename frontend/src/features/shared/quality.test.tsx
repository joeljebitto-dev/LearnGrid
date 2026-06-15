import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import { dispatchNetworkError, dispatchSessionExpired } from '../../api/client';
import { FrontendQualityShell, RouteErrorBoundary, useUnsavedChangesWarning } from './quality';

function ThrowingRoute(): ReactElement {
  throw new Error('Route failed');
}

function UnsavedChangesProbe({ enabled }: { enabled: boolean }) {
  useUnsavedChangesWarning(enabled, 'Unsaved probe');
  return <div>Probe</div>;
}

beforeEach(() => {
  window.localStorage.clear();
});

test('quality shell renders skip link and session expiry message', async () => {
  render(
    <MemoryRouter>
      <FrontendQualityShell>
        <main id="main-content">Dashboard</main>
      </FrontendQualityShell>
    </MemoryRouter>
  );

  expect(screen.getByRole('link', { name: /skip to main content/i })).toHaveAttribute(
    'href',
    '#main-content'
  );

  await act(async () => {
    dispatchSessionExpired();
  });
  expect((await screen.findAllByText(/session expired/i)).length).toBeGreaterThan(0);
  expect(screen.getByRole('link', { name: /sign in again/i })).toHaveAttribute('href', '/login');
});

test('quality shell displays dismissible network errors', async () => {
  render(
    <MemoryRouter>
      <FrontendQualityShell>
        <main id="main-content">Dashboard</main>
      </FrontendQualityShell>
    </MemoryRouter>
  );

  await act(async () => {
    dispatchNetworkError('Backend unavailable');
  });
  expect((await screen.findAllByText(/backend unavailable/i)).length).toBeGreaterThan(0);

  await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));
  expect(screen.queryByText(/backend unavailable/i)).not.toBeInTheDocument();
});

test('route error boundary reports controlled retry state', () => {
  const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
  render(
    <MemoryRouter>
      <RouteErrorBoundary route="/broken">
        <ThrowingRoute />
      </RouteErrorBoundary>
    </MemoryRouter>
  );

  expect(screen.getByRole('alert')).toHaveTextContent(/this page could not be rendered/i);
  expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  spy.mockRestore();
});

test('unsaved changes hook registers beforeunload protection', () => {
  render(<UnsavedChangesProbe enabled />);
  const event = new Event('beforeunload', { cancelable: true }) as BeforeUnloadEvent;

  window.dispatchEvent(event);

  expect(event.defaultPrevented).toBe(true);
});
