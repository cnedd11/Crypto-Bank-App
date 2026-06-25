// client/src/components/Customers.js
import { useState, useEffect } from 'react';
import axios from 'axios';

// Client-side email format check (mirrors the server-side rule).
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// Phone: digits, spaces, +, -, (, ) only.
const PHONE_RE = /^[\d\s+\-(). ]{1,30}$/;

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [name, setName]           = useState('');
  const [email, setEmail]         = useState('');
  const [phone, setPhone]         = useState('');
  const [error, setError]         = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [userRole, setUserRole]   = useState(null);

  // 1) Fetch current user role
  useEffect(() => {
    axios.get('/api/me', { withCredentials: true })
      .then(res => setUserRole(res.data.user.role))
      .catch(() => setUserRole(null));
  }, []);

  // 2) Fetch existing customers
  useEffect(() => {
    axios.get('/api/customers', { withCredentials: true })
      .then(res => setCustomers(res.data))
      .catch(() => setError('Failed to load customers'));
  }, []);

  // Client-side validation — returns an object of field → message.
  const validateCustomer = () => {
    const errors = {};
    if (!name.trim()) {
      errors.name = 'Name is required';
    } else if (name.length > 120) {
      errors.name = 'Name must be at most 120 characters';
    }
    if (!email.trim()) {
      errors.email = 'Email is required';
    } else if (!EMAIL_RE.test(email)) {
      errors.email = 'Invalid email format';
    } else if (email.length > 120) {
      errors.email = 'Email must be at most 120 characters';
    }
    if (phone && !PHONE_RE.test(phone)) {
      errors.phone = 'Phone: digits, spaces, + - ( ) only (max 30 chars)';
    }
    return errors;
  };

  // Add customer
  const handleAdd = async e => {
    e.preventDefault();
    setError('');

    const errors = validateCustomer();
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});

    try {
      const res = await axios.post(
        '/api/customers',
        { name, email, phone },
        { withCredentials: true }
      );
      setCustomers(prev => [...prev, res.data]);
      setName(''); setEmail(''); setPhone('');
    } catch (err) {
      setError(err.response?.data.error || 'Add customer failed');
    }
  };

  // Delete customer (admin only), with confirmation
  const handleDelete = async id => {
    if (!window.confirm('Are you sure you want to delete this customer?')) {
      return;
    }
    try {
      await axios.delete(`/api/customers/${id}`, { withCredentials: true });
      setCustomers(prev => prev.filter(c => c.id !== id));
    } catch (err) {
      setError(err.response?.data.error || 'Delete failed');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card">
        <div className="card-body">
          <h2 className="text-center auth-title">Customers</h2>

          {error && (
            <div className="alert alert-danger auth-error">
              {error}
            </div>
          )}

          <form onSubmit={handleAdd} className="mb-4">
            <div className="mb-2">
              <input
                type="text"
                className={`form-control ${fieldErrors.name ? 'is-invalid' : ''}`}
                placeholder="Name"
                value={name}
                onChange={e => { setName(e.target.value); setFieldErrors(f => ({...f, name: ''})); }}
                required
              />
              {fieldErrors.name && (
                <div className="invalid-feedback">{fieldErrors.name}</div>
              )}
            </div>
            <div className="mb-2">
              <input
                type="email"
                className={`form-control ${fieldErrors.email ? 'is-invalid' : ''}`}
                placeholder="Email"
                value={email}
                onChange={e => { setEmail(e.target.value); setFieldErrors(f => ({...f, email: ''})); }}
                required
              />
              {fieldErrors.email && (
                <div className="invalid-feedback">{fieldErrors.email}</div>
              )}
            </div>
            <div className="mb-3">
              <input
                type="tel"
                className={`form-control ${fieldErrors.phone ? 'is-invalid' : ''}`}
                placeholder="Phone (optional)"
                value={phone}
                onChange={e => { setPhone(e.target.value); setFieldErrors(f => ({...f, phone: ''})); }}
              />
              {fieldErrors.phone && (
                <div className="invalid-feedback">{fieldErrors.phone}</div>
              )}
            </div>
            <button type="submit" className="btn btn-success w-100">
              Add Customer
            </button>
          </form>

          <ul className="list-group">
            {customers.map(c => (
              <li key={c.id} className="list-group-item d-flex justify-content-between align-items-center">
                <div>
                  <strong>{c.name}</strong><br/>
                  <small>
                    {c.email}
                    {c.phone ? ` • ${c.phone}` : ''}
                  </small>
                </div>

                {userRole === 'admin' && (
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleDelete(c.id)}
                  >
                    Delete
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
