// client/src/components/Customers.js
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [name, setName]           = useState('');
  const [email, setEmail]         = useState('');
  const [phone, setPhone]         = useState('');
  const [error, setError]         = useState('');
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

  // Add customer
  const handleAdd = async e => {
    e.preventDefault();
    try {
      const res = await axios.post(
        '/api/customers',
        { name, email, phone },
        { withCredentials: true }
      );
      setCustomers(prev => [...prev, res.data]);
      setName(''); setEmail(''); setPhone(''); setError('');
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
            <input
              type="text"
              className="form-control mb-2"
              placeholder="Name"
              value={name}
              onChange={e => setName(e.target.value)}
              required
            />
            <input
              type="email"
              className="form-control mb-2"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
            <input
              type="tel"
              className="form-control mb-3"
              placeholder="Phone (optional)"
              value={phone}
              onChange={e => setPhone(e.target.value)}
            />
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
