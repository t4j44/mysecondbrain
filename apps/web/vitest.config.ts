import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react() as any],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    globals: true,
    exclude: ['e2e/**', 'node_modules/**'],
    env: {
      NEXT_PUBLIC_SUPABASE_URL: 'https://mock.supabase.co',
      NEXT_PUBLIC_SUPABASE_ANON_KEY: 'mock-anon-key-for-vitest-only',
      NEXT_PUBLIC_API_BASE_URL: 'http://localhost:8000/api/v1',
    },
  },
});
