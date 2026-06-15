import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';

import {
  Button,
  EmptyState,
  FormField,
  Input,
  PaginationControls,
  StatusBadge
} from './ui';

test('button exposes loading and disabled reason states', () => {
  render(
    <Button id="submit-button" loading disabledReason="Wait for upload validation">
      Submit
    </Button>
  );

  const button = screen.getByRole('button', { name: /working/i });
  expect(button).toBeDisabled();
  expect(screen.getByText(/wait for upload validation/i)).toBeInTheDocument();
});

test('form field renders label, required marker, help text, and error text', () => {
  render(
    <FormField
      label="Course title"
      htmlFor="course-title"
      required
      helpText="Shown in the catalog."
      error="Title is required."
    >
      <Input id="course-title" />
    </FormField>
  );

  expect(screen.getByLabelText(/course title/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/course title/i)).toHaveAttribute(
    'aria-describedby',
    'course-title-help course-title-error'
  );
  expect(screen.getByLabelText(/course title/i)).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByLabelText(/required/i)).toBeInTheDocument();
  expect(screen.getByText(/shown in the catalog/i)).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('Title is required.');
});

test('status badge normalizes status values', () => {
  render(<StatusBadge value="in_progress" />);

  expect(screen.getByText(/in progress/i)).toBeInTheDocument();
});

test('pagination controls call previous and next handlers', async () => {
  const onPrevious = vi.fn();
  const onNext = vi.fn();
  render(
    <PaginationControls page={2} onPrevious={onPrevious} onNext={onNext} />
  );

  await userEvent.click(screen.getByRole('button', { name: /previous/i }));
  await userEvent.click(screen.getByRole('button', { name: /next/i }));

  expect(onPrevious).toHaveBeenCalledTimes(1);
  expect(onNext).toHaveBeenCalledTimes(1);
});

test('empty state can show an action', () => {
  render(<EmptyState message="No modules yet." action={<Button>Create module</Button>} />);

  expect(screen.getByText(/no modules yet/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /create module/i })).toBeInTheDocument();
});
