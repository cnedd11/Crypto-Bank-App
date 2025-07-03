import { useState, useEffect } from 'react';
import axios from 'axios';

export default function CryptoWallets() {
  const [customers, setCustomers]     = useState([]);
  const [selectedCust, setSelected]   = useState(null);
  const [wallets, setWallets]         = useState([]);
  const [form, setForm]               = useState({ wallet_name: '', balance: '' });
  const [editing, setEditing]         = useState(null);
  const [userRole, setUserRole]       = useState(null);
  const [error, setError]             = useState('');

  // fetch user role
  useEffect(() => {
    axios.get('/api/me', { withCredentials: true })
      .then(r => setUserRole(r.data.user.role))
      .catch(() => setUserRole(null));
  }, []);

  // fetch customers
  useEffect(() => {
    axios.get('/api/customers', { withCredentials: true })
      .then(r => setCustomers(r.data))
      .catch(() => setError('Failed to load customers'));
  }, []);

  // fetch wallets on customer change
  useEffect(() => {
    if (!selectedCust) return;
    axios.get(`/api/customers/${selectedCust.id}/wallets`, { withCredentials: true })
      .then(r => setWallets(r.data))
      .catch(() => setError('Failed to load wallets'));
  }, [selectedCust]);

  // handle form change
  const onChange = e => {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  };

  // add or edit wallet
  const onSubmit = async e => {
    e.preventDefault();
    try {
      let res;
      if (editing) {
        res = await axios.put(
          `/api/wallets/${editing.id}`,
          { wallet_name: form.wallet_name, balance: parseFloat(form.balance) },
          { withCredentials: true }
        );
        setWallets(ws => ws.map(w => w.id === res.data.id ? res.data : w));
      } else {
        res = await axios.post(
          '/api/wallets',
          { wallet_name: form.wallet_name, balance: parseFloat(form.balance), customer_id: selectedCust.id },
          { withCredentials: true }
        );
        setWallets(ws => [...ws, res.data]);
      }
      setEditing(null);
      setForm({ wallet_name: '', balance: '' });
      setError('');
    } catch (err) {
      setError(err.response?.data.error || 'Operation failed');
    }
  };

  // start editing
  const startEdit = w => {
    setEditing(w);
    setForm({ wallet_name: w.wallet_name, balance: w.balance.toString() });
  };

  // delete wallet (admin only)
  const deleteWallet = async id => {
    try {
      await axios.delete(`/api/wallets/${id}`, { withCredentials: true });
      setWallets(ws => ws.filter(w => w.id !== id));
    } catch (err) {
      setError(err.response?.data.error || 'Delete failed');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card" style={{ maxWidth: 600 }}>
        <div className="card-body">
          <h2 className="text-center auth-title">Crypto Wallets</h2>
          {error && <div className="alert alert-danger auth-error">{error}</div>}

          {/* select customer */}
          <div className="d-flex flex-wrap mb-4">
            {customers.map(c => (
              <button
                key={c.id}
                className={`btn btn-outline-primary me-2 mb-2${selectedCust?.id===c.id?' active':''}`}
                onClick={() => { setSelected(c); setEditing(null); setForm({wallet_name:'',balance:''}); }}
              >
                {c.name}
              </button>
            ))}
          </div>

          {selectedCust && (
            <>
              <h5>Wallets for {selectedCust.name}:</h5>
              <ul className="list-group mb-4">
                {wallets.map(w => (
                  <li key={w.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                      {w.wallet_name} — {w.balance.toFixed(4)}
                    </div>
                    <div>
                      <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => startEdit(w)}>
                        Edit
                      </button>
                      {userRole==='admin' && (
                        <button className="btn btn-sm btn-outline-danger" onClick={() => deleteWallet(w.id)}>
                          Delete
                        </button>
                      )}
                    </div>
                  </li>
                ))}
                {!wallets.length && (
                  <li className="list-group-item text-muted">No wallets yet.</li>
                )}
              </ul>

              {/* form */}
              <form onSubmit={onSubmit}>
                <h6>{editing?'Edit Wallet':'Add Wallet'}</h6>
                <input
                  name="wallet_name"
                  type="text"
                  className="form-control mb-2"
                  placeholder="Wallet Name"
                  value={form.wallet_name}
                  onChange={onChange}
                  required
                />
                <input
                  name="balance"
                  type="number"
                  step="0.0001"
                  className="form-control mb-3"
                  placeholder="Balance"
                  value={form.balance}
                  onChange={onChange}
                  required
                />
                <button type="submit" className="btn btn-success w-100">
                  {editing?'Save Changes':'Add Wallet'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
