/**
 * RECEPTOR Brand System
 * Centralized design tokens for consistent visual identity.
 *
 * Primary: Emerald green — growth, freshness, restaurant industry
 * Neutral: Gray scale — professional, dark-mode native
 * Accents: Blue (analytics), Purple (insights), Amber (warnings)
 */

export const BRAND = {
  name: 'RECEPTOR',
  tagline: 'AI-копилот для ресторанного бизнеса',
  taglineEn: 'AI Restaurant Co-Pilot',

  colors: {
    // Primary brand
    primary: {
      50:  '#ecfdf5',
      100: '#d1fae5',
      200: '#a7f3d0',
      300: '#6ee7b7',
      400: '#34d399',
      500: '#10b981', // Main brand color
      600: '#059669', // Buttons, accents
      700: '#047857',
      800: '#065f46',
      900: '#064e3b',
    },
    // Neutral (dark theme base)
    neutral: {
      50:  '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937', // Card backgrounds
      900: '#111827', // App background
      950: '#030712', // Sidebar
    },
    // Semantic
    success: '#10b981',
    error:   '#ef4444',
    warning: '#f59e0b',
    info:    '#3b82f6',

    // Feature accents
    analytics: '#3b82f6', // Blue — BI Dashboard
    insights:  '#8b5cf6', // Purple — AI insights
    iiko:      '#06b6d4', // Cyan — iiko integration
  },

  // Chart palette (for recharts, pie charts etc.)
  chartColors: [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
  ],

  typography: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif",
    fontMono: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  },

  spacing: {
    sidebarWidth: '16rem',    // 256px
    headerHeight: '3.5rem',   // 56px
    maxContentWidth: '48rem', // 768px — chat area
  },

  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },
};

// Gradient presets used across the app
export const GRADIENTS = {
  primary:   'bg-gradient-to-r from-emerald-600 to-emerald-700',
  analytics: 'bg-gradient-to-r from-blue-600 to-blue-700',
  insights:  'bg-gradient-to-r from-purple-600 to-purple-700',
  card:      'bg-gradient-to-br from-gray-800 to-gray-900',
  glow: {
    primary:   'shadow-lg shadow-emerald-500/20',
    analytics: 'shadow-lg shadow-blue-500/20',
    insights:  'shadow-lg shadow-purple-500/20',
  },
};
