const read = (k, d) => {
  // Vite
  if (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env[k] !== undefined)
    return import.meta.env[k];
  // CRA
  if (typeof process !== 'undefined' && process.env && process.env[k] !== undefined)
    return process.env[k];
  // Window inject / fallback
  if (typeof window !== 'undefined' && window.__ENV__ && window.__ENV__[k] !== undefined)
    return window.__ENV__[k];
  return d;
};

// URL override (?haccp=1) и localStorage override для быстрых проверок
const url = (typeof window !== 'undefined' && new URLSearchParams(window.location.search)) || null;
const q = url ? url.get('haccp') : null;
const ls = (typeof window !== 'undefined' && window.localStorage && window.localStorage.getItem('VITE_FEATURE_HACCP')) || null;

const rawHaccp =
  q ?? ls ?? read('VITE_FEATURE_HACCP', read('REACT_APP_FEATURE_HACCP', 'false'));

export const FEATURE_HACCP = String(rawHaccp) === 'true';
export const STRICT_MODE   = String(read('VITE_STRICT_MODE',   read('REACT_APP_STRICT_MODE',   'true')))  === 'true';
export const PRINT_GOST    = String(read('VITE_PRINT_GOST',    read('REACT_APP_PRINT_GOST',    'true')))  === 'true';

// отладочный лог один раз на старте
if (typeof window !== 'undefined') {
  console.info('[FF] FEATURE_HACCP=', FEATURE_HACCP, {
    VITE: import.meta?.env?.VITE_FEATURE_HACCP,
    CRA:  process?.env?.REACT_APP_FEATURE_HACCP,
    url:  q, ls
  });
}