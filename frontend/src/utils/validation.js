// src/utils/validation.js
// Shared client-side validation helpers used across Login, Register, and Customers.
// These mirror the server-side rules so errors are caught early without a round-trip.

/** Basic email format check: must contain exactly one @, with text on both sides. */
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Phone: optional field; allows digits, spaces, +, -, (, ) — up to 30 chars. */
export const PHONE_RE = /^[\d\s+\-().]{1,30}$/;

/**
 * OWASP A07: Password complexity rule that mirrors the server-side check.
 * Min 8 chars, at least one uppercase, lowercase, digit, and special character.
 */
export const PASSWORD_RE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/;
