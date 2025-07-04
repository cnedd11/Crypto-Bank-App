// client/src/components/__tests__/Footer.test.js

import React from 'react';
import { render, screen } from '@testing-library/react';
import Footer from '../Footer';

describe('Footer component', () => {
  const currentYear = new Date().getFullYear();

  beforeEach(() => {
    render(<Footer />);
  });

  it('renders the CryptoBank heading', () => {
    const heading = screen.getByRole('heading', { name: /CryptoBank/i });
    expect(heading).toBeInTheDocument();
  });

  it('renders the description text', () => {
    expect(
      screen.getByText(/Securely manage your crypto assets with ease\./i)
    ).toBeInTheDocument();
  });

  it('renders the Main Website link with correct href', () => {
    // Find by its visible text, then check href
    const mainLink = screen.getByText(/Main Website/i);
    expect(mainLink).toBeInTheDocument();
    expect(mainLink).toHaveAttribute(
      'href',
      'https://country.db.com/uk/index?language_id=1&kid=uk.redirect-en.shortcut'
    );
  });

  it('renders the GitHub link with correct href', () => {
    const githubLink = screen.getByRole('link', { name: /GitHub/i });
    expect(githubLink).toBeInTheDocument();
    expect(githubLink).toHaveAttribute(
      'href',
      'https://github.com/cnedd11/Crypto-Bank-App/tree/main'
    );
  });

  it('renders a horizontal rule', () => {
    const hr = screen.getByRole('separator');
    expect(hr).toBeInTheDocument();
  });

  it('renders the dynamic copyright notice', () => {
    const text = `© ${currentYear} Deutsche Bank. All rights reserved.`;
    expect(screen.getByText(text)).toBeInTheDocument();
  });
});