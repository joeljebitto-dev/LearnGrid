import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const proxyTargets = {
  auth: process.env.LEARNGRID_AUTH_PROXY_TARGET ?? 'http://127.0.0.1:8001',
  users: process.env.LEARNGRID_USER_PROXY_TARGET ?? 'http://127.0.0.1:8002',
  courses: process.env.LEARNGRID_COURSE_PROXY_TARGET ?? 'http://127.0.0.1:8003',
  content: process.env.LEARNGRID_CONTENT_PROXY_TARGET ?? 'http://127.0.0.1:8004',
  enrollments: process.env.LEARNGRID_ENROLLMENT_PROXY_TARGET ?? 'http://127.0.0.1:8005',
  progress: process.env.LEARNGRID_PROGRESS_PROXY_TARGET ?? 'http://127.0.0.1:8006',
  assessments: process.env.LEARNGRID_ASSESSMENT_PROXY_TARGET ?? 'http://127.0.0.1:8007',
  grading: process.env.LEARNGRID_GRADING_PROXY_TARGET ?? 'http://127.0.0.1:8008',
  notifications: process.env.LEARNGRID_NOTIFICATION_PROXY_TARGET ?? 'http://127.0.0.1:8009',
  analytics: process.env.LEARNGRID_ANALYTICS_PROXY_TARGET ?? 'http://127.0.0.1:8010'
};
const allowedHosts = (process.env.LEARNGRID_VITE_ALLOWED_HOSTS ?? 'localhost,127.0.0.1,frontend-service')
  .split(',')
  .map((host) => host.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts,
    proxy: {
      '/api/auth': proxyTargets.auth,
      '/api/users': proxyTargets.users,
      '/api/courses': proxyTargets.courses,
      '/api/content': proxyTargets.content,
      '/api/enrollments': proxyTargets.enrollments,
      '/api/progress': proxyTargets.progress,
      '/api/assessments': proxyTargets.assessments,
      '/api/grading': proxyTargets.grading,
      '/api/notifications': proxyTargets.notifications,
      '/api/analytics': proxyTargets.analytics
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    pool: 'threads',
    setupFiles: './src/test/setup.ts'
  }
});
