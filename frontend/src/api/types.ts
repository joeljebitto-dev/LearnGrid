export type Entity = Record<string, unknown> & {
  id: string;
  title?: string | null;
  name?: string | null;
  status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type ListResponse<T> = PaginatedResponse<T> | T[];

export type QueryParams = Record<
  string,
  string | number | boolean | null | undefined
>;

export function toList<T>(response: ListResponse<T> | null | undefined): T[] {
  if (!response) {
    return [];
  }
  return Array.isArray(response) ? response : response.results;
}

export function resultCount<T>(response: ListResponse<T> | null | undefined): number {
  if (!response) {
    return 0;
  }
  return Array.isArray(response) ? response.length : response.count;
}

export function cleanParams(params: QueryParams = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== '' && value !== null && value !== undefined)
  );
}

export function apiErrorMessage(error: unknown, fallback = 'The request failed.') {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    error.response &&
    typeof error.response === 'object' &&
    'data' in error.response
  ) {
    const data = error.response.data;
    if (data && typeof data === 'object') {
      if ('detail' in data) {
        return String(data.detail);
      }
      const firstEntry = Object.entries(data)[0];
      if (firstEntry) {
        const [key, value] = firstEntry;
        return `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`;
      }
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}
