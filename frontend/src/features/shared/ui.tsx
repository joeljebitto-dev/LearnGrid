/* eslint-disable react-refresh/only-export-components */
import {
  Children,
  cloneElement,
  isValidElement,
  useEffect,
  useRef,
  type ReactElement,
  type ReactNode,
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  SelectHTMLAttributes,
  TableHTMLAttributes,
  TextareaHTMLAttributes
} from 'react';

import { apiErrorMessage, resultCount, toList, type Entity, type ListResponse } from '../../api/types';

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

const focusClass = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600';
const controlClass =
  'mt-2 w-full rounded-control border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500';

export const fieldClass = controlClass;
export const buttonClass =
  'inline-flex items-center justify-center gap-2 rounded-control bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-400 disabled:text-white';
export const secondaryButtonClass =
  'inline-flex items-center justify-center gap-2 rounded-control border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500';
export const dangerButtonClass =
  'inline-flex items-center justify-center gap-2 rounded-control bg-rose-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600 disabled:cursor-not-allowed disabled:bg-slate-400';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive' | 'link';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

const buttonVariants: Record<ButtonVariant, string> = {
  primary: buttonClass,
  secondary: secondaryButtonClass,
  ghost:
    'inline-flex items-center justify-center gap-2 rounded-control px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:text-slate-400',
  destructive: dangerButtonClass,
  link:
    'inline-flex items-center justify-center gap-2 rounded-control text-sm font-semibold text-emerald-700 underline-offset-4 transition hover:text-emerald-800 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:text-slate-400'
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: '',
  lg: 'px-5 py-2.5 text-base',
  icon: 'h-9 w-9 p-0'
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingLabel = 'Working',
  disabledReason,
  className,
  disabled,
  type = 'button',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  loadingLabel?: string;
  disabledReason?: string;
}) {
  const isDisabled = disabled || loading || Boolean(disabledReason);
  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        className={cx(buttonVariants[variant], buttonSizes[size], className)}
        disabled={isDisabled}
        type={type}
        aria-busy={loading || undefined}
        aria-live={loading ? 'polite' : undefined}
        aria-describedby={disabledReason ? `${props.id ?? 'button'}-disabled-reason` : undefined}
        {...props}
      >
        {loading ? <span aria-hidden="true" className="h-2 w-2 rounded-full bg-current" /> : null}
        {loading ? loadingLabel : children}
      </button>
      {disabledReason ? (
        <span
          id={`${props.id ?? 'button'}-disabled-reason`}
          className="max-w-xs text-xs text-slate-500"
        >
          {disabledReason}
        </span>
      ) : null}
    </span>
  );
}

export function FormField({
  label,
  htmlFor,
  helpText,
  error,
  required,
  children
}: {
  label: string;
  htmlFor: string;
  helpText?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
}) {
  const helpId = helpText ? `${htmlFor}-help` : undefined;
  const errorId = error ? `${htmlFor}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined;
  const enhancedChildren = Children.map(children, (child) => {
    if (!isValidElement(child)) {
      return child;
    }
    const element = child as ReactElement<Record<string, unknown>>;
    return cloneElement(element, {
      'aria-describedby': describedBy ?? element.props['aria-describedby'],
      'aria-invalid': error ? true : element.props['aria-invalid']
    });
  });

  return (
    <div className="block text-sm font-medium text-slate-700">
      <label htmlFor={htmlFor}>
        {label}
        {required ? <span className="ml-1 text-rose-700" aria-label="required">*</span> : null}
      </label>
      {helpText ? <p id={helpId} className="mt-1 text-xs font-normal text-slate-500">{helpText}</p> : null}
      {enhancedChildren}
      {error ? (
        <p id={errorId} className="mt-1 text-xs font-medium text-rose-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function Field(props: {
  label: string;
  htmlFor: string;
  helpText?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
}) {
  return <FormField {...props} />;
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cx(controlClass, className)} {...props} />;
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cx(controlClass, className)} {...props}>
      {children}
    </select>
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cx(controlClass, className)} {...props} />;
}

export function CheckboxField({
  label,
  helpText,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; helpText?: string }) {
  return (
    <label className={cx('flex gap-3 rounded-panel border border-slate-200 bg-white p-3 text-sm', className)}>
      <input
        className={cx('mt-0.5 h-4 w-4 rounded border-slate-300 text-emerald-700', focusClass)}
        type="checkbox"
        {...props}
      />
      <span>
        <span className="font-medium text-slate-900">{label}</span>
        {helpText ? <span className="mt-1 block text-xs text-slate-500">{helpText}</span> : null}
      </span>
    </label>
  );
}

export function RadioField({
  label,
  helpText,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; helpText?: string }) {
  return (
    <label className={cx('flex gap-3 rounded-panel border border-slate-200 bg-white p-3 text-sm', className)}>
      <input
        className={cx('mt-0.5 h-4 w-4 border-slate-300 text-emerald-700', focusClass)}
        type="radio"
        {...props}
      />
      <span>
        <span className="font-medium text-slate-900">{label}</span>
        {helpText ? <span className="mt-1 block text-xs text-slate-500">{helpText}</span> : null}
      </span>
    </label>
  );
}

export function DateTimeField({
  label,
  htmlFor,
  type = 'date',
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; htmlFor: string; type?: 'date' | 'time' | 'datetime-local' }) {
  return (
    <FormField label={label} htmlFor={htmlFor}>
      <Input id={htmlFor} type={type} {...props} />
    </FormField>
  );
}

export function PageHeader({
  title,
  description,
  eyebrow,
  breadcrumbs,
  children
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  children?: ReactNode;
}) {
  return (
    <header className="mb-6">
      {breadcrumbs?.length ? <Breadcrumbs items={breadcrumbs} className="mb-3" /> : null}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          {eyebrow ? (
            <p className="text-xs font-semibold uppercase tracking-normal text-emerald-700">{eyebrow}</p>
          ) : null}
          <h2 className="text-page-title text-slate-950">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p> : null}
        </div>
        {children ? <div className="flex flex-wrap gap-2">{children}</div> : null}
      </div>
    </header>
  );
}

export function Section({
  title,
  description,
  children,
  actions,
  className
}: {
  title?: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx('space-y-4', className)}>
      {title || description || actions ? (
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            {title ? <h3 className="text-section-title text-slate-950">{title}</h3> : null}
            {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function Panel({
  title,
  description,
  children,
  actions,
  className
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx('rounded-panel border border-slate-200 bg-white p-5 shadow-panel', className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-section-title text-slate-950">{title}</h3>
          {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function Card({
  children,
  className,
  interactive = false
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <article
      className={cx(
        'rounded-panel border border-slate-200 bg-white p-5 shadow-panel',
        interactive && 'transition hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md',
        className
      )}
    >
      {children}
    </article>
  );
}

export function Toolbar({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cx('flex flex-wrap items-end gap-3 rounded-panel border border-slate-200 bg-white p-4 shadow-panel', className)}>
      {children}
    </div>
  );
}

export function Divider({ label }: { label?: string }) {
  if (!label) {
    return <hr className="border-slate-200" />;
  }
  return (
    <div className="flex items-center gap-3 text-xs font-semibold uppercase text-slate-500">
      <span className="h-px flex-1 bg-slate-200" />
      {label}
      <span className="h-px flex-1 bg-slate-200" />
    </div>
  );
}

const badgeToneClass: Record<string, string> = {
  success: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  warning: 'bg-amber-50 text-amber-800 ring-amber-200',
  error: 'bg-rose-50 text-rose-800 ring-rose-200',
  info: 'bg-blue-50 text-blue-800 ring-blue-200',
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  draft: 'bg-violet-50 text-violet-800 ring-violet-200',
  published: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  archived: 'bg-slate-100 text-slate-700 ring-slate-200',
  completed: 'bg-teal-50 text-teal-800 ring-teal-200',
  pending: 'bg-amber-50 text-amber-800 ring-amber-200',
  failed: 'bg-rose-50 text-rose-800 ring-rose-200',
  active: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  unread: 'bg-blue-50 text-blue-800 ring-blue-200',
  revoked: 'bg-rose-50 text-rose-800 ring-rose-200'
};

const toastToneClass: Record<'success' | 'warning' | 'error' | 'info', string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  error: 'border-rose-200 bg-rose-50 text-rose-900',
  info: 'border-blue-200 bg-blue-50 text-blue-900'
};

function statusTone(value?: string | null) {
  if (!value) {
    return 'neutral';
  }
  const normalized = value.toLowerCase();
  if (normalized.includes('fail') || normalized.includes('denied') || normalized.includes('error')) {
    return 'error';
  }
  if (normalized.includes('pending') || normalized.includes('draft') || normalized.includes('late')) {
    return normalized.includes('draft') ? 'draft' : 'warning';
  }
  if (normalized.includes('publish') || normalized.includes('active') || normalized.includes('complete') || normalized.includes('valid')) {
    return normalized.includes('complete') ? 'completed' : 'success';
  }
  if (normalized.includes('archive') || normalized.includes('revoke') || normalized.includes('closed')) {
    return normalized.includes('revoke') ? 'revoked' : 'archived';
  }
  return normalized in badgeToneClass ? normalized : 'neutral';
}

export function Badge({
  children,
  tone = 'neutral',
  className
}: {
  children: ReactNode;
  tone?: keyof typeof badgeToneClass | string;
  className?: string;
}) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-control px-2 py-1 text-xs font-semibold ring-1 ring-inset',
        badgeToneClass[tone] ?? badgeToneClass.neutral,
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusChip({ value }: { value?: string | null }) {
  const label = value || 'unknown';
  return <Badge tone={statusTone(label)}>{label.replaceAll('_', ' ')}</Badge>;
}

export function StatusBadge({ value }: { value?: string | null }) {
  return <StatusChip value={value} />;
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
      {children}
    </span>
  );
}

export function Avatar({ name, src, size = 'md' }: { name: string; src?: string | null; size?: 'sm' | 'md' | 'lg' }) {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  const sizeClass = size === 'lg' ? 'h-12 w-12 text-base' : size === 'sm' ? 'h-8 w-8 text-xs' : 'h-10 w-10 text-sm';
  if (src) {
    return <img alt="" className={cx('rounded-full object-cover', sizeClass)} src={src} />;
  }
  return (
    <span className={cx('inline-flex items-center justify-center rounded-full bg-emerald-100 font-semibold text-emerald-800', sizeClass)}>
      {initials || 'LG'}
    </span>
  );
}

export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-max max-w-xs -translate-x-1/2 rounded bg-slate-950 px-2 py-1 text-xs font-medium text-white shadow-lg group-hover:block group-focus-within:block">
        {label}
      </span>
    </span>
  );
}

export function Toast({
  title,
  message,
  tone = 'info'
}: {
  title: string;
  message?: string;
  tone?: 'success' | 'warning' | 'error' | 'info';
}) {
  return (
    <div className={cx('rounded-panel border p-4 shadow-panel', toastToneClass[tone])}>
      <p className="font-semibold">{title}</p>
      {message ? <p className="mt-1 text-sm">{message}</p> : null}
    </div>
  );
}

export function Modal({
  title,
  open,
  children,
  footer,
  onClose
}: {
  title: string;
  open: boolean;
  children: ReactNode;
  footer?: ReactNode;
  onClose?: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const previousActive = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const focusable = panelRef.current?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusable?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onCloseRef.current?.();
      }
      if (event.key !== 'Tab' || !panelRef.current) {
        return;
      }
      const elements = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
      );
      if (!elements.length) {
        return;
      }
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousActive?.focus();
    };
  }, [open]);

  if (!open) {
    return null;
  }
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div ref={panelRef} className="w-full max-w-lg rounded-panel bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
        <div className="mt-4">{children}</div>
        {footer ? <div className="mt-5 flex flex-wrap justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  );
}

export function Drawer({
  title,
  open,
  children,
  onClose
}: {
  title: string;
  open: boolean;
  children: ReactNode;
  onClose?: () => void;
}) {
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const previousActive = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    panelRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose?.();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousActive?.focus();
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }
  return (
    <aside
      ref={panelRef}
      className="fixed inset-y-0 right-0 z-40 w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-xl"
      aria-label={title}
      tabIndex={-1}
    >
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      <div className="mt-4">{children}</div>
    </aside>
  );
}

export function Tabs({
  items,
  value,
  onChange
}: {
  items: Array<{ key: string; label: string; disabled?: boolean }>;
  value: string;
  onChange: (key: string) => void;
}) {
  return (
    <div className="inline-flex rounded-panel border border-slate-200 bg-white p-1 shadow-panel" role="tablist">
      {items.map((item) => (
        <button
          key={item.key}
          className={cx(
            'rounded-control px-3 py-1.5 text-sm font-medium transition',
            item.key === value ? 'bg-emerald-700 text-white' : 'text-slate-700 hover:bg-slate-100',
            item.disabled && 'cursor-not-allowed opacity-50'
          )}
          disabled={item.disabled}
          role="tab"
          type="button"
          aria-selected={item.key === value}
          onClick={() => onChange(item.key)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

export function Breadcrumbs({
  items,
  className
}: {
  items: Array<{ label: string; href?: string }>;
  className?: string;
}) {
  return (
    <nav className={cx('flex flex-wrap items-center gap-2 text-xs text-slate-500', className)} aria-label="Breadcrumb">
      {items.map((item, index) => (
        <span className="inline-flex items-center gap-2" key={`${item.label}-${index}`}>
          {index > 0 ? <span aria-hidden="true">/</span> : null}
          {item.href ? (
            <a className="font-medium text-emerald-700 hover:underline" href={item.href}>
              {item.label}
            </a>
          ) : (
            <span className="font-medium text-slate-700">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

export function PaginationControls({
  page,
  hasNext = true,
  onPrevious,
  onNext
}: {
  page: number;
  hasNext?: boolean;
  onPrevious: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <Button variant="secondary" size="sm" disabled={page <= 1} onClick={onPrevious}>
        Previous
      </Button>
      <span className="min-w-16 text-center text-sm font-medium text-slate-600">Page {page}</span>
      <Button variant="secondary" size="sm" disabled={!hasNext} onClick={onNext}>
        Next
      </Button>
    </div>
  );
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  emptyMessage = 'No records found.',
  caption,
  className,
  ...props
}: TableHTMLAttributes<HTMLTableElement> & {
  columns: Array<{ key: string; header: string; render?: (row: T) => ReactNode }>;
  rows: T[];
  emptyMessage?: string;
  caption?: string;
}) {
  if (!rows.length) {
    return <EmptyState message={emptyMessage} />;
  }
  return (
    <div className="overflow-x-auto rounded-panel border border-slate-200 bg-white">
      <table className={cx('min-w-full divide-y divide-slate-200 text-sm', className)} {...props}>
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
          <tr>
            {columns.map((column) => (
              <th className="px-4 py-3" key={column.key} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, index) => (
            <tr key={String(row.id ?? index)}>
              {columns.map((column) => (
                <td className="px-4 py-3 text-slate-700" key={column.key}>
                  {column.render ? column.render(row) : String(row[column.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SkeletonBlock({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-3 rounded-panel border border-slate-200 bg-white p-5 shadow-panel" aria-label="Loading skeleton" role="status">
      {Array.from({ length: rows }).map((_, index) => (
        <div className={cx('h-4 rounded bg-slate-200', index === rows - 1 ? 'w-2/3' : 'w-full')} key={index} />
      ))}
    </div>
  );
}

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex min-h-[280px] items-center justify-center rounded-panel border border-slate-200 bg-white text-sm font-medium text-slate-600 shadow-panel" aria-live="polite" role="status">
      <span className="mr-2 h-2 w-2 rounded-full bg-emerald-700" aria-hidden="true" />
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
    <div className="rounded-panel border border-rose-200 bg-rose-50 p-5 shadow-panel" role="alert">
      <h2 className="text-base font-semibold text-rose-950">{title}</h2>
      <p className="mt-1 text-sm text-rose-800">
        {apiErrorMessage(error, 'The service denied the request or could not be reached.')}
      </p>
      {onRetry ? (
        <Button className="mt-4" variant="secondary" type="button" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  message = 'No data yet.',
  action
}: {
  message?: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-panel border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-600">
      <p>{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function PermissionDeniedState({
  message = 'You do not have permission to view this workflow.'
}: {
  message?: string;
}) {
  return (
    <div className="rounded-panel border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900" role="alert">
      <h2 className="font-semibold">No access</h2>
      <p className="mt-1">{message}</p>
    </div>
  );
}

export function DisabledWithReason({ reason }: { reason: string }) {
  return <p className="text-xs font-medium text-slate-500">{reason}</p>;
}

export function MetricCard({
  label,
  value,
  hint,
  tone = 'neutral'
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: string;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
          <div className="mt-2 text-2xl font-semibold text-slate-950">{value}</div>
        </div>
        <Badge tone={tone}>{tone}</Badge>
      </div>
      {hint ? <p className="mt-2 text-xs text-slate-500">{hint}</p> : null}
    </Card>
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
        <MetricCard key={key} label={key.replaceAll('_', ' ')} value={value} tone={value > 0 ? 'success' : 'neutral'} />
      ))}
    </div>
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
    <Panel title={title} actions={<span className="text-sm text-slate-500">{resultCount(response)} total</span>}>
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
    <pre className="max-h-64 overflow-auto rounded-panel bg-slate-950 p-3 text-xs text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
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
    <section className="rounded-panel border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-section-title text-slate-950">{title}</h3>
        <Badge>{items.length}</Badge>
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
