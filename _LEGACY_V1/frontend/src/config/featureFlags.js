const read = (k, d) => {
  try {
    if (import.meta && import.meta.env && import.meta.env[k] !== undefined) {
      return import.meta.env[k];
    }
  } catch (e) {}
  
  try {
    if (process && process.env && process.env[k] !== undefined) {
      return process.env[k];
    }
  } catch (e) {}
  
  try {
    if (window && window.__ENV__ && window.__ENV__[k] !== undefined) {
      return window.__ENV__[k];
    }
  } catch (e) {}
  
  return d;
};

let url = null;
let q = null;
let ls = null;

try {
  if (typeof window !== 'undefined') {
    url = new URLSearchParams(window.location.search);
    q = url.get('haccp');
    ls = window.localStorage.getItem('VITE_FEATURE_HACCP');
  }
} catch (e) {}

const rawHaccp = q || ls || read('VITE_FEATURE_HACCP', read('REACT_APP_FEATURE_HACCP', 'false'));

export const FEATURE_HACCP = String(rawHaccp) === 'true';
export const STRICT_MODE = String(read('VITE_STRICT_MODE', read('REACT_APP_STRICT_MODE', 'true'))) === 'true';
export const PRINT_GOST = String(read('VITE_PRINT_GOST', read('REACT_APP_PRINT_GOST', 'true'))) === 'true';
export const FORCE_TECHCARD_V2 = String(read('VITE_FORCE_TECHCARD_V2', read('REACT_APP_FORCE_TECHCARD_V2', 'true'))) === 'true';

try {
  if (typeof window !== 'undefined') {
    console.info('[FF] FEATURE_HACCP=', FEATURE_HACCP, {
      VITE: read('VITE_FEATURE_HACCP', undefined),
      CRA: read('REACT_APP_FEATURE_HACCP', undefined),
      url: q, 
      ls: ls
    });
    console.info('[FF] FORCE_TECHCARD_V2=', FORCE_TECHCARD_V2, {
      VITE: read('VITE_FORCE_TECHCARD_V2', undefined),
      CRA: read('REACT_APP_FORCE_TECHCARD_V2', undefined)
    });
  }
} catch (e) {}