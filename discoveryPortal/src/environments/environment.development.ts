/**
 * Development Environment Configuration
 * Uses proxy configuration (proxy.conf.json) to avoid CORS issues
 * All requests to /api will be proxied to the backend server
 */
export const environment = {
  production: false,
  apiUrl: '/api'  // Will use proxy configuration to avoid CORS
};
