import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import 'bootstrap/dist/css/bootstrap.min.css';
import Navbar from './component/Navbar';
import Login from './component/Login';
import Register from './component/Register';
import Customers from './component/Customers';
import Footer from './component/Footer';
import PrivateRoute from './component/PrivateRoute';
import CryptoWallets from './component/CryptoWallets';
import './css/App.css';

const container = document.getElementById('root');
const root = createRoot(container);             // Create a root.
root.render(
  <BrowserRouter>
    <div className="app-wrapper">
      <Navbar />

      <main className="app-content container my-4">

        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/login"  element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* All routes under here require auth */}
          <Route element={<PrivateRoute />}>
            <Route path="/customers" element={<Customers />} />
            <Route path="/wallets"   element={<CryptoWallets />} />
            {/* add more protected routes */}
          </Route>
        </Routes>
      </main>

      <Footer />
    </div>
  </BrowserRouter>
);