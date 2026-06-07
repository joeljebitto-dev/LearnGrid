import { render, screen } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import { queryClient } from './app/queryClient';
import { App } from './App';

function renderApp() {
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

test('renders the frontend service identity', async () => {
  renderApp();

  expect(await screen.findByText(/SVC-011 frontend-service/i)).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /LearnGrid LMS/i })).toBeInTheDocument();
});

