import { sleep } from 'k6';
import { get, login, post } from './common.js';

export const options = {
  vus: Number(__ENV.LOAD_VUS || 10),
  duration: __ENV.LOAD_DURATION || '2m',
  thresholds: {
    checks: ['rate>0.95'],
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<300'],
  },
};

export default function () {
  const studentToken = login('student');
  const instructorToken = login('instructor');
  const adminToken = login('admin');

  get('/analytics/dashboards/student/', studentToken, 'student dashboard');
  get('/analytics/dashboards/instructor/', instructorToken, 'instructor dashboard');
  get('/analytics/dashboards/admin/system/', adminToken, 'admin dashboard');
  get('/courses/', studentToken, 'course listing');
  get('/content/assets/', studentToken, 'lesson access');
  post('/assessments/attempts/00000000-0000-0000-0000-000000000000/submit/', studentToken, {}, 'quiz submission');
  get('/notifications/', studentToken, 'notifications');
  sleep(1);
}
