/**
 * Default Environment Configuration
 * This file is replaced during build based on the target environment
 * - For development: replaced with environment.development.ts
 * - For production: replaced with environment.production.ts
 */
export const environment = {
  production: false,
  apiUrl: '/api'  // Will use proxy configuration to avoid CORS
};
