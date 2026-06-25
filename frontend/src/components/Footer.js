import React from 'react';
import { Link } from 'react-router-dom';
import './../css/Footer.css';

export default function Footer() {
  return (
    <footer className="footer bg-light text-center text-sm-start">
      <div className="container py-4">
        <div className="row">

          <div className="col-sm-6 mb-3 mb-sm-0">
            <h5>CryptoBank</h5>
            <p className="text-muted small">
              Securely manage your crypto assets with ease.
            </p>
          </div>

          <div className="col-sm-3">
            <h6>Links</h6>
            <ul className="list-unstyled footer-social">
              <li><a href="https://country.db.com/uk/index?language_id=1&kid=uk.redirect-en.shortcut" aria-label="Twitter">Main Website</a></li>
              <li><a href="https://github.com/cnedd11/Crypto-Bank-App/tree/main" aria-label="GitHub">GitHub</a></li>
            </ul>
          </div>

        </div>

        <hr />

        <div className="text-center small">
          © {new Date().getFullYear()} Deutsche Bank. All rights reserved.
        </div>
      </div>
    </footer>
  );
}