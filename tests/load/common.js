import http from 'k6/http';
import { check, sleep } from 'k6';

export const baseUrl = (__ENV.LOAD_BASE_URL || '').replace(/\/$/, '');
export const apiBaseUrl = `${baseUrl}/api`;
export const offlineSmoke = !baseUrl;

export function credentials(role) {
  const prefix = `LOAD_${role.toUpperCase()}`;
  return {
    email: __ENV[`${prefix}_EMAIL`] || '',
    password: __ENV[`${prefix}_PASSWORD`] || '',
  };
}

export function login(role = 'student') {
  if (offlineSmoke) {
    check({ ready: true }, { 'offline load smoke initialized': (value) => value.ready });
    return null;
  }
  const creds = credentials(role);
  if (!creds.email || !creds.password) {
    check({ skipped: true }, { [`${role} credentials optional`]: (value) => value.skipped });
    return null;
  }
  const response = http.post(
    `${apiBaseUrl}/auth/token/issue/`,
    JSON.stringify(creds),
    { headers: { 'Content-Type': 'application/json' } },
  );
  check(response, { [`${role} login accepted`]: (res) => [200, 201].includes(res.status) });
  return response.status < 300 ? response.json('access') : null;
}

export function get(path, token, label) {
  if (offlineSmoke) {
    check({ ready: true }, { [`${label} offline scenario registered`]: (value) => value.ready });
    sleep(0.1);
    return;
  }
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = http.get(`${apiBaseUrl}${path}`, { headers });
  check(response, { [`${label} responded`]: (res) => res.status < 500 });
}

export function post(path, token, body, label) {
  if (offlineSmoke) {
    check({ ready: true }, { [`${label} offline scenario registered`]: (value) => value.ready });
    sleep(0.1);
    return;
  }
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = http.post(`${apiBaseUrl}${path}`, JSON.stringify(body), { headers });
  check(response, { [`${label} responded`]: (res) => res.status < 500 });
}
