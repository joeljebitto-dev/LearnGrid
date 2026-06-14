/* eslint-disable react-refresh/only-export-components */
import type { ReactNode } from 'react';

import { apiErrorMessage, resultCount, toList, type Entity, type ListResponse } from '../../api/types';

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex min-h-[280px] items-center justify-center rounded border border-slate-200 bg-white text-sm font-medium text-slate-600">
      {label}
    </div>
  );
}

export function ErrorState({
  title = 'Unable to load data',
  error,
  onRetry
}: {
  title?: string;
  error?: unknown;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded border border-rose-200 bg-rose-50 p-5" role="alert">
      <h2 className="text-base font-semibold text-rose-950">{title}</h2>
      <p className="mt-1 text-sm text-rose-800">
        {apiErrorMessage(error, 'The service denied the request or could not be reached.')}
      </p>
      {onRetry ? (
        <button
          className="mt-4 rounded border border-rose-300 bg-white px-3 py-2 text-sm font-medium text-rose-900 hover:bg-rose-100"
          type="button"
          onClick={onRetry}
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ message = 'No data yet.' }: { message?: string }) {
  return (
    <div className="rounded border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-600">
      {message}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  children
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h2 className="text-2xl font-semibold text-slate-950">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-sm text-slate-600">{description}</p> : null}
      </div>
      {children}
    </div>
  );
}

export function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded border border-slate-200 bg-white p-5">
      <h3 className="text-base font-semibold text-slate-950">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function Field({
  label,
  htmlFor,
  error,
  children
}: {
  label: string;
  htmlFor: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm font-medium text-slate-700" htmlFor={htmlFor}>
      {label}
      {children}
      {error ? <span className="mt-1 block text-xs text-rose-700">{error}</span> : null}
    </label>
  );
}

export const fieldClass =
  'mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 disabled:bg-slate-100';

export const buttonClass =
  'rounded bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-400';

export const secondaryButtonClass =
  'rounded border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500';

export function StatusBadge({ value }: { value?: string | null }) {
  const label = value || 'unknown';
  return (
    <span className="inline-flex rounded bg-slate-100 px-2 py-1 text-xs font-medium capitalize text-slate-700">
      {label.replaceAll('_', ' ')}
    </span>
  );
}

export function itemTitle(item: Record<string, unknown>, fallback = 'Untitled') {
  const value =
    item.title ||
    item.name ||
    item.course_title ||
    item.display_name ||
    item.certificate_number ||
    item.event_type ||
    item.id ||
    fallback;
  return String(value);
}

export function metadataLine(item: Record<string, unknown>, keys?: string[]) {
  const entries = keys
    ? keys.map((key) => [key, item[key]] as const)
    : Object.entries(item).filter(([key]) => key !== 'id').slice(0, 4);
  return entries
    .filter(([, value]) => value !== null && value !== undefined && typeof value !== 'object')
    .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${String(value)}`)
    .join(' · ');
}

export function EntityList({
  title,
  response,
  emptyMessage,
  detailKeys,
  actions
}: {
  title: string;
  response?: ListResponse<Entity> | null;
  emptyMessage?: string;
  detailKeys?: string[];
  actions?: (item: Entity) => ReactNode;
}) {
  const items = toList(response);
  return (
    <Panel title={title}>
      <div className="mb-3 text-sm text-slate-500">{resultCount(response)} total</div>
      {items.length ? (
        <ul className="divide-y divide-slate-100">
          {items.map((item) => (
            <li className="flex flex-wrap items-center justify-between gap-3 py-3" key={item.id}>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-950">{itemTitle(item)}</span>
                  <StatusBadge value={typeof item.status === 'string' ? item.status : null} />
                </div>
                <div className="mt-1 max-w-3xl truncate text-xs text-slate-500">
                  {metadataLine(item, detailKeys)}
                </div>
              </div>
              {actions ? <div className="flex flex-wrap gap-2">{actions(item)}</div> : null}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState message={emptyMessage} />
      )}
    </Panel>
  );
}

export function JsonPreview({ value }: { value: unknown }) {
  return (
    <pre className="max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export function SummaryGrid({ summary }: { summary: Record<string, number> }) {
  const entries = Object.entries(summary);
  if (!entries.length) {
    return <EmptyState message="No summary data yet." />;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded border border-slate-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">
            {key.replaceAll('_', ' ')}
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-950">{value}</div>
        </div>
      ))}
    </div>
  );
}

export function ListBand({
  title,
  items
}: {
  title: string;
  items: Array<Record<string, unknown>>;
}) {
  return (
    <section className="rounded border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-base font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      {items.length ? (
        <ul className="mt-4 divide-y divide-slate-100">
          {items.slice(0, 6).map((item, index) => (
            <li className="py-3" key={`${title}-${index}`}>
              <div className="text-sm font-medium text-slate-900">
                {itemTitle(item, `${title} ${index + 1}`)}
              </div>
              <div className="mt-1 truncate text-xs text-slate-500">
                {metadataLine(item)}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4">
          <EmptyState message={`No ${title.toLowerCase()} yet.`} />
        </div>
      )}
    </section>
  );
}

export function parseCsv(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}
