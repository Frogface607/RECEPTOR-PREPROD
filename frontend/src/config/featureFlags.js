const read = (k, d) => {
  // Try different environment variable prefixes
  const envValue = 
    (typeof process !== 'undefined' && process.env && process.env[`REACT_APP_${k.replace('VITE_', '')}`]) ||
    (typeof process !== 'undefined' && process.env && process.env[k]) ||
    (typeof window !== 'undefined' && import.meta && import.meta.env && import.meta.env[k]) ||
    d;
  
  // Debug logging
  console.log(`FeatureFlag ${k}: value="${envValue}", default="${d}"`);
  
  return envValue;
};

export const FEATURE_HACCP = String(read('VITE_FEATURE_HACCP', 'false')) === 'true';
export const STRICT_MODE   = String(read('VITE_STRICT_MODE',   'true'))  === 'true';
export const PRINT_GOST    = String(read('VITE_PRINT_GOST',    'true'))  === 'true';

// Debug exports
console.log('Feature flags loaded:', { FEATURE_HACCP, STRICT_MODE, PRINT_GOST });