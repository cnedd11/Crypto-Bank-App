// client/src/App.js
import 'bootstrap/dist/css/bootstrap.min.css';
import './../css/LoginRegister.css';

export default function App() {
  return (
    <div className="auth-wrapper">
      <div className="card shadow-sm auth-card" style={{ maxWidth: 600 }}>
        <div className="card-body">
          <h1 className="text-center mb-4">Welcome to CryptoBank’s internal portal</h1>

          <h2>Here’s what you can do:</h2>
          <ul className="list-unstyled mb-4">
            <li>Manage customer profiles and link multiple crypto wallets to each customer.</li>
            <li>View and adjust wallet balances in real time.</li>
            <li>Maintain a full, auditable history of every entry for compliance.</li>
            <li>Work within a secure, role-based system—Regular users can add and edit records, while Admins also have deletion rights.</li>
          </ul>

          <p>
            Getting started is easy: simply register for a new account or log in with your credentials.
            Once you’re in, you’ll have instant access to all customer and wallet management tools.
          </p>
        </div>
      </div>
    </div>
  );
}