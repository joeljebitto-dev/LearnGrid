import axios from 'axios';

const TOKEN_STORAGE_KEY = 'learngrid.tokens';

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

apiClient.interceptors.request.use((config) => {
  const token = getStoredTokens()?.access;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
