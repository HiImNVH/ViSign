// apps/web/src/main.tsx
// Diem vao frontend: mount App vao phan tu #root.
import { lazy, StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';

const AdminTraining = lazy(() => import('./features/admin/AdminTraining'));
const adminRoute = window.location.pathname.replace(/\/+$/, '') === '/admin/train-model';

const rootElement = document.getElementById('root');

if (rootElement === null) {
  throw new Error('[ERROR] Khong tim thay phan tu #root trong index.html');
}

createRoot(rootElement).render(
  <StrictMode>
    {adminRoute ? <Suspense fallback={<main>Đang tải công cụ admin…</main>}><AdminTraining /></Suspense> : <App />}
  </StrictMode>,
);
