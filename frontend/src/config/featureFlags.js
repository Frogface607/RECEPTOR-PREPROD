const read = (k, d) => {
  if (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env[k] !== undefined) {
    return import.meta.env[k];
  }
  if (typeof process !== 'undefined' && process.env && process.env[k] !== undefined) {
    return process.env[k];
  }
  if (typeof window !== 'undefined' && window.__ENV__ && window.__ENV__[k] !== undefined) {
    return window.__ENV__[k];
  }
  return d;
};

const url = (typeof window !== 'undefined' && new URLSearchParams(window.location.search)) || null;
const q = url ? url.get('haccp') : null;
const ls = (typeof window !== 'undefined' && window.localStorage && window.localStorage.getItem('VITE_FEATURE_HACCP')) || null;

const rawHaccp = q || ls || read('VITE_FEATURE_HACCP', read('REACT_APP_FEATURE_HACCP', 'false'));

export const FEATURE_HACCP = String(rawHaccp) === 'true';
export const STRICT_MODE   = String(read('VITE_STRICT_MODE',   read('REACT_APP_STRICT_MODE',   'true')))  === 'true';
export const PRINT_GOST    = String(read('VITE_PRINT_GOST',    read('REACT_APP_PRINT_GOST',    'true')))  === 'true';

if (typeof window !== 'undefined') {
  console.info('[FF] FEATURE_HACCP=', FEATURE_HACCP, {
    VITE: (typeof import !== 'undefined' && import.meta && import.meta.env) ? import.meta.env.VITE_FEATURE_HACCP : undefined,
    CRA:  (typeof process !== 'undefined' && process.env) ? process.env.REACT_APP_FEATURE_HACCP : undefined,
    url:  q, 
    ls: ls
  });
}