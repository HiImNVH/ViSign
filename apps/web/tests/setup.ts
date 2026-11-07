// apps/web/tests/setup.ts
// Nap matcher DOM cua Testing Library cho moi file test Vitest.
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(cleanup);
