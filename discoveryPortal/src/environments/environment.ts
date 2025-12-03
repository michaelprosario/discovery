/**
 * Default Environment Configuration
 * This file is replaced during build based on the target environment
 * - For development: replaced with environment.development.ts
 * - For production: replaced with environment.production.ts
 */
export const environment = {
  production: false,
  apiUrl: '/api',  // Will use proxy configuration to avoid CORS
  firebase: {
    apiKey: 'YOUR_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_PROJECT_ID.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
