import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';

import { DesignSystemPreview } from './DesignSystemPreview';

test('design system preview has no automated accessibility violations', async () => {
  const { container } = render(
    <MemoryRouter>
      <DesignSystemPreview />
    </MemoryRouter>
  );

  expect(await axe(container)).toHaveNoViolations();
});
