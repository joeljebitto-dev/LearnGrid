import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';

import { DesignSystemPreview } from './DesignSystemPreview';

test('design system preview documents tokens, primitives, and product components', () => {
  render(
    <MemoryRouter>
      <DesignSystemPreview />
    </MemoryRouter>
  );

  expect(screen.getByRole('heading', { name: /learngrid ui design system preview/i })).toBeInTheDocument();
  expect(screen.getByRole('region', { name: /design tokens/i })).toBeInTheDocument();
  expect(screen.getByRole('region', { name: /forms and feedback/i })).toBeInTheDocument();
  expect(screen.getByRole('region', { name: /lms product components/i })).toBeInTheDocument();
  expect(screen.getByText(/learning management foundations/i)).toBeInTheDocument();
});
