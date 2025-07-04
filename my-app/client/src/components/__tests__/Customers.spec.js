// client/src/components/__tests__/Customers.test.js

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Customers from '../Customers';
import axios from 'axios';

jest.mock('axios');

describe('Customers component', () => {
  const alice = { id: 1, name: 'Alice', email: 'alice@mail.com', phone: '123' };
  const bob   = { id: 2, name: 'Bob',   email: 'bob@mail.com',   phone: ''    };
  const customerList = [alice, bob];

  beforeEach(() => {
    jest.clearAllMocks();
    // stub confirm globally
    jest.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    window.confirm.mockRestore();
  });

  function mockFetch(role = 'admin', customers = customerList) {
    axios.get.mockImplementation(url => {
      switch (url) {
        case '/api/me':
          return Promise.resolve({ data: { user: { role } } });
        case '/api/customers':
          return Promise.resolve({ data: customers });
        default:
          return Promise.reject(new Error('Unexpected GET ' + url));
      }
    });
  }

  it('loads role and customer list and displays them', async () => {
    mockFetch('admin');

    render(<Customers />);

    // wait for both calls
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/me', { withCredentials: true })
    );
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/customers', { withCredentials: true })
    );

    // Alice & Bob appear
    expect(await screen.findByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@mail.com • 123')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('hides delete button for non-admin users', async () => {
    mockFetch('regular');

    render(<Customers />);
    await screen.findByText('Alice');

    expect(screen.queryByRole('button', { name: /Delete/i })).toBeNull();
  });

  it('adds a new customer on form submit', async () => {
    mockFetch('admin');
    render(<Customers />);
    await screen.findByText('Alice');

    const newCust = { id: 3, name: 'Carol', email: 'carol@mail.com', phone: '555' };
    axios.post.mockResolvedValueOnce({ data: newCust });

    fireEvent.change(screen.getByPlaceholderText('Name'), {
      target: { value: newCust.name }
    });
    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: newCust.email }
    });
    fireEvent.change(screen.getByPlaceholderText('Phone (optional)'), {
      target: { value: newCust.phone }
    });
    fireEvent.click(screen.getByRole('button', { name: /Add Customer/i }));

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledWith(
        '/api/customers',
        { name: newCust.name, email: newCust.email, phone: newCust.phone },
        { withCredentials: true }
      )
    );

    // Carol appears
    expect(await screen.findByText('Carol')).toBeInTheDocument();
    expect(screen.getByText('carol@mail.com • 555')).toBeInTheDocument();

    // inputs are cleared
    expect(screen.getByPlaceholderText('Name')).toHaveValue('');
    expect(screen.getByPlaceholderText('Email')).toHaveValue('');
    expect(screen.getByPlaceholderText('Phone (optional)')).toHaveValue('');
  });

  it('shows error when customers fetch fails', async () => {
    // /api/me succeeds
    axios.get.mockResolvedValueOnce({ data: { user: { role: 'admin' } } });
    // /api/customers fails
    axios.get.mockRejectedValueOnce(new Error());
    
    render(<Customers />);

    // should render the fetch-error message
    expect(
      await screen.findByText('Failed to load customers')
    ).toBeInTheDocument();
  });

  it('shows error when add-customer fails', async () => {
    mockFetch('admin');
    render(<Customers />);
    await screen.findByText('Alice');

    axios.post.mockRejectedValueOnce({
      response: { data: { error: 'Add failed' } }
    });

    fireEvent.click(screen.getByRole('button', { name: /Add Customer/i }));

    expect(
      await screen.findByText('Add failed')
    ).toBeInTheDocument();
  });

  it('deletes a customer when confirmed', async () => {
    mockFetch('admin');
    axios.delete.mockResolvedValueOnce({});
    render(<Customers />);
    await screen.findByText('Alice');

    // click Delete for Alice
    fireEvent.click(screen.getAllByRole('button', { name: /Delete/i })[0]);
    expect(window.confirm).toHaveBeenCalledWith(
      'Are you sure you want to delete this customer?'
    );

    // wait for delete API call
    await waitFor(() =>
      expect(axios.delete).toHaveBeenCalledWith(
        '/api/customers/1',
        { withCredentials: true }
      )
    );

    // wait for Alice to be removed
    await waitFor(() =>
      expect(screen.queryByText('Alice')).not.toBeInTheDocument()
    );
  });

  it('does nothing when delete is canceled', async () => {
    mockFetch('admin');
    window.confirm.mockReturnValueOnce(false);
    render(<Customers />);
    await screen.findByText('Alice');

    fireEvent.click(screen.getAllByRole('button', { name: /Delete/i })[0]);
    expect(axios.delete).not.toHaveBeenCalled();
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });
});