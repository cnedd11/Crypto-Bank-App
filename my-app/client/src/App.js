// client/src/App.js
import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './css/LoginRegister.css';  // for .auth-wrapper/.auth-card if you like

export default function App() {
  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card" style={{ maxWidth: 600 }}>
        <div className="card-body">
          <h1 className="text-center mb-4">Welcome to CryptoBank</h1>

          <h3>💼 Key Features:</h3>
          <ul className="list-unstyled mb-4">
            <li>🔐 Secure Login &amp; User Roles: Admin and Regular users with tailored access.</li>
            <li>💳 Crypto Wallet Management: Track balances and view multiple wallets in different cryptocurrencies.</li>
            <li>📊 Transaction Tracking: Record and view all your deposits, withdrawals, buys, and sells.</li>
            <li>🧑‍💼 Customer Management: Admins can create and manage customer profiles and linked wallets.</li>
          </ul>

          <h3>🚀 Getting Started:</h3>
          <ul className="list-unstyled">
            <li>✅ Register as a new user or log in with your existing account.</li>
            <li>👤 Admins can manage all users, wallets, and transactions.</li>
            <li>🙋 Regular users can explore and update their personal wallet data.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}