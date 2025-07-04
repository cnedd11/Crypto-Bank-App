// client/src/Register.js
import { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './../css/LoginRegister.css';

export default function Register() {
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole]             = useState('user');
  const [error, setError]           = useState('');
  const navigate = useNavigate();

  // Regex: min 6 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{6,}$/;

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    // client-side validation
    if (!passwordRegex.test(password)) {
      setError(
        'Password must be at least 6 characters and include uppercase, lowercase, number, and special character.'
      );
      return;
    }

    try {
      // 1. Register
      await axios.post(
        '/api/register',
        { email, password, role },
        { withCredentials: true }
      );

      // 2. Immediately log in
      await axios.post(
        '/api/login',
        { email, password },
        { withCredentials: true }
      );

      // 3. Redirect home and reload so Navbar updates
      navigate('/');
      window.location.reload();
    } catch (err) {
      setError(err.response?.data.error || 'Registration failed');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card">
        <div className="card-body">
          <h2 className="text-center auth-title">Register</h2>

          {error && (
            <div className="alert alert-danger auth-error" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div className="mb-3">
              <label htmlFor="email" className="form-label">Email</label>
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

            {/* Password with toggle */}
            <div className="mb-3">
              <label htmlFor="password" className="form-label">Password</label>
              <div className="input-group">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className={`form-control ${password && !passwordRegex.test(password) ? 'is-invalid' : ''}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setShowPassword(s => !s)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
                <div className="invalid-feedback">
                  Must be ≥6 chars, include upper, lower, number & special.
                </div>
              </div>
            </div>

            {/* Role Selector */}
            <div className="mb-4">
              <label htmlFor="role" className="form-label">Role</label>
              <select
                id="role"
                className="form-select"
                value={role}
                onChange={e => setRole(e.target.value)}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary w-100">
              Sign Up
            </button>
          </form>

          <div className="text-center mt-3">
            Already have an account? <Link to="/login">Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
}