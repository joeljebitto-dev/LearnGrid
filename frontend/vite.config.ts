import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/auth': 'http://127.0.0.1:8001',
      '/api/users': 'http://127.0.0.1:8002',
      '/api/analytics': 'http://127.0.0.1:8010'
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts'
  }
});
