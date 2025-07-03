import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import 'bootstrap/dist/css/bootstrap.min.css';
import Navbar from './component/Navbar';
import Login from './component/Login';
import Register from './component/Register';
import Footer from './component/Footer';
import './css/App.css';

const container = document.getElementById('root');
const root = createRoot(container);             // Create a root.
root.render(
  <BrowserRouter>
    <div className="app-wrapper">
      <Navbar />

      <main className="app-content container my-4">
        <Routes>
          <Route path="/"        element={<App />}      />
          <Route path="/login"   element={<Login />}    />
          <Route path="/register" element={<Register />} />
        </Routes>
      </main>

      <Footer />
    </div>
  </BrowserRouter>
);