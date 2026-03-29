/**
 * Shared application configuration.
 * All env-dependent values live here — no hardcoded URLs in components.
 */

// API URL — set REACT_APP_API_URL in your environment / Vercel settings
export const API_URL = process.env.REACT_APP_API_URL || '/api';

// Temporary user ID (replace with real auth later)
export const USER_ID = 'default_user';
