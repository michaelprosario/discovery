/**
 * Production Environment Configuration
 * Direct connection to the API server
 */
export const environment = {
  production: true,
  apiUrl: '/',  // For Firebase Hosting with Cloud Run backend
  firebase: {
    apiKey: 'YOUR_PROD_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_PROJECT_ID.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
