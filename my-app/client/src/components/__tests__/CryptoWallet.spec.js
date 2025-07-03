// client/src/components/__tests__/CryptoWallets.test.js

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CryptoWallets from '../CryptoWallets';
import axios from 'axios';

// mock axios
jest.mock('axios');

describe('CryptoWallets Component', () => {
  const customersMock = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' }
  ];
  const walletsMock = [
    { id: 10, wallet_name: 'BTC Wallet', balance: 1.23, customer_id: 1 },
    { id: 11, wallet_name: 'ETH Wallet', balance: 4.56, customer_id: 1 }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    // default: user is admin
    axios.get.mockImplementation(url => {
      if (url === '/api/me') {
        return Promise.resolve({ data: { user: { email: 'a@b.com', role: 'admin' } } });
      }
      if (url === '/api/customers') {
        return Promise.resolve({ data: customersMock });
      }
      // fetch wallets for Alice
      if (url === '/api/customers/1/wallets') {
        return Promise.resolve({ data: walletsMock });
      }
      return Promise.reject(new Error('not found'));
    });
    // intercept other axios calls
    axios.post.mockResolvedValue({ data: {} });
    axios.put.mockResolvedValue({ data: {} });
    axios.delete.mockResolvedValue({ data: {} });
    // always confirm
    jest.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('renders customer buttons and fetches wallets on select', async () => {
    render(<CryptoWallets />);

    // wait for customer buttons
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Alice' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Bob' })).toBeInTheDocument();
    });

    // click Alice
    fireEvent.click(screen.getByRole('button', { name: 'Alice' }));

    // wait for wallet items
    await waitFor(() => {
      expect(screen.getByText(/BTC Wallet — 1.2300/)).toBeInTheDocument();
      expect(screen.getByText(/ETH Wallet — 4.5600/)).toBeInTheDocument();
    });
  });

  it('adds a new wallet and displays it', async () => {
    // intercept post /api/wallets
    axios.post.mockResolvedValueOnce({
      data: { id: 12, wallet_name: 'LTC Wallet', balance: 7.89, customer_id: 1 }
    });

    render(<CryptoWallets />);

    // select customer
    await waitFor(() => screen.getByRole('button', { name: 'Alice' }));
    fireEvent.click(screen.getByRole('button', { name: 'Alice' }));

    // fill form
    fireEvent.change(screen.getByPlaceholderText('Wallet Name'), {
      target: { value: 'LTC Wallet' }
    });
    fireEvent.change(screen.getByPlaceholderText('Balance'), {
      target: { value: '7.89' }
    });

    // submit
    fireEvent.click(screen.getByRole('button', { name: /Add Wallet/i }));

    // new wallet appears
    await waitFor(() => {
      expect(screen.getByText(/LTC Wallet — 7.8900/)).toBeInTheDocument();
    });
  });

  it('edits an existing wallet', async () => {
    // intercept put /api/wallets/10
    axios.put.mockResolvedValueOnce({
      data: { id: 10, wallet_name: 'BTC Super', balance: 2.00, customer_id: 1 }
    });

    render(<CryptoWallets />);

    // select customer
    await waitFor(() => screen.getByRole('button', { name: 'Alice' }));
    fireEvent.click(screen.getByRole('button', { name: 'Alice' }));

    // click Edit on first wallet
    await waitFor(() => screen.getAllByText('Edit'));
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    // form populated
    expect(screen.getByDisplayValue('BTC Wallet')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1.23')).toBeInTheDocument();

    // change values
    fireEvent.change(screen.getByPlaceholderText('Wallet Name'), {
      target: { value: 'BTC Super' }
    });
    fireEvent.change(screen.getByPlaceholderText('Balance'), {
      target: { value: '2.00' }
    });

    // submit
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));

    // updated wallet appears
    await waitFor(() => {
      expect(screen.getByText(/BTC Super — 2.0000/)).toBeInTheDocument();
    });
  });

  it('deletes a wallet when admin confirms', async () => {
    render(<CryptoWallets />);

    // select customer
    await waitFor(() => screen.getByRole('button', { name: 'Alice' }));
    fireEvent.click(screen.getByRole('button', { name: 'Alice' }));

    // wait for delete button
    await waitFor(() => screen.getAllByText('Delete'));

    // click first delete
    const delButtons = screen.getAllByText('Delete');
    fireEvent.click(delButtons[0]);

    // confirm called
    expect(window.confirm).toHaveBeenCalledWith(
      'Are you sure you want to delete this wallet?'
    );
    // axios.delete called
    expect(axios.delete).toHaveBeenCalledWith('/api/wallets/10', { withCredentials: true });

    // wallet removed from list
    await waitFor(() => {
      expect(screen.queryByText(/BTC Wallet — 1.2300/)).not.toBeInTheDocument();
    });
  });

  it('does not delete if user cancels confirmation', async () => {
    // make confirm return false
    window.confirm.mockReturnValueOnce(false);

    render(<CryptoWallets />);

    // select customer
    await waitFor(() => screen.getByRole('button', { name: 'Alice' }));
    fireEvent.click(screen.getByRole('button', { name: 'Alice' }));

    // wait for delete
    await waitFor(() => screen.getAllByText('Delete'));

    // click delete
    const delBtn = screen.getAllByText('Delete')[0];
    fireEvent.click(delBtn);

    // axios.delete should not be called
    expect(axios.delete).not.toHaveBeenCalled();
  });
});