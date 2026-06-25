// client/src/components/__tests__/PrivateRoute.test.js

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import {
  MemoryRouter,
  Routes,
  Route,
  Link
} from 'react-router-dom';
import PrivateRoute from '../PrivateRoute';

jest.mock('axios');

describe('PrivateRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  function renderWithRouter(ui, { route = '/' } = {}) {
    return render(
      <MemoryRouter initialEntries={[route]}>
        {ui}
      </MemoryRouter>
    );
  }

  it('shows login prompt when not authenticated', async () => {
    // simulate /api/me failure
    axios.get.mockRejectedValueOnce(new Error('Unauthorized'));

    renderWithRouter(
      <Routes>
        <Route path="/" element={<PrivateRoute />}>
          <Route index element={<div>Protected Content</div>} />
        </Route>
      </Routes>
    );

    // initial render returns null, no text
    expect(screen.queryByText(/Protected Content/i)).toBeNull();

    // after axios rejects, should show message
    expect(await screen.findByText(/You must/i)).toBeInTheDocument();
    expect(screen.getByText(/log in/i)).toBeInTheDocument();

    const loginLink = screen.getByRole('link', { name: /log in/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('renders child routes when authenticated', async () => {
    // simulate /api/me success
    axios.get.mockResolvedValueOnce({ data: { user: { email: 'x@y.com', role: 'user' } } });

    renderWithRouter(
      <Routes>
        <Route path="/" element={<PrivateRoute />}>
          <Route index element={<div>Protected Content</div>} />
        </Route>
      </Routes>
    );

    // wait for axios to resolve and component to re-render
    expect(await screen.findByText(/Protected Content/i)).toBeInTheDocument();
    // nothing else should appear
    expect(screen.queryByText(/You must/i)).toBeNull();
  });
});