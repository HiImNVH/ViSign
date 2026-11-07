// apps/web/vite.config.ts
// Cau hinh Vite dev/build va Vitest cho frontend ViSign.
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Proxy /api ve backend local de frontend goi cung origin khi dev
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    // CP1 chi dung khung test; test component dau tien den tu T031
    passWithNoTests: true,
  },
});
