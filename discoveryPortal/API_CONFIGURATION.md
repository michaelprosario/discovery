# API Configuration Guide

## Overview

The Angular application is configured to work with the Python API backend. The configuration handles CORS issues and provides environment-specific settings.

## Configuration Files

### Environment Files

- **`src/environments/environment.ts`** - Base environment configuration
- **`src/environments/environment.development.ts`** - Development environment
- **`src/environments/environment.production.ts`** - Production environment

### Development Environment

```typescript
apiUrl: '/api'
```

In development, all API requests use the `/api` prefix which is proxied to the backend server to avoid CORS issues.

### Production Environment

```typescript
apiUrl: 'https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev'
```

In production, requests go directly to the Python API server.

## Proxy Configuration

The `proxy.conf.json` file handles request proxying in development:

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

### How it works:

1. Angular app makes request to `/api/notebooks`
2. Proxy intercepts and rewrites to `https://musical-zebra-pj6xv5g7vwh7wxw-8000.app.github.dev/notebooks`
3. Response is sent back to Angular app
4. CORS is avoided because the request appears to be same-origin

## Usage

### Running in Development

```bash
cd discoveryPortal
npm start
```

The proxy configuration is automatically loaded. All HTTP requests will be proxied to the Python backend.

### Building for Production

```bash
npm run build
```

The production environment configuration will be used, pointing directly to the API server.

## Changing the API Server URL

### For Development

Edit `proxy.conf.json` and update the `target` property:

```json
{
  "/api": {
    "target": "https://your-new-api-url.com",
    ...
  }
}
```

### For Production

Edit `src/environments/environment.production.ts` and update the `apiUrl` property:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-new-api-url.com'
};
```

## HTTP Client Service

The `HttpClientService` automatically uses the environment configuration through the `ApiConfigService`. All API calls are automatically prefixed with the correct base URL.

### Example Usage

```typescript
// In a service
constructor(private httpClient: HttpClientService) {}

getNotebooks(): Observable<Notebook[]> {
  // Will call /api/notebooks in dev, or https://musical-zebra.../notebooks in prod
  return this.httpClient.get<Notebook[]>('notebooks');
}
```

## Troubleshooting

### CORS Errors

If you see CORS errors in development:

1. Verify the proxy configuration is correct in `proxy.conf.json`
2. Restart the Angular dev server: `npm start`
3. Check that requests are being proxied (check browser Network tab)
4. Verify the Python backend allows the request origin

### API URL Not Updating

1. Clear browser cache
2. Restart the Angular dev server
3. Check that the correct environment file is being used
4. Verify `angular.json` has the correct `fileReplacements` configuration

### Proxy Not Working

1. Check `angular.json` has `proxyConfig` in the serve options
2. Verify proxy.conf.json syntax is valid JSON
3. Check the Angular CLI output for proxy errors
4. Use `logLevel: "debug"` in proxy.conf.json to see detailed logs
