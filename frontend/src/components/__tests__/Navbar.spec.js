// src/components/__tests__/Navbar.spec.js
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Navbar from '../Navbar';
import axios from 'axios';
import { MemoryRouter } from 'react-router-dom';

jest.mock('axios');

const mockNavigate = jest.fn();

// only override useNavigate, leave everything else intact
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Navbar', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows Login/Register when unauthorized', async () => {
    axios.get.mockRejectedValueOnce({ response: { status: 401 } });

    render(<Navbar />, { wrapper: MemoryRouter });

    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/me', { withCredentials: true })
    );

    expect(screen.getByText(/Login/i)).toBeInTheDocument();
    expect(screen.getByText(/Register/i)).toBeInTheDocument();
    expect(screen.queryByText(/Customers/i)).not.toBeInTheDocument();
  });

  it('shows customer links and logout when logged in', async () => {
    axios.get.mockResolvedValueOnce({
      data: { user: { email: 'a@b.com', role: 'admin' } }
    });

    render(<Navbar />, { wrapper: MemoryRouter });

    // wait for the “Customers” link to appear
    await waitFor(() => screen.getByText(/Customers/i));

    expect(screen.getByText(/Wallets/i)).toBeInTheDocument();
    expect(screen.getByText(/Hello,/)).toHaveTextContent('Hello, a@b.com (admin)');
    expect(screen.getByRole('button', { name: /Logout/i })).toBeInTheDocument();
  });

  it('logs out and navigates to /login', async () => {
    axios.get.mockResolvedValueOnce({
      data: { user: { email: 'a@b.com', role: 'admin' } }
    });
    axios.post.mockResolvedValueOnce({});

    render(<Navbar />, { wrapper: MemoryRouter });
    await waitFor(() => screen.getByRole('button', { name: /Logout/i }));

    fireEvent.click(screen.getByRole('button', { name: /Logout/i }));

    expect(axios.post).toHaveBeenCalledWith(
      '/api/logout',
      {},
      { withCredentials: true }
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });
});