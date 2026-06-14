import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/auth': 'http://127.0.0.1:8001',
      '/api/users': 'http://127.0.0.1:8002',
      '/api/courses': 'http://127.0.0.1:8003',
      '/api/content': 'http://127.0.0.1:8004',
      '/api/enrollments': 'http://127.0.0.1:8005',
      '/api/progress': 'http://127.0.0.1:8006',
      '/api/assessments': 'http://127.0.0.1:8007',
      '/api/grading': 'http://127.0.0.1:8008',
      '/api/notifications': 'http://127.0.0.1:8009',
      '/api/analytics': 'http://127.0.0.1:8010'
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    pool: 'threads',
    setupFiles: './src/test/setup.ts'
  }
});
