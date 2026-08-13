/* ============================================================
   PASTE YOUR FIREBASE KEYS HERE  (free Spark plan is enough)
   Console: https://console.firebase.google.com
   Project settings (gear) → Your apps → </ > Web → config
   ============================================================ */
window.FIREBASE_CONFIG = {
  apiKey: '',
  authDomain: '',
  projectId: '',
  storageBucket: '',
  messagingSenderId: '',
  appId: '',
  /* This Gmail becomes Admin on first sign-up */
  adminEmail: '',
};

window.firebaseReady = function () {
  const c = window.FIREBASE_CONFIG || {};
  return !!(c.apiKey && c.projectId && window.firebase);
};
