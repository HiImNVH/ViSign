// apps/web/tests/App.test.tsx - Xac nhan component ung dung khoi dong duoc.
import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { App } from '../src/App';

test('renders the application shell without recognition controls', () => {
  render(<App />);
  expect(screen.getByRole('main')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'ViSign', level: 1 })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Bật camera' })).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Quay ký hiệu' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Gửi nhận diện' })).not.toBeInTheDocument();
});
