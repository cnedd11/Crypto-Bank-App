import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import 'bootstrap/dist/css/bootstrap.min.css';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import Customers from './components/Customers';
import Footer from './components/Footer';
import PrivateRoute from './components/PrivateRoute';
import CryptoWallets from './components/CryptoWallets';
import './css/App.css';

const container = document.getElementById('root');
const root = createRoot(container);             // Create a root.
root.render(
  <BrowserRouter>
    <div className="app-wrapper">
      <Navbar />

      <main className="app-content container my-4">

        <Routes>
          <Route path="/" element={<Home />} />
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