// client/src/Login.js
import { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './../css/LoginRegister.css';

export default function Login() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await axios.post(
        '/api/login',
        { email, password },
        { withCredentials: true }
      );
      navigate('/');
    } catch (err) {
      setError(err.response?.data.error || 'Login failed');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card">
        <div className="card-body">
          <h2 className="text-center auth-title">Login</h2>

          {error && (
            <div className="alert alert-danger auth-error" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <input
                id="email"
                type="email"
                className="form-control"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="mb-4">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="form-control"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary w-100">
              Log In
            </button>
          </form>

          <div className="text-center mt-3">
            New here?{' '}
            <Link to="/register" className="text-decoration-none">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}