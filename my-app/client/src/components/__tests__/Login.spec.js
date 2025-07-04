// client/src/components/__tests__/Login.test.js

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';
import axios from 'axios';
import { MemoryRouter } from 'react-router-dom';

jest.mock('axios');

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const original = jest.requireActual('react-router-dom');
  return {
    ...original,
    useNavigate: () => mockNavigate,
  };
});

describe('Login component', () => {
  // Keep original location so we can restore it
  const originalLocation = window.location;

  beforeAll(() => {
    // Override window.location.reload with a jest.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        reload: jest.fn(),
      },
    });
  });

  afterAll(() => {
    // Restore original location object
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the login form fields and link', () => {
    render(<Login />, { wrapper: MemoryRouter });

    expect(screen.getByRole('heading', { name: /Login/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();
    expect(screen.getByText(/Create an account/i)).toHaveAttribute('href', '/register');
  });

  it('submits credentials, navigates home and calls reload on success', async () => {
    axios.post.mockResolvedValueOnce({}); 

    render(<Login />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'user@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'secret123' }
    });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/login',
        { email: 'user@test.com', password: 'secret123' },
        { withCredentials: true }
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
    expect(window.location.reload).toHaveBeenCalled();
  });

  it('displays server error message when login fails with payload', async () => {
    // simulate API returning { error: 'Invalid creds' }
    axios.post.mockRejectedValueOnce({
      response: { data: { error: 'Invalid creds' } }
    });

    render(<Login />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'bad@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'wrong' }
    });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    expect(await screen.findByText('Invalid creds')).toBeInTheDocument();
  });

  it('falls back to generic message when login fails without payload', async () => {
    // simulate network error / no response body
    axios.post.mockRejectedValueOnce(new Error('Network down'));

    render(<Login />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'x@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'pass' }
    });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    expect(await screen.findByText('Login failed')).toBeInTheDocument();
  });
});