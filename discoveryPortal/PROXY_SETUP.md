# Proxy Configuration Guide

## Overview
This document explains how the Angular application connects to the Python API server and avoids CORS issues.

## How It Works

### Development Environment
In development mode, the Angular dev server uses a proxy configuration to forward API requests to the backend server:

1. **Angular requests** go to `/api/*` (relative URL)
2. **Proxy intercepts** these requests (configured in `proxy.conf.json`)
3. **Proxy forwards** to `https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev`
4. **Response** comes back through the proxy to Angular

This avoids CORS issues because from the browser's perspective, all requests are to the same origin (the Angular dev server).

### Production Environment
In production, the application directly connects to the API server URL without a proxy.

## Configuration Files

### 1. proxy.conf.json
```json
{
  "/api": {
    "target": "https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev",
    "secure": true,
    "changeOrigin": true,
    "logLevel": "debug",
    "pathRewrite": {
      "^/api": ""
    }
  }
}
```

- **target**: The Python API server URL
- **secure**: Use HTTPS
- **changeOrigin**: Changes the origin header to match the target
- **pathRewrite**: Removes `/api` prefix before forwarding (e.g., `/api/notebooks` → `/notebooks`)

### 2. Environment Files

#### environment.development.ts
```typescript
export const environment = {
  production: false,
  apiUrl: '/api'  // Uses proxy
};
```

#### environment.production.ts
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev'
};
```

### 3. angular.json
The serve configuration already includes:
```json
"serve": {
  "options": {
    "proxyConfig": "proxy.conf.json"
  }
}
```

## Usage

### Starting the Development Server
```bash
npm start
```
or
```bash
ng serve
```

The proxy will automatically be loaded and API requests will be forwarded.

### Changing the API Server URL

1. **For Development**: Update the `target` in `proxy.conf.json`
2. **For Production**: Update `apiUrl` in `src/environments/environment.production.ts`

### Testing the Proxy

You can verify the proxy is working by:
1. Open browser DevTools → Network tab
2. Make an API request from the Angular app
3. Check the request URL - it should show `/api/...` (not the full backend URL)
4. Check the response - it should come from the backend server

### Troubleshooting

#### CORS Errors
If you still see CORS errors:
- Ensure `npm start` or `ng serve` is running (not just a build)
- Check that API requests use the `apiUrl` from environment
- Verify `proxy.conf.json` is correctly formatted
- Check browser console for proxy errors

#### Connection Refused
- Verify the Python API server is running
- Check the target URL in `proxy.conf.json` is correct
- Ensure the backend server is accessible from your development environment

#### Proxy Not Working
- Restart the Angular dev server after changing proxy configuration
- Check terminal output for proxy-related messages
- Verify `angular.json` includes the `proxyConfig` option

## API Configuration Service

The `ApiConfigService` allows runtime configuration of the API URL:

```typescript
import { ApiConfigService } from './infrastructure/config/api-config.service';

constructor(private apiConfig: ApiConfigService) {}

// Change API URL at runtime
this.apiConfig.setBaseUrl('https://new-api-url.com');
```

However, for most use cases, the environment-based configuration is sufficient.
