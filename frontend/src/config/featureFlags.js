const read = (k, d) => {
  if (typeof import !== 'undefined' && import.meta?.env?.[k]) {
    return import.meta.env[k];
  }
  if (typeof process !== 'undefined' && process.env?.[k]) {
    return process.env[k];
  }
  return d;
};

export const FEATURE_HACCP = String(read('VITE_FEATURE_HACCP', 'false')) === 'true';
export const STRICT_MODE   = String(read('VITE_STRICT_MODE',   'true'))  === 'true';
export const PRINT_GOST    = String(read('VITE_PRINT_GOST',    'true'))  === 'true';