// client/src/components/PrivateRoute.js
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Outlet, Link, useLocation } from 'react-router-dom';

export default function PrivateRoute() {
  const [loggedIn, setLoggedIn] = useState(null);
  const location = useLocation();

  useEffect(() => {
    axios
      .get('/api/me', { withCredentials: true })
      .then(res => setLoggedIn(true))
      .catch(() => setLoggedIn(false));
  }, [location]);

  // still checking
  if (loggedIn === null) return null;

  // not logged in
  if (!loggedIn) {
    return (
      <div className="text-center mt-5">
        <p>
          You must <Link to="/login">log in</Link> to view this page.
        </p>
      </div>
    );
  }

  // authorized
  return <Outlet />;
}