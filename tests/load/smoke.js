import { sleep } from 'k6';
import { get, login, post } from './common.js';

export const options = {
  vus: Number(__ENV.LOAD_VUS || 1),
  duration: __ENV.LOAD_DURATION || '10s',
  thresholds: {
    checks: ['rate>0.95'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function () {
  const studentToken = login('student');
  get('/analytics/dashboards/student/', studentToken, 'student dashboard');
  get('/courses/', studentToken, 'course listing');
  get('/content/assets/', studentToken, 'lesson content access');
  post('/assessments/attempts/00000000-0000-0000-0000-000000000000/submit/', studentToken, {}, 'quiz submission');
  get('/notifications/', studentToken, 'notifications');
  sleep(1);
}
