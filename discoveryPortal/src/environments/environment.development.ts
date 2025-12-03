/**
 * Development Environment Configuration
 * Uses proxy configuration (proxy.conf.json) to avoid CORS issues
 * All requests to /api will be proxied to the backend server
 */
export const environment = {
  production: false,
  apiUrl: '/api',  // Will use proxy configuration to avoid CORS
  firebase: {
    apiKey: "AIzaSyBDX2vLdIKYwfcQB_ndNNkp7s55gX-SoNs",
    authDomain: "discovery-notebooks.firebaseapp.com",
    projectId: "discovery-notebooks",
    storageBucket: "discovery-notebooks.firebasestorage.app",
    messagingSenderId: "445271003640",
    appId: "1:445271003640:web:00a2f035dc9a2a782cc60d"
  }
};
