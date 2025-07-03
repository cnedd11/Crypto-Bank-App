
// client/src/components/Navbar.js
import React, { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './../css/Navbar.css';  // if you have custom styles
export default function Navbar() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  // On mount, fetch current user info (email + role) or 401 if not logged in
  useEffect(() => {
    axios
      .get('/api/me', { withCredentials: true })
      .then(res => {
        // expecting { user: { email: '…', role: 'admin' } }
        setUser(res.data.user);
      })
      .catch(() => {
        setUser(null);
      });
  }, []);
  const handleLogout = () => {
    axios
      .post('/api/logout', {}, { withCredentials: true })
      .then(() => {
        setUser(null);
        navigate('/login');
      });
  };
  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light mb-4">
      <div className="container">
        <Link className="navbar-brand" to="/">CryptoBank</Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto align-items-center">
            <li className="nav-item">
              <NavLink className="nav-link" to="/" end>
                Home
              </NavLink>
            </li>
            {user ? (
              <>
                {/* Show customers link only when logged in */}
                <li className="nav-item">
                  <NavLink className="nav-link" to="/customers">
                    Customers
                  </NavLink>
                </li>
                <li className="nav-item">
                    <NavLink className="nav-link" to="/wallets">
                        Wallets
                    </NavLink>
                </li>
                {/* Greeting + role */}
                <li className="nav-item mx-3">
                  <span className="navbar-text">
                    Hello, <strong>{user.email}</strong> ({user.role})
                  </span>
                </li>
                {/* Logout button */}
                <li className="nav-item">
                  <button
                    className="btn btn-outline-secondary"
                    onClick={handleLogout}
                  >
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item">
                  <NavLink className="nav-link" to="/login">
                    Login
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink className="nav-link" to="/register">
                    Register
                  </NavLink>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}
