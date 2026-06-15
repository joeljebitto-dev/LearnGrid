import axios from 'axios';

const TOKEN_STORAGE_KEY = 'learngrid.tokens';
const SESSION_EXPIRED_EVENT = 'learngrid:session-expired';
const NETWORK_ERROR_EVENT = 'learngrid:network-error';

export type TokenPair = {
  access: string;
  refresh: string;
  access_expires_at: string;
  refresh_expires_at: string;
};

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10_000
});

export function getStoredTokens(): TokenPair | null {
  const raw = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as TokenPair;
  } catch {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    return null;
  }
}

export function storeTokens(tokens: TokenPair) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
}

export function clearStoredTokens() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function hasStoredAccessToken() {
  return Boolean(getStoredTokens()?.access);
}

export function isStoredAccessTokenExpired(now = Date.now()) {
  const tokens = getStoredTokens();
  if (!tokens?.access_expires_at) {
    return false;
  }
  return new Date(tokens.access_expires_at).getTime() <= now;
}

export function dispatchSessionExpired() {
  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
}

export function dispatchNetworkError(message = 'The network request failed.') {
  window.dispatchEvent(new CustomEvent(NETWORK_ERROR_EVENT, { detail: { message } }));
}

export function subscribeToSessionExpired(listener: () => void) {
  window.addEventListener(SESSION_EXPIRED_EVENT, listener);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
}

export function subscribeToNetworkError(listener: (message: string) => void) {
  const wrapped = (event: Event) => {
    const detail = event instanceof CustomEvent ? event.detail : null;
    listener(typeof detail?.message === 'string' ? detail.message : 'The network request failed.');
  };
  window.addEventListener(NETWORK_ERROR_EVENT, wrapped);
  return () => window.removeEventListener(NETWORK_ERROR_EVENT, wrapped);
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredTokens()?.access;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearStoredTokens();
      dispatchSessionExpired();
    }
    if (!error?.response) {
      dispatchNetworkError(error instanceof Error ? error.message : 'The service could not be reached.');
    }
    return Promise.reject(error);
  }
);
