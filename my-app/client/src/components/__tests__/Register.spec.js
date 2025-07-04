// client/src/components/__tests__/Register.test.js

import React from 'react';
import {
  render,
  screen,
  fireEvent,
  waitFor
} from '@testing-library/react';
import Register from '../Register';
import axios from 'axios';
import { MemoryRouter } from 'react-router-dom';

jest.mock('axios');

// mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const original = jest.requireActual('react-router-dom');
  return {
    ...original,
    useNavigate: () => mockNavigate,
  };
});

describe('Register component', () => {
  const originalLocation = window.location;

  beforeAll(() => {
    // stub reload
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        reload: jest.fn(),
      },
    });
  });

  afterAll(() => {
    // restore
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders form fields and initial state', () => {
    render(<Register />, { wrapper: MemoryRouter });

    expect(screen.getByRole('heading', { name: /Register/i }))
      .toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@example.com')).toHaveValue('');
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    // password type is hidden initially
    expect(screen.getByPlaceholderText('••••••••')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('button', { name: /Show/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Role/i)).toHaveValue('user');
    expect(screen.getByRole('button', { name: /Sign Up/i })).toBeInTheDocument();
    // Login link
    const loginLink = screen.getByText(/Login/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('toggles password visibility when Show/Hide clicked', () => {
    render(<Register />, { wrapper: MemoryRouter });
    const pwdInput = screen.getByPlaceholderText('••••••••');
    const toggleBtn = screen.getByRole('button', { name: /Show/i });

    // show
    fireEvent.click(toggleBtn);
    expect(pwdInput).toHaveAttribute('type', 'text');
    expect(toggleBtn).toHaveTextContent('Hide');

    // hide
    fireEvent.click(toggleBtn);
    expect(pwdInput).toHaveAttribute('type', 'password');
    expect(toggleBtn).toHaveTextContent('Show');
  });

  it('validates password complexity before submit', async () => {
    render(<Register />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'user@test.com' }
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'abc' } // invalid
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));
    expect(await screen.findByText(/Password must be at least 6 characters/))
      .toBeInTheDocument();

    // axios not called
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('submits register and login then navigates and reloads', async () => {
    axios.post
      .mockResolvedValueOnce({ data: { message: 'Registered' } })  // register
      .mockResolvedValueOnce({ data: { message: 'Logged in' } });  // login

    render(<Register />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'user@test.com' }
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'Abc123!' }
    });
    fireEvent.change(screen.getByLabelText(/Role/i), {
      target: { value: 'admin' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));

    await waitFor(() => {
      expect(axios.post).toHaveBeenNthCalledWith(
        1,
        '/api/register',
        { email: 'user@test.com', password: 'Abc123!', role: 'admin' },
        { withCredentials: true }
      );
      expect(axios.post).toHaveBeenNthCalledWith(
        2,
        '/api/login',
        { email: 'user@test.com', password: 'Abc123!' },
        { withCredentials: true }
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
    expect(window.location.reload).toHaveBeenCalled();
  });

  it('displays server error on registration failure', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { error: 'Email taken' } }
    });

    render(<Register />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'dup@test.com' }
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'Abc123!' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));

    expect(await screen.findByText('Email taken')).toBeInTheDocument();
  });

  it('displays generic error on unknown failure', async () => {
    axios.post.mockRejectedValueOnce(new Error('Network error'));

    render(<Register />, { wrapper: MemoryRouter });

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'x@test.com' }
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'Abc123!' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));

    expect(await screen.findByText('Registration failed')).toBeInTheDocument();
  });
});